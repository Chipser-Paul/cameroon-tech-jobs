import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from config.decorators import conditional_ratelimit
from .models import Company, CompanyVerificationToken
from .forms import CompanyRegistrationForm
from jobs.models import Job
from seekers.models import Seeker


def register(request):
    form = CompanyRegistrationForm()
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            login(request, company, backend='django.contrib.auth.backends.ModelBackend')
            verification_token = CompanyVerificationToken.objects.create(
                company=company,
                token=uuid.uuid4(),
            )
            verify_url = request.build_absolute_uri(reverse('company_verify', args=[verification_token.token]))
            try:
                send_mail(
                    'Verify your CameroonTechJobs company account',
                    f'Hi {company.company_name},\n\nPlease verify your company email by clicking the link below:\n{verify_url}\n\nIf you did not sign up, ignore this message.\n',
                    settings.DEFAULT_FROM_EMAIL,
                    [company.email],
                    fail_silently=False,
                )
                messages.success(request, f'Welcome {company.company_name}! Please check your email to verify your account and activate future jobs faster.')
            except Exception:
                messages.warning(request, f'Welcome {company.company_name}! We were unable to send a verification email right now, but your account is created.')
            return redirect('dashboard')
    return render(request, 'companies/register.html', {'form': form})


@conditional_ratelimit(key='ip', rate='5/m')
def company_login(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password, backend='django.contrib.auth.backends.ModelBackend')
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'companies/login.html', {'form': {}})


def verify_company(request, token):
    verification_token = get_object_or_404(CompanyVerificationToken, token=token, is_used=False)
    company = verification_token.company
    company.is_verified = True
    company.save()
    verification_token.is_used = True
    verification_token.save()
    messages.success(request, 'Your company has been verified. Future free jobs from your account may be activated automatically.')
    return redirect('dashboard')


def company_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    if isinstance(request.user, Seeker):
        return redirect('seeker_dashboard')

    jobs = Job.objects.filter(company=request.user).annotate(
        applicant_count=Count('applications', distinct=True)
    ).order_by('-date_posted')
    total_views = sum(job.views_count for job in jobs)
    total_applicants = sum(job.applicant_count for job in jobs)
    context = {
        'jobs': jobs,
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(status='active').count(),
        'pending_jobs': jobs.filter(status='pending').count(),
        'total_views': total_views,
        'total_applicants': total_applicants,
    }
    return render(request, 'companies/dashboard.html', context)


@login_required
def company_profile(request, pk):
    company = get_object_or_404(Company, pk=pk)
    jobs = Job.objects.filter(company=company, status='active')
    return render(request, 'companies/company_profile.html', {'company': company, 'jobs': jobs})


@login_required
def payment_info(request):
    if isinstance(request.user, Seeker):
        return redirect('seeker_dashboard')

    return render(request, 'companies/payment_info.html')
