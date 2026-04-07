from django.conf import settings
from django.core.mail import send_mail

from seekers.models import Seeker


def send_job_alerts(job):
    """
    Send email alerts to seekers whose preferences match the newly activated job.
    """
    seekers = Seeker.objects.filter(
        job_alerts_enabled=True,
        is_active=True,
    )

    matching_seekers = []
    for seeker in seekers:
        preferred_cats = seeker.preferred_categories.all()
        if not preferred_cats.exists():
            matching_seekers.append(seeker)
        elif job.category and job.category in preferred_cats:
            matching_seekers.append(seeker)

    site_url = getattr(settings, 'SITE_URL', '').rstrip('/') or 'http://127.0.0.1:8000'
    job_url = f'{site_url}/jobs/{job.pk}/'
    profile_url = f'{site_url}/seeker/profile/edit/'

    for seeker in matching_seekers:
        try:
            subject = f'New Job Alert: {job.title} at {job.company.company_name}'
            salary_line = f'Salary: {job.salary_range}\n' if job.salary_range else ''
            message = (
                f'Hi {seeker.full_name},\n\n'
                'A new job matching your preferences has been posted on CameroonTechJobs!\n\n'
                '---------------------------\n'
                f'{job.title}\n'
                f'{job.company.company_name}\n'
                '---------------------------\n\n'
                f'Location: {job.get_location_display()}\n'
                f'Type: {job.get_job_type_display()}\n'
                f"Category: {job.category.name if job.category else 'General'}\n"
                f'{salary_line}'
                'Posted: Today\n\n'
                'View & Apply:\n'
                f'{job_url}\n\n'
                '---------------------------\n'
                'To stop receiving alerts, update your preferences:\n'
                f'{profile_url}\n\n'
                'CameroonTechJobs - Built in Douala\n'
            )

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
