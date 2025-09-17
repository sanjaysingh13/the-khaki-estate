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
    """Maintenance and complaint requests"""

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
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
    resident = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.CharField(
        max_length=100,
    )  # e.g., "Flat A-101", "Common Area - Lobby"
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    # Status tracking
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
        related_name="assigned_requests",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Attachments
    attachment = models.ImageField(upload_to="maintenance/", blank=True)

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate unique ticket number
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

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    class Meta:
        ordering = ["-created_at"]


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
                model = apps.get_model(
                    "the_khaki_estate.backend",
                    self.related_object_type,
                )
                return model.objects.get(id=self.related_object_id)
            except:
                return None
        return None

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"

    class Meta:
        ordering = ["-created_at"]
