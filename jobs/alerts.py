from django.core.mail import send_mail
from django.conf import settings
from seekers.models import Seeker


def send_job_alerts(job):
    """
    Send email alerts to all seekers whose preferences
    match the newly activated job.
    """
    # Find matching seekers
    seekers = Seeker.objects.filter(
        job_alerts_enabled=True,
        is_active=True
    )

    # Filter by preferred category if seeker has preferences
    matching_seekers = []
    for seeker in seekers:
        preferred_cats = seeker.preferred_categories.all()
        # If seeker has no preferences, send all alerts
        # If seeker has preferences, only send if job matches
        if not preferred_cats.exists():
            matching_seekers.append(seeker)
        elif job.category and job.category in preferred_cats:
            matching_seekers.append(seeker)

    # Send email to each matching seeker
    for seeker in matching_seekers:
        try:
            subject = f'New Job Alert: {job.title} at {job.company.company_name}'

            message = f"""
Hi {seeker.full_name},

A new job matching your preferences has been posted on CameroonTechJobs!

━━━━━━━━━━━━━━━━━━━━━━━━━━━
{job.title}
{job.company.company_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 Location: {job.get_location_display()}
💼 Type: {job.get_job_type_display()}
📂 Category: {job.category.name if job.category else 'General'}
{f"💰 Salary: {job.salary_range}" if job.salary_range else ""}
📅 Posted: Today

View & Apply:
http://127.0.0.1:8000/jobs/{job.pk}/

━━━━━━━━━━━━━━━━━━━━━━━━━━━
To stop receiving alerts, update your preferences:
http://127.0.0.1:8000/seeker/profile/edit/

CameroonTechJobs — Built in Douala 🇨🇲
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seeker.email],
                fail_silently=True,
            )
        except Exception:
            pass

    return len(matching_seekers)