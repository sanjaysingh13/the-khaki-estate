from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Announcement
from .models import AnnouncementCategory
from .models import ApproverAssignment
from .models import Booking
from .models import CommonArea
from .models import Event
from .models import GalleryComment
from .models import GalleryLike
from .models import GalleryPhoto
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


# ============================================================================
# GALLERY ADMIN INTERFACES
# ============================================================================

@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    """
    Admin interface for managing gallery photos.
    
    Provides comprehensive management of community photos with
    moderation capabilities, approval workflows, and bulk operations.
    """
    
    list_display = [
        'id',
        'photo_thumbnail',
        'author_name',
        'caption_preview',
        'is_approved',
        'is_featured',
        'like_count_display',
        'comment_count_display',
        'created_at',
    ]
    
    list_filter = [
        'is_approved',
        'is_featured',
        'created_at',
        'author__user_type',
    ]
    
    search_fields = [
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
        'caption',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'like_count_display',
        'comment_count_display',
    ]
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('photo', 'caption', 'author')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_featured'),
            'description': 'Control photo visibility and featured status'
        }),
        ('Statistics', {
            'fields': ('like_count_display', 'comment_count_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_photos',
        'unapprove_photos',
        'feature_photos',
        'unfeature_photos',
        'delete_selected_photos',
    ]
    
    def photo_thumbnail(self, obj):
        """Display a thumbnail of the photo in the admin list."""
        if obj.photo:
            return f'<img src="{obj.photo.url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">'
        return "No photo"
    photo_thumbnail.allow_tags = True
    photo_thumbnail.short_description = "Photo"
    
    def author_name(self, obj):
        """Display the author's full name."""
        return obj.author.get_full_name() or obj.author.username
    author_name.short_description = "Author"
    author_name.admin_order_field = "author__first_name"
    
    def caption_preview(self, obj):
        """Display a preview of the caption."""
        if obj.caption:
            return obj.caption[:50] + "..." if len(obj.caption) > 50 else obj.caption
        return "No caption"
    caption_preview.short_description = "Caption"
    
    def like_count_display(self, obj):
        """Display the number of likes."""
        return obj.get_like_count()
    like_count_display.short_description = "Likes"
    
    def comment_count_display(self, obj):
        """Display the number of comments."""
        return obj.get_comment_count()
    comment_count_display.short_description = "Comments"
    
    def approve_photos(self, request, queryset):
        """Bulk approve selected photos."""
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f'{updated} photos have been approved and are now visible to residents.'
        )
    approve_photos.short_description = "Approve selected photos"
    
    def unapprove_photos(self, request, queryset):
        """Bulk unapprove selected photos."""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f'{updated} photos have been unapproved and are now hidden from residents.'
        )
    unapprove_photos.short_description = "Unapprove selected photos"
    
    def feature_photos(self, request, queryset):
        """Bulk feature selected photos."""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f'{updated} photos have been featured and will appear prominently in the gallery.'
        )
    feature_photos.short_description = "Feature selected photos"
    
    def unfeature_photos(self, request, queryset):
        """Bulk unfeature selected photos."""
        updated = queryset.update(is_featured=False)
        self.message_user(
            request,
            f'{updated} photos have been unfeatured.'
        )
    unfeature_photos.short_description = "Unfeature selected photos"
    
    def delete_selected_photos(self, request, queryset):
        """Bulk delete selected photos with confirmation."""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f'{count} photos have been permanently deleted.'
        )
    delete_selected_photos.short_description = "Delete selected photos"


@admin.register(GalleryComment)
class GalleryCommentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing gallery comments.
    
    Provides moderation capabilities for photo comments with
    approval workflows and content management.
    """
    
    list_display = [
        'id',
        'author_name',
        'photo_preview',
        'content_preview',
        'is_approved',
        'is_reply',
        'created_at',
    ]
    
    list_filter = [
        'is_approved',
        'created_at',
        'photo__author__user_type',
    ]
    
    search_fields = [
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
        'content',
        'photo__caption',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('photo', 'author', 'content', 'parent')
        }),
        ('Moderation', {
            'fields': ('is_approved',),
            'description': 'Control comment visibility'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'approve_comments',
        'unapprove_comments',
        'delete_selected_comments',
    ]
    
    def author_name(self, obj):
        """Display the author's full name."""
        return obj.author.get_full_name() or obj.author.username
    author_name.short_description = "Author"
    author_name.admin_order_field = "author__first_name"
    
    def photo_preview(self, obj):
        """Display a preview of the associated photo."""
        if obj.photo.photo:
            return f'<img src="{obj.photo.photo.url}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">'
        return "No photo"
    photo_preview.allow_tags = True
    photo_preview.short_description = "Photo"
    
    def content_preview(self, obj):
        """Display a preview of the comment content."""
        if obj.content:
            return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        return "No content"
    content_preview.short_description = "Content"
    
    def is_reply(self, obj):
        """Check if this is a reply to another comment."""
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = "Is Reply"
    
    def approve_comments(self, request, queryset):
        """Bulk approve selected comments."""
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f'{updated} comments have been approved and are now visible.'
        )
    approve_comments.short_description = "Approve selected comments"
    
    def unapprove_comments(self, request, queryset):
        """Bulk unapprove selected comments."""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f'{updated} comments have been unapproved and are now hidden.'
        )
    unapprove_comments.short_description = "Unapprove selected comments"
    
    def delete_selected_comments(self, request, queryset):
        """Bulk delete selected comments."""
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request,
            f'{count} comments have been permanently deleted.'
        )
    delete_selected_comments.short_description = "Delete selected comments"


@admin.register(GalleryLike)
class GalleryLikeAdmin(admin.ModelAdmin):
    """
    Admin interface for managing gallery likes.
    
    Provides read-only access to like data for analytics and moderation.
    """
    
    list_display = [
        'id',
        'user_name',
        'photo_preview',
        'created_at',
    ]
    
    list_filter = [
        'created_at',
        'user__user_type',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'photo__caption',
    ]
    
    readonly_fields = [
        'user',
        'photo',
        'created_at',
    ]
    
    def user_name(self, obj):
        """Display the user's full name."""
        return obj.user.get_full_name() or obj.user.username
    user_name.short_description = "User"
    user_name.admin_order_field = "user__first_name"
    
    def photo_preview(self, obj):
        """Display a preview of the liked photo."""
        if obj.photo.photo:
            return f'<img src="{obj.photo.photo.url}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;">'
        return "No photo"
    photo_preview.allow_tags = True
    photo_preview.short_description = "Photo"
    
    def has_add_permission(self, request):
        """Disable adding likes through admin (likes are created via user interaction)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing likes through admin."""
        return False
