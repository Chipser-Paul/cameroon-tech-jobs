from django.contrib import admin
from django.contrib import messages as admin_messages
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Job, JobApplication, ApplicationMessage, ApplicationInterview, Notification, Category, TechStack
from companies.models import Company
from seekers.models import Seeker
from payments.models import Payment


# Custom analytics view that integrates with default admin
def analytics_view(request):
    """Custom analytics dashboard view"""
    now = timezone.now()
    
    # Time periods
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Revenue metrics
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    revenue_today = Payment.objects.filter(
        status='completed',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_week = Payment.objects.filter(
        status='completed',
        created_at__date__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    revenue_month = Payment.objects.filter(
        status='completed',
        created_at__date__gte=month_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Conversion rates
    total_payments = Payment.objects.count()
    completed_payments = Payment.objects.filter(status='completed').count()
    conversion_rate = (completed_payments / total_payments * 100) if total_payments > 0 else 0
    
    # User metrics
    total_companies = Company.objects.exclude(company_name='Admin').count()
    companies_this_month = Company.objects.filter(
        date_joined__date__gte=month_ago
    ).exclude(company_name='Admin').count()
    
    total_seekers = Seeker.objects.count()
    seekers_this_month = Seeker.objects.filter(
        date_joined__date__gte=month_ago
    ).count()
    
    # Job metrics
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(status='active').count()
    pending_jobs = Job.objects.filter(status='pending').count()
    expired_jobs = Job.objects.filter(status='expired').count()
    jobs_this_month = Job.objects.filter(date_posted__date__gte=month_ago).count()
    
    # Applications
    total_applications = JobApplication.objects.count()
    applications_this_month = JobApplication.objects.filter(
        date_applied__date__gte=month_ago
    ).count()
    
    # Popular categories
    popular_categories = Category.objects.annotate(
        job_count=Count('job', filter=Q(job__status='active'))
    ).order_by('-job_count')[:5]
    
    # Top spending companies
    top_companies = Company.objects.annotate(
        total_spent=Sum('payment__amount', filter=Q(payment__status='completed'))
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:5]
    
    # Recent activity
    recent_payments = Payment.objects.select_related('job', 'job__company').order_by('-created_at')[:10]
    recent_jobs = Job.objects.select_related('company').order_by('-date_posted')[:10]
    
    context = {
        **admin.site.each_context(request),
        'title': 'Analytics Dashboard',
        # Revenue
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,
        # Conversions
        'total_payments': total_payments,
        'completed_payments': completed_payments,
        'conversion_rate': round(conversion_rate, 2),
        # Users
        'total_companies': total_companies,
        'companies_this_month': companies_this_month,
        'total_seekers': total_seekers,
        'seekers_this_month': seekers_this_month,
        # Jobs
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'pending_jobs': pending_jobs,
        'expired_jobs': expired_jobs,
        'jobs_this_month': jobs_this_month,
        # Applications
        'total_applications': total_applications,
        'applications_this_month': applications_this_month,
        # Categories & Companies
        'popular_categories': popular_categories,
        'top_companies': top_companies,
        # Recent activity
        'recent_payments': recent_payments,
        'recent_jobs': recent_jobs,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TechStack)
class TechStackAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'company',
        'plan_badge',
        'status_badge',
        'is_featured',
        'location',
        'job_type',
        'views_count',
        'applicant_count',
        'date_posted',
        'date_expires',
    )
    list_filter = ('status', 'plan', 'is_featured', 'location', 'job_type', 'date_posted')
    search_fields = ('title', 'company__company_name', 'description')
    list_select_related = ('company', 'category')
    ordering = ('-date_posted',)
    readonly_fields = ('date_posted', 'views_count')
    actions = ('approve_jobs', 'reject_jobs', 'feature_jobs', 'unfeature_jobs')

    fieldsets = (
        ('Job Information', {
            'fields': ('company', 'title', 'category', 'tech_stacks')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'experience_level', 'location', 'job_type', 'salary_range')
        }),
        ('Application', {
            'fields': ('apply_link', 'apply_email')
        }),
        ('Status & Plan', {
            'fields': ('plan', 'status', 'is_featured', 'date_expires')
        }),
        ('Analytics', {
            'fields': ('views_count', 'date_posted'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Plan')
    def plan_badge(self, obj):
        colors = {
            'free': '#6c757d',
            'basic': '#0b724d',
            'featured': '#c28b00',
        }
        color = colors.get(obj.plan, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:4px 12px;border-radius:12px;font-weight:600;font-size:0.85rem;">{}</span>',
            color,
            obj.get_plan_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'active': '#198754',
            'expired': '#6c757d',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:4px 12px;border-radius:12px;font-weight:600;font-size:0.85rem;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Applicants')
    def applicant_count(self, obj):
        count = obj.applications.count()
        if count > 0:
            return format_html(
                '<a href="{}" style="font-weight:600;color:#0b724d;">{} applicants</a>',
                reverse('admin:jobs_jobapplication_changelist') + f'?job__id__exact={obj.id}',
                count
            )
        return '0'

    @admin.action(description='✅ Approve selected jobs')
    def approve_jobs(self, request, queryset):
        approved = queryset.filter(status='pending').update(status='active')
        if approved:
            self.message_user(request, f'{approved} job(s) approved and are now active!')
        else:
            self.message_user(request, 'No pending jobs selected.', level=admin_messages.WARNING)

    @admin.action(description='❌ Reject selected jobs')
    def reject_jobs(self, request, queryset):
        rejected = queryset.filter(status='pending').update(status='rejected')
        if rejected:
            self.message_user(request, f'{rejected} job(s) rejected.')
        else:
            self.message_user(request, 'No pending jobs selected.', level=admin_messages.WARNING)

    @admin.action(description='⭐ Feature selected jobs')
    def feature_jobs(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} job(s) marked as featured.')

    @admin.action(description='Remove featured status')
    def unfeature_jobs(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} job(s) unmarked as featured.')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('applications')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'seeker',
        'job',
        'job_company',
        'status',
        'date_applied',
    )
    list_filter = ('status', 'date_applied')
    search_fields = ('seeker__full_name', 'job__title', 'job__company__company_name')
    list_select_related = ('seeker', 'job', 'job__company')
    ordering = ('-date_applied',)

    @admin.display(description='Company')
    def job_company(self, obj):
        return obj.job.company.company_name


@admin.register(ApplicationMessage)
class ApplicationMessageAdmin(admin.ModelAdmin):
    list_display = ('application', 'sender_name', 'sender_role_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('body', 'application__job__title', 'sender_company__company_name', 'sender_seeker__full_name')
    list_select_related = ('application', 'application__job', 'sender_company', 'sender_seeker')
    ordering = ('-created_at',)

    @admin.display(description='Sender Role')
    def sender_role_display(self, obj):
        return obj.sender_role.title()


@admin.register(ApplicationInterview)
class ApplicationInterviewAdmin(admin.ModelAdmin):
    list_display = (
        'application',
        'scheduled_for',
        'meeting_type',
        'status',
        'created_at',
    )
    list_filter = ('status', 'meeting_type', 'scheduled_for')
    search_fields = ('application__job__title', 'application__seeker__full_name')
    list_select_related = ('application', 'application__job', 'application__seeker')
    ordering = ('-scheduled_for',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'recipient',
        'is_read',
        'created_at',
    )
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'body')
    ordering = ('-created_at',)
    actions = ('mark_as_read', 'mark_as_unread')

    @admin.display(description='Recipient')
    def recipient(self, obj):
        if obj.recipient_company:
            return f'Company: {obj.recipient_company.company_name}'
        if obj.recipient_seeker:
            return f'Seeker: {obj.recipient_seeker.full_name}'
        return 'Unknown'

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')

    @admin.action(description='Mark selected as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')


# Add analytics URL to admin site
from django.urls import path

def get_admin_urls():
    """Add custom analytics URL to admin"""
    return [
        path('analytics/', admin.site.admin_view(analytics_view), name='analytics'),
    ]

# Monkey-patch admin site to include analytics URL
original_get_urls = admin.site.get_urls
def custom_get_urls():
    return original_get_urls() + get_admin_urls()
admin.site.get_urls = custom_get_urls
