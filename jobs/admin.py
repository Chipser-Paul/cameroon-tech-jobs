from django.contrib import admin
from django.contrib import messages

from .alerts import send_job_alerts
from .models import ApplicationMessage, Category, Job, JobApplication, TechStack


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
            try:
                count = send_job_alerts(obj)
                if count > 0:
                    self.message_user(
                        request,
                        f'Job activated successfully. Job alerts were attempted for {count} matching seeker(s).',
                        messages.SUCCESS,
                    )
            except Exception:
                self.message_user(
                    request,
                    'Job activated successfully, but job alert emails could not be sent right now.',
                    messages.WARNING,
                )


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
    autocomplete_fields = ['application', 'sender_company', 'sender_seeker']
    ordering = ['-created_at']
