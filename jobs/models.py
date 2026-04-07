from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class TechStack(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]

    LOCATION_CHOICES = [
        ('douala', 'Douala'),
        ('yaounde', 'Yaounde'),
        ('bafoussam', 'Bafoussam'),
        ('bamenda', 'Bamenda'),
        ('buea', 'Buea'),
        ('remote', 'Remote'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic - 5,000 XAF'),
        ('featured', 'Featured - 15,000 XAF'),
    ]

    EXPERIENCE_CHOICES = [
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (2-5 years)'),
        ('senior', 'Senior Level (5+ years)'),
        ('any', 'Any Level'),
    ]

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='jobs',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='jobs',
    )
    tech_stacks = models.ManyToManyField(
        TechStack,
        blank=True,
        related_name='jobs',
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='any',
    )
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    salary_range = models.CharField(max_length=100, blank=True)
    apply_link = models.URLField(blank=True)
    apply_email = models.EmailField(blank=True)

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)

    views_count = models.PositiveIntegerField(default=0)
    date_posted = models.DateTimeField(auto_now_add=True)
    date_expires = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.date_expires:
            self.date_expires = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.date_expires

    def days_ago(self):
        delta = timezone.now() - self.date_posted
        if delta.days == 0:
            return 'Today'
        if delta.days == 1:
            return '1 day ago'
        return f'{delta.days} days ago'

    def __str__(self):
        return f'{self.title} - {self.company.company_name}'

    class Meta:
        ordering = ['-is_featured', '-date_posted']


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    seeker = models.ForeignKey(
        'seekers.Seeker',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    cover_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    date_applied = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.seeker.full_name} -> {self.job.title}'

    class Meta:
        ordering = ['-date_applied']
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'seeker'],
                name='unique_job_application_per_seeker',
            )
        ]


class ApplicationMessage(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='sent_application_messages',
        blank=True,
        null=True,
    )
    sender_seeker = models.ForeignKey(
        'seekers.Seeker',
        on_delete=models.CASCADE,
        related_name='sent_application_messages',
        blank=True,
        null=True,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def sender_name(self):
        if self.sender_company:
            return self.sender_company.company_name
        if self.sender_seeker:
            return self.sender_seeker.full_name
        return 'Unknown'

    @property
    def sender_role(self):
        if self.sender_company:
            return 'company'
        if self.sender_seeker:
            return 'seeker'
        return 'unknown'

    def __str__(self):
        return f'Message on {self.application.job.title} by {self.sender_name}'

    class Meta:
        ordering = ['created_at']
