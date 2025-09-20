from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Resident(models.Model):
    """Resident profile linked to Django User"""

    RESIDENT_TYPES = [
        ("owner", "Owner"),
        ("tenant", "Tenant"),
        ("family", "Family Member"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="resident")
    flat_number = models.CharField(max_length=4)
    block = models.CharField(max_length=2, blank=True)
    phone_number = models.CharField(max_length=13)
    alternate_phone = models.CharField(max_length=13, blank=True)
    resident_type = models.CharField(
        max_length=10,
        choices=RESIDENT_TYPES,
        default="owner",
    )
    is_committee_member = models.BooleanField(default=False)
    move_in_date = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    urgent_only = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.flat_number}"


class Staff(models.Model):
    """
    Staff profile for maintenance and management personnel.
    This includes Facility Managers, Accountants, and other maintenance staff.
    """

    # Staff role choices - different types of maintenance staff
    STAFF_ROLES = [
        ("facility_manager", "Facility Manager"),
        ("accountant", "Accountant"),
        ("security_head", "Security Head"),
        ("maintenance_supervisor", "Maintenance Supervisor"),
        ("electrician", "Electrician"),
        ("plumber", "Plumber"),
        ("cleaner", "Cleaner"),
        ("gardener", "Gardener"),
    ]

    # Employment status choices
    EMPLOYMENT_STATUS = [
        ("full_time", "Full Time"),
        ("part_time", "Part Time"),
        ("contract", "Contract"),
        ("consultant", "Consultant"),
    ]

    # Link to User model - staff members are also users but with different permissions
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")

    # Staff identification and role information
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique employee identifier",
    )
    staff_role = models.CharField(
        max_length=25,
        choices=STAFF_ROLES,
        help_text="Role/designation of the staff member",
    )
    department = models.CharField(
        max_length=50,
        blank=True,
        help_text="Department or team",
    )

    # Contact and personal information
    phone_number = models.CharField(max_length=13, help_text="Primary contact number")
    alternate_phone = models.CharField(
        max_length=13,
        blank=True,
        help_text="Alternate contact number",
    )
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)

    # Employment details
    employment_status = models.CharField(
        max_length=15,
        choices=EMPLOYMENT_STATUS,
        default="full_time",
    )
    hire_date = models.DateField(help_text="Date of joining")
    reporting_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subordinates",
        help_text="Direct supervisor/manager",
    )

    # Work permissions and access levels
    can_access_all_maintenance = models.BooleanField(
        default=False,
        help_text="Can view and manage all maintenance requests",
    )
    can_assign_requests = models.BooleanField(
        default=False,
        help_text="Can assign maintenance requests to other staff",
    )
    can_close_requests = models.BooleanField(
        default=False,
        help_text="Can mark maintenance requests as resolved/closed",
    )
    can_manage_finances = models.BooleanField(
        default=False,
        help_text="Can access financial reports and billing",
    )
    can_send_announcements = models.BooleanField(
        default=False,
        help_text="Can create and send announcements to residents",
    )

    # Work schedule and availability
    work_schedule = models.TextField(
        blank=True,
        help_text="Work schedule description (e.g., Mon-Fri 9AM-6PM)",
    )
    is_available_24x7 = models.BooleanField(
        default=False,
        help_text="Available for emergency calls 24/7",
    )

    # Status and activity tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Is currently employed and active",
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last system activity",
    )

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    urgent_only = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_staff_role_display()} ({self.employee_id})"

    def is_facility_manager(self) -> bool:
        """Check if staff member is a Facility Manager."""
        return self.staff_role == "facility_manager"

    def is_accountant(self) -> bool:
        """Check if staff member is an Accountant."""
        return self.staff_role == "accountant"

    def can_handle_maintenance(self) -> bool:
        """Check if staff member can handle maintenance requests."""
        # Facility managers and maintenance supervisors can handle all maintenance
        # Specific technicians can handle requests in their domain
        return (
            self.staff_role
            in [
                "facility_manager",
                "maintenance_supervisor",
                "electrician",
                "plumber",
            ]
            or self.can_access_all_maintenance
        )

    def get_subordinate_count(self) -> int:
        """Get count of direct subordinates."""
        return self.subordinates.filter(is_active=True).count()

    class Meta:
        verbose_name = "Staff Member"
        verbose_name_plural = "Staff Members"
        ordering = ["staff_role", "user__name"]


class AnnouncementCategory(models.Model):
    """Categories for announcements"""

    name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=7, default="#007bff")  # Hex color
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    is_urgent = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Announcement Categories"


class Announcement(models.Model):
    """Main announcements/notices"""

    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(AnnouncementCategory, on_delete=models.CASCADE)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="announcements",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Display options
    is_pinned = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Attachments
    attachment = models.FileField(upload_to="announcements/", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-is_pinned", "-is_urgent", "-created_at"]


class AnnouncementRead(models.Model):
    """Track who has read announcements"""

    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["announcement", "resident"]


class Comment(models.Model):
    """Comments on announcements"""

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.get_full_name()}"

    class Meta:
        ordering = ["created_at"]


class MaintenanceCategory(models.Model):
    """Categories for maintenance requests"""

    name = models.CharField(max_length=50)
    priority_level = models.IntegerField(
        default=1,
    )  # 1=Low, 2=Medium, 3=High, 4=Emergency
    estimated_resolution_hours = models.IntegerField(default=24)

    def __str__(self):
        return self.name


class MaintenanceRequest(models.Model):
    """
    Maintenance and complaint requests with enhanced staff assignment capabilities.
    Supports assignment to specific staff members based on their roles and permissions.
    """

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
        (4, "Emergency"),
    ]

    ticket_number = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(MaintenanceCategory, on_delete=models.CASCADE)

    # Request details
    resident = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
        help_text="Resident who submitted the request",
    )
    location = models.CharField(
        max_length=100,
        help_text="e.g., 'Flat A-101', 'Common Area - Lobby'",
    )
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    # Enhanced status tracking with staff assignment
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="submitted",
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_maintenance_requests",
        help_text="Staff member assigned to handle this request",
    )
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_maintenance_by",
        help_text="Staff member who assigned this request",
    )
    assigned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was assigned to a staff member",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was first acknowledged by staff",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was marked as resolved",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the request was officially closed",
    )

    # Attachments and documentation
    attachment = models.ImageField(upload_to="maintenance/", blank=True)

    # Estimated completion and actual completion tracking
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Estimated completion date/time",
    )
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual completion date/time",
    )

    # Cost tracking
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated cost for the maintenance work",
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual cost incurred for the maintenance work",
    )

    # Resident satisfaction
    resident_rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[(i, f"{i} Star{'s' if i != 1 else ''}") for i in range(1, 6)],
        help_text="Resident rating (1-5 stars)",
    )
    resident_feedback = models.TextField(
        blank=True,
        help_text="Resident feedback on the completed work",
    )

    def save(self, *args, **kwargs):
        # Generate unique ticket number if not already set
        if not self.ticket_number:
            last_ticket = (
                MaintenanceRequest.objects.filter(
                    created_at__year=timezone.now().year,
                )
                .order_by("id")
                .last()
            )

            if last_ticket:
                last_number = int(last_ticket.ticket_number.split("-")[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.ticket_number = f"MNT-{timezone.now().year}-{new_number:04d}"

        # Auto-set timestamps based on status changes
        if self.status == "acknowledged" and not self.acknowledged_at:
            self.acknowledged_at = timezone.now()
        elif self.status == "assigned" and not self.assigned_at:
            self.assigned_at = timezone.now()
        elif self.status == "resolved" and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status == "closed" and not self.closed_at:
            self.closed_at = timezone.now()

        super().save(*args, **kwargs)

    def assign_to_staff(self, staff_user, assigned_by_user=None):
        """
        Assign this maintenance request to a specific staff member.

        Args:
            staff_user: User object of the staff member to assign to
            assigned_by_user: User object of who is making the assignment
        """
        self.assigned_to = staff_user
        self.assigned_by = assigned_by_user
        self.assigned_at = timezone.now()

        # Update status to assigned if it's still in submitted/acknowledged state
        if self.status in ["submitted", "acknowledged"]:
            self.status = "assigned"

        self.save()

    def can_be_assigned_to(self, staff_user):
        """
        Check if this request can be assigned to a specific staff member.

        Args:
            staff_user: User object to check

        Returns:
            bool: True if the staff member can handle this request
        """
        if not staff_user.is_staff_member():
            return False

        try:
            staff_profile = staff_user.staff
            return staff_profile.can_handle_maintenance()
        except:
            return False

    def get_suitable_staff(self):
        """
        Get a queryset of staff members who can handle this maintenance request.

        Returns:
            QuerySet: Staff members who can handle this request
        """
        # Get all active staff who can handle maintenance
        suitable_staff = Staff.objects.filter(
            is_active=True,
            user__is_active=True,
        ).filter(
            models.Q(can_access_all_maintenance=True)
            | models.Q(
                staff_role__in=[
                    "facility_manager",
                    "maintenance_supervisor",
                    "electrician",
                    "plumber",
                ],
            ),
        )

        # For specific categories, we could add more filtering logic here
        # For example, electrical issues to electricians, plumbing to plumbers

        return suitable_staff

    def is_overdue(self):
        """Check if the maintenance request is overdue based on estimated completion."""
        if self.estimated_completion and self.status not in [
            "resolved",
            "closed",
            "cancelled",
        ]:
            return timezone.now() > self.estimated_completion
        return False

    def get_duration_since_created(self):
        """Get the duration since the request was created."""
        return timezone.now() - self.created_at

    def get_resolution_time(self):
        """Get the time taken to resolve the request."""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    class Meta:
        ordering = ["-priority", "-created_at"]
        verbose_name = "Maintenance Request"
        verbose_name_plural = "Maintenance Requests"


class MaintenanceUpdate(models.Model):
    """Updates/comments on maintenance requests"""

    request = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.CASCADE,
        related_name="updates",
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    status_changed_to = models.CharField(max_length=15, blank=True)
    attachment = models.ImageField(upload_to="maintenance_updates/", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update for {self.request.ticket_number}"

    class Meta:
        ordering = ["created_at"]


class CommonArea(models.Model):
    """Bookable common areas and amenities"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    capacity = models.IntegerField(default=1)
    booking_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    advance_booking_days = models.IntegerField(default=30)
    min_booking_hours = models.IntegerField(default=1)
    max_booking_hours = models.IntegerField(default=24)

    # Availability
    is_active = models.BooleanField(default=True)
    available_start_time = models.TimeField(default="06:00")
    available_end_time = models.TimeField(default="22:00")

    def __str__(self):
        return self.name


class Booking(models.Model):
    """Bookings for common areas"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    booking_number = models.CharField(max_length=20, unique=True)
    common_area = models.ForeignKey(CommonArea, on_delete=models.CASCADE)
    resident = models.ForeignKey(User, on_delete=models.CASCADE)

    # Booking details
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    purpose = models.CharField(max_length=200)
    guests_count = models.IntegerField(default=0)

    # Status and payment
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    total_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_number:
            # Generate unique booking number
            last_booking = (
                Booking.objects.filter(
                    created_at__year=timezone.now().year,
                )
                .order_by("id")
                .last()
            )

            if last_booking:
                last_number = int(last_booking.booking_number.split("-")[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.booking_number = f"BKG-{timezone.now().year}-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_number} - {self.common_area.name}"

    class Meta:
        ordering = ["-booking_date", "-start_time"]


class Event(models.Model):
    """Society events and meetings"""

    EVENT_TYPES = [
        ("meeting", "Committee Meeting"),
        ("maintenance", "Maintenance Activity"),
        ("social", "Social Event"),
        ("festival", "Festival Celebration"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)

    # Date and time
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)

    # Location and details
    location = models.CharField(max_length=200)
    max_attendees = models.IntegerField(null=True, blank=True)
    is_rsvp_required = models.BooleanField(default=False)

    # Organizer
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["start_datetime"]


class EventRSVP(models.Model):
    """RSVP responses for events"""

    RESPONSE_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("maybe", "Maybe"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rsvps")
    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    response = models.CharField(max_length=5, choices=RESPONSE_CHOICES)
    guests_count = models.IntegerField(default=0)
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["event", "resident"]


class MarketplaceItem(models.Model):
    """Marketplace for residents"""

    ITEM_TYPES = [
        ("sell", "For Sale"),
        ("buy", "Looking to Buy"),
        ("service", "Service Offered"),
        ("need_service", "Service Needed"),
        ("lost", "Lost Item"),
        ("found", "Found Item"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("sold", "Sold/Completed"),
        ("expired", "Expired"),
        ("removed", "Removed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    item_type = models.CharField(max_length=15, choices=ITEM_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Listing details
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="marketplace_items",
    )
    contact_phone = models.CharField(max_length=15, blank=True)

    # Status and dates
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Images
    image1 = models.ImageField(upload_to="marketplace/", blank=True)
    image2 = models.ImageField(upload_to="marketplace/", blank=True)
    image3 = models.ImageField(upload_to="marketplace/", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-created_at"]


class Document(models.Model):
    """Document repository"""

    DOCUMENT_TYPES = [
        ("bylaw", "Society Bylaws"),
        ("minutes", "Meeting Minutes"),
        ("financial", "Financial Reports"),
        ("policy", "Policies"),
        ("form", "Forms"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="documents/")

    # Access control
    is_public = models.BooleanField(default=True)  # All residents can view
    committee_only = models.BooleanField(default=False)

    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-uploaded_at"]


class EmergencyContact(models.Model):
    """Emergency and important contacts"""

    CONTACT_TYPES = [
        ("emergency", "Emergency Services"),
        ("maintenance", "Maintenance Staff"),
        ("security", "Security"),
        ("management", "Management"),
        ("vendor", "Approved Vendors"),
        ("medical", "Medical Services"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=100)
    contact_type = models.CharField(max_length=15, choices=CONTACT_TYPES)
    phone_number = models.CharField(max_length=15)
    alternate_phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)

    # Availability
    available_24x7 = models.BooleanField(default=False)
    available_hours = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_contact_type_display()})"

    class Meta:
        ordering = ["contact_type", "name"]


# Create your models here.
class NotificationType(models.Model):
    """Types of notifications"""

    DELIVERY_METHODS = [
        ("email", "Email Only"),
        ("sms", "SMS Only"),
        ("both", "Email + SMS"),
        ("in_app", "In-App Only"),
        ("all", "All Methods"),
    ]

    name = models.CharField(max_length=50)
    template_name = models.CharField(max_length=100)  # Email template
    sms_template = models.TextField(blank=True)  # SMS template
    default_delivery = models.CharField(
        max_length=10,
        choices=DELIVERY_METHODS,
        default="email",
    )
    is_urgent = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Notification(models.Model):
    """In-app notifications storage"""

    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("read", "Read"),
        ("failed", "Failed"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)

    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Extra data for links, etc.

    # Delivery tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="sent")
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Related objects (generic foreign key alternative)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    def mark_as_read(self):
        if self.status != "read":
            self.status = "read"
            self.read_at = timezone.now()
            self.save()

    def get_related_object(self):
        """Get the related object (announcement, maintenance request, etc.)"""
        if self.related_object_type and self.related_object_id:
            from django.apps import apps

            try:
                # Try different app configurations
                app_labels = ["backend", "the_khaki_estate.backend"]

                for app_label in app_labels:
                    try:
                        model = apps.get_model(app_label, self.related_object_type)
                        return model.objects.get(id=self.related_object_id)
                    except (LookupError, ValueError):
                        continue

                # If no app label worked, try getting the model directly from current module
                model_name = self.related_object_type.lower()
                if model_name == "maintenancerequest":
                    return MaintenanceRequest.objects.get(id=self.related_object_id)
                if model_name == "announcement":
                    return Announcement.objects.get(id=self.related_object_id)

            except Exception as e:
                print(f"Error getting related object: {e}")
                return None
        return None

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"

    class Meta:
        ordering = ["-created_at"]
