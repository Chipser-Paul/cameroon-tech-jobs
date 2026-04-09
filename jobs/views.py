from datetime import datetime
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import stripe

from .forms import JobForm
from .models import ApplicationInterview, ApplicationMessage, Job, Category, Notification, TechStack, JobApplication, Payment
from .notifications import notify_company, notify_seeker
from .tasks import send_job_alerts_task
from companies.models import Company
from seekers.models import Seeker

logger = logging.getLogger(__name__)


def job_list(request):
    cache_key = f'job_list_{request.GET.urlencode()}'
    cached_data = None
    
    try:
        cached_data = cache.get(cache_key)
    except Exception as exc:
        logger.warning(f'Cache GET failed: {exc}')
    
    if cached_data:
        return render(request, 'jobs/job_list.html', cached_data)

    jobs = Job.objects.filter(status='active').select_related('company', 'category').prefetch_related('tech_stacks')
    categories = Category.objects.all()
    tech_stacks = TechStack.objects.all()

    q = request.GET.get('q')
    if q:
        jobs = jobs.filter(title__icontains=q) | jobs.filter(description__icontains=q)

    category = request.GET.get('category')
    if category:
        jobs = jobs.filter(category__slug=category)

    location = request.GET.get('location')
    if location:
        jobs = jobs.filter(location=location)

    job_type = request.GET.get('job_type')
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    tech = request.GET.get('tech')
    if tech:
        jobs = jobs.filter(tech_stacks__name__icontains=tech)

    experience = request.GET.get('experience')
    if experience:
        jobs = jobs.filter(experience_level=experience)

    jobs = jobs.distinct().order_by('-is_featured', '-date_posted')
    paginator = Paginator(jobs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'jobs': page_obj,
        'categories': categories,
        'tech_stacks': tech_stacks,
        'total_jobs': jobs.count(),
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }

    try:
        cache.set(cache_key, context, 300)  # Cache for 5 minutes
    except Exception as exc:
        logger.warning(f'Cache SET failed: {exc}')
    
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, status='active')
    job.views_count += 1
    job.save()
    has_applied = False
    can_apply = False

    if request.user.is_authenticated and isinstance(request.user, Seeker):
        can_apply = True
        has_applied = JobApplication.objects.filter(job=job, seeker=request.user).exists()

    related_jobs = Job.objects.filter(
        status='active',
        category=job.category
    ).exclude(pk=pk)[:3]
    context = {
        'job': job,
        'related_jobs': related_jobs,
        'has_applied': has_applied,
        'can_apply': can_apply,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def post_job(request):
    if not isinstance(request.user, Company):
        messages.error(request, 'Only company accounts can post jobs.')
        return redirect('seeker_dashboard')

    company = request.user
    is_free = not company.has_used_free_listing

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company

            if is_free:
                job.plan = 'free'
                job.status = 'active' if company.is_verified else 'pending'
                company.has_used_free_listing = True
                company.save()
                job.save()
                form.save_m2m()
                form.save_custom_tech(job)

                if job.status == 'active':
                    send_job_alerts_task.delay(job.pk)
                    messages.success(request, '🎉 Your free job listing is now active and job alerts are being sent.')
                else:
                    messages.success(request, '🎉 Your free job listing has been submitted and will be reviewed shortly.')
                return redirect('dashboard')

            plan = form.cleaned_data['plan']
            if plan == 'basic':
                amount = 5000
            elif plan == 'featured':
                amount = 15000
            else:
                messages.error(request, 'Please select a valid plan.')
                return redirect('post_job')

            job.plan = plan
            job.status = 'pending'
            job.save()
            form.save_m2m()
            form.save_custom_tech(job)

            # Create Stripe PaymentIntent
            stripe.api_key = settings.STRIPE_SECRET_KEY
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='xaf',
                metadata={'job_id': str(job.id)},
            )

            # Save Payment record
            Payment.objects.create(
                job=job,
                stripe_payment_intent_id=intent.id,
                client_secret=intent.client_secret,
                amount=amount,
                status='pending'
            )

            messages.success(request, 'Job submitted! Complete payment to activate the listing.')
            return redirect('payment', payment_intent_id=intent.id)
    else:
        form = JobForm()

    # Hide plan field for free listings
    if is_free:
        form.fields['plan'].required = False
        form.fields['plan'].initial = 'free'

    context = {
        'form': form,
        'is_free': is_free,
    }
    return render(request, 'jobs/post_job.html', context)


@login_required
def payment(request, payment_intent_id):
    if not isinstance(request.user, Company):
        messages.error(request, 'Access denied.')
        return redirect('seeker_dashboard')

    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id, job__company=request.user)
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('dashboard')

    context = {
        'payment': payment,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': payment.client_secret,
    }
    return render(request, 'jobs/payment.html', context)


@login_required
def payment_success(request, payment_intent_id):
    if not isinstance(request.user, Company):
        messages.error(request, 'Access denied.')
        return redirect('seeker_dashboard')

    try:
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id, job__company=request.user)
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('dashboard')

    # Confirm payment with Stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)

    if intent.status == 'succeeded':
        payment.status = 'completed'
        payment.save()
        payment.job.status = 'active'
        payment.job.save()
        send_job_alerts_task.delay(payment.job.pk)
        messages.success(request, 'Payment successful! Your job is now active.')
    else:
        payment.status = 'failed'
        payment.save()
        messages.error(request, 'Payment failed. Please try again.')

    return redirect('dashboard')


@login_required
def apply_job(request, pk):
    if request.method != 'POST':
        return redirect('job_detail', pk=pk)

    if not isinstance(request.user, Seeker):
        messages.error(request, 'Only job seeker accounts can apply for jobs.')
        return redirect('seeker_login')

    job = get_object_or_404(Job, pk=pk, status='active')

    existing_application = JobApplication.objects.filter(job=job, seeker=request.user).first()
    if existing_application:
        messages.info(
            request,
            f'You already applied for this job. Current status: {existing_application.get_status_display()}.',
        )
        return redirect('job_detail', pk=job.pk)

    application = JobApplication.objects.create(
        job=job,
        seeker=request.user,
        cover_note=request.POST.get('cover_note', '').strip(),
    )
    notify_company(
        job.company,
        'New job application received',
        f'{request.user.full_name} applied for {job.title}.',
        link=f'/applications/{application.pk}/conversation/',
    )
    messages.success(request, 'Application submitted successfully. The employer can now review your profile.')
    return redirect('job_detail', pk=job.pk)


@login_required
def job_applicants(request, pk):
    if not isinstance(request.user, Company):
        messages.error(request, 'Only company accounts can view applicants.')
        return redirect('seeker_dashboard')

    job = get_object_or_404(
        Job.objects.select_related('company', 'category').prefetch_related(
            'applications__seeker__skills',
        ),
        pk=pk,
        company=request.user,
    )
    applications = job.applications.select_related('seeker').all()

    context = {
        'job': job,
        'applications': applications,
        'total_applications': applications.count(),
    }
    return render(request, 'jobs/job_applicants.html', context)


@login_required
def update_application_status(request, pk):
    if request.method != 'POST':
        return redirect('dashboard')

    if not isinstance(request.user, Company):
        messages.error(request, 'Only company accounts can manage applications.')
        return redirect('seeker_dashboard')

    application = get_object_or_404(
        JobApplication.objects.select_related('job'),
        pk=pk,
        job__company=request.user,
    )
    new_status = request.POST.get('status', '').strip()
    valid_statuses = {choice[0] for choice in JobApplication.STATUS_CHOICES}

    if new_status not in valid_statuses:
        messages.error(request, 'Invalid application status selected.')
        return redirect('job_applicants', pk=application.job.pk)

    application.status = new_status
    application.save(update_fields=['status'])
    notify_seeker(
        application.seeker,
        'Application status updated',
        f'Your application for {application.job.title} is now marked as {application.get_status_display()}.',
        link=f'/applications/{application.pk}/conversation/',
    )
    messages.success(request, 'Application status updated successfully.')
    return redirect('job_applicants', pk=application.job.pk)


@login_required
def application_conversation(request, pk):
    application = get_object_or_404(
        JobApplication.objects.select_related('job', 'job__company', 'seeker').prefetch_related('messages', 'interviews'),
        pk=pk,
    )

    is_company = isinstance(request.user, Company) and application.job.company_id == request.user.id
    is_seeker = isinstance(request.user, Seeker) and application.seeker_id == request.user.id

    if not (is_company or is_seeker):
        messages.error(request, 'You do not have permission to access this conversation.')
        return redirect('home')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            message_kwargs = {
                'application': application,
                'body': body,
            }
            if is_company:
                message_kwargs['sender_company'] = request.user
            else:
                message_kwargs['sender_seeker'] = request.user
            ApplicationMessage.objects.create(**message_kwargs)
            if is_company:
                notify_seeker(
                    application.seeker,
                    'New message from employer',
                    f'{application.job.company.company_name} sent you a new message about {application.job.title}.',
                    link=f'/applications/{application.pk}/conversation/',
                )
            else:
                notify_company(
                    application.job.company,
                    'New message from candidate',
                    f'{application.seeker.full_name} sent a new message about {application.job.title}.',
                    link=f'/applications/{application.pk}/conversation/',
                )
            messages.success(request, 'Message sent successfully.')
            return redirect('application_conversation', pk=application.pk)
        messages.error(request, 'Please enter a message before sending.')

    context = {
        'application': application,
        'conversation_messages': application.messages.select_related('sender_company', 'sender_seeker').all(),
        'interviews': application.interviews.all(),
        'is_company_participant': is_company,
        'is_seeker_participant': is_seeker,
    }
    return render(request, 'jobs/application_conversation.html', context)


@login_required
def schedule_interview(request, pk):
    if request.method != 'POST':
        return redirect('dashboard')

    application = get_object_or_404(
        JobApplication.objects.select_related('job', 'job__company', 'seeker'),
        pk=pk,
    )

    if not isinstance(request.user, Company) or application.job.company_id != request.user.id:
        messages.error(request, 'Only the hiring company can schedule interviews for this application.')
        return redirect('home')

    scheduled_for_raw = request.POST.get('scheduled_for', '').strip()
    meeting_type = request.POST.get('meeting_type', 'video').strip()
    meeting_link = request.POST.get('meeting_link', '').strip()
    location = request.POST.get('location', '').strip()
    notes = request.POST.get('notes', '').strip()

    scheduled_for = parse_datetime(scheduled_for_raw)
    if scheduled_for is None:
        messages.error(request, 'Please provide a valid interview date and time.')
        return redirect('application_conversation', pk=application.pk)

    if timezone.is_naive(scheduled_for):
        scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())

    if scheduled_for <= timezone.now():
        messages.error(request, 'Interview time must be in the future.')
        return redirect('application_conversation', pk=application.pk)

    if meeting_type == 'video' and not meeting_link:
        messages.error(request, 'Please add a meeting link for video interviews.')
        return redirect('application_conversation', pk=application.pk)

    if meeting_type == 'in_person' and not location:
        messages.error(request, 'Please add a location for in-person interviews.')
        return redirect('application_conversation', pk=application.pk)

    interview = ApplicationInterview.objects.create(
        application=application,
        scheduled_for=scheduled_for,
        meeting_type=meeting_type,
        meeting_link=meeting_link,
        location=location,
        notes=notes,
    )
    ApplicationMessage.objects.create(
        application=application,
        sender_company=request.user,
        body=(
            f'Interview invitation sent for {timezone.localtime(interview.scheduled_for).strftime("%b %d, %Y at %I:%M %p")} '
            f'via {interview.get_meeting_type_display()}.'
        ),
    )
    notify_seeker(
        application.seeker,
        'New interview invitation',
        f'You have been invited to an interview for {application.job.title}.',
        link=f'/applications/{application.pk}/conversation/',
    )
    messages.success(request, 'Interview invitation sent successfully.')
    return redirect('application_conversation', pk=application.pk)


@login_required
def respond_to_interview(request, pk):
    if request.method != 'POST':
        return redirect('home')

    interview = get_object_or_404(
        ApplicationInterview.objects.select_related('application', 'application__job', 'application__job__company', 'application__seeker'),
        pk=pk,
    )

    if not isinstance(request.user, Seeker) or interview.application.seeker_id != request.user.id:
        messages.error(request, 'Only the invited seeker can respond to this interview.')
        return redirect('home')

    decision = request.POST.get('decision', '').strip()
    if decision not in {'accepted', 'declined'}:
        messages.error(request, 'Invalid interview response.')
        return redirect('application_conversation', pk=interview.application.pk)

    interview.status = decision
    interview.save(update_fields=['status'])
    ApplicationMessage.objects.create(
        application=interview.application,
        sender_seeker=request.user,
        body=f'Interview invitation {interview.get_status_display().lower()}.',
    )
    notify_company(
        interview.application.job.company,
        'Interview response received',
        f'{request.user.full_name} {interview.get_status_display().lower()} the interview for {interview.application.job.title}.',
        link=f'/applications/{interview.application.pk}/conversation/',
    )
    messages.success(request, f'Interview invitation {interview.get_status_display().lower()}.')
    return redirect('application_conversation', pk=interview.application.pk)


@login_required
def notifications_list(request):
    user = request.user
    if isinstance(user, Company):
        notifications = user.notifications.all()
    elif isinstance(user, Seeker):
        notifications = user.notifications.all()
    else:
        notifications = Notification.objects.none()

    context = {
        'notifications': notifications,
    }
    return render(request, 'jobs/notifications.html', context)


@login_required
def mark_notification_read(request, pk):
    if request.method != 'POST':
        return redirect('notifications')

    user = request.user
    if isinstance(user, Company):
        notification = get_object_or_404(Notification, pk=pk, recipient_company=user)
    elif isinstance(user, Seeker):
        notification = get_object_or_404(Notification, pk=pk, recipient_seeker=user)
    else:
        return redirect('home')

    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.link or 'notifications')


@login_required
def mark_all_notifications_read(request):
    if request.method != 'POST':
        return redirect('notifications')

    user = request.user
    if isinstance(user, Company):
        user.notifications.filter(is_read=False).update(is_read=True)
    elif isinstance(user, Seeker):
        user.notifications.filter(is_read=False).update(is_read=True)

    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications')
