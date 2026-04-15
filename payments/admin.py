from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'company',
        'job',
        'job_status',
        'tier',
        'amount',
        'currency',
        'status',
        'mch_transaction_ref',
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
    list_select_related = ('company', 'job')
    ordering = ('-created_at',)
    readonly_fields = (
        'company',
        'job',
        'tier',
        'amount',
        'currency',
        'status',
        'created_at',
        'updated_at',
        'tranzak_request_id',
        'mch_transaction_ref',
    )
    actions = ('mark_as_cancelled', 'mark_as_failed')

    @admin.display(description='Job Status')
    def job_status(self, obj):
        if not obj.job:
            return '-'
        return obj.job.get_status_display()

    @admin.action(description='Mark selected pending payments as cancelled')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status=Payment.STATUS_PENDING).update(status=Payment.STATUS_CANCELLED)
        self.message_user(request, f'{updated} payment(s) marked as cancelled.')

    @admin.action(description='Mark selected pending payments as failed')
    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status=Payment.STATUS_PENDING).update(status=Payment.STATUS_FAILED)
        self.message_user(request, f'{updated} payment(s) marked as failed.')
