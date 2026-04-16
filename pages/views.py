from django.shortcuts import render
from django.conf import settings
from django.core.mail import send_mail
from jobs.models import Job, Category
from companies.models import Company
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def home(request):
    try:
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
    except Exception as e:
        logger.error(f'Home page error: {str(e)}', exc_info=True)
        return render(request, 'pages/home.html', {
            'featured_jobs': [],
            'latest_jobs': [],
            'categories': [],
            'total_jobs': 0,
            'total_companies': 0,
            'total_categories': 0,
        })


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    """
    Contact page view with bulletproof error handling.
    Even if email fails or database errors occur, the page will still render.
    """
    context = {
        'sent': False,
        'error_message': None,
    }
    
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
                recipient = settings.EMAIL_HOST_USER or 'chipseremmanuel@gmail.com'
                
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
                        context['sent'] = True
                        logger.info(f'Contact email sent to {recipient}')
                    else:
                        context['error_message'] = 'Message received but email delivery failed. Please contact us via WhatsApp (+237 675 952 537).'
                except Exception as e:
                    context['error_message'] = 'Message received but email delivery failed. Please contact us via WhatsApp (+237 675 952 537).'
                    logger.error(f'Contact form email error: {str(e)}')
            else:
                context['error_message'] = 'Please fill in all required fields.'
        except Exception as e:
            context['error_message'] = 'An error occurred. Please try again or contact us via WhatsApp.'
            logger.error(f'Contact form error: {str(e)}', exc_info=True)
    
    try:
        return render(request, 'pages/contact.html', context)
    except Exception as e:
        # If even template rendering fails, return a simple HTML response
        logger.error(f'Contact page render error: {str(e)}', exc_info=True)
        from django.http import HttpResponse
        error_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Contact Us - CameroonTechJobs</title></head>
        <body style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
            <h1>Oops! Something went wrong</h1>
            <p>We're having trouble loading this page. Please contact us directly:</p>
            <p><strong>WhatsApp:</strong> +237 675 952 537</p>
            <p><strong>Email:</strong> chipseremmanuel@gmail.com</p>
            <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background: #1a7a4a; color: white; text-decoration: none; border-radius: 5px;">Go to Homepage</a>
        </body>
        </html>
        """
        return HttpResponse(error_html, status=500)


def terms(request):
    """Terms of Service page"""
    context = {
        'current_date': datetime.now().strftime('%B %d, %Y')
    }
    return render(request, 'pages/terms.html', context)


def privacy(request):
    """Privacy Policy page"""
    context = {
        'current_date': datetime.now().strftime('%B %d, %Y')
    }
    return render(request, 'pages/privacy.html', context)


def refunds(request):
    """Refund Policy page"""
    context = {
        'current_date': datetime.now().strftime('%B %d, %Y')
    }
    return render(request, 'pages/refunds.html', context)


# Custom Error Views
def error_404(request, exception):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)


def error_500(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)


def error_403(request, exception):
    """Custom 403 error page"""
    return render(request, '403.html', status=403)
