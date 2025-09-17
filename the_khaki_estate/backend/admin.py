from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Announcement
from .models import AnnouncementCategory
from .models import Booking
from .models import CommonArea
from .models import Event
from .models import MaintenanceCategory
from .models import MaintenanceRequest
from .models import MarketplaceItem
from .models import Notification
from .models import NotificationType
from .models import Resident

User = get_user_model()


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    """Admin interface for managing resident profiles"""

    list_display = [
        "user",
        "flat_number",
        "block",
        "resident_type",
        "is_committee_member",
        "phone_number",
        "move_in_date",
    ]
    list_filter = [
        "resident_type",
        "is_committee_member",
        "block",
        "email_notifications",
        "sms_notifications",
    ]
    search_fields = [
        "user__username",
        "user__email",
        "user__name",
        "flat_number",
        "phone_number",
    ]
    readonly_fields = ["user"]

    fieldsets = (
        (
            "User Information",
            {
                "fields": ("user",),
            },
        ),
        (
            "Residence Details",
            {
                "fields": ("flat_number", "block", "resident_type", "move_in_date"),
            },
        ),
        (
            "Contact Information",
            {
                "fields": ("phone_number", "alternate_phone"),
            },
        ),
        (
            "Emergency Contact",
            {
                "fields": ("emergency_contact_name", "emergency_contact_phone"),
            },
        ),
        (
            "Permissions",
            {
                "fields": ("is_committee_member",),
            },
        ),
        (
            "Notification Preferences",
            {
                "fields": ("email_notifications", "sms_notifications", "urgent_only"),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


# Inline admin for showing Resident info in User admin
class ResidentInline(admin.StackedInline):
    model = Resident
    can_delete = False
    verbose_name_plural = "Resident Profile"
    fields = [
        "flat_number",
        "block",
        "resident_type",
        "phone_number",
        "alternate_phone",
        "is_committee_member",
        "move_in_date",
        "emergency_contact_name",
        "emergency_contact_phone",
        "email_notifications",
        "sms_notifications",
        "urgent_only",
    ]


# Extend User admin to include Resident profile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    inlines = (ResidentInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register User admin with Resident inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register other models with basic admin
admin.site.register(AnnouncementCategory)
admin.site.register(Announcement)
admin.site.register(MaintenanceCategory)
admin.site.register(MaintenanceRequest)
admin.site.register(CommonArea)
admin.site.register(Booking)
admin.site.register(Event)
admin.site.register(MarketplaceItem)
admin.site.register(NotificationType)
admin.site.register(Notification)
