from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Job, Category, TechStack
from .forms import JobForm


def job_list(request):
    jobs = Job.objects.filter(status='active')
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

    context = {
        'jobs': jobs.distinct(),
        'categories': categories,
        'tech_stacks': tech_stacks,
        'total_jobs': jobs.distinct().count(),
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk, status='active')
    job.views_count += 1
    job.save()
    related_jobs = Job.objects.filter(
        status='active',
        category=job.category
    ).exclude(pk=pk)[:3]
    context = {
        'job': job,
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def post_job(request):
    company = request.user
    is_free = not company.has_used_free_listing

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company

            if is_free:
                job.plan = 'free'
                job.status = 'pending'
                company.has_used_free_listing = True
                company.save()
                messages.success(request, '🎉 Your free job listing has been submitted! It will be activated within 24 hours.')
            else:
                job.status = 'pending'
                messages.success(request, '✅ Job submitted! Please complete your payment to activate the listing.')

            job.save()
            return redirect('dashboard')
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