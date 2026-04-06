from django.shortcuts import render
from django.contrib import messages
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
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        if name and email and message:
            sent = True
    return render(request, 'pages/contact.html', {'sent': sent})