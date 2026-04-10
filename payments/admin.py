from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('job', 'tier', 'amount', 'status', 'campay_reference', 'created_at')
    list_filter = ('status', 'tier', 'created_at')
    search_fields = ('job__title', 'campay_reference')
    readonly_fields = ('created_at', 'updated_at', 'campay_reference')
