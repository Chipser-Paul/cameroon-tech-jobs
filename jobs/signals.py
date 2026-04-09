from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Job
from .tasks import send_job_alerts_task


@receiver(pre_save, sender=Job)
def store_previous_job_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = sender.objects.values_list('status', flat=True).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Job)
def handle_job_activation(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_previous_status', None)
    if instance.status == 'active' and (created or old_status != 'active'):
        send_job_alerts_task.delay(instance.pk)
