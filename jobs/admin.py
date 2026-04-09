from django.contrib import admin
from django.contrib import messages

from .tasks import send_job_alerts_task
from .models import ApplicationInterview, ApplicationMessage, Category, Job, JobApplication, Notification, TechStack
from companies.models import Company


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(TechStack)
class TechStackAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'category', 'experience_level', 'location', 'job_type', 'plan', 'status', 'is_featured', 'date_posted']
    list_filter = ['status', 'job_type', 'location', 'plan', 'is_featured', 'experience_level']
    search_fields = ['title', 'company__company_name']
    list_editable = ['status', 'is_featured']
    filter_horizontal = ['tech_stacks']
    ordering = ['-date_posted']
    actions = ['approve_jobs', 'reject_jobs']

    def save_model(self, request, obj, form, change):
        is_newly_activated = False
        if change:
            try:
                old_obj = Job.objects.get(pk=obj.pk)
                if old_obj.status != 'active' and obj.status == 'active':
                    is_newly_activated = True
            except Job.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        if is_newly_activated:
            send_job_alerts_task.delay(obj.pk)
            self.message_user(
                request,
                'Job activated successfully and job alert delivery has been queued.',
                messages.SUCCESS,
            )

    def approve_jobs(self, request, queryset):
        activated = 0
        for job in queryset:
            if job.status != 'active':
                job.status = 'active'
                job.save()
                activated += 1
        if activated:
            self.message_user(request, f'{activated} job(s) approved and alerts queued.', messages.SUCCESS)
        else:
            self.message_user(request, 'No jobs were approved.', messages.INFO)

    approve_jobs.short_description = 'Approve selected jobs'

    def reject_jobs(self, request, queryset):
        rejected = queryset.update(status='rejected')
        self.message_user(request, f'{rejected} job(s) rejected.', messages.SUCCESS)

    reject_jobs.short_description = 'Reject selected jobs'


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'seeker', 'status', 'date_applied']
    list_filter = ['status', 'date_applied', 'job__company']
    search_fields = ['job__title', 'seeker__full_name', 'seeker__email']
    autocomplete_fields = ['job', 'seeker']
    ordering = ['-date_applied']


@admin.register(ApplicationMessage)
class ApplicationMessageAdmin(admin.ModelAdmin):
    list_display = ['application', 'sender_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['application__job__title', 'application__seeker__full_name', 'body']
    autocomplete_fields = ['application', 'sender_seeker']
    ordering = ['-created_at']


@admin.register(ApplicationInterview)
class ApplicationInterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'scheduled_for', 'meeting_type', 'status', 'created_at']
    list_filter = ['status', 'meeting_type', 'scheduled_for', 'created_at']
    search_fields = ['application__job__title', 'application__seeker__full_name', 'location', 'notes']
    autocomplete_fields = ['application']
    ordering = ['-scheduled_for']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient_company', 'recipient_seeker', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'body']
    autocomplete_fields = ['recipient_seeker']
    ordering = ['-created_at']
