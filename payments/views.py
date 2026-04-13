import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from companies.models import Company
from jobs.models import Job
from jobs.tasks import send_job_alerts_task

from .models import Payment
from .tranzak_service import (
    TranzakServiceError,
    create_payment_request,
    fetch_request_details,
)


logger = logging.getLogger(__name__)


def _tier_to_plan(tier):
    return 'basic' if tier == Payment.BASIC_TIER else 'featured'


def _tier_description(tier):
    if tier == Payment.BASIC_TIER:
        return 'CameroonTechJobs - Basic Job Posting'
    return 'CameroonTechJobs - Premium Job Posting'


def _payment_urls():
    base_url = settings.SITE_URL.rstrip('/')
    return {
        'returnUrl': f'{base_url}{reverse("payment_success")}',
        'cancelUrl': f'{base_url}{reverse("payment_cancel")}',
        'callbackUrl': f'{base_url}{reverse("payment_webhook")}',
    }


def _resolve_job_for_payment(company, tier, job_id=None):
    if job_id:
        return get_object_or_404(Job, pk=job_id, company=company)

    return (
        Job.objects.filter(
            company=company,
            status='pending',
            plan=_tier_to_plan(tier),
        )
        .order_by('-date_posted')
        .first()
    )


def _activate_job_from_payment(payment):
    if not payment.job:
        return

    job = payment.job
    job.status = 'active'
    job.is_featured = payment.tier == Payment.PREMIUM_TIER
    duration_days = 60 if payment.tier == Payment.PREMIUM_TIER else 30
    job.date_expires = timezone.now() + timezone.timedelta(days=duration_days)
    job.save(update_fields=['status', 'is_featured', 'date_expires'])

    try:
        send_job_alerts_task.delay(job.pk)
    except Exception:
        logger.exception('Unable to queue job alert notifications for job %s.', job.pk)

    try:
        send_mail(
            'Your Job Posting is Now Active',
            (
                f'Hi {job.company.company_name},\n\n'
                f'Your payment for "{job.title}" was confirmed and the listing is now active.\n\n'
                f'Plan: {job.get_plan_display()}\n'
                f'Expires on: {job.date_expires:%d %b %Y}\n\n'
                'Best regards,\nCameroonTechJobs Team'
            ),
            settings.DEFAULT_FROM_EMAIL,
            [job.company.email],
            fail_silently=True,
        )
    except Exception:
        logger.exception('Unable to send payment confirmation email for job %s.', job.pk)


def _update_payment_from_status(payment, status):
    normalized = (status or '').upper()
    valid_statuses = {
        Payment.STATUS_PENDING,
        Payment.STATUS_SUCCESSFUL,
        Payment.STATUS_FAILED,
        Payment.STATUS_CANCELLED,
    }
    payment.status = normalized if normalized in valid_statuses else Payment.STATUS_PENDING
    payment.save(update_fields=['status', 'updated_at'])

    if payment.status == Payment.STATUS_SUCCESSFUL:
        _activate_job_from_payment(payment)


@login_required
@require_POST
def initiate_payment(request):
    if not isinstance(request.user, Company):
        messages.error(request, 'Only company accounts can make payments.')
        return redirect('seeker_dashboard')

    try:
        tier = int(request.POST.get('tier', '0'))
    except ValueError:
        tier = 0

    if tier not in {Payment.BASIC_TIER, Payment.PREMIUM_TIER}:
        messages.error(request, 'Please choose a valid payment tier.')
        return redirect('pricing')

    job_id = request.POST.get('job_id')
    job = _resolve_job_for_payment(request.user, tier, job_id)
    if not job:
        messages.error(request, 'Create a pending paid job first before starting payment.')
        return redirect('post_job')

    mch_transaction_ref = uuid.uuid4().hex
    payload = {
        'amount': tier,
        'currencyCode': 'XAF',
        'description': _tier_description(tier),
        'mchTransactionRef': mch_transaction_ref,
        **_payment_urls(),
    }

    try:
        response_data = create_payment_request(payload)
    except TranzakServiceError as exc:
        messages.error(request, str(exc))
        return redirect('pricing')

    data = response_data.get('data', {})
    payment_auth_url = data.get('links', {}).get('paymentAuthUrl')
    request_id = data.get('requestId')

    if not payment_auth_url or not request_id:
        messages.error(request, 'Tranzak did not return a payment authorization link.')
        return redirect('pricing')

    payment = Payment.objects.create(
        company=request.user,
        job=job,
        tier=tier,
        amount=tier,
        currency='XAF',
        status=Payment.STATUS_PENDING,
        tranzak_request_id=request_id,
        mch_transaction_ref=mch_transaction_ref,
    )

    request.session['latest_payment_id'] = payment.id
    return redirect(payment_auth_url)


@csrf_exempt
@require_POST
def webhook(request):
    try:
        payload = request.POST.dict() if request.POST else None
        if not payload:
            import json

            payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        logger.exception('Invalid Tranzak webhook payload.')
        return HttpResponse(status=200)

    auth_key = payload.get('authKey')
    resource = payload.get('resource') or {}
    request_id = resource.get('requestId') or payload.get('resourceId')
    status = resource.get('status')

    if settings.TRANZAK_WEBHOOK_KEY and auth_key != settings.TRANZAK_WEBHOOK_KEY:
        logger.warning('Ignored Tranzak webhook with invalid authKey for request %s.', request_id)
        return HttpResponse(status=200)

    if payload.get('eventType') != 'REQUEST.COMPLETED' or not request_id:
        logger.info('Ignored Tranzak webhook event %s.', payload.get('eventType'))
        return HttpResponse(status=200)

    payment = Payment.objects.filter(tranzak_request_id=request_id).select_related('job', 'company').first()
    if not payment:
        logger.warning('No payment record found for Tranzak request %s.', request_id)
        return HttpResponse(status=200)

    _update_payment_from_status(payment, status)
    return HttpResponse(status=200)


@login_required
@require_GET
def check_payment_status(request, request_id):
    payment = get_object_or_404(
        Payment.objects.select_related('job', 'company'),
        tranzak_request_id=request_id,
        company=request.user,
    )

    try:
        response_data = fetch_request_details(request_id)
    except TranzakServiceError as exc:
        messages.error(request, str(exc))
        return redirect('payment_success')

    status = response_data.get('data', {}).get('status')
    _update_payment_from_status(payment, status)

    if payment.status == Payment.STATUS_SUCCESSFUL:
        messages.success(request, 'Payment confirmed and your listing is now active.')
        return redirect('dashboard')

    if payment.status == Payment.STATUS_FAILED:
        messages.error(request, 'Payment failed. Please try again.')
        return redirect('payment_cancel')

    if payment.status == Payment.STATUS_CANCELLED:
        messages.info(request, 'Payment was cancelled.')
        return redirect('payment_cancel')

    messages.info(request, 'Payment is still pending. Please check again in a moment.')
    return redirect('payment_success')


@login_required
def pricing(request):
    job_id = request.GET.get('job_id')
    selected_tier = request.GET.get('tier')
    job = None

    if isinstance(request.user, Company) and job_id:
        job = Job.objects.filter(pk=job_id, company=request.user).first()

    return render(
        request,
        'payments/pricing.html',
        {
            'job': job,
            'job_id': job_id,
            'selected_tier': selected_tier,
            'basic_price': Payment.BASIC_TIER,
            'premium_price': Payment.PREMIUM_TIER,
        },
    )


def payment_success(request):
    payment = None
    payment_id = request.session.get('latest_payment_id')
    if request.user.is_authenticated and payment_id:
        payment = Payment.objects.filter(
            id=payment_id,
            company=request.user,
        ).select_related('job').first()

    return render(request, 'payments/success.html', {'payment': payment})


def payment_cancel(request):
    payment = None
    payment_id = request.session.get('latest_payment_id')
    if request.user.is_authenticated and payment_id:
        payment = Payment.objects.filter(
            id=payment_id,
            company=request.user,
        ).select_related('job').first()

    return render(request, 'payments/cancel.html', {'payment': payment})
