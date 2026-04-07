from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .forms import JobForm
from .models import ApplicationInterview, ApplicationMessage, Job, Category, TechStack, JobApplication
from companies.models import Company
from seekers.models import Seeker


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
                job.status = 'pending'
                company.has_used_free_listing = True
                company.save()
                messages.success(request, '🎉 Your free job listing has been submitted! It will be activated within 24 hours.')
            else:
                job.status = 'pending'
                messages.success(request, '✅ Job submitted! Please complete your payment to activate the listing.')

            job.save()
            form.save_m2m()
            form.save_custom_tech(job)
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

    JobApplication.objects.create(
        job=job,
        seeker=request.user,
        cover_note=request.POST.get('cover_note', '').strip(),
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

    try:
        scheduled_for = datetime.strptime(scheduled_for_raw, '%Y-%m-%dT%H:%M')
        scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
    except ValueError:
        messages.error(request, 'Please provide a valid interview date and time.')
        return redirect('application_conversation', pk=application.pk)

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
    messages.success(request, f'Interview invitation {interview.get_status_display().lower()}.')
    return redirect('application_conversation', pk=interview.application.pk)
