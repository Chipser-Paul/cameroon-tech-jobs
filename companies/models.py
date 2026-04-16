from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from cloudinary.models import CloudinaryField


class CompanyManager(BaseUserManager):
    def create_user(self, email, company_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, company_name=company_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, company_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, company_name, password, **extra_fields)


class Company(AbstractBaseUser, PermissionsMixin):
    company_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = CloudinaryField('image', blank=True, null=True, folder='cameroon_tech_jobs/companies')
    location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    has_used_free_listing = models.BooleanField(default=False)

    objects = CompanyManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['company_name']

    def __str__(self):
        return self.company_name

    @property
    def logo_url(self):
        """Safely get logo URL for both Cloudinary and legacy values."""
        if self.logo:
            if hasattr(self.logo, 'url'):
                return self.logo.url
            return str(self.logo)
        return None

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'


class CompanyVerificationToken(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='verification_tokens',
    )
    token = models.UUIDField(unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Verification token for {self.company.company_name} ({self.token})'

    class Meta:
        ordering = ['-created_at']