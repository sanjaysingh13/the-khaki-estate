"""
Factory classes for creating test data for backend models.
These factories use factory_boy to generate realistic test data for all models.
"""

import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from django.utils import timezone
from factory import Faker
from factory import LazyAttribute
from factory import SubFactory
from factory.django import DjangoModelFactory

from the_khaki_estate.backend.models import Announcement
from the_khaki_estate.backend.models import AnnouncementCategory
from the_khaki_estate.backend.models import AnnouncementRead
from the_khaki_estate.backend.models import Booking
from the_khaki_estate.backend.models import Comment
from the_khaki_estate.backend.models import CommonArea
from the_khaki_estate.backend.models import Document
from the_khaki_estate.backend.models import EmergencyContact
from the_khaki_estate.backend.models import Event
from the_khaki_estate.backend.models import EventRSVP
from the_khaki_estate.backend.models import MaintenanceCategory
from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import MaintenanceUpdate
from the_khaki_estate.backend.models import MarketplaceItem
from the_khaki_estate.backend.models import Notification
from the_khaki_estate.backend.models import NotificationType
from the_khaki_estate.backend.models import Resident
from the_khaki_estate.backend.models import Staff
from the_khaki_estate.users.tests.factories import ResidentUserFactory
from the_khaki_estate.users.tests.factories import StaffUserFactory
from the_khaki_estate.users.tests.factories import UserFactory


class ResidentFactory(DjangoModelFactory):
    """
    Factory for creating Resident instances with realistic test data.
    Generates residents with various types (owner, tenant, family) and realistic flat numbers.
    """

    # Link to User model
    user = SubFactory(ResidentUserFactory)

    # Resident-specific fields
    flat_number = Faker("numerify", text="###")  # 3-digit flat number
    block = Faker("random_element", elements=["A", "B", "C", "D"])
    phone_number = Faker("bothify", text="+91##########")  # Indian phone format
    alternate_phone = Faker("bothify", text="+91##########")
    resident_type = Faker("random_element", elements=["owner", "tenant", "family"])
    is_committee_member = Faker("boolean", chance_of_getting_true=20)  # 20% chance

    # Dates and emergency contacts
    move_in_date = Faker("date_between", start_date="-5y", end_date="today")
    emergency_contact_name = Faker("name")
    emergency_contact_phone = Faker("bothify", text="+91##########")

    # Notification preferences
    email_notifications = Faker("boolean", chance_of_getting_true=80)
    sms_notifications = Faker("boolean", chance_of_getting_true=30)
    urgent_only = Faker("boolean", chance_of_getting_true=10)

    class Meta:
        model = Resident
        django_get_or_create = ["flat_number"]


class StaffFactory(DjangoModelFactory):
    """
    Factory for creating Staff instances with realistic test data.
    Generates staff with various roles and appropriate permissions.
    """

    # Link to User model
    user = SubFactory(StaffUserFactory)

    # Staff identification and role information
    employee_id = Faker("bothify", text="EMP###")  # EMP001, EMP002, etc.
    staff_role = Faker(
        "random_element",
        elements=[
            "facility_manager",
            "accountant",
            "security_head",
            "maintenance_supervisor",
            "electrician",
            "plumber",
            "cleaner",
            "gardener",
        ],
    )
    department = LazyAttribute(
        lambda obj: {
            "facility_manager": "Management",
            "accountant": "Finance",
            "security_head": "Security",
            "maintenance_supervisor": "Maintenance",
            "electrician": "Maintenance",
            "plumber": "Maintenance",
            "cleaner": "Housekeeping",
            "gardener": "Landscaping",
        }.get(obj.staff_role, "General"),
    )

    # Contact and personal information
    phone_number = Faker("bothify", text="+91##########")
    alternate_phone = Faker("bothify", text="+91##########")
    emergency_contact_name = Faker("name")
    emergency_contact_phone = Faker("bothify", text="+91##########")

    # Employment details
    employment_status = Faker(
        "random_element",
        elements=["full_time", "part_time", "contract", "consultant"],
    )
    hire_date = Faker("date_between", start_date="-3y", end_date="today")
    reporting_to = None  # Can be set manually in tests

    # Work permissions and access levels - set based on role
    can_access_all_maintenance = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "maintenance_supervisor",
        ],
    )
    can_assign_requests = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "maintenance_supervisor",
        ],
    )
    can_close_requests = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "maintenance_supervisor",
            "electrician",
            "plumber",
        ],
    )
    can_manage_finances = LazyAttribute(lambda obj: obj.staff_role == "accountant")
    can_send_announcements = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "accountant",
            "security_head",
        ],
    )

    # Work schedule and availability
    work_schedule = LazyAttribute(
        lambda obj: {
            "facility_manager": "Mon-Fri 9AM-6PM, On-call weekends",
            "accountant": "Mon-Fri 9AM-5PM",
            "security_head": "24/7 On-call",
            "maintenance_supervisor": "Mon-Sat 8AM-6PM, Emergency on-call",
            "electrician": "Mon-Fri 8AM-5PM, Emergency on-call",
            "plumber": "Mon-Fri 8AM-5PM, Emergency on-call",
            "cleaner": "Mon-Sat 6AM-2PM",
            "gardener": "Mon-Fri 7AM-3PM",
        }.get(obj.staff_role, "Mon-Fri 9AM-5PM"),
    )

    is_available_24x7 = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "security_head",
        ],
    )

    # Status and activity tracking
    is_active = True  # Default to active
    last_activity = Faker(
        "date_time_between",
        start_date="-7d",
        end_date="now",
        tzinfo=UTC,
    )

    # Notification preferences
    email_notifications = Faker("boolean", chance_of_getting_true=90)
    sms_notifications = LazyAttribute(
        lambda obj: obj.staff_role
        in [
            "facility_manager",
            "security_head",
            "maintenance_supervisor",
        ],
    )
    urgent_only = Faker("boolean", chance_of_getting_true=30)

    class Meta:
        model = Staff
        django_get_or_create = ["employee_id"]


class AnnouncementCategoryFactory(DjangoModelFactory):
    """
    Factory for creating AnnouncementCategory instances.
    Generates categories with realistic names and color codes.
    """

    name = Faker(
        "random_element",
        elements=[
            "General",
            "Maintenance",
            "Security",
            "Events",
            "Financial",
            "Emergency",
            "Policy",
            "Community",
            "Utilities",
        ],
    )
    color_code = Faker(
        "random_element",
        elements=[
            "#007bff",
            "#28a745",
            "#dc3545",
            "#ffc107",
            "#17a2b8",
            "#6f42c1",
            "#fd7e14",
            "#20c997",
            "#6c757d",
        ],
    )
    icon = Faker(
        "random_element",
        elements=[
            "fas fa-bullhorn",
            "fas fa-tools",
            "fas fa-shield-alt",
            "fas fa-calendar",
            "fas fa-dollar-sign",
            "fas fa-exclamation-triangle",
        ],
    )
    is_urgent = Faker("boolean", chance_of_getting_true=20)

    class Meta:
        model = AnnouncementCategory


class AnnouncementFactory(DjangoModelFactory):
    """
    Factory for creating Announcement instances.
    Generates announcements with realistic content and metadata.
    """

    title = Faker("sentence", nb_words=6)
    content = Faker("text", max_nb_chars=500)
    category = SubFactory(AnnouncementCategoryFactory)
    author = SubFactory(UserFactory)

    # Display options
    is_pinned = Faker("boolean", chance_of_getting_true=10)
    is_urgent = Faker("boolean", chance_of_getting_true=15)
    valid_until = LazyAttribute(
        lambda obj: timezone.now() + timedelta(days=random.randint(1, 30))
        if random.random() > 0.3
        else None,
    )

    class Meta:
        model = Announcement


class MaintenanceCategoryFactory(DjangoModelFactory):
    """
    Factory for creating MaintenanceCategory instances.
    Generates maintenance categories with realistic names and priority levels.
    """

    name = Faker(
        "random_element",
        elements=[
            "Plumbing",
            "Electrical",
            "HVAC",
            "Elevator",
            "Security",
            "Cleaning",
            "Landscaping",
            "Structural",
            "Appliance",
            "Common Area",
        ],
    )
    priority_level = Faker("random_element", elements=[1, 2, 3, 4])
    estimated_resolution_hours = Faker("random_int", min=1, max=168)  # 1 hour to 1 week

    class Meta:
        model = MaintenanceCategory


class MaintenanceRequestFactory(DjangoModelFactory):
    """
    Factory for creating MaintenanceRequest instances.
    Generates maintenance requests with realistic ticket numbers and details.
    """

    title = Faker("sentence", nb_words=5)
    description = Faker("text", max_nb_chars=300)
    category = SubFactory(MaintenanceCategoryFactory)
    resident = SubFactory(UserFactory, user_type="resident")

    # Request details
    location = Faker("sentence", nb_words=3)  # e.g., "Flat A-101"
    priority = Faker("random_element", elements=[1, 2, 3, 4])
    status = Faker(
        "random_element",
        elements=[
            "submitted",
            "acknowledged",
            "assigned",
            "in_progress",
            "resolved",
            "closed",
        ],
    )

    # Enhanced assignment to staff (set to None by default, can be overridden in tests)
    assigned_to = None
    assigned_by = None

    # Timestamps with enhanced tracking (simplified for factory)
    created_at = Faker("date_time_between", start_date="-30d", end_date="now")
    acknowledged_at = None
    assigned_at = None
    resolved_at = None
    closed_at = None

    # Cost tracking (simplified for factory)
    estimated_cost = None
    actual_cost = None

    # Resident feedback (simplified for factory)
    resident_rating = None
    resident_feedback = ""

    class Meta:
        model = MaintenanceRequest


class CommonAreaFactory(DjangoModelFactory):
    """
    Factory for creating CommonArea instances.
    Generates common areas with realistic amenities and booking rules.
    """

    name = Faker(
        "random_element",
        elements=[
            "Community Hall",
            "Swimming Pool",
            "Gym",
            "Tennis Court",
            "Party Hall",
            "Library",
            "Garden",
            "Playground",
            "Conference Room",
        ],
    )
    description = Faker("text", max_nb_chars=200)
    capacity = Faker("random_int", min=5, max=100)
    booking_fee = Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    advance_booking_days = Faker("random_int", min=1, max=60)
    min_booking_hours = Faker("random_int", min=1, max=4)
    max_booking_hours = Faker("random_int", min=4, max=24)

    # Availability
    is_active = Faker("boolean", chance_of_getting_true=90)
    available_start_time = Faker("time")
    available_end_time = LazyAttribute(
        lambda obj: datetime.strptime(str(obj.available_start_time), "%H:%M:%S")
        .replace(
            hour=(datetime.strptime(str(obj.available_start_time), "%H:%M:%S").hour + 8)
            % 24,
        )
        .time(),
    )

    class Meta:
        model = CommonArea


class BookingFactory(DjangoModelFactory):
    """
    Factory for creating Booking instances.
    Generates bookings with realistic dates, times, and status.
    """

    common_area = SubFactory(CommonAreaFactory)
    resident = SubFactory(UserFactory, user_type="resident")

    # Booking details
    booking_date = Faker("date_between", start_date="today", end_date="+30d")
    start_time = Faker("time")
    end_time = LazyAttribute(
        lambda obj: datetime.strptime(str(obj.start_time), "%H:%M:%S")
        .replace(
            hour=(
                datetime.strptime(str(obj.start_time), "%H:%M:%S").hour
                + random.randint(1, 4)
            )
            % 24,
        )
        .time(),
    )
    purpose = Faker("sentence", nb_words=4)
    guests_count = Faker("random_int", min=0, max=20)

    # Status and payment
    status = Faker(
        "random_element",
        elements=["pending", "confirmed", "cancelled", "completed"],
    )
    total_fee = LazyAttribute(lambda obj: obj.common_area.booking_fee)
    is_paid = Faker("boolean", chance_of_getting_true=70)

    class Meta:
        model = Booking


class EventFactory(DjangoModelFactory):
    """
    Factory for creating Event instances.
    Generates events with realistic dates, types, and details.
    """

    title = Faker("sentence", nb_words=4)
    description = Faker("text", max_nb_chars=300)
    event_type = Faker(
        "random_element",
        elements=["meeting", "maintenance", "social", "festival", "other"],
    )

    # Date and time
    start_datetime = Faker("date_time_between", start_date="+1d", end_date="+30d")
    end_datetime = LazyAttribute(
        lambda obj: obj.start_datetime + timedelta(hours=random.randint(1, 8)),
    )
    is_all_day = Faker("boolean", chance_of_getting_true=20)

    # Location and details
    location = Faker(
        "random_element",
        elements=[
            "Community Hall",
            "Swimming Pool Area",
            "Garden",
            "Conference Room",
            "Main Lobby",
            "Rooftop",
            "Playground",
        ],
    )
    max_attendees = Faker("random_int", min=10, max=100)
    is_rsvp_required = Faker("boolean", chance_of_getting_true=60)

    # Organizer
    organizer = SubFactory(UserFactory, user_type="resident")

    class Meta:
        model = Event


class MarketplaceItemFactory(DjangoModelFactory):
    """
    Factory for creating MarketplaceItem instances.
    Generates marketplace items with realistic types, prices, and status.
    """

    title = Faker("sentence", nb_words=4)
    description = Faker("text", max_nb_chars=200)
    item_type = Faker(
        "random_element",
        elements=["sell", "buy", "service", "need_service", "lost", "found"],
    )
    price = LazyAttribute(
        lambda obj: Faker(
            "pydecimal",
            left_digits=4,
            right_digits=2,
            positive=True,
        ).generate()
        if obj.item_type in ["sell", "service"]
        else None,
    )

    # Listing details
    seller = SubFactory(UserFactory, user_type="resident")
    contact_phone = Faker("phone_number")

    # Status and dates
    status = Faker("random_element", elements=["active", "sold", "expired", "removed"])
    expires_at = Faker("date_time_between", start_date="+1d", end_date="+30d")

    class Meta:
        model = MarketplaceItem


class NotificationTypeFactory(DjangoModelFactory):
    """
    Factory for creating NotificationType instances.
    Generates notification types with realistic templates and delivery methods.
    """

    name = Faker(
        "random_element",
        elements=[
            "new_announcement",
            "urgent_announcement",
            "maintenance_update",
            "booking_confirmed",
            "event_reminder",
            "payment_due",
            "security_alert",
        ],
    )
    template_name = LazyAttribute(lambda obj: f"{obj.name}.html")
    sms_template = Faker("sentence", nb_words=10)
    default_delivery = Faker(
        "random_element",
        elements=["email", "sms", "both", "in_app", "all"],
    )
    is_urgent = Faker("boolean", chance_of_getting_true=30)

    class Meta:
        model = NotificationType


class NotificationFactory(DjangoModelFactory):
    """
    Factory for creating Notification instances.
    Generates notifications with realistic content and status.
    """

    recipient = SubFactory(UserFactory, user_type="resident")
    notification_type = SubFactory(NotificationTypeFactory)

    # Content
    title = Faker("sentence", nb_words=6)
    message = Faker("text", max_nb_chars=200)
    data = LazyAttribute(
        lambda obj: {
            "url": f"/notifications/{obj.id}/",
            "category": obj.notification_type.name,
        },
    )

    # Delivery tracking
    status = Faker("random_element", elements=["sent", "delivered", "read", "failed"])
    email_sent = Faker("boolean", chance_of_getting_true=80)
    sms_sent = Faker("boolean", chance_of_getting_true=40)

    # Timestamps
    created_at = Faker("date_time_between", start_date="-7d", end_date="now")
    sent_at = LazyAttribute(
        lambda obj: obj.created_at + timedelta(minutes=random.randint(1, 60))
        if obj.status in ["delivered", "read"]
        else None,
    )
    read_at = LazyAttribute(
        lambda obj: obj.sent_at + timedelta(hours=random.randint(1, 24))
        if obj.status == "read" and obj.sent_at
        else None,
    )

    class Meta:
        model = Notification


class EmergencyContactFactory(DjangoModelFactory):
    """
    Factory for creating EmergencyContact instances.
    Generates emergency contacts with realistic types and information.
    """

    name = Faker("name")
    contact_type = Faker(
        "random_element",
        elements=[
            "emergency",
            "maintenance",
            "security",
            "management",
            "vendor",
            "medical",
            "other",
        ],
    )
    phone_number = Faker("phone_number")
    alternate_phone = Faker("phone_number")
    email = Faker("email")
    address = Faker("address")
    description = Faker("text", max_nb_chars=100)

    # Availability
    available_24x7 = Faker("boolean", chance_of_getting_true=40)
    available_hours = LazyAttribute(
        lambda obj: "24/7" if obj.available_24x7 else "9:00 AM - 6:00 PM",
    )

    is_active = Faker("boolean", chance_of_getting_true=90)
    added_by = SubFactory(UserFactory, user_type="resident")

    class Meta:
        model = EmergencyContact


class DocumentFactory(DjangoModelFactory):
    """
    Factory for creating Document instances.
    Generates documents with realistic types and metadata.
    """

    title = Faker("sentence", nb_words=5)
    description = Faker("text", max_nb_chars=150)
    document_type = Faker(
        "random_element",
        elements=[
            "bylaw",
            "minutes",
            "financial",
            "policy",
            "form",
            "other",
        ],
    )

    # Access control
    is_public = Faker("boolean", chance_of_getting_true=80)
    committee_only = Faker("boolean", chance_of_getting_true=20)

    uploaded_by = SubFactory(UserFactory, user_type="resident")

    class Meta:
        model = Document


class CommentFactory(DjangoModelFactory):
    """
    Factory for creating Comment instances.
    Generates comments on announcements with realistic content.
    """

    announcement = SubFactory(AnnouncementFactory)
    author = SubFactory(UserFactory)
    content = Faker("text", max_nb_chars=200)
    parent = None  # Top-level comments by default

    class Meta:
        model = Comment


class MaintenanceUpdateFactory(DjangoModelFactory):
    """
    Factory for creating MaintenanceUpdate instances.
    Generates maintenance updates with realistic content and status changes.
    """

    request = SubFactory(MaintenanceRequestFactory)
    author = SubFactory(UserFactory)
    content = Faker("text", max_nb_chars=200)
    status_changed_to = Faker(
        "random_element",
        elements=[
            "acknowledged",
            "in_progress",
            "resolved",
            "closed",
        ],
    )

    class Meta:
        model = MaintenanceUpdate


class EventRSVPFactory(DjangoModelFactory):
    """
    Factory for creating EventRSVP instances.
    Generates RSVP responses for events with realistic responses.
    """

    event = SubFactory(EventFactory)
    resident = SubFactory(UserFactory, user_type="resident")
    response = Faker("random_element", elements=["yes", "no", "maybe"])
    guests_count = Faker("random_int", min=0, max=5)
    comment = Faker("text", max_nb_chars=100)

    class Meta:
        model = EventRSVP


class AnnouncementReadFactory(DjangoModelFactory):
    """
    Factory for creating AnnouncementRead instances.
    Generates read status records for announcements.
    """

    announcement = SubFactory(AnnouncementFactory)
    resident = SubFactory(UserFactory, user_type="resident")
    read_at = Faker("date_time_between", start_date="-7d", end_date="now")

    class Meta:
        model = AnnouncementRead
