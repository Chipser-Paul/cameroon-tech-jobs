from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Company
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
            messages.success(request, f'Welcome {company.company_name}! Your account is ready. Post your first job for free!')
            return redirect('dashboard')
    return render(request, 'companies/register.html', {'form': form})


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


def company_logout(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    if isinstance(request.user, Seeker):
        return redirect('seeker_dashboard')

    jobs = Job.objects.filter(company=request.user).order_by('-date_posted')
    total_views = sum(job.views_count for job in jobs)
    context = {
        'jobs': jobs,
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(status='active').count(),
        'pending_jobs': jobs.filter(status='pending').count(),
        'total_views': total_views,
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
