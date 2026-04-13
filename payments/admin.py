from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'company',
        'job',
        'tier',
        'amount',
        'currency',
        'status',
        'tranzak_request_id',
        'created_at',
    )
    list_filter = ('status', 'tier', 'currency', 'created_at')
    search_fields = (
        'company__company_name',
        'job__title',
        'tranzak_request_id',
        'mch_transaction_ref',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'tranzak_request_id',
        'mch_transaction_ref',
    )
