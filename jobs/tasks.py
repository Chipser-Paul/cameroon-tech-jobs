from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from .alerts import send_job_alerts
from .models import Job


@shared_task(bind=True)
def send_job_alerts_task(self, job_id):
    try:
        job = Job.objects.get(pk=job_id, status='active')
    except ObjectDoesNotExist:
        return 0

    return send_job_alerts(job)
