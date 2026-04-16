from django.contrib import admin
from django.contrib import messages as admin_messages
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from .models import Job, JobApplication, ApplicationMessage, ApplicationInterview, Notification, Category, TechStack


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
    list_filter = ('created_at',)  # Removed 'sender_role' - it's a property, not a field
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