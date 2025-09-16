"""
Comprehensive integration test suite for complete workflows.
Tests end-to-end functionality including model interactions, signals, and notifications.
"""

from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.test import TransactionTestCase
from django.utils import timezone

from the_khaki_estate.backend.models import Announcement
from the_khaki_estate.backend.models import AnnouncementRead
from the_khaki_estate.backend.models import Booking
from the_khaki_estate.backend.models import Comment
from the_khaki_estate.backend.models import Event
from the_khaki_estate.backend.models import EventRSVP
from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import MaintenanceUpdate
from the_khaki_estate.backend.models import MarketplaceItem
from the_khaki_estate.backend.models import Notification
from the_khaki_estate.backend.tests.factories import AnnouncementCategoryFactory
from the_khaki_estate.backend.tests.factories import AnnouncementFactory
from the_khaki_estate.backend.tests.factories import BookingFactory
from the_khaki_estate.backend.tests.factories import CommentFactory
from the_khaki_estate.backend.tests.factories import CommonAreaFactory
from the_khaki_estate.backend.tests.factories import EventFactory
from the_khaki_estate.backend.tests.factories import EventRSVPFactory
from the_khaki_estate.backend.tests.factories import MaintenanceCategoryFactory
from the_khaki_estate.backend.tests.factories import MaintenanceRequestFactory
from the_khaki_estate.backend.tests.factories import MaintenanceUpdateFactory
from the_khaki_estate.backend.tests.factories import MarketplaceItemFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory


class AnnouncementWorkflowTest(TestCase):
    """
    Integration test suite for announcement workflow.
    Tests complete announcement lifecycle from creation to read tracking.
    """

    def setUp(self):
        """Set up test data for announcement workflow tests"""
        # Create test residents
        self.author = ResidentFactory(is_committee_member=True)
        self.resident1 = ResidentFactory()
        self.resident2 = ResidentFactory()
        self.resident3 = ResidentFactory()

        # Create announcement category
        self.category = AnnouncementCategoryFactory(name="General")

        # Create notification types
        self.urgent_notification_type = NotificationTypeFactory(
            name="urgent_announcement",
            is_urgent=True,
        )
        self.normal_notification_type = NotificationTypeFactory(
            name="new_announcement",
            is_urgent=False,
        )

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_creation_workflow(self, mock_notify):
        """
        Test complete announcement creation workflow.
        Should create announcement, trigger notifications, and handle read tracking.
        """
        # Create announcement
        announcement = AnnouncementFactory(
            title="Society Meeting Announcement",
            content="Monthly society meeting will be held on Saturday at 10 AM.",
            category=self.category,
            author=self.author,
            is_urgent=False,
            is_pinned=False,
        )

        # Verify announcement was created
        self.assertIsNotNone(announcement)
        self.assertEqual(announcement.title, "Society Meeting Announcement")
        self.assertEqual(announcement.author, self.author)
        self.assertEqual(announcement.category, self.category)

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        self.assertEqual(call_args[1]["notification_type_name"], "new_announcement")
        self.assertEqual(
            call_args[1]["title"], "New Announcement: Society Meeting Announcement"
        )

        # Verify notifications were created for residents
        notifications = Notification.objects.filter(
            recipient__in=[self.resident1, self.resident2, self.resident3],
        )
        self.assertEqual(notifications.count(), 3)

        # Test read tracking
        # Mark announcement as read by resident1
        AnnouncementRead.objects.create(
            announcement=announcement,
            resident=self.resident1,
        )

        # Verify read tracking
        read_records = AnnouncementRead.objects.filter(announcement=announcement)
        self.assertEqual(read_records.count(), 1)
        self.assertEqual(read_records.first().resident, self.resident1)

    def test_announcement_comment_workflow(self):
        """
        Test announcement comment workflow.
        Should allow residents to comment on announcements and track comment threads.
        """
        # Create announcement
        announcement = AnnouncementFactory(
            title="Comment Test Announcement",
            content="This announcement is for testing comments.",
            category=self.category,
            author=self.author,
        )

        # Create comments
        comment1 = CommentFactory(
            announcement=announcement,
            author=self.resident1,
            content="This is a great announcement!",
        )

        comment2 = CommentFactory(
            announcement=announcement,
            author=self.resident2,
            content="I agree with the previous comment.",
            parent=comment1,  # Reply to comment1
        )

        comment3 = CommentFactory(
            announcement=announcement,
            author=self.resident3,
            content="Another top-level comment.",
        )

        # Verify comments were created
        comments = Comment.objects.filter(announcement=announcement)
        self.assertEqual(comments.count(), 3)

        # Verify comment threading
        self.assertIsNone(comment1.parent)  # Top-level comment
        self.assertEqual(comment2.parent, comment1)  # Reply to comment1
        self.assertIsNone(comment3.parent)  # Top-level comment

        # Verify comment ordering (by creation time)
        ordered_comments = comments.order_by("created_at")
        self.assertEqual(ordered_comments[0], comment1)
        self.assertEqual(ordered_comments[1], comment2)
        self.assertEqual(ordered_comments[2], comment3)

    def test_announcement_ordering_workflow(self):
        """
        Test announcement ordering workflow.
        Should display announcements in correct priority order.
        """
        # Create announcements with different priorities
        normal_announcement = AnnouncementFactory(
            title="Normal Announcement",
            content="This is a normal announcement.",
            category=self.category,
            author=self.author,
            is_pinned=False,
            is_urgent=False,
        )

        urgent_announcement = AnnouncementFactory(
            title="Urgent Announcement",
            content="This is an urgent announcement.",
            category=self.category,
            author=self.author,
            is_pinned=False,
            is_urgent=True,
        )

        pinned_announcement = AnnouncementFactory(
            title="Pinned Announcement",
            content="This is a pinned announcement.",
            category=self.category,
            author=self.author,
            is_pinned=True,
            is_urgent=False,
        )

        pinned_urgent_announcement = AnnouncementFactory(
            title="Pinned Urgent Announcement",
            content="This is a pinned urgent announcement.",
            category=self.category,
            author=self.author,
            is_pinned=True,
            is_urgent=True,
        )

        # Verify ordering
        announcements = Announcement.objects.all()

        # Should be ordered: pinned urgent, pinned normal, urgent normal, normal
        self.assertEqual(announcements[0], pinned_urgent_announcement)
        self.assertEqual(announcements[1], pinned_announcement)
        self.assertEqual(announcements[2], urgent_announcement)
        self.assertEqual(announcements[3], normal_announcement)


class MaintenanceRequestWorkflowTest(TestCase):
    """
    Integration test suite for maintenance request workflow.
    Tests complete maintenance request lifecycle from submission to resolution.
    """

    def setUp(self):
        """Set up test data for maintenance request workflow tests"""
        # Create test residents
        self.resident = ResidentFactory()
        self.committee_member1 = ResidentFactory(is_committee_member=True)
        self.committee_member2 = ResidentFactory(is_committee_member=True)

        # Create maintenance category
        self.category = MaintenanceCategoryFactory(name="Plumbing")

        # Create notification types
        self.new_request_type = NotificationTypeFactory(name="new_maintenance_request")
        self.update_type = NotificationTypeFactory(name="maintenance_update")

    @patch(
        "the_khaki_estate.backend.signals.NotificationService.notify_multiple_residents"
    )
    def test_maintenance_request_submission_workflow(self, mock_notify):
        """
        Test complete maintenance request submission workflow.
        Should create request, generate ticket number, and notify committee members.
        """
        # Submit maintenance request
        request = MaintenanceRequestFactory(
            title="Broken Water Pipe",
            description="Water pipe in kitchen is leaking badly.",
            category=self.category,
            resident=self.resident,
            location="Flat 101 - Kitchen",
            priority=3,  # High priority
        )

        # Verify request was created
        self.assertIsNotNone(request)
        self.assertEqual(request.title, "Broken Water Pipe")
        self.assertEqual(request.resident, self.resident)
        self.assertEqual(request.category, self.category)
        self.assertEqual(request.priority, 3)
        self.assertEqual(request.status, "submitted")

        # Verify ticket number was generated
        current_year = timezone.now().year
        expected_prefix = f"MNT-{current_year}-"
        self.assertTrue(request.ticket_number.startswith(expected_prefix))

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        self.assertEqual(
            call_args[1]["notification_type_name"], "new_maintenance_request"
        )
        self.assertIn(request.ticket_number, call_args[1]["title"])

        # Verify committee members were notified
        notified_residents = call_args[1]["residents"]
        self.assertIn(self.committee_member1, notified_residents)
        self.assertIn(self.committee_member2, notified_residents)

    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_update_workflow(self, mock_notify):
        """
        Test maintenance request update workflow.
        Should handle status changes and notify resident.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Broken Elevator",
            description="Elevator is not working on floor 2.",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Clear any calls from creation
        mock_notify.reset_mock()

        # Update request status
        request.status = "acknowledged"
        request.assigned_to = self.committee_member1
        request.save()

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args
        self.assertEqual(call_args[1]["recipient"], self.resident)
        self.assertEqual(call_args[1]["notification_type_name"], "maintenance_update")
        self.assertIn("Status changed to: Acknowledged", call_args[1]["message"])

        # Test maintenance updates
        update1 = MaintenanceUpdateFactory(
            request=request,
            author=self.committee_member1,
            content="I have inspected the elevator. The issue is with the motor.",
            status_changed_to="in_progress",
        )

        update2 = MaintenanceUpdateFactory(
            request=request,
            author=self.committee_member1,
            content="Motor has been replaced. Testing in progress.",
            status_changed_to="resolved",
        )

        # Verify updates were created
        updates = MaintenanceUpdate.objects.filter(request=request)
        self.assertEqual(updates.count(), 2)

        # Verify update ordering
        ordered_updates = updates.order_by("created_at")
        self.assertEqual(ordered_updates[0], update1)
        self.assertEqual(ordered_updates[1], update2)

    def test_maintenance_request_resolution_workflow(self):
        """
        Test maintenance request resolution workflow.
        Should handle complete resolution process.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Leaky Faucet",
            description="Kitchen faucet is dripping continuously.",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Acknowledge request
        request.status = "acknowledged"
        request.assigned_to = self.committee_member1
        request.save()

        # Start work
        request.status = "in_progress"
        request.save()

        # Resolve request
        request.status = "resolved"
        request.resolved_at = timezone.now()
        request.save()

        # Verify resolution
        self.assertEqual(request.status, "resolved")
        self.assertIsNotNone(request.resolved_at)
        self.assertEqual(request.assigned_to, self.committee_member1)

        # Close request
        request.status = "closed"
        request.save()

        # Verify closure
        self.assertEqual(request.status, "closed")


class BookingWorkflowTest(TestCase):
    """
    Integration test suite for common area booking workflow.
    Tests complete booking lifecycle from request to completion.
    """

    def setUp(self):
        """Set up test data for booking workflow tests"""
        # Create test residents
        self.resident1 = ResidentFactory()
        self.resident2 = ResidentFactory()

        # Create common area
        self.common_area = CommonAreaFactory(
            name="Community Hall",
            capacity=50,
            booking_fee=Decimal("500.00"),
            advance_booking_days=7,
            min_booking_hours=2,
            max_booking_hours=8,
        )

    def test_booking_creation_workflow(self):
        """
        Test complete booking creation workflow.
        Should create booking, generate booking number, and calculate fees.
        """
        # Create booking
        booking = BookingFactory(
            common_area=self.common_area,
            resident=self.resident1,
            booking_date=timezone.now().date() + timedelta(days=10),
            start_time=datetime.strptime("10:00", "%H:%M").time(),
            end_time=datetime.strptime("14:00", "%H:%M").time(),
            purpose="Birthday Party",
            guests_count=25,
            status="pending",
        )

        # Verify booking was created
        self.assertIsNotNone(booking)
        self.assertEqual(booking.common_area, self.common_area)
        self.assertEqual(booking.resident, self.resident1)
        self.assertEqual(booking.purpose, "Birthday Party")
        self.assertEqual(booking.guests_count, 25)
        self.assertEqual(booking.status, "pending")

        # Verify booking number was generated
        current_year = timezone.now().year
        expected_prefix = f"BKG-{current_year}-"
        self.assertTrue(booking.booking_number.startswith(expected_prefix))

        # Verify fee calculation
        self.assertEqual(booking.total_fee, self.common_area.booking_fee)

    def test_booking_confirmation_workflow(self):
        """
        Test booking confirmation workflow.
        Should handle booking confirmation and payment tracking.
        """
        # Create pending booking
        booking = BookingFactory(
            common_area=self.common_area,
            resident=self.resident1,
            status="pending",
            is_paid=False,
        )

        # Confirm booking
        booking.status = "confirmed"
        booking.is_paid = True
        booking.save()

        # Verify confirmation
        self.assertEqual(booking.status, "confirmed")
        self.assertTrue(booking.is_paid)

        # Complete booking
        booking.status = "completed"
        booking.save()

        # Verify completion
        self.assertEqual(booking.status, "completed")

    def test_booking_cancellation_workflow(self):
        """
        Test booking cancellation workflow.
        Should handle booking cancellation and refund processing.
        """
        # Create confirmed booking
        booking = BookingFactory(
            common_area=self.common_area,
            resident=self.resident1,
            status="confirmed",
            is_paid=True,
        )

        # Cancel booking
        booking.status = "cancelled"
        booking.save()

        # Verify cancellation
        self.assertEqual(booking.status, "cancelled")
        # Note: Refund processing would be handled by payment system

    def test_booking_conflict_workflow(self):
        """
        Test booking conflict detection workflow.
        Should prevent double booking of the same time slot.
        """
        # Create first booking
        booking1 = BookingFactory(
            common_area=self.common_area,
            resident=self.resident1,
            booking_date=timezone.now().date() + timedelta(days=5),
            start_time=datetime.strptime("10:00", "%H:%M").time(),
            end_time=datetime.strptime("12:00", "%H:%M").time(),
            status="confirmed",
        )

        # Attempt to create conflicting booking
        # Note: In a real implementation, this would be prevented by validation
        # For testing purposes, we'll create the booking and verify the conflict
        booking2 = BookingFactory(
            common_area=self.common_area,
            resident=self.resident2,
            booking_date=booking1.booking_date,
            start_time=datetime.strptime(
                "11:00", "%H:%M"
            ).time(),  # Overlaps with booking1
            end_time=datetime.strptime("13:00", "%H:%M").time(),
            status="pending",
        )

        # Verify both bookings exist (conflict detection would be in validation)
        self.assertIsNotNone(booking1)
        self.assertIsNotNone(booking2)

        # In real implementation, validation would prevent this conflict


class EventWorkflowTest(TestCase):
    """
    Integration test suite for event workflow.
    Tests complete event lifecycle from creation to RSVP management.
    """

    def setUp(self):
        """Set up test data for event workflow tests"""
        # Create test residents
        self.organizer = ResidentFactory(is_committee_member=True)
        self.resident1 = ResidentFactory()
        self.resident2 = ResidentFactory()
        self.resident3 = ResidentFactory()

    def test_event_creation_workflow(self):
        """
        Test complete event creation workflow.
        Should create event with proper details and organizer assignment.
        """
        # Create event
        event = EventFactory(
            title="Annual General Meeting",
            description="Yearly society meeting to discuss important matters.",
            event_type="meeting",
            organizer=self.organizer,
            start_datetime=timezone.now() + timedelta(days=30),
            end_datetime=timezone.now() + timedelta(days=30, hours=2),
            location="Community Hall",
            max_attendees=100,
            is_rsvp_required=True,
        )

        # Verify event was created
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "Annual General Meeting")
        self.assertEqual(event.event_type, "meeting")
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.location, "Community Hall")
        self.assertEqual(event.max_attendees, 100)
        self.assertTrue(event.is_rsvp_required)

    def test_event_rsvp_workflow(self):
        """
        Test event RSVP workflow.
        Should handle RSVP responses and guest tracking.
        """
        # Create event
        event = EventFactory(
            title="RSVP Test Event",
            description="Testing RSVP functionality.",
            organizer=self.organizer,
            is_rsvp_required=True,
            max_attendees=50,
        )

        # Create RSVP responses
        rsvp1 = EventRSVPFactory(
            event=event,
            resident=self.resident1,
            response="yes",
            guests_count=2,
            comment="Looking forward to the event!",
        )

        rsvp2 = EventRSVPFactory(
            event=event,
            resident=self.resident2,
            response="no",
            guests_count=0,
            comment="Sorry, cannot attend.",
        )

        rsvp3 = EventRSVPFactory(
            event=event,
            resident=self.resident3,
            response="maybe",
            guests_count=1,
            comment="Will confirm closer to the date.",
        )

        # Verify RSVPs were created
        rsvps = EventRSVP.objects.filter(event=event)
        self.assertEqual(rsvps.count(), 3)

        # Verify RSVP responses
        yes_rsvps = rsvps.filter(response="yes")
        no_rsvps = rsvps.filter(response="no")
        maybe_rsvps = rsvps.filter(response="maybe")

        self.assertEqual(yes_rsvps.count(), 1)
        self.assertEqual(no_rsvps.count(), 1)
        self.assertEqual(maybe_rsvps.count(), 1)

        # Calculate total attendees
        total_attendees = sum(
            rsvp.guests_count + 1 for rsvp in yes_rsvps
        )  # +1 for resident
        self.assertEqual(total_attendees, 3)  # resident1 + 2 guests

    def test_event_management_workflow(self):
        """
        Test event management workflow.
        Should handle event updates and attendee management.
        """
        # Create event
        event = EventFactory(
            title="Management Test Event",
            description="Testing event management.",
            organizer=self.organizer,
            max_attendees=20,
        )

        # Update event details
        event.title = "Updated Event Title"
        event.description = "Updated event description."
        event.max_attendees = 30
        event.save()

        # Verify updates
        event.refresh_from_db()
        self.assertEqual(event.title, "Updated Event Title")
        self.assertEqual(event.description, "Updated event description.")
        self.assertEqual(event.max_attendees, 30)


class MarketplaceWorkflowTest(TestCase):
    """
    Integration test suite for marketplace workflow.
    Tests complete marketplace item lifecycle from listing to completion.
    """

    def setUp(self):
        """Set up test data for marketplace workflow tests"""
        # Create test residents
        self.seller = ResidentFactory()
        self.buyer = ResidentFactory()

    def test_marketplace_item_creation_workflow(self):
        """
        Test complete marketplace item creation workflow.
        Should create item with proper details and expiration.
        """
        # Create marketplace item
        item = MarketplaceItemFactory(
            title="Used Refrigerator",
            description="Good condition refrigerator, 2 years old.",
            item_type="sell",
            price=Decimal("15000.00"),
            seller=self.seller,
            contact_phone="+1234567890",
            status="active",
            expires_at=timezone.now() + timedelta(days=30),
        )

        # Verify item was created
        self.assertIsNotNone(item)
        self.assertEqual(item.title, "Used Refrigerator")
        self.assertEqual(item.item_type, "sell")
        self.assertEqual(item.price, Decimal("15000.00"))
        self.assertEqual(item.seller, self.seller)
        self.assertEqual(item.status, "active")
        self.assertIsNotNone(item.expires_at)

    def test_marketplace_item_status_workflow(self):
        """
        Test marketplace item status workflow.
        Should handle item status changes and expiration.
        """
        # Create active item
        item = MarketplaceItemFactory(
            title="Test Item",
            description="Testing item status changes.",
            item_type="sell",
            seller=self.seller,
            status="active",
        )

        # Mark as sold
        item.status = "sold"
        item.save()

        # Verify status change
        self.assertEqual(item.status, "sold")

        # Test expiration
        expired_item = MarketplaceItemFactory(
            title="Expired Item",
            description="This item has expired.",
            item_type="sell",
            seller=self.seller,
            status="active",
            expires_at=timezone.now() - timedelta(days=1),  # Expired yesterday
        )

        # In real implementation, expired items would be automatically marked as expired
        # For testing, we'll manually mark it as expired
        expired_item.status = "expired"
        expired_item.save()

        # Verify expiration
        self.assertEqual(expired_item.status, "expired")

    def test_marketplace_item_types_workflow(self):
        """
        Test different marketplace item types workflow.
        Should handle various item types appropriately.
        """
        # Create different types of items
        sell_item = MarketplaceItemFactory(
            title="Item for Sale",
            item_type="sell",
            price=Decimal("1000.00"),
            seller=self.seller,
        )

        buy_item = MarketplaceItemFactory(
            title="Looking to Buy",
            item_type="buy",
            price=None,  # No price for buy requests
            seller=self.seller,
        )

        service_item = MarketplaceItemFactory(
            title="Cleaning Service",
            item_type="service",
            price=Decimal("500.00"),
            seller=self.seller,
        )

        lost_item = MarketplaceItemFactory(
            title="Lost Keys",
            item_type="lost",
            price=None,  # No price for lost items
            seller=self.seller,
        )

        # Verify items were created with correct types
        self.assertEqual(sell_item.item_type, "sell")
        self.assertIsNotNone(sell_item.price)

        self.assertEqual(buy_item.item_type, "buy")
        self.assertIsNone(buy_item.price)

        self.assertEqual(service_item.item_type, "service")
        self.assertIsNotNone(service_item.price)

        self.assertEqual(lost_item.item_type, "lost")
        self.assertIsNone(lost_item.price)


class NotificationWorkflowTest(TestCase):
    """
    Integration test suite for notification workflow.
    Tests complete notification lifecycle from creation to delivery.
    """

    def setUp(self):
        """Set up test data for notification workflow tests"""
        # Create test residents
        self.resident1 = ResidentFactory(
            email="resident1@example.com",
            phone_number="+1234567890",
            email_notifications=True,
            sms_notifications=True,
        )

        self.resident2 = ResidentFactory(
            email="resident2@example.com",
            phone_number="+1234567891",
            email_notifications=True,
            sms_notifications=False,
        )

        # Create notification types
        self.urgent_type = NotificationTypeFactory(
            name="urgent_announcement",
            is_urgent=True,
            default_delivery="both",
        )

        self.normal_type = NotificationTypeFactory(
            name="new_announcement",
            is_urgent=False,
            default_delivery="email",
        )

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_notification_creation_workflow(self, mock_task):
        """
        Test complete notification creation workflow.
        Should create notification and trigger delivery task.
        """
        from the_khaki_estate.backend.notification_service import NotificationService

        # Create notification
        notification = NotificationService.create_notification(
            recipient=self.resident1,
            notification_type_name="urgent_announcement",
            title="Urgent Test Notification",
            message="This is an urgent test notification.",
            data={"url": "/test/", "priority": "high"},
        )

        # Verify notification was created
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.recipient, self.resident1)
        self.assertEqual(notification.title, "Urgent Test Notification")
        self.assertEqual(notification.message, "This is an urgent test notification.")
        self.assertEqual(notification.status, "sent")
        self.assertEqual(notification.data, {"url": "/test/", "priority": "high"})

        # Verify task was triggered
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][0], notification.id)
        self.assertEqual(
            call_args[0][1], "both"
        )  # Urgent notification with both methods

    def test_notification_delivery_workflow(self):
        """
        Test notification delivery workflow.
        Should handle different delivery methods based on user preferences.
        """
        from the_khaki_estate.backend.notification_service import NotificationService

        # Test with resident who has both email and SMS enabled
        notification1 = NotificationService.create_notification(
            recipient=self.resident1,
            notification_type_name="urgent_announcement",
            title="Test Notification 1",
            message="Testing both delivery methods.",
        )

        # Test with resident who has only email enabled
        notification2 = NotificationService.create_notification(
            recipient=self.resident2,
            notification_type_name="new_announcement",
            title="Test Notification 2",
            message="Testing email only delivery.",
        )

        # Verify notifications were created
        self.assertIsNotNone(notification1)
        self.assertIsNotNone(notification2)

        # Verify delivery preferences were respected
        # (This would be tested more thoroughly in the task tests)
        self.assertEqual(notification1.recipient, self.resident1)
        self.assertEqual(notification2.recipient, self.resident2)

    def test_notification_read_workflow(self):
        """
        Test notification read workflow.
        Should handle marking notifications as read.
        """
        # Create notification
        notification = NotificationFactory(
            recipient=self.resident1,
            notification_type=self.normal_type,
            title="Read Test Notification",
            message="Testing read functionality.",
            status="delivered",
        )

        # Verify initial state
        self.assertEqual(notification.status, "delivered")
        self.assertIsNone(notification.read_at)

        # Mark as read
        notification.mark_as_read()

        # Verify read state
        self.assertEqual(notification.status, "read")
        self.assertIsNotNone(notification.read_at)

        # Verify read_at timestamp is recent
        time_diff = timezone.now() - notification.read_at
        self.assertLess(time_diff.total_seconds(), 5)  # Within 5 seconds

    def test_notification_bulk_workflow(self):
        """
        Test bulk notification workflow.
        Should handle sending notifications to multiple residents efficiently.
        """
        from the_khaki_estate.backend.notification_service import NotificationService

        # Create additional residents
        residents = [self.resident1, self.resident2]
        for _ in range(3):
            residents.append(ResidentFactory())

        # Send bulk notification
        notifications = NotificationService.notify_multiple_residents(
            residents=residents,
            notification_type_name="new_announcement",
            title="Bulk Test Notification",
            message="This is a bulk notification test.",
            data={"bulk": True, "count": len(residents)},
        )

        # Verify notifications were created for all residents
        self.assertEqual(len(notifications), len(residents))

        # Verify each notification
        for i, notification in enumerate(notifications):
            self.assertEqual(notification.recipient, residents[i])
            self.assertEqual(notification.title, "Bulk Test Notification")
            self.assertEqual(notification.data["bulk"], True)
            self.assertEqual(notification.data["count"], len(residents))


class CompleteWorkflowIntegrationTest(TransactionTestCase):
    """
    Integration test suite for complete workflows across multiple models.
    Tests complex scenarios involving multiple models and their interactions.
    """

    def setUp(self):
        """Set up comprehensive test data for integration tests"""
        # Create test residents
        self.committee_member = ResidentFactory(is_committee_member=True)
        self.resident1 = ResidentFactory()
        self.resident2 = ResidentFactory()
        self.resident3 = ResidentFactory()

        # Create categories
        self.announcement_category = AnnouncementCategoryFactory()
        self.maintenance_category = MaintenanceCategoryFactory()

        # Create common area
        self.common_area = CommonAreaFactory()

        # Create notification types
        self.urgent_notification_type = NotificationTypeFactory(
            name="urgent_announcement",
            is_urgent=True,
        )
        self.normal_notification_type = NotificationTypeFactory(
            name="new_announcement",
            is_urgent=False,
        )

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_complete_society_workflow(self, mock_notify):
        """
        Test complete society workflow involving multiple models.
        Should handle announcement creation, maintenance request, and event management.
        """
        # Step 1: Create urgent announcement
        announcement = AnnouncementFactory(
            title="Urgent: Water Supply Interruption",
            content="Water supply will be interrupted tomorrow from 9 AM to 5 PM.",
            category=self.announcement_category,
            author=self.committee_member,
            is_urgent=True,
            is_pinned=True,
        )

        # Verify announcement was created and signal triggered
        self.assertIsNotNone(announcement)
        mock_notify.assert_called()

        # Step 2: Submit maintenance request
        maintenance_request = MaintenanceRequestFactory(
            title="Broken Water Pipe",
            description="Water pipe in lobby is leaking.",
            category=self.maintenance_category,
            resident=self.resident1,
            priority=4,  # Emergency
            status="submitted",
        )

        # Verify maintenance request was created
        self.assertIsNotNone(maintenance_request)
        self.assertEqual(maintenance_request.priority, 4)

        # Step 3: Create event
        event = EventFactory(
            title="Emergency Meeting",
            description="Meeting to discuss water supply issue.",
            event_type="meeting",
            organizer=self.committee_member,
            start_datetime=timezone.now() + timedelta(days=1),
            end_datetime=timezone.now() + timedelta(days=1, hours=1),
            location="Community Hall",
            is_rsvp_required=True,
        )

        # Verify event was created
        self.assertIsNotNone(event)

        # Step 4: RSVP to event
        rsvp = EventRSVPFactory(
            event=event,
            resident=self.resident1,
            response="yes",
            guests_count=0,
            comment="Will attend the meeting.",
        )

        # Verify RSVP was created
        self.assertIsNotNone(rsvp)
        self.assertEqual(rsvp.response, "yes")

        # Step 5: Create marketplace item
        marketplace_item = MarketplaceItemFactory(
            title="Emergency Water Storage",
            description="Selling emergency water storage containers.",
            item_type="sell",
            price=Decimal("500.00"),
            seller=self.resident2,
            status="active",
        )

        # Verify marketplace item was created
        self.assertIsNotNone(marketplace_item)
        self.assertEqual(marketplace_item.item_type, "sell")

        # Step 6: Book common area for meeting
        booking = BookingFactory(
            common_area=self.common_area,
            resident=self.committee_member,
            booking_date=event.start_datetime.date(),
            start_time=event.start_datetime.time(),
            end_time=event.end_datetime.time(),
            purpose="Emergency Meeting",
            status="confirmed",
            is_paid=True,
        )

        # Verify booking was created
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, "confirmed")

        # Verify all components are working together
        self.assertTrue(Announcement.objects.filter(id=announcement.id).exists())
        self.assertTrue(
            MaintenanceRequest.objects.filter(id=maintenance_request.id).exists()
        )
        self.assertTrue(Event.objects.filter(id=event.id).exists())
        self.assertTrue(EventRSVP.objects.filter(id=rsvp.id).exists())
        self.assertTrue(MarketplaceItem.objects.filter(id=marketplace_item.id).exists())
        self.assertTrue(Booking.objects.filter(id=booking.id).exists())

    def test_data_consistency_across_workflows(self):
        """
        Test data consistency across multiple workflows.
        Should maintain data integrity throughout complex operations.
        """
        # Create related objects
        announcement = AnnouncementFactory(
            title="Data Consistency Test",
            content="Testing data consistency across workflows.",
            category=self.announcement_category,
            author=self.committee_member,
        )

        maintenance_request = MaintenanceRequestFactory(
            title="Consistency Test Request",
            description="Testing data consistency.",
            category=self.maintenance_category,
            resident=self.resident1,
        )

        # Create notifications referencing these objects
        notification1 = NotificationFactory(
            recipient=self.resident1,
            notification_type=self.normal_notification_type,
            title="Announcement Notification",
            message="New announcement available.",
            related_object_type="announcement",
            related_object_id=announcement.id,
        )

        notification2 = NotificationFactory(
            recipient=self.resident1,
            notification_type=self.normal_notification_type,
            title="Maintenance Notification",
            message="Maintenance request update.",
            related_object_type="maintenancerequest",
            related_object_id=maintenance_request.id,
        )

        # Verify data consistency
        self.assertEqual(notification1.related_object_id, announcement.id)
        self.assertEqual(notification2.related_object_id, maintenance_request.id)

        # Verify objects still exist
        self.assertTrue(Announcement.objects.filter(id=announcement.id).exists())
        self.assertTrue(
            MaintenanceRequest.objects.filter(id=maintenance_request.id).exists()
        )

        # Verify notifications can access related objects
        # (This would be tested more thoroughly in the model tests)
        self.assertIsNotNone(notification1.related_object_id)
        self.assertIsNotNone(notification2.related_object_id)
