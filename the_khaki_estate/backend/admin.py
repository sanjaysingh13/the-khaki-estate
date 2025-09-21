from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Announcement
from .models import AnnouncementCategory
from .models import ApproverAssignment
from .models import Booking
from .models import CommonArea
from .models import Event
from .models import MaintenanceCategory
from .models import MaintenanceRequest
from .models import MarketplaceItem
from .models import Notification
from .models import NotificationType
from .models import Resident
from .models import Staff

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


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """
    Admin interface for managing staff profiles.
    Provides comprehensive management of maintenance staff including their roles,
    permissions, and employment details.
    """

    list_display = [
        "user",
        "employee_id",
        "staff_role",
        "department",
        "employment_status",
        "is_active",
        "hire_date",
        "can_access_all_maintenance",
    ]
    list_filter = [
        "staff_role",
        "employment_status",
        "is_active",
        "department",
        "can_access_all_maintenance",
        "can_assign_requests",
        "can_close_requests",
        "can_manage_finances",
        "is_available_24x7",
    ]
    search_fields = [
        "user__username",
        "user__email",
        "user__name",
        "employee_id",
        "phone_number",
        "department",
    ]
    readonly_fields = ["user", "created_at", "updated_at", "last_activity"]

    fieldsets = (
        (
            "User Information",
            {
                "fields": ("user",),
            },
        ),
        (
            "Staff Details",
            {
                "fields": (
                    "employee_id",
                    "staff_role",
                    "department",
                    "employment_status",
                    "hire_date",
                    "reporting_to",
                ),
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "phone_number",
                    "alternate_phone",
                    "emergency_contact_name",
                    "emergency_contact_phone",
                ),
            },
        ),
        (
            "Work Permissions",
            {
                "fields": (
                    "can_access_all_maintenance",
                    "can_assign_requests",
                    "can_close_requests",
                    "can_manage_finances",
                    "can_send_announcements",
                ),
                "description": "Define what this staff member can do in the system",
            },
        ),
        (
            "Schedule & Availability",
            {
                "fields": (
                    "work_schedule",
                    "is_available_24x7",
                    "is_active",
                ),
            },
        ),
        (
            "Notification Preferences",
            {
                "fields": ("email_notifications", "sms_notifications", "urgent_only"),
            },
        ),
        (
            "Activity Tracking",
            {
                "fields": ("last_activity", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return (
            super().get_queryset(request).select_related("user", "reporting_to__user")
        )

    def save_model(self, request, obj, form, change):
        """
        Custom save method to set default permissions based on staff role
        if this is a new staff member.
        """
        if not change:  # New staff member
            # Set default permissions based on role
            role_permissions = {
                "facility_manager": {
                    "can_access_all_maintenance": True,
                    "can_assign_requests": True,
                    "can_close_requests": True,
                    "can_send_announcements": True,
                },
                "accountant": {
                    "can_manage_finances": True,
                    "can_send_announcements": True,
                },
                "maintenance_supervisor": {
                    "can_access_all_maintenance": True,
                    "can_assign_requests": True,
                    "can_close_requests": True,
                },
            }

            permissions = role_permissions.get(obj.staff_role, {})
            for perm, value in permissions.items():
                if not hasattr(obj, perm) or getattr(obj, perm) is None:
                    setattr(obj, perm, value)

        super().save_model(request, obj, form, change)


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


# Inline admin for showing Staff info in User admin
class StaffInline(admin.StackedInline):
    model = Staff
    can_delete = False
    verbose_name_plural = "Staff Profile"
    fields = [
        "employee_id",
        "staff_role",
        "department",
        "employment_status",
        "hire_date",
        "phone_number",
        "alternate_phone",
        "can_access_all_maintenance",
        "can_assign_requests",
        "can_close_requests",
        "can_manage_finances",
        "can_send_announcements",
        "is_active",
        "work_schedule",
        "is_available_24x7",
        "email_notifications",
        "sms_notifications",
        "urgent_only",
    ]


# Inline admin for showing ApproverAssignment in CommonArea admin
class ApproverAssignmentInline(admin.TabularInline):
    model = ApproverAssignment
    extra = 1
    verbose_name = "Approver Assignment"
    verbose_name_plural = "Approver Assignments"
    fields = [
        "approver",
        "is_active",
        "assigned_at",
        "notes",
    ]
    readonly_fields = ["assigned_at"]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("approver", "assigned_by")
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the approver field to only show active residents.
        """
        if db_field.name == "approver":
            # Only show active residents
            residents = User.objects.filter(
                user_type="resident",
                is_active=True,
                resident__isnull=False
            ).select_related("resident")
            kwargs["queryset"] = residents
        elif db_field.name == "assigned_by":
            # Only show staff users who can manage assignments
            staff_users = User.objects.filter(
                user_type="staff",
                is_active=True,
                staff__is_active=True,
                staff__can_send_announcements=True,  # Staff with admin privileges
            ).union(
                User.objects.filter(
                    user_type="staff",
                    is_active=True,
                    staff__is_active=True,
                    staff__staff_role__in=[
                        "facility_manager",
                        "maintenance_supervisor",
                    ],
                ),
            )
            kwargs["queryset"] = staff_users
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Extend User admin to include both Resident and Staff profiles
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin that dynamically shows either Resident or Staff inline
    based on the user's user_type field.
    """

    # Add user_type to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (("User Type", {"fields": ("user_type",)}),)

    # Add user_type to the list display
    list_display = BaseUserAdmin.list_display + ("user_type",)
    list_filter = BaseUserAdmin.list_filter + ("user_type",)

    def get_inline_instances(self, request, obj=None):
        """
        Dynamically return appropriate inline based on user type.
        - For residents: show ResidentInline
        - For staff: show StaffInline
        """
        if not obj:
            return list()

        inlines = []

        # Show appropriate inline based on user type
        if obj.user_type == "resident":
            # Check if resident profile exists
            if hasattr(obj, "resident"):
                inlines = [ResidentInline(self.model, self.admin_site)]
        elif obj.user_type == "staff":
            # Check if staff profile exists
            if hasattr(obj, "staff"):
                inlines = [StaffInline(self.model, self.admin_site)]

        return [inline for inline in inlines]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("resident", "staff")


# Re-register User admin with enhanced functionality
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Enhanced MaintenanceRequest admin with staff assignment capabilities
@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    """
    Enhanced admin for maintenance requests with staff assignment and tracking.
    """

    list_display = [
        "ticket_number",
        "title",
        "resident",
        "category",
        "priority",
        "status",
        "assigned_to",
        "created_at",
        "is_overdue",
    ]

    list_filter = [
        "status",
        "priority",
        "category",
        "assigned_to",
        "created_at",
        "resolved_at",
    ]

    search_fields = [
        "ticket_number",
        "title",
        "description",
        "resident__username",
        "resident__name",
        "location",
    ]

    readonly_fields = [
        "ticket_number",
        "created_at",
        "updated_at",
        "acknowledged_at",
        "assigned_at",
        "resolved_at",
        "closed_at",
    ]

    fieldsets = (
        (
            "Request Details",
            {
                "fields": (
                    "ticket_number",
                    "title",
                    "description",
                    "category",
                    "location",
                    "priority",
                    "attachment",
                ),
            },
        ),
        (
            "Requester Information",
            {
                "fields": ("resident",),
            },
        ),
        (
            "Assignment & Status",
            {
                "fields": (
                    "status",
                    "assigned_to",
                    "assigned_by",
                    "estimated_completion",
                    "actual_completion",
                ),
            },
        ),
        (
            "Cost Tracking",
            {
                "fields": ("estimated_cost", "actual_cost"),
                "classes": ("collapse",),
            },
        ),
        (
            "Resident Feedback",
            {
                "fields": ("resident_rating", "resident_feedback"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "acknowledged_at",
                    "assigned_at",
                    "resolved_at",
                    "closed_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "resident",
                "assigned_to",
                "assigned_by",
                "category",
            )
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize the assigned_to field to only show staff members who can handle maintenance.
        """
        if db_field.name == "assigned_to":
            # Only show staff users who can handle maintenance
            staff_users = User.objects.filter(
                user_type="staff",
                is_active=True,
                staff__is_active=True,
                staff__can_access_all_maintenance=True,
            ).union(
                User.objects.filter(
                    user_type="staff",
                    is_active=True,
                    staff__is_active=True,
                    staff__staff_role__in=[
                        "facility_manager",
                        "maintenance_supervisor",
                        "electrician",
                        "plumber",
                    ],
                ),
            )
            kwargs["queryset"] = staff_users
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(
        description="Overdue",
        boolean=True,
    )
    def is_overdue(self, obj):
        """Display whether the request is overdue."""
        return obj.is_overdue()


# Enhanced CommonArea admin with approver assignment management
@admin.register(CommonArea)
class CommonAreaAdmin(admin.ModelAdmin):
    """
    Enhanced admin for CommonArea with inline approver assignment management.
    """
    
    list_display = [
        "name",
        "capacity",
        "booking_fee",
        "is_active",
        "get_current_approver",
        "advance_booking_days",
    ]
    
    list_filter = [
        "is_active",
        "advance_booking_days",
        "min_booking_hours",
        "max_booking_hours",
    ]
    
    search_fields = [
        "name",
        "description",
    ]
    
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "description",
                    "is_active",
                ),
            },
        ),
        (
            "Capacity & Booking",
            {
                "fields": (
                    "capacity",
                    "booking_fee",
                    "advance_booking_days",
                    "min_booking_hours",
                    "max_booking_hours",
                ),
            },
        ),
        (
            "Availability",
            {
                "fields": (
                    "available_start_time",
                    "available_end_time",
                ),
            },
        ),
    )
    
    inlines = [ApproverAssignmentInline]
    
    def get_current_approver(self, obj):
        """
        Display the current active approver for this common area.
        """
        approver = obj.get_designated_approver()
        if approver:
            return f"{approver.get_full_name() or approver.username} ({approver.email})"
        return "No approver assigned"
    get_current_approver.short_description = "Current Approver"
    get_current_approver.admin_order_field = "approver_assignments__approver__username"


# Enhanced ApproverAssignment admin
@admin.register(ApproverAssignment)
class ApproverAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing approver assignments.
    """
    
    list_display = [
        "common_area",
        "approver",
        "is_active",
        "assigned_by",
        "assigned_at",
    ]
    
    list_filter = [
        "is_active",
        "common_area",
        "assigned_at",
        "assigned_by",
    ]
    
    search_fields = [
        "common_area__name",
        "approver__username",
        "approver__email",
        "approver__first_name",
        "approver__last_name",
        "notes",
    ]
    
    readonly_fields = ["assigned_at"]
    
    fieldsets = (
        (
            "Assignment Details",
            {
                "fields": (
                    "common_area",
                    "approver",
                    "is_active",
                ),
            },
        ),
        (
            "Administration",
            {
                "fields": (
                    "assigned_by",
                    "assigned_at",
                ),
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            "common_area", "approver", "assigned_by"
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customize foreign key fields with appropriate filters.
        """
        if db_field.name == "approver":
            # Only show active residents
            residents = User.objects.filter(
                user_type="resident",
                is_active=True,
                resident__isnull=False
            ).select_related("resident")
            kwargs["queryset"] = residents
        elif db_field.name == "assigned_by":
            # Only show staff users who can manage assignments
            staff_users = User.objects.filter(
                user_type="staff",
                is_active=True,
                staff__is_active=True,
                staff__can_send_announcements=True,
            ).union(
                User.objects.filter(
                    user_type="staff",
                    is_active=True,
                    staff__is_active=True,
                    staff__staff_role__in=[
                        "facility_manager",
                        "maintenance_supervisor",
                    ],
                ),
            )
            kwargs["queryset"] = staff_users
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Set the assigned_by field to the current user if not set.
        """
        if not obj.assigned_by:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


# Register other models with basic admin
admin.site.register(AnnouncementCategory)
admin.site.register(Announcement)
admin.site.register(MaintenanceCategory)
admin.site.register(Booking)
admin.site.register(Event)
admin.site.register(MarketplaceItem)
admin.site.register(NotificationType)
admin.site.register(Notification)
