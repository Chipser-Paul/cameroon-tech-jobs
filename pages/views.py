from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from jobs.models import Job, Category
from companies.models import Company


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
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
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
                send_mail(
                    subject=f'CameroonTechJobs Contact: {subject_label}',
                    message=(
                        f'Name: {name}\n'
                        f'Email: {email}\n'
                        f'Subject: {subject_label}\n\n'
                        f'{message}'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                sent = True
            except Exception as e:
                error_message = 'We encountered an issue sending your message. Please try again or contact us directly via WhatsApp or email.'
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Contact form email failed: {str(e)}')
    return render(request, 'pages/contact.html', {'sent': sent, 'error_message': error_message})
