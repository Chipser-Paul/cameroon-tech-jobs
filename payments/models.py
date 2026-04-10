from django.db import models
from django.utils import timezone
from jobs.models import Job


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    TIER_CHOICES = [
        ('basic', 'Basic - 5,000 FCFA'),
        ('featured', 'Featured - 15,000 FCFA'),
    ]

    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name='campay_payment',
    )
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # in XAF/FCFA
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    campay_reference = models.CharField(max_length=255, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.job.title} - {self.amount} FCFA ({self.status})"
