from django.db import models


class Payment(models.Model):
    BASIC_TIER = 5000
    PREMIUM_TIER = 15000

    TIER_CHOICES = [
        (BASIC_TIER, 'Basic - 5,000 FCFA'),
        (PREMIUM_TIER, 'Premium - 15,000 FCFA'),
    ]

    STATUS_PENDING = 'PENDING'
    STATUS_SUCCESSFUL = 'SUCCESSFUL'
    STATUS_FAILED = 'FAILED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESSFUL, 'Successful'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='payments',
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
        blank=True,
    )
    tier = models.PositiveIntegerField(choices=TIER_CHOICES)
    amount = models.IntegerField()
    currency = models.CharField(max_length=3, default='XAF')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    tranzak_request_id = models.CharField(max_length=64, blank=True, db_index=True)
    mch_transaction_ref = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.company.company_name} - {self.amount} {self.currency} ({self.status})'
