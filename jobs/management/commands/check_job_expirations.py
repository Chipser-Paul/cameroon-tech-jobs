from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from jobs.models import Job
from companies.models import Company
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for expiring jobs and send warning emails to companies'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking for expiring jobs...')
        
        now = timezone.now()
        today = now.date()
        
        # Jobs expiring in 7 days
        seven_days = today + timedelta(days=7)
        jobs_7_days = Job.objects.filter(
            status='active',
            date_expires__date=seven_days
        )
        
        # Jobs expiring in 3 days
        three_days = today + timedelta(days=3)
        jobs_3_days = Job.objects.filter(
            status='active',
            date_expires__date=three_days
        )
        
        # Jobs expiring tomorrow
        tomorrow = today + timedelta(days=1)
        jobs_1_day = Job.objects.filter(
            status='active',
            date_expires__date=tomorrow
        )
        
        # Jobs that have expired (past expiration date)
        expired_jobs = Job.objects.filter(
            status='active',
            date_expires__lt=now
        )
        
        # Track statistics
        stats = {
            '7_days': 0,
            '3_days': 0,
            '1_day': 0,
            'expired': 0,
            'emails_sent': 0,
            'errors': 0,
        }
        
        # Send 7-day warning emails
        for job in jobs_7_days:
            try:
                self.send_expiration_warning(job, days=7)
                stats['7_days'] += 1
                stats['emails_sent'] += 1
                self.stdout.write(f'  ✓ Sent 7-day warning for: {job.title}')
            except Exception as e:
                stats['errors'] += 1
                logger.error(f'Failed to send 7-day warning for job {job.id}: {e}')
        
        # Send 3-day warning emails
        for job in jobs_3_days:
            try:
                self.send_expiration_warning(job, days=3)
                stats['3_days'] += 1
                stats['emails_sent'] += 1
                self.stdout.write(f'  ✓ Sent 3-day warning for: {job.title}')
            except Exception as e:
                stats['errors'] += 1
                logger.error(f'Failed to send 3-day warning for job {job.id}: {e}')
        
        # Send 1-day warning emails
        for job in jobs_1_day:
            try:
                self.send_expiration_warning(job, days=1)
                stats['1_day'] += 1
                stats['emails_sent'] += 1
                self.stdout.write(f'  ✓ Sent 1-day warning for: {job.title}')
            except Exception as e:
                stats['errors'] += 1
                logger.error(f'Failed to send 1-day warning for job {job.id}: {e}')
        
        # Expire jobs that are past expiration date
        for job in expired_jobs:
            try:
                job.status = 'expired'
                job.save(update_fields=['status'])
                stats['expired'] += 1
                self.stdout.write(f'  ✗ Expired job: {job.title}')
                
                # Notify company about expiration
                self.send_expiration_notification(job)
                stats['emails_sent'] += 1
            except Exception as e:
                stats['errors'] += 1
                logger.error(f'Failed to expire job {job.id}: {e}')
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n✅ Job Expiration Check Complete!'))
        self.stdout.write(f'   7-day warnings sent: {stats["7_days"]}')
        self.stdout.write(f'   3-day warnings sent: {stats["3_days"]}')
        self.stdout.write(f'   1-day warnings sent: {stats["1_day"]}')
        self.stdout.write(f'   Jobs expired: {stats["expired"]}')
        self.stdout.write(f'   Total emails sent: {stats["emails_sent"]}')
        if stats['errors'] > 0:
            self.stdout.write(self.style.WARNING(f'   Errors: {stats["errors"]}'))

    def send_expiration_warning(self, job, days):
        """Send expiration warning email to company"""
        company = job.company
        
        if days == 7:
            subject = f'⚠️ Your job "{job.title}" expires in 7 days'
            message = f'''Hi {company.company_name},

This is a friendly reminder that your job listing "{job.title}" will expire in 7 days (on {job.date_expires.strftime('%B %d, %Y')}).

To keep your job listing active and visible to job seekers, you can renew it now:

🔗 Renew your job: {settings.SITE_URL}/dashboard/

Renewing is quick and easy - your job will stay at the top of search results and continue receiving applications.

Best regards,
CameroonTechJobs Team
'''
        elif days == 3:
            subject = f'⏰ Your job "{job.title}" expires in 3 days'
            message = f'''Hi {company.company_name},

Your job listing "{job.title}" will expire in 3 days (on {job.date_expires.strftime('%B %d, %Y')}).

Don't miss out on potential candidates! Renew now to keep your listing active:

🔗 Renew your job: {settings.SITE_URL}/dashboard/

Best regards,
CameroonTechJobs Team
'''
        elif days == 1:
            subject = f'🚨 Your job "{job.title}" expires TOMORROW'
            message = f'''Hi {company.company_name},

URGENT: Your job listing "{job.title}" expires TOMORROW (on {job.date_expires.strftime('%B %d, %Y')}).

Renew now to avoid losing your listing and all the applications you've received:

🔗 Renew immediately: {settings.SITE_URL}/dashboard/

Best regards,
CameroonTechJobs Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [company.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Failed to send expiration warning email to {company.email}: {e}')
            raise

    def send_expiration_notification(self, job):
        """Send notification that job has expired"""
        company = job.company
        
        subject = f'❌ Your job "{job.title}" has expired'
        message = f'''Hi {company.company_name},

Your job listing "{job.title}" has expired and is no longer visible to job seekers.

If you'd like to continue receiving applications, you can renew your job listing:

🔗 Renew your job: {settings.SITE_URL}/dashboard/

Renewing will reactivate your listing and keep it visible to thousands of tech professionals in Cameroon.

Best regards,
CameroonTechJobs Team
'''
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [company.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f'Failed to send expiration notification to {company.email}: {e}')
            raise