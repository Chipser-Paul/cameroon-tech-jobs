from django.db import models
from django.utils import timezone
from datetime import timedelta


class Job(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('featured', 'Featured'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ]
    
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='jobs')
    tech_stacks = models.ManyToManyField('TechStack', blank=True, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    experience_level = models.CharField(max_length=50, choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('lead', 'Lead/Manager'),
    ])
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50, choices=[
        ('full-time', 'Full-time'),
        ('part-time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ])
    salary_range = models.CharField(max_length=100, blank=True)
    apply_link = models.URLField(blank=True)
    apply_email = models.EmailField(blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    date_posted = models.DateTimeField(auto_now_add=True)
    date_expires = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_featured', '-date_posted']
    
    def __str__(self):
        return self.title
    
    @property
    def days_until_expiry(self):
        """Calculate days remaining until job expires"""
        if not self.date_expires:
            return None
        delta = self.date_expires - timezone.now()
        return max(0, delta.days)
    
    @property
    def is_expiring_soon(self):
        """Check if job expires within 7 days"""
        if not self.date_expires:
            return False
        return 0 < self.days_until_expiry <= 7
    
    @property
    def has_expired(self):
        """Check if job has expired"""
        if not self.date_expires:
            return False
        return timezone.now() > self.date_expires
    
    def renew_job(self, plan=None, duration_days=None):
        """Renew job with new expiration date"""
        if plan:
            self.plan = plan
            self.is_featured = (plan == 'featured')
        
        if duration_days is None:
            duration_days = 60 if self.plan == 'featured' else 30
        
        self.status = 'active'
        self.date_expires = timezone.now() + timedelta(days=duration_days)
        self.save(update_fields=['plan', 'is_featured', 'status', 'date_expires'])


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


class ApplicationInterview(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='interviews',
    )
    scheduled_for = models.DateTimeField()
    meeting_type = models.CharField(max_length=20, choices=[
        ('video', 'Video Call'),
        ('phone', 'Phone Call'),
        ('in_person', 'In Person'),
    ], default='video')
    meeting_link = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Interview for {self.application.job.title} with {self.application.seeker.full_name}'

    class Meta:
        ordering = ['-scheduled_for']


class Notification(models.Model):
    recipient_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True,
    )
    recipient_seeker = models.ForeignKey(
        'seekers.Seeker',
        on_delete=models.CASCADE,
        related_name='notifications',
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
