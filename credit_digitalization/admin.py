from django.contrib import admin

from .models import ApplicationAuditTrail, CreditApplication


class ApplicationAuditInline(admin.TabularInline):
    model = ApplicationAuditTrail
    extra = 0
    can_delete = False
    readonly_fields = (
        'actor', 'action', 'from_status', 'to_status', 'notes', 'created_at'
    )


@admin.register(CreditApplication)
class CreditApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'application_number', 'consumer_name', 'dealer_name',
        'status', 'created_by', 'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('application_number', 'consumer_name', 'nik', 'dealer_name')
    readonly_fields = (
        'application_number', 'status', 'created_by', 'reviewed_by',
        'consent_at', 'submitted_at', 'reviewed_at', 'created_at', 'updated_at',
    )
    inlines = [ApplicationAuditInline]


@admin.register(ApplicationAuditTrail)
class ApplicationAuditTrailAdmin(admin.ModelAdmin):
    list_display = ('application', 'action', 'actor', 'from_status', 'to_status', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('application__application_number', 'actor__username', 'notes')
    readonly_fields = (
        'application', 'actor', 'action', 'from_status',
        'to_status', 'notes', 'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
