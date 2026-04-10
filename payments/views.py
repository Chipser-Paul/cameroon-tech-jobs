import json
import logging
import hmac
import hashlib
import os
import re
import requests
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from companies.models import Company
from jobs.models import Job
from .models import Payment

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, job_id):
    """Initiate a CamPay payment for a job posting"""
    if not isinstance(request.user, Company):
        messages.error(request, 'Only companies can make payments.')
        return redirect('dashboard')

    job = get_object_or_404(Job, pk=job_id, company=request.user)
    tier = request.GET.get('tier', 'basic')

    # Validate tier
    if tier not in ['basic', 'featured']:
        messages.error(request, 'Invalid tier selected.')
        return redirect('post_job')

    # Check if company has a phone number for payment
    if not request.user.phone or not request.user.phone.strip():
        messages.error(request, '📱 Please add your phone number (e.g., +237677777777 or 237677777777) to your company account. Payment will be sent to this MTN/Orange number.')
        return redirect('company_edit_profile')
    
    # Validate phone number format - accept both +237XXXXXXXXXX and 237XXXXXXXXXX
    phone = request.user.phone.strip()
    # Remove any spaces, dashes, or parentheses
    phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Check if it's in valid format (10 digits after 237, not 9)
    if re.match(r'^\+237\d{10}$', phone_clean):
        # Format: +237XXXXXXXXXX - remove the + for CamPay
        phone_final = phone_clean[1:]  # Remove the + sign
    elif re.match(r'^237\d{10}$', phone_clean):
        # Format: 237XXXXXXXXXX - already correct for CamPay
        phone_final = phone_clean
    else:
        messages.warning(request, '📱 Phone should be in format 237XXXXXXXXXX or +237XXXXXXXXXX (10 digits after 237). Please update your profile.')
        return redirect('company_edit_profile')

    # Determine amount based on tier
    amount = 5000 if tier == 'basic' else 15000

    # Get CamPay credentials
    campay_username = settings.CAMPAY_USERNAME
    campay_password = settings.CAMPAY_PASSWORD
    campay_token = settings.CAMPAY_TOKEN
    campay_base_url = settings.CAMPAY_BASE_URL

    if not all([campay_username, campay_password, campay_token, campay_base_url]):
        messages.error(request, 'Payment processing is not configured. Please contact support.')
        logger.error('CamPay credentials not configured')
        return redirect('post_job')

    try:
        # Call CamPay collect endpoint
        collect_url = f'{campay_base_url}/collect/'
        
        # Use the cleaned phone number (CamPay expects format without +)
        payload = {
            'username': campay_username,
            'password': campay_password,
            'phone': phone_final,  # Format: 237XXXXXXXXX (no +)
            'amount': amount,
            'description': f'Job posting: {job.title}',
            'external_reference': str(job.id),  # Reference back to job
        }
        
        # Log what we're sending for debugging
        logger.info(f'Initiating CamPay payment - Phone: {phone_final}, Amount: {amount}, Job: {job.id}')

        response = requests.post(
            collect_url,
            json=payload,
            headers={'Authorization': f'Token {campay_token}'},
            timeout=10
        )

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', 'Unknown error')
            error_code = error_data.get('error_code', '')
            logger.error(f'CamPay collect request failed ({error_code}): {error_msg}. Phone sent: {phone_final}')
            
            # Provide helpful error messages
            if 'phone' in error_msg.lower() or error_code == 'ER101':
                messages.error(request, '📱 The phone number format seems invalid to CamPay. Try using format like 237XXXXXXXXXX (10 digits after 237).')
            else:
                messages.error(request, f'Payment processing error: {error_msg}. Please try again.')
            return redirect('post_job')

        data = response.json()
        payment_url = data.get('payment_url')
        campay_reference = data.get('reference')

        if not payment_url or not campay_reference:
            logger.error(f'Invalid CamPay response: {data}')
            messages.error(request, 'Payment initiation failed. Please try again.')
            return redirect('post_job')

        # Save Payment record
        payment = Payment.objects.create(
            job=job,
            tier=tier,
            amount=Decimal(amount),
            campay_reference=campay_reference,
            status='pending'
        )

        # Redirect to CamPay payment URL
        return redirect(payment_url)

    except requests.exceptions.RequestException as e:
        logger.error(f'CamPay request error: {str(e)}')
        messages.error(request, 'Payment service temporarily unavailable. Please try again.')
        return redirect('post_job')
    except Exception as e:
        logger.error(f'Unexpected error in initiate_payment: {str(e)}')
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return redirect('post_job')


@csrf_exempt
@require_POST
def webhook(request):
    """Handle CamPay webhook callbacks"""
    try:
        # Get webhook key from settings
        webhook_key = settings.CAMPAY_WEBHOOK_KEY
        
        if not webhook_key:
            logger.error('CAMPAY_WEBHOOK_KEY not configured')
            return JsonResponse({'status': 'error', 'message': 'Webhook key not configured'}, status=400)

        # Get the raw body
        body = request.body
        
        # Get the signature from headers
        signature = request.headers.get('Signature', '')
        
        # Verify signature
        expected_signature = hmac.new(
            webhook_key.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f'Invalid webhook signature: {signature}')
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=403)

        # Parse payload
        data = json.loads(body)
        
        reference = data.get('reference')
        external_reference = data.get('external_reference')
        status = data.get('status')
        
        if not reference or not external_reference:
            logger.error(f'Missing required fields in webhook: {data}')
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        # Get payment record
        payment = get_object_or_404(Payment, campay_reference=reference)
        
        # Update payment status
        if status == 'success':
            payment.status = 'successful'
            payment.save()

            # Activate the job
            job = payment.job
            job.status = 'active'
            job.save()

            # Send confirmation email to company
            try:
                send_mail(
                    'Your Job Posting is Now Active',
                    f'Hi {job.company.company_name},\n\nYour job posting "{job.title}" has been successfully paid and is now active on CameroonTechJobs.\n\nCompany: {job.company.company_name}\nLocation: {job.location}\nJob Type: {job.job_type}\n\nView your job: {request.build_absolute_uri(f"/jobs/{job.id}/")}\n\nBest regards,\nCameroonTechJobs Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [job.company.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'Failed to send confirmation email: {str(e)}')

            logger.info(f'Payment {reference} successful, job {job.id} activated')
            
        elif status == 'failed' or status == 'declined':
            payment.status = 'failed'
            payment.save()
            
            # Delete the pending job
            job = payment.job
            job_title = job.title
            job.delete()
            
            logger.info(f'Payment {reference} failed, job deleted')

        return JsonResponse({'status': 'success'}, status=200)

    except Payment.DoesNotExist:
        logger.error(f'Payment with reference {reference} not found')
        return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
    except json.JSONDecodeError:
        logger.error('Invalid JSON in webhook request')
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f'Webhook error: {str(e)}')
        return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)


def payment_success(request):
    """Display success page after payment"""
    return render(request, 'payments/success.html')


def payment_failure(request):
    """Display failure page if payment failed"""
    return render(request, 'payments/failure.html')


def pricing(request):
    """Display pricing page with tier options"""
    return render(request, 'payments/pricing.html')
