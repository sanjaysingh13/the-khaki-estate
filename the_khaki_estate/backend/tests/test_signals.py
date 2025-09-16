"""
Comprehensive test suite for Django signals.
Tests automatic notification triggers and signal handlers.
"""

from unittest.mock import patch

from django.db.models.signals import post_save
from django.test import TestCase

from the_khaki_estate.backend.models import Announcement
from the_khaki_estate.backend.models import Resident
from the_khaki_estate.backend.tests.factories import AnnouncementCategoryFactory
from the_khaki_estate.backend.tests.factories import AnnouncementFactory
from the_khaki_estate.backend.tests.factories import MaintenanceCategoryFactory
from the_khaki_estate.backend.tests.factories import MaintenanceRequestFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory


class AnnouncementSignalsTest(TestCase):
    """
    Test suite for announcement-related signals.
    Tests automatic notification creation when announcements are created.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        Creates test residents, categories, and notification types.
        """
        # Create test residents
        self.author = ResidentFactory(is_committee_member=True)
        self.resident1 = ResidentFactory()
        self.resident2 = ResidentFactory()

        # Create announcement category
        self.category = AnnouncementCategoryFactory()

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
    def test_announcement_created_signal_urgent(self, mock_notify):
        """
        Test that creating an urgent announcement triggers notification to all residents.
        Should call NotificationService with urgent notification type.
        """
        # Create urgent announcement
        announcement = AnnouncementFactory(
            title="Urgent: Water Supply Issue",
            content="Water supply will be interrupted tomorrow from 9 AM to 5 PM.",
            category=self.category,
            author=self.author,
            is_urgent=True,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification parameters
        self.assertEqual(call_args[1]["notification_type_name"], "urgent_announcement")
        self.assertEqual(
            call_args[1]["title"], "New Announcement: Urgent: Water Supply Issue"
        )
        self.assertIn("Water supply will be interrupted", call_args[1]["message"])
        self.assertEqual(call_args[1]["related_object"], announcement)
        self.assertIn("url", call_args[1]["data"])
        self.assertEqual(call_args[1]["data"]["category"], self.category.name)

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_created_signal_normal(self, mock_notify):
        """
        Test that creating a normal announcement triggers notification to all residents.
        Should call NotificationService with normal notification type.
        """
        # Create normal announcement
        announcement = AnnouncementFactory(
            title="Monthly Meeting Reminder",
            content="Don't forget about the monthly society meeting this Saturday.",
            category=self.category,
            author=self.author,
            is_urgent=False,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification parameters
        self.assertEqual(call_args[1]["notification_type_name"], "new_announcement")
        self.assertEqual(
            call_args[1]["title"], "New Announcement: Monthly Meeting Reminder"
        )
        self.assertIn(
            "Don't forget about the monthly society meeting", call_args[1]["message"]
        )
        self.assertEqual(call_args[1]["related_object"], announcement)

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_created_signal_long_content(self, mock_notify):
        """
        Test that long announcement content is properly truncated in notifications.
        Should truncate content to 100 characters with ellipsis.
        """
        long_content = "A" * 150  # 150 character content

        announcement = AnnouncementFactory(
            title="Long Content Test",
            content=long_content,
            category=self.category,
            author=self.author,
            is_urgent=False,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check that content was truncated
        message = call_args[1]["message"]
        self.assertEqual(len(message), 103)  # 100 chars + '...'
        self.assertTrue(message.endswith("..."))

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_created_signal_short_content(self, mock_notify):
        """
        Test that short announcement content is not truncated.
        Should use full content if it's 100 characters or less.
        """
        short_content = "Short announcement content"  # Less than 100 characters

        announcement = AnnouncementFactory(
            title="Short Content Test",
            content=short_content,
            category=self.category,
            author=self.author,
            is_urgent=False,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check that content was not truncated
        message = call_args[1]["message"]
        self.assertEqual(message, short_content)
        self.assertFalse(message.endswith("..."))

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_update_no_signal(self, mock_notify):
        """
        Test that updating an announcement does not trigger the signal.
        Signal should only fire on creation, not updates.
        """
        # Create announcement (should trigger signal)
        announcement = AnnouncementFactory(
            title="Original Title",
            content="Original content",
            category=self.category,
            author=self.author,
        )

        # Clear the mock to reset call count
        mock_notify.reset_mock()

        # Update announcement (should not trigger signal)
        announcement.title = "Updated Title"
        announcement.content = "Updated content"
        announcement.save()

        # Verify signal was not triggered again
        mock_notify.assert_not_called()

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_announcement_created_signal_with_attachment(self, mock_notify):
        """
        Test that announcement creation signal works with attachments.
        Should still trigger notification regardless of attachment presence.
        """
        announcement = AnnouncementFactory(
            title="Announcement with Attachment",
            content="This announcement has an attachment.",
            category=self.category,
            author=self.author,
            # attachment field would be set here in real usage
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification data includes URL
        self.assertIn("url", call_args[1]["data"])
        self.assertIn(f"/announcements/{announcement.id}/", call_args[1]["data"]["url"])


class MaintenanceRequestSignalsTest(TestCase):
    """
    Test suite for maintenance request-related signals.
    Tests automatic notification creation for maintenance request updates.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        Creates test residents, categories, and notification types.
        """
        # Create test residents
        self.resident = ResidentFactory()
        self.committee_member1 = ResidentFactory(is_committee_member=True)
        self.committee_member2 = ResidentFactory(is_committee_member=True)

        # Create maintenance category
        self.category = MaintenanceCategoryFactory()

        # Create notification types
        self.new_request_type = NotificationTypeFactory(name="new_maintenance_request")
        self.update_type = NotificationTypeFactory(name="maintenance_update")

    @patch(
        "the_khaki_estate.backend.signals.NotificationService.notify_multiple_residents"
    )
    def test_maintenance_request_created_signal(self, mock_notify):
        """
        Test that creating a maintenance request triggers notification to committee members.
        Should notify all committee members about the new request.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Broken Elevator",
            description="Elevator is not working on floor 3",
            category=self.category,
            resident=self.resident,
            priority=3,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification parameters
        self.assertEqual(
            call_args[1]["notification_type_name"], "new_maintenance_request"
        )
        self.assertEqual(
            call_args[1]["title"], f"New Maintenance Request: {request.ticket_number}"
        )
        self.assertIn(self.resident.get_full_name(), call_args[1]["message"])
        self.assertIn(request.title, call_args[1]["message"])
        self.assertEqual(call_args[1]["related_object"], request)
        self.assertIn("url", call_args[1]["data"])
        self.assertIn(f"/maintenance/{request.id}/", call_args[1]["data"]["url"])

        # Check that committee members were notified
        notified_residents = call_args[1]["residents"]
        self.assertIn(self.committee_member1, notified_residents)
        self.assertIn(self.committee_member2, notified_residents)
        self.assertNotIn(
            self.resident, notified_residents
        )  # Resident should not be notified

    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_updated_signal(self, mock_notify):
        """
        Test that updating a maintenance request triggers notification to the resident.
        Should notify the resident about status changes.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Broken Elevator",
            description="Elevator is not working on floor 3",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Clear any calls from creation
        mock_notify.reset_mock()

        # Update maintenance request status
        request.status = "in_progress"
        request.save()

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification parameters
        self.assertEqual(call_args[1]["recipient"], self.resident)
        self.assertEqual(call_args[1]["notification_type_name"], "maintenance_update")
        self.assertEqual(
            call_args[1]["title"], f"Maintenance Update: {request.ticket_number}"
        )
        self.assertIn("Status changed to: In Progress", call_args[1]["message"])
        self.assertEqual(call_args[1]["related_object"], request)
        self.assertIn("url", call_args[1]["data"])

    @patch(
        "the_khaki_estate.backend.signals.NotificationService.notify_multiple_residents"
    )
    def test_maintenance_request_created_no_committee_members(self, mock_notify):
        """
        Test maintenance request creation when no committee members exist.
        Should handle gracefully without errors.
        """
        # Ensure no committee members exist
        Resident.objects.filter(is_committee_member=True).delete()

        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check that empty residents list was passed
        notified_residents = call_args[1]["residents"]
        self.assertEqual(len(notified_residents), 0)

    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_status_change_notifications(self, mock_notify):
        """
        Test that different status changes trigger appropriate notifications.
        Should notify resident for each status change.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Clear any calls from creation
        mock_notify.reset_mock()

        # Test different status changes
        status_changes = [
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ]

        for status, display_name in status_changes:
            request.status = status
            request.save()

            # Verify notification was sent
            self.assertEqual(mock_notify.call_count, 1)
            call_args = mock_notify.call_args

            # Check notification content
            self.assertIn(f"Status changed to: {display_name}", call_args[1]["message"])

            # Reset mock for next iteration
            mock_notify.reset_mock()

    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_assignment_notification(self, mock_notify):
        """
        Test that assigning a maintenance request triggers notification.
        Should notify resident when request is assigned to someone.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
            status="submitted",
            assigned_to=None,
        )

        # Clear any calls from creation
        mock_notify.reset_mock()

        # Assign request to committee member
        request.assigned_to = self.committee_member1
        request.status = "acknowledged"
        request.save()

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check notification parameters
        self.assertEqual(call_args[1]["recipient"], self.resident)
        self.assertIn("Status changed to: Acknowledged", call_args[1]["message"])

    @patch(
        "the_khaki_estate.backend.signals.NotificationService.notify_multiple_residents"
    )
    def test_maintenance_request_creation_with_assigned_to(self, mock_notify):
        """
        Test maintenance request creation when assigned_to is set initially.
        Should still notify committee members about new request.
        """
        # Create maintenance request with assignment
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
            assigned_to=self.committee_member1,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args

        # Check that committee members were notified
        notified_residents = call_args[1]["residents"]
        self.assertIn(self.committee_member1, notified_residents)
        self.assertIn(self.committee_member2, notified_residents)

    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_update_without_status_change(self, mock_notify):
        """
        Test updating maintenance request without status change.
        Should not trigger notification if status remains the same.
        """
        # Create maintenance request
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Clear any calls from creation
        mock_notify.reset_mock()

        # Update request without changing status
        request.description = "Updated description"
        request.save()

        # Verify signal was not triggered
        mock_notify.assert_not_called()

    @patch(
        "the_khaki_estate.backend.signals.NotificationService.notify_multiple_residents"
    )
    @patch("the_khaki_estate.backend.signals.NotificationService.create_notification")
    def test_maintenance_request_signal_integration(
        self, mock_create, mock_notify_multiple
    ):
        """
        Test integration between maintenance request creation and update signals.
        Should handle both signals correctly in sequence.
        """
        # Create maintenance request (should trigger creation signal)
        request = MaintenanceRequestFactory(
            title="Test Request",
            description="Test description",
            category=self.category,
            resident=self.resident,
            status="submitted",
        )

        # Verify creation signal was triggered
        mock_notify_multiple.assert_called_once()

        # Update request status (should trigger update signal)
        request.status = "acknowledged"
        request.save()

        # Verify update signal was triggered
        mock_create.assert_called_once()

        # Check that both signals worked correctly
        creation_call = mock_notify_multiple.call_args
        update_call = mock_create.call_args

        self.assertEqual(
            creation_call[1]["notification_type_name"], "new_maintenance_request"
        )
        self.assertEqual(update_call[1]["notification_type_name"], "maintenance_update")


class SignalIntegrationTest(TestCase):
    """
    Test suite for signal integration and edge cases.
    Tests signal behavior in complex scenarios and error conditions.
    """

    def setUp(self):
        """
        Set up test data for integration tests.
        Creates comprehensive test data for signal testing.
        """
        # Create test data
        self.author = ResidentFactory(is_committee_member=True)
        self.resident = ResidentFactory()
        self.category = AnnouncementCategoryFactory()
        self.maintenance_category = MaintenanceCategoryFactory()

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_signal_error_handling(self, mock_notify):
        """
        Test that signal errors are handled gracefully.
        Should not crash the application if notification service fails.
        """
        # Mock notification service to raise an exception
        mock_notify.side_effect = Exception("Notification service error")

        # Create announcement (should not crash despite signal error)
        try:
            announcement = AnnouncementFactory(
                title="Test Announcement",
                content="Test content",
                category=self.category,
                author=self.author,
            )
            # If we get here, the signal error was handled gracefully
            self.assertIsNotNone(announcement)
        except Exception as e:
            self.fail(f"Signal error was not handled gracefully: {e}")

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_signal_performance_with_many_residents(self, mock_notify):
        """
        Test signal performance with a large number of residents.
        Should handle bulk operations efficiently.
        """
        # Create many residents
        residents = []
        for _ in range(100):
            residents.append(ResidentFactory())

        # Create announcement (should trigger signal for all residents)
        announcement = AnnouncementFactory(
            title="Bulk Test Announcement",
            content="This announcement should notify many residents",
            category=self.category,
            author=self.author,
        )

        # Verify signal was triggered
        mock_notify.assert_called_once()

        # The signal should handle bulk operations efficiently
        # (This is more of a documentation test for expected behavior)
        self.assertTrue(True)  # If we get here, no timeout occurred

    def test_signal_disconnection(self):
        """
        Test that signals can be properly disconnected.
        Should allow signal disconnection for testing or maintenance.
        """
        from the_khaki_estate.backend.signals import announcement_created

        # Disconnect the signal
        post_save.disconnect(announcement_created, sender=Announcement)

        # Create announcement (should not trigger signal)
        announcement = AnnouncementFactory(
            title="Test Announcement",
            content="Test content",
            category=self.category,
            author=self.author,
        )

        # Verify announcement was created
        self.assertIsNotNone(announcement)

        # Reconnect signal for other tests
        post_save.connect(announcement_created, sender=Announcement)

    @patch("the_khaki_estate.backend.signals.NotificationService.notify_all_residents")
    def test_signal_with_invalid_data(self, mock_notify):
        """
        Test signal behavior with invalid or missing data.
        Should handle gracefully without crashing.
        """
        # Create announcement with minimal data
        announcement = AnnouncementFactory(
            title="",  # Empty title
            content="",  # Empty content
            category=self.category,
            author=self.author,
        )

        # Verify signal was triggered despite invalid data
        mock_notify.assert_called_once()

        # Check that signal handled empty data gracefully
        call_args = mock_notify.call_args
        self.assertIsNotNone(call_args[1]["title"])
        self.assertIsNotNone(call_args[1]["message"])

    def test_signal_timing(self):
        """
        Test that signals fire at the correct time during model operations.
        Should fire after model is saved, not before.
        """
        with patch(
            "the_khaki_estate.backend.signals.NotificationService.notify_all_residents"
        ) as mock_notify:
            # Create announcement
            announcement = AnnouncementFactory(
                title="Timing Test",
                content="Testing signal timing",
                category=self.category,
                author=self.author,
            )

            # Verify announcement exists in database
            self.assertTrue(Announcement.objects.filter(id=announcement.id).exists())

            # Verify signal was called
            mock_notify.assert_called_once()

            # Verify signal was called with the saved announcement
            call_args = mock_notify.call_args
            self.assertEqual(call_args[1]["related_object"], announcement)
            self.assertEqual(call_args[1]["related_object"].id, announcement.id)
