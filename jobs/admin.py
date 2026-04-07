from django.contrib import admin
from django.contrib import messages
from .models import Job, Category, TechStack, JobApplication
from .alerts import send_job_alerts


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
        # Check if job is being activated for first time
        is_newly_activated = False
        if change:
            try:
                old_obj = Job.objects.get(pk=obj.pk)
                if old_obj.status != 'active' and obj.status == 'active':
                    is_newly_activated = True
            except Job.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)

        # Send alerts if job just got activated
        if is_newly_activated:
            count = send_job_alerts(obj)
            if count > 0:
                self.message_user(
                    request,
                    f'✅ Job activated! Job alerts sent to {count} matching seeker(s).',
                    messages.SUCCESS
                )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'seeker', 'status', 'date_applied']
    list_filter = ['status', 'date_applied', 'job__company']
    search_fields = ['job__title', 'seeker__full_name', 'seeker__email']
    autocomplete_fields = ['job', 'seeker']
    ordering = ['-date_applied']
