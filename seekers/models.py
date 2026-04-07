from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from jobs.models import Category, Job, TechStack


class SeekerManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, full_name, password, **extra_fields)


class Seeker(AbstractBaseUser, PermissionsMixin):
    EXPERIENCE_CHOICES = [
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (2-5 years)'),
        ('senior', 'Senior Level (5+ years)'),
    ]

    AVAILABILITY_CHOICES = [
        ('immediately', 'Immediately Available'),
        ('2weeks', 'Available in 2 Weeks'),
        ('1month', 'Available in 1 Month'),
        ('not_looking', 'Not Actively Looking'),
    ]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='seeker_set',
        related_query_name='seeker',
        help_text='The groups this seeker belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='seeker_set',
        related_query_name='seeker',
        help_text='Specific permissions for this seeker.',
        verbose_name='user permissions',
    )

    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='seeker_photos/', blank=True, null=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, blank=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, blank=True)

    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

    skills = models.ManyToManyField(TechStack, blank=True, related_name='seekers')
    preferred_categories = models.ManyToManyField(Category, blank=True, related_name='seekers')
    preferred_locations = models.CharField(max_length=200, blank=True)
    saved_jobs = models.ManyToManyField(Job, blank=True, related_name='saved_by')

    job_alerts_enabled = models.BooleanField(default=True)

    objects = SeekerManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Job Seeker'
        verbose_name_plural = 'Job Seekers'
