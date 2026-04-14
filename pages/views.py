from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from jobs.models import Job, Category
from companies.models import Company
import logging

logger = logging.getLogger(__name__)


def home(request):
    featured_jobs = Job.objects.filter(status='active', is_featured=True)[:4]
    latest_jobs = Job.objects.filter(status='active')[:6]
    categories = Category.objects.all()
    total_jobs = Job.objects.filter(status='active').count()
    total_companies = Company.objects.exclude(company_name='Admin').count()
    total_categories = Category.objects.count()

    context = {
        'featured_jobs': featured_jobs,
        'latest_jobs': latest_jobs,
        'categories': categories,
        'total_jobs': total_jobs,
        'total_companies': total_companies,
        'total_categories': total_categories,
    }
    return render(request, 'pages/home.html', context)


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    sent = False
    error_message = None
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '')
            message = request.POST.get('message', '').strip()
            
            if name and email and message:
                subject_labels = {
                    'job_posting': 'Job Posting Question',
                    'payment': 'Payment Issue',
                    'technical': 'Technical Problem',
                    'partnership': 'Partnership',
                    'other': 'Other',
                }
                subject_label = subject_labels.get(subject, 'General Inquiry')
                
                # Always send to admin email, fallback if EMAIL_HOST_USER not set
                recipient = settings.EMAIL_HOST_USER or 'chipseremmanuel@gmail.com'
                
                # Use fail_silently=True to absolutely prevent 500 errors
                # This is critical for Render free tier where SMTP may be blocked
                try:
                    sent_count = send_mail(
                        subject=f'CameroonTechJobs Contact: {subject_label}',
                        message=(
                            f'Name: {name}\n'
                            f'Email: {email}\n'
                            f'Subject: {subject_label}\n\n'
                            f'{message}'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@cameroontechjobs.com',
                        recipient_list=[recipient],
                        fail_silently=True,
                    )
                    
                    if sent_count and sent_count > 0:
                        sent = True
                        logger.info(f'Contact form email sent successfully to {recipient}')
                    else:
                        # Email failed but we don't crash - show friendly error
                        error_message = 'Message received but email delivery failed. Please contact us directly via WhatsApp (+237 675 952 537) or email.'
                        logger.warning(f'Contact form email not delivered (sent_count={sent_count})')
                except Exception as email_error:
                    # Ultra-safe fallback - should never reach here with fail_silently=True
                    error_message = 'Message received but email delivery failed. Please contact us directly via WhatsApp (+237 675 952 537) or email.'
                    logger.error(f'Contact form email exception: {str(email_error)}')
            else:
                error_message = 'Please fill in all required fields.'
        except Exception as e:
            # Catch-all to absolutely prevent 500 errors
            error_message = 'An unexpected error occurred. Please try again or contact us via WhatsApp.'
            logger.error(f'Contact form unexpected error: {str(e)}', exc_info=True)
    
    return render(request, 'pages/contact.html', {'sent': sent, 'error_message': error_message})