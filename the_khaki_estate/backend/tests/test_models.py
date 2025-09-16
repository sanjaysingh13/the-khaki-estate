"""
Comprehensive test suite for backend models.
Tests all model functionality including validation, relationships, and business logic.
"""

from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from the_khaki_estate.backend.models import Announcement
from the_khaki_estate.backend.models import AnnouncementCategory
from the_khaki_estate.backend.models import Booking
from the_khaki_estate.backend.models import Comment
from the_khaki_estate.backend.models import CommonArea
from the_khaki_estate.backend.models import Document
from the_khaki_estate.backend.models import EmergencyContact
from the_khaki_estate.backend.models import Event
from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import MarketplaceItem
from the_khaki_estate.backend.models import Notification
from the_khaki_estate.backend.models import Resident
from the_khaki_estate.backend.tests.factories import AnnouncementCategoryFactory
from the_khaki_estate.backend.tests.factories import AnnouncementFactory
from the_khaki_estate.backend.tests.factories import BookingFactory
from the_khaki_estate.backend.tests.factories import CommentFactory
from the_khaki_estate.backend.tests.factories import CommonAreaFactory
from the_khaki_estate.backend.tests.factories import DocumentFactory
from the_khaki_estate.backend.tests.factories import EmergencyContactFactory
from the_khaki_estate.backend.tests.factories import EventFactory
from the_khaki_estate.backend.tests.factories import MaintenanceCategoryFactory
from the_khaki_estate.backend.tests.factories import MaintenanceRequestFactory
from the_khaki_estate.backend.tests.factories import MarketplaceItemFactory
from the_khaki_estate.backend.tests.factories import NotificationFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory


class ResidentModelTest(TestCase):
    """
    Test suite for the Resident model.
    Tests user creation, validation, and resident-specific functionality.
    """

    def setUp(self):
        """Set up test data before each test method"""
        # Create a test resident with all required fields
        self.resident = ResidentFactory(
            flat_number="101",
            block="A",
            phone_number="+1234567890",
            resident_type="owner",
            is_committee_member=True,
        )

    def test_resident_creation(self):
        """
        Test that a resident can be created with all required fields.
        Verifies that the resident object is properly instantiated.
        """
        self.assertIsInstance(self.resident, Resident)
        self.assertEqual(self.resident.flat_number, "101")
        self.assertEqual(self.resident.block, "A")
        self.assertEqual(self.resident.resident_type, "owner")
        self.assertTrue(self.resident.is_committee_member)

    def test_resident_str_representation(self):
        """
        Test the string representation of a resident.
        Should return full name and flat number.
        """
        expected_str = f"{self.resident.get_full_name()} - {self.resident.flat_number}"
        self.assertEqual(str(self.resident), expected_str)

    def test_resident_type_choices(self):
        """
        Test that resident type choices are properly defined.
        Verifies all valid resident types are available.
        """
        valid_types = [choice[0] for choice in Resident.RESIDENT_TYPES]
        self.assertIn("owner", valid_types)
        self.assertIn("tenant", valid_types)
        self.assertIn("family", valid_types)

    def test_notification_preferences_defaults(self):
        """
        Test that notification preferences have correct default values.
        Ensures proper default settings for email and SMS notifications.
        """
        resident = ResidentFactory()
        self.assertTrue(resident.email_notifications)  # Default should be True
        self.assertFalse(resident.sms_notifications)  # Default should be False
        self.assertFalse(resident.urgent_only)  # Default should be False

    def test_flat_number_required(self):
        """
        Test that flat number is required for resident creation.
        Should raise validation error if flat number is missing.
        """
        with self.assertRaises(IntegrityError):
            Resident.objects.create(
                username="testuser",
                email="test@example.com",
                phone_number="+1234567890",
                # Missing flat_number
            )


class AnnouncementCategoryModelTest(TestCase):
    """
    Test suite for the AnnouncementCategory model.
    Tests category creation, validation, and display properties.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.category = AnnouncementCategoryFactory(
            name="Maintenance",
            color_code="#ff0000",
            icon="fas fa-tools",
            is_urgent=True,
        )

    def test_category_creation(self):
        """
        Test that an announcement category can be created successfully.
        Verifies all fields are properly set.
        """
        self.assertIsInstance(self.category, AnnouncementCategory)
        self.assertEqual(self.category.name, "Maintenance")
        self.assertEqual(self.category.color_code, "#ff0000")
        self.assertEqual(self.category.icon, "fas fa-tools")
        self.assertTrue(self.category.is_urgent)

    def test_category_str_representation(self):
        """
        Test the string representation of an announcement category.
        Should return the category name.
        """
        self.assertEqual(str(self.category), "Maintenance")

    def test_category_default_values(self):
        """
        Test that announcement category has correct default values.
        Verifies default color code and urgent status.
        """
        category = AnnouncementCategoryFactory()
        self.assertEqual(category.color_code, "#007bff")  # Default blue color
        self.assertFalse(category.is_urgent)  # Default not urgent


class AnnouncementModelTest(TestCase):
    """
    Test suite for the Announcement model.
    Tests announcement creation, validation, and ordering.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.category = AnnouncementCategoryFactory()
        self.author = ResidentFactory()
        self.announcement = AnnouncementFactory(
            title="Test Announcement",
            content="This is a test announcement content.",
            category=self.category,
            author=self.author,
            is_pinned=True,
            is_urgent=False,
        )

    def test_announcement_creation(self):
        """
        Test that an announcement can be created with all required fields.
        Verifies proper relationship with category and author.
        """
        self.assertIsInstance(self.announcement, Announcement)
        self.assertEqual(self.announcement.title, "Test Announcement")
        self.assertEqual(self.announcement.category, self.category)
        self.assertEqual(self.announcement.author, self.author)
        self.assertTrue(self.announcement.is_pinned)

    def test_announcement_str_representation(self):
        """
        Test the string representation of an announcement.
        Should return the announcement title.
        """
        self.assertEqual(str(self.announcement), "Test Announcement")

    def test_announcement_ordering(self):
        """
        Test that announcements are ordered correctly.
        Order should be: pinned first, then urgent, then by creation date (newest first).
        """
        # Create multiple announcements with different priorities
        pinned_urgent = AnnouncementFactory(is_pinned=True, is_urgent=True)
        pinned_normal = AnnouncementFactory(is_pinned=True, is_urgent=False)
        urgent_normal = AnnouncementFactory(is_pinned=False, is_urgent=True)
        normal = AnnouncementFactory(is_pinned=False, is_urgent=False)

        announcements = Announcement.objects.all()

        # First should be pinned urgent
        self.assertEqual(announcements[0], pinned_urgent)
        # Second should be pinned normal
        self.assertEqual(announcements[1], pinned_normal)
        # Third should be urgent normal
        self.assertEqual(announcements[2], urgent_normal)
        # Last should be normal
        self.assertEqual(announcements[3], normal)

    def test_announcement_timestamps(self):
        """
        Test that announcement timestamps are automatically set.
        Verifies created_at and updated_at are properly managed.
        """
        announcement = AnnouncementFactory()
        self.assertIsNotNone(announcement.created_at)
        self.assertIsNotNone(announcement.updated_at)

        # Test that updated_at changes when announcement is modified
        original_updated = announcement.updated_at
        announcement.title = "Updated Title"
        announcement.save()
        self.assertGreater(announcement.updated_at, original_updated)


class MaintenanceRequestModelTest(TestCase):
    """
    Test suite for the MaintenanceRequest model.
    Tests maintenance request creation, ticket number generation, and status tracking.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.category = MaintenanceCategoryFactory()
        self.resident = ResidentFactory()
        self.request = MaintenanceRequestFactory(
            title="Broken Elevator",
            description="Elevator is not working properly",
            category=self.category,
            resident=self.resident,
            priority=4,  # Emergency
            status="submitted",
        )

    def test_maintenance_request_creation(self):
        """
        Test that a maintenance request can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.request, MaintenanceRequest)
        self.assertEqual(self.request.title, "Broken Elevator")
        self.assertEqual(self.request.priority, 4)
        self.assertEqual(self.request.status, "submitted")
        self.assertEqual(self.request.resident, self.resident)
        self.assertEqual(self.request.category, self.category)

    def test_ticket_number_generation(self):
        """
        Test that ticket numbers are automatically generated.
        Should follow format MNT-YYYY-NNNN where YYYY is year and NNNN is sequential number.
        """
        current_year = timezone.now().year
        expected_prefix = f"MNT-{current_year}-"

        self.assertTrue(self.request.ticket_number.startswith(expected_prefix))
        self.assertEqual(
            len(self.request.ticket_number), len(f"MNT-{current_year}-0001")
        )

    def test_ticket_number_uniqueness(self):
        """
        Test that ticket numbers are unique across all maintenance requests.
        Each request should have a different ticket number.
        """
        request1 = MaintenanceRequestFactory()
        request2 = MaintenanceRequestFactory()

        self.assertNotEqual(request1.ticket_number, request2.ticket_number)

    def test_priority_choices(self):
        """
        Test that priority choices are properly defined.
        Verifies all valid priority levels are available.
        """
        valid_priorities = [choice[0] for choice in MaintenanceRequest.PRIORITY_CHOICES]
        self.assertIn(1, valid_priorities)  # Low
        self.assertIn(2, valid_priorities)  # Medium
        self.assertIn(3, valid_priorities)  # High
        self.assertIn(4, valid_priorities)  # Emergency

    def test_status_choices(self):
        """
        Test that status choices are properly defined.
        Verifies all valid status values are available.
        """
        valid_statuses = [choice[0] for choice in MaintenanceRequest.STATUS_CHOICES]
        self.assertIn("submitted", valid_statuses)
        self.assertIn("acknowledged", valid_statuses)
        self.assertIn("in_progress", valid_statuses)
        self.assertIn("resolved", valid_statuses)
        self.assertIn("closed", valid_statuses)

    def test_maintenance_request_str_representation(self):
        """
        Test the string representation of a maintenance request.
        Should return ticket number and title.
        """
        expected_str = f"{self.request.ticket_number} - {self.request.title}"
        self.assertEqual(str(self.request), expected_str)


class CommonAreaModelTest(TestCase):
    """
    Test suite for the CommonArea model.
    Tests common area creation, booking rules, and availability settings.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.common_area = CommonAreaFactory(
            name="Swimming Pool",
            capacity=50,
            booking_fee=Decimal("100.00"),
            advance_booking_days=7,
            min_booking_hours=2,
            max_booking_hours=8,
        )

    def test_common_area_creation(self):
        """
        Test that a common area can be created successfully.
        Verifies all fields are properly set with realistic values.
        """
        self.assertIsInstance(self.common_area, CommonArea)
        self.assertEqual(self.common_area.name, "Swimming Pool")
        self.assertEqual(self.common_area.capacity, 50)
        self.assertEqual(self.common_area.booking_fee, Decimal("100.00"))
        self.assertEqual(self.common_area.advance_booking_days, 7)

    def test_common_area_str_representation(self):
        """
        Test the string representation of a common area.
        Should return the area name.
        """
        self.assertEqual(str(self.common_area), "Swimming Pool")

    def test_common_area_default_values(self):
        """
        Test that common area has correct default values.
        Verifies sensible defaults for booking rules and availability.
        """
        area = CommonAreaFactory()
        self.assertEqual(area.capacity, 1)  # Default capacity
        self.assertEqual(area.booking_fee, Decimal("0.00"))  # Default no fee
        self.assertEqual(area.advance_booking_days, 30)  # Default 30 days
        self.assertTrue(area.is_active)  # Default active


class BookingModelTest(TestCase):
    """
    Test suite for the Booking model.
    Tests booking creation, validation, and booking number generation.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.common_area = CommonAreaFactory()
        self.resident = ResidentFactory()
        self.booking = BookingFactory(
            common_area=self.common_area,
            resident=self.resident,
            booking_date=timezone.now().date() + timedelta(days=7),
            start_time=datetime.strptime("10:00", "%H:%M").time(),
            end_time=datetime.strptime("12:00", "%H:%M").time(),
            purpose="Birthday Party",
            guests_count=20,
        )

    def test_booking_creation(self):
        """
        Test that a booking can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.booking, Booking)
        self.assertEqual(self.booking.common_area, self.common_area)
        self.assertEqual(self.booking.resident, self.resident)
        self.assertEqual(self.booking.purpose, "Birthday Party")
        self.assertEqual(self.booking.guests_count, 20)

    def test_booking_number_generation(self):
        """
        Test that booking numbers are automatically generated.
        Should follow format BKG-YYYY-NNNN where YYYY is year and NNNN is sequential number.
        """
        current_year = timezone.now().year
        expected_prefix = f"BKG-{current_year}-"

        self.assertTrue(self.booking.booking_number.startswith(expected_prefix))
        self.assertEqual(
            len(self.booking.booking_number), len(f"BKG-{current_year}-0001")
        )

    def test_booking_number_uniqueness(self):
        """
        Test that booking numbers are unique across all bookings.
        Each booking should have a different booking number.
        """
        booking1 = BookingFactory()
        booking2 = BookingFactory()

        self.assertNotEqual(booking1.booking_number, booking2.booking_number)

    def test_booking_status_choices(self):
        """
        Test that booking status choices are properly defined.
        Verifies all valid status values are available.
        """
        valid_statuses = [choice[0] for choice in Booking.STATUS_CHOICES]
        self.assertIn("pending", valid_statuses)
        self.assertIn("confirmed", valid_statuses)
        self.assertIn("cancelled", valid_statuses)
        self.assertIn("completed", valid_statuses)

    def test_booking_str_representation(self):
        """
        Test the string representation of a booking.
        Should return booking number and common area name.
        """
        expected_str = (
            f"{self.booking.booking_number} - {self.booking.common_area.name}"
        )
        self.assertEqual(str(self.booking), expected_str)


class EventModelTest(TestCase):
    """
    Test suite for the Event model.
    Tests event creation, validation, and event type handling.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.organizer = ResidentFactory(is_committee_member=True)
        self.event = EventFactory(
            title="Annual General Meeting",
            description="Yearly society meeting to discuss important matters",
            event_type="meeting",
            organizer=self.organizer,
            start_datetime=timezone.now() + timedelta(days=30),
            end_datetime=timezone.now() + timedelta(days=30, hours=2),
            location="Community Hall",
            max_attendees=100,
            is_rsvp_required=True,
        )

    def test_event_creation(self):
        """
        Test that an event can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.event, Event)
        self.assertEqual(self.event.title, "Annual General Meeting")
        self.assertEqual(self.event.event_type, "meeting")
        self.assertEqual(self.event.organizer, self.organizer)
        self.assertEqual(self.event.max_attendees, 100)
        self.assertTrue(self.event.is_rsvp_required)

    def test_event_str_representation(self):
        """
        Test the string representation of an event.
        Should return the event title.
        """
        self.assertEqual(str(self.event), "Annual General Meeting")

    def test_event_type_choices(self):
        """
        Test that event type choices are properly defined.
        Verifies all valid event types are available.
        """
        valid_types = [choice[0] for choice in Event.EVENT_TYPES]
        self.assertIn("meeting", valid_types)
        self.assertIn("maintenance", valid_types)
        self.assertIn("social", valid_types)
        self.assertIn("festival", valid_types)
        self.assertIn("other", valid_types)

    def test_event_ordering(self):
        """
        Test that events are ordered by start datetime.
        Events should be ordered chronologically.
        """
        # Create events with different start times
        past_event = EventFactory(start_datetime=timezone.now() - timedelta(days=1))
        future_event = EventFactory(start_datetime=timezone.now() + timedelta(days=1))

        events = Event.objects.all()

        # Should be ordered by start_datetime (ascending)
        self.assertEqual(events[0], past_event)
        self.assertEqual(events[1], future_event)


class MarketplaceItemModelTest(TestCase):
    """
    Test suite for the MarketplaceItem model.
    Tests marketplace item creation, validation, and status management.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.seller = ResidentFactory()
        self.item = MarketplaceItemFactory(
            title="Used Refrigerator",
            description="Good condition refrigerator for sale",
            item_type="sell",
            price=Decimal("5000.00"),
            seller=self.seller,
            status="active",
        )

    def test_marketplace_item_creation(self):
        """
        Test that a marketplace item can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.item, MarketplaceItem)
        self.assertEqual(self.item.title, "Used Refrigerator")
        self.assertEqual(self.item.item_type, "sell")
        self.assertEqual(self.item.price, Decimal("5000.00"))
        self.assertEqual(self.item.seller, self.seller)
        self.assertEqual(self.item.status, "active")

    def test_marketplace_item_str_representation(self):
        """
        Test the string representation of a marketplace item.
        Should return the item title.
        """
        self.assertEqual(str(self.item), "Used Refrigerator")

    def test_item_type_choices(self):
        """
        Test that item type choices are properly defined.
        Verifies all valid item types are available.
        """
        valid_types = [choice[0] for choice in MarketplaceItem.ITEM_TYPES]
        self.assertIn("sell", valid_types)
        self.assertIn("buy", valid_types)
        self.assertIn("service", valid_types)
        self.assertIn("need_service", valid_types)
        self.assertIn("lost", valid_types)
        self.assertIn("found", valid_types)

    def test_status_choices(self):
        """
        Test that status choices are properly defined.
        Verifies all valid status values are available.
        """
        valid_statuses = [choice[0] for choice in MarketplaceItem.STATUS_CHOICES]
        self.assertIn("active", valid_statuses)
        self.assertIn("sold", valid_statuses)
        self.assertIn("expired", valid_statuses)
        self.assertIn("removed", valid_statuses)

    def test_price_optional_for_certain_types(self):
        """
        Test that price is optional for certain item types.
        Items like 'lost' or 'found' may not have prices.
        """
        lost_item = MarketplaceItemFactory(
            item_type="lost",
            price=None,
        )
        self.assertIsNone(lost_item.price)


class NotificationModelTest(TestCase):
    """
    Test suite for the Notification model.
    Tests notification creation, status tracking, and read functionality.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.recipient = ResidentFactory()
        self.notification_type = NotificationTypeFactory()
        self.notification = NotificationFactory(
            recipient=self.recipient,
            notification_type=self.notification_type,
            title="Test Notification",
            message="This is a test notification message",
            status="sent",
        )

    def test_notification_creation(self):
        """
        Test that a notification can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.notification, Notification)
        self.assertEqual(self.notification.recipient, self.recipient)
        self.assertEqual(self.notification.notification_type, self.notification_type)
        self.assertEqual(self.notification.title, "Test Notification")
        self.assertEqual(self.notification.status, "sent")

    def test_notification_str_representation(self):
        """
        Test the string representation of a notification.
        Should return title and recipient's full name.
        """
        expected_str = (
            f"{self.notification.title} - {self.notification.recipient.get_full_name()}"
        )
        self.assertEqual(str(self.notification), expected_str)

    def test_mark_as_read_functionality(self):
        """
        Test the mark_as_read method functionality.
        Should update status to 'read' and set read_at timestamp.
        """
        self.assertEqual(self.notification.status, "sent")
        self.assertIsNone(self.notification.read_at)

        self.notification.mark_as_read()

        self.assertEqual(self.notification.status, "read")
        self.assertIsNotNone(self.notification.read_at)

    def test_status_choices(self):
        """
        Test that status choices are properly defined.
        Verifies all valid status values are available.
        """
        valid_statuses = [choice[0] for choice in Notification.STATUS_CHOICES]
        self.assertIn("sent", valid_statuses)
        self.assertIn("delivered", valid_statuses)
        self.assertIn("read", valid_statuses)
        self.assertIn("failed", valid_statuses)

    def test_notification_ordering(self):
        """
        Test that notifications are ordered by creation date (newest first).
        Most recent notifications should appear first.
        """
        old_notification = NotificationFactory(
            created_at=timezone.now() - timedelta(days=1)
        )
        new_notification = NotificationFactory(created_at=timezone.now())

        notifications = Notification.objects.all()

        # Should be ordered by created_at (descending)
        self.assertEqual(notifications[0], new_notification)
        self.assertEqual(notifications[1], old_notification)


class CommentModelTest(TestCase):
    """
    Test suite for the Comment model.
    Tests comment creation, threading, and relationship management.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.announcement = AnnouncementFactory()
        self.author = ResidentFactory()
        self.comment = CommentFactory(
            announcement=self.announcement,
            author=self.author,
            content="This is a test comment",
        )

    def test_comment_creation(self):
        """
        Test that a comment can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.comment, Comment)
        self.assertEqual(self.comment.announcement, self.announcement)
        self.assertEqual(self.comment.author, self.author)
        self.assertEqual(self.comment.content, "This is a test comment")
        self.assertIsNone(self.comment.parent)  # Top-level comment

    def test_comment_str_representation(self):
        """
        Test the string representation of a comment.
        Should return author's full name.
        """
        expected_str = f"Comment by {self.comment.author.get_full_name()}"
        self.assertEqual(str(self.comment), expected_str)

    def test_comment_threading(self):
        """
        Test that comments can be threaded (replies to comments).
        Verifies parent-child relationship functionality.
        """
        parent_comment = CommentFactory(announcement=self.announcement)
        reply_comment = CommentFactory(
            announcement=self.announcement,
            parent=parent_comment,
        )

        self.assertEqual(reply_comment.parent, parent_comment)
        self.assertIsNone(parent_comment.parent)

    def test_comment_ordering(self):
        """
        Test that comments are ordered by creation date (oldest first).
        Comments should appear in chronological order.
        """
        first_comment = CommentFactory(announcement=self.announcement)
        second_comment = CommentFactory(announcement=self.announcement)

        comments = Comment.objects.all()

        # Should be ordered by created_at (ascending)
        self.assertEqual(comments[0], first_comment)
        self.assertEqual(comments[1], second_comment)


class EmergencyContactModelTest(TestCase):
    """
    Test suite for the EmergencyContact model.
    Tests emergency contact creation, validation, and contact type handling.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.added_by = ResidentFactory(is_committee_member=True)
        self.contact = EmergencyContactFactory(
            name="Emergency Services",
            contact_type="emergency",
            phone_number="911",
            available_24x7=True,
            added_by=self.added_by,
        )

    def test_emergency_contact_creation(self):
        """
        Test that an emergency contact can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.contact, EmergencyContact)
        self.assertEqual(self.contact.name, "Emergency Services")
        self.assertEqual(self.contact.contact_type, "emergency")
        self.assertEqual(self.contact.phone_number, "911")
        self.assertTrue(self.contact.available_24x7)
        self.assertEqual(self.contact.added_by, self.added_by)

    def test_emergency_contact_str_representation(self):
        """
        Test the string representation of an emergency contact.
        Should return name and contact type display.
        """
        expected_str = (
            f"{self.contact.name} ({self.contact.get_contact_type_display()})"
        )
        self.assertEqual(str(self.contact), expected_str)

    def test_contact_type_choices(self):
        """
        Test that contact type choices are properly defined.
        Verifies all valid contact types are available.
        """
        valid_types = [choice[0] for choice in EmergencyContact.CONTACT_TYPES]
        self.assertIn("emergency", valid_types)
        self.assertIn("maintenance", valid_types)
        self.assertIn("security", valid_types)
        self.assertIn("management", valid_types)
        self.assertIn("vendor", valid_types)
        self.assertIn("medical", valid_types)
        self.assertIn("other", valid_types)

    def test_emergency_contact_ordering(self):
        """
        Test that emergency contacts are ordered by contact type and name.
        Contacts should be grouped by type and sorted alphabetically within each type.
        """
        maintenance_contact = EmergencyContactFactory(
            contact_type="maintenance", name="Bob"
        )
        security_contact = EmergencyContactFactory(
            contact_type="security", name="Alice"
        )

        contacts = EmergencyContact.objects.all()

        # Should be ordered by contact_type, then name
        self.assertEqual(contacts[0], self.contact)  # emergency comes first
        self.assertEqual(contacts[1], maintenance_contact)  # maintenance comes second
        self.assertEqual(contacts[2], security_contact)  # security comes last


class DocumentModelTest(TestCase):
    """
    Test suite for the Document model.
    Tests document creation, access control, and document type handling.
    """

    def setUp(self):
        """Set up test data before each test method"""
        self.uploaded_by = ResidentFactory(is_committee_member=True)
        self.document = DocumentFactory(
            title="Society Bylaws",
            description="Official society bylaws document",
            document_type="bylaw",
            is_public=True,
            committee_only=False,
            uploaded_by=self.uploaded_by,
        )

    def test_document_creation(self):
        """
        Test that a document can be created successfully.
        Verifies all fields are properly set and relationships established.
        """
        self.assertIsInstance(self.document, Document)
        self.assertEqual(self.document.title, "Society Bylaws")
        self.assertEqual(self.document.document_type, "bylaw")
        self.assertTrue(self.document.is_public)
        self.assertFalse(self.document.committee_only)
        self.assertEqual(self.document.uploaded_by, self.uploaded_by)

    def test_document_str_representation(self):
        """
        Test the string representation of a document.
        Should return the document title.
        """
        self.assertEqual(str(self.document), "Society Bylaws")

    def test_document_type_choices(self):
        """
        Test that document type choices are properly defined.
        Verifies all valid document types are available.
        """
        valid_types = [choice[0] for choice in Document.DOCUMENT_TYPES]
        self.assertIn("bylaw", valid_types)
        self.assertIn("minutes", valid_types)
        self.assertIn("financial", valid_types)
        self.assertIn("policy", valid_types)
        self.assertIn("form", valid_types)
        self.assertIn("other", valid_types)

    def test_document_access_control(self):
        """
        Test document access control settings.
        Verifies that public and committee-only settings work correctly.
        """
        public_doc = DocumentFactory(is_public=True, committee_only=False)
        committee_doc = DocumentFactory(is_public=False, committee_only=True)

        self.assertTrue(public_doc.is_public)
        self.assertFalse(public_doc.committee_only)
        self.assertFalse(committee_doc.is_public)
        self.assertTrue(committee_doc.committee_only)

    def test_document_ordering(self):
        """
        Test that documents are ordered by upload date (newest first).
        Most recently uploaded documents should appear first.
        """
        old_document = DocumentFactory(uploaded_at=timezone.now() - timedelta(days=1))
        new_document = DocumentFactory(uploaded_at=timezone.now())

        documents = Document.objects.all()

        # Should be ordered by uploaded_at (descending)
        self.assertEqual(documents[0], new_document)
        self.assertEqual(documents[1], old_document)
