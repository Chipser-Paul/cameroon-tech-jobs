from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Seeker
from .forms import SeekerRegistrationForm, SeekerProfileForm
from jobs.models import Job


def seeker_register(request):
    form = SeekerRegistrationForm()
    if request.method == 'POST':
        form = SeekerRegistrationForm(request.POST)
        if form.is_valid():
            seeker = form.save()
            login(request, seeker, backend='seekers.backends.SeekerBackend')
            messages.success(request, f'Welcome {seeker.full_name}! Complete your profile to get noticed by companies.')
            return redirect('seeker_dashboard')
    return render(request, 'seekers/register.html', {'form': form})


def seeker_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password, backend='seekers.backends.SeekerBackend')
        if user is not None:
            login(request, user, backend='seekers.backends.SeekerBackend')
            return redirect('seeker_dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'seekers/login.html')


def seeker_logout(request):
    logout(request)
    return redirect('home')


@login_required
def seeker_dashboard(request):
    if not isinstance(request.user, Seeker):
        return redirect('dashboard')
    seeker = request.user
    saved = seeker.saved_jobs.filter(status='active')
    recommended = Job.objects.filter(
        status='active',
        category__in=seeker.preferred_categories.all()
    ).exclude(saved_by=seeker)[:6]
    context = {
        'seeker': seeker,
        'saved_jobs': saved,
        'recommended_jobs': recommended,
        'saved_count': saved.count(),
        'skills_count': seeker.skills.count(),
    }
    return render(request, 'seekers/dashboard.html', context)


@login_required
def seeker_profile(request):
    if not isinstance(request.user, Seeker):
        return redirect('dashboard')
    return render(request, 'seekers/profile.html', {'seeker': request.user})


@login_required
def edit_profile(request):
    if not isinstance(request.user, Seeker):
        return redirect('dashboard')
    seeker = request.user
    form = SeekerProfileForm(instance=seeker)
    if request.method == 'POST':
        form = SeekerProfileForm(request.POST, request.FILES, instance=seeker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('seeker_profile')
    return render(request, 'seekers/edit_profile.html', {'form': form})


@login_required
def saved_jobs(request):
    if not isinstance(request.user, Seeker):
        return redirect('dashboard')
    jobs = request.user.saved_jobs.filter(status='active')
    return render(request, 'seekers/saved_jobs.html', {'jobs': jobs})


@login_required
def save_job(request, pk):
    if not isinstance(request.user, Seeker):
        messages.error(request, 'Please log in as a job seeker to save jobs.')
        return redirect('seeker_login')
    job = get_object_or_404(Job, pk=pk)
    seeker = request.user
    if job in seeker.saved_jobs.all():
        seeker.saved_jobs.remove(job)
        messages.info(request, 'Job removed from saved list.')
    else:
        seeker.saved_jobs.add(job)
        messages.success(request, 'Job saved successfully!')
    return redirect('job_detail', pk=pk)


def seeker_list(request):
    seekers = Seeker.objects.filter(is_active=True).exclude(experience_level='')
    skill = request.GET.get('skill')
    if skill:
        seekers = seekers.filter(skills__name__icontains=skill)
    experience = request.GET.get('experience')
    if experience:
        seekers = seekers.filter(experience_level=experience)
    return render(request, 'seekers/seeker_list.html', {'seekers': seekers})


def seeker_detail(request, pk):
    seeker = get_object_or_404(Seeker, pk=pk, is_active=True)
    return render(request, 'seekers/seeker_detail.html', {'seeker': seeker})
