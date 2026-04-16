from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Company, CompanyVerificationToken


class CompanyAdmin(UserAdmin):
    model = Company
    list_display = ['company_name', 'email', 'phone', 'has_used_free_listing', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['is_active', 'has_used_free_listing', 'is_verified']
    search_fields = ['company_name', 'email']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Company Info', {'fields': ('company_name', 'phone', 'website', 'description', 'logo', 'location')}),
        ('Status', {'fields': ('has_used_free_listing', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'company_name', 'password1', 'password2'),
        }),
    )


admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyVerificationToken)