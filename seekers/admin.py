from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Seeker


class SeekerAdmin(UserAdmin):
    model = Seeker
    list_display = ['full_name', 'email', 'experience_level', 'availability', 'job_alerts_enabled', 'date_joined']
    list_filter = ['experience_level', 'availability', 'job_alerts_enabled']
    search_fields = ['full_name', 'email']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'location', 'bio', 'profile_photo')}),
        ('Professional', {'fields': ('experience_level', 'availability', 'skills', 'preferred_categories', 'preferred_locations')}),
        ('Links', {'fields': ('github', 'portfolio', 'linkedin')}),
        ('Settings', {'fields': ('job_alerts_enabled', 'saved_jobs')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )


admin.site.register(Seeker, SeekerAdmin)