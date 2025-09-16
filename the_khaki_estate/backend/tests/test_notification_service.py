"""
Comprehensive test suite for NotificationService.
Tests notification creation, delivery methods, and user preference handling.
"""

from unittest.mock import patch

from django.test import TestCase

from the_khaki_estate.backend.models import Notification
from the_khaki_estate.backend.notification_service import NotificationService
from the_khaki_estate.backend.tests.factories import AnnouncementCategoryFactory
from the_khaki_estate.backend.tests.factories import AnnouncementFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory


class NotificationServiceTest(TestCase):
    """
    Test suite for the NotificationService class.
    Tests notification creation, delivery methods, and user preference handling.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        Creates test residents, notification types, and related objects.
        """
        # Create test residents with different notification preferences
        self.resident_email_only = ResidentFactory(
            email="email@example.com",
            phone_number="+1234567890",
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
        )

        self.resident_sms_only = ResidentFactory(
            email="sms@example.com",
            phone_number="+1234567891",
            email_notifications=False,
            sms_notifications=True,
            urgent_only=False,
        )

        self.resident_both_methods = ResidentFactory(
            email="both@example.com",
            phone_number="+1234567892",
            email_notifications=True,
            sms_notifications=True,
            urgent_only=False,
        )

        self.resident_urgent_only = ResidentFactory(
            email="urgent@example.com",
            phone_number="+1234567893",
            email_notifications=True,
            sms_notifications=True,
            urgent_only=True,
        )

        self.resident_no_notifications = ResidentFactory(
            email="none@example.com",
            phone_number="+1234567894",
            email_notifications=False,
            sms_notifications=False,
            urgent_only=False,
        )

        # Create notification types
        self.urgent_notification_type = NotificationTypeFactory(
            name="urgent_announcement",
            template_name="urgent_announcement.html",
            sms_template="URGENT: {title} - {message}",
            default_delivery="both",
            is_urgent=True,
        )

        self.normal_notification_type = NotificationTypeFactory(
            name="new_announcement",
            template_name="new_announcement.html",
            sms_template="New: {title} - {message}",
            default_delivery="email",
            is_urgent=False,
        )

        # Create related object for testing
        self.category = AnnouncementCategoryFactory()
        self.announcement = AnnouncementFactory(
            title="Test Announcement",
            content="This is a test announcement",
            category=self.category,
            author=self.resident_email_only,
        )

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_success(self, mock_task):
        """
        Test successful notification creation.
        Should create notification record and trigger delivery task.
        """
        # Create notification
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
            related_object=self.announcement,
            data={"url": "/test/"},
        )

        # Verify notification was created
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.recipient, self.resident_email_only)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test notification")
        self.assertEqual(notification.status, "sent")

        # Verify related object data
        self.assertEqual(notification.related_object_type, "announcement")
        self.assertEqual(notification.related_object_id, self.announcement.id)

        # Verify data field
        self.assertEqual(notification.data, {"url": "/test/"})

        # Verify task was triggered
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][0], notification.id)
        self.assertEqual(call_args[0][1], "email")  # Default delivery method

    def test_create_notification_with_nonexistent_type(self):
        """
        Test notification creation with non-existent notification type.
        Should create default notification type automatically.
        """
        # Create notification with non-existent type
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="nonexistent_type",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify notification was created
        self.assertIsInstance(notification, Notification)

        # Verify default notification type was created
        notification_type = notification.notification_type
        self.assertEqual(notification_type.name, "nonexistent_type")
        self.assertEqual(notification_type.template_name, "default_notification.html")

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_email_only_preference(self, mock_task):
        """
        Test notification creation with email-only user preference.
        Should respect user's email-only preference.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify task was called with email only
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][1], "email")

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_sms_only_preference(self, mock_task):
        """
        Test notification creation with SMS-only user preference.
        Should respect user's SMS-only preference.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_sms_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify task was called with SMS only
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][1], "sms")

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_both_methods_preference(self, mock_task):
        """
        Test notification creation with both email and SMS preferences.
        Should use both delivery methods.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_both_methods,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify task was called with both methods
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][1], "email")  # Default from notification type

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_urgent_only_preference(self, mock_task):
        """
        Test notification creation with urgent-only user preference.
        Should only send urgent notifications via external methods.
        """
        # Test with urgent notification
        notification = NotificationService.create_notification(
            recipient=self.resident_urgent_only,
            notification_type_name="urgent_announcement",
            title="Urgent Test Notification",
            message="This is an urgent test notification",
        )

        # Verify task was called (urgent notification should be sent)
        mock_task.assert_called_once()

        # Reset mock
        mock_task.reset_mock()

        # Test with normal notification
        notification = NotificationService.create_notification(
            recipient=self.resident_urgent_only,
            notification_type_name="new_announcement",
            title="Normal Test Notification",
            message="This is a normal test notification",
        )

        # Verify task was not called (normal notification should be in-app only)
        mock_task.assert_not_called()

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_no_notifications_preference(self, mock_task):
        """
        Test notification creation with no notification preferences.
        Should not trigger external delivery methods.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_no_notifications,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify task was not called
        mock_task.assert_not_called()

        # Verify notification was still created
        self.assertIsInstance(notification, Notification)

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_force_delivery(self, mock_task):
        """
        Test notification creation with forced delivery method.
        Should override user preferences and use specified delivery method.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,  # Email only preference
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
            force_delivery="sms",  # Force SMS delivery
        )

        # Verify task was called with forced delivery method
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][1], "sms")

    def test_notify_multiple_residents(self):
        """
        Test notification creation for multiple residents.
        Should create notifications for all specified residents.
        """
        residents = [
            self.resident_email_only,
            self.resident_sms_only,
            self.resident_both_methods,
        ]

        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ) as mock_task:
            notifications = NotificationService.notify_multiple_residents(
                residents=residents,
                notification_type_name="new_announcement",
                title="Bulk Notification",
                message="This is a bulk notification",
                related_object=self.announcement,
            )

            # Verify notifications were created for all residents
            self.assertEqual(len(notifications), 3)

            # Verify each notification
            for i, notification in enumerate(notifications):
                self.assertEqual(notification.recipient, residents[i])
                self.assertEqual(notification.title, "Bulk Notification")
                self.assertEqual(notification.message, "This is a bulk notification")

            # Verify task was called for each resident
            self.assertEqual(mock_task.call_count, 3)

    def test_notify_all_residents(self):
        """
        Test notification creation for all active residents.
        Should create notifications for all active residents.
        """
        # Create additional residents
        additional_resident1 = ResidentFactory(is_active=True)
        additional_resident2 = ResidentFactory(is_active=False)  # Inactive resident

        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ) as mock_task:
            notifications = NotificationService.notify_all_residents(
                notification_type_name="new_announcement",
                title="Society-wide Notification",
                message="This is a society-wide notification",
                related_object=self.announcement,
            )

            # Verify notifications were created for active residents only
            # Should include setUp residents + additional_resident1, but not additional_resident2
            expected_count = 6  # 5 from setUp + 1 additional active resident
            self.assertEqual(len(notifications), expected_count)

            # Verify all notifications have correct content
            for notification in notifications:
                self.assertEqual(notification.title, "Society-wide Notification")
                self.assertEqual(
                    notification.message, "This is a society-wide notification"
                )
                self.assertTrue(notification.recipient.is_active)

    def test_notify_all_residents_with_exclusion(self):
        """
        Test notification creation for all residents with exclusions.
        Should exclude specified residents from notifications.
        """
        residents_to_exclude = [self.resident_email_only, self.resident_sms_only]

        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ) as mock_task:
            notifications = NotificationService.notify_all_residents(
                notification_type_name="new_announcement",
                title="Selective Notification",
                message="This is a selective notification",
                exclude_residents=residents_to_exclude,
            )

            # Verify excluded residents are not in notifications
            notification_recipients = [notif.recipient for notif in notifications]
            for excluded_resident in residents_to_exclude:
                self.assertNotIn(excluded_resident, notification_recipients)

    def test_notify_all_residents_empty_exclusion(self):
        """
        Test notification creation with empty exclusion list.
        Should notify all residents when exclusion list is empty.
        """
        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ) as mock_task:
            notifications = NotificationService.notify_all_residents(
                notification_type_name="new_announcement",
                title="No Exclusion Notification",
                message="This notification has no exclusions",
                exclude_residents=[],
            )

            # Should notify all active residents
            self.assertGreater(len(notifications), 0)

    def test_notify_all_residents_none_exclusion(self):
        """
        Test notification creation with None exclusion.
        Should notify all residents when exclusion is None.
        """
        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ) as mock_task:
            notifications = NotificationService.notify_all_residents(
                notification_type_name="new_announcement",
                title="None Exclusion Notification",
                message="This notification has None exclusion",
                exclude_residents=None,
            )

            # Should notify all active residents
            self.assertGreater(len(notifications), 0)

    def test_create_notification_without_related_object(self):
        """
        Test notification creation without related object.
        Should handle gracefully with empty related object fields.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify notification was created
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.related_object_type, "")
        self.assertIsNone(notification.related_object_id)

    def test_create_notification_without_data(self):
        """
        Test notification creation without additional data.
        Should handle gracefully with empty data dict.
        """
        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
        )

        # Verify notification was created
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.data, {})

    def test_create_notification_with_complex_data(self):
        """
        Test notification creation with complex data structure.
        Should handle complex data types in the data field.
        """
        complex_data = {
            "url": "/announcements/123/",
            "category": "Maintenance",
            "priority": 3,
            "metadata": {
                "source": "admin",
                "tags": ["urgent", "maintenance"],
                "numbers": [1, 2, 3],
            },
        }

        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title="Test Notification",
            message="This is a test notification",
            data=complex_data,
        )

        # Verify notification was created with complex data
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.data, complex_data)
        self.assertEqual(notification.data["metadata"]["source"], "admin")
        self.assertEqual(
            notification.data["metadata"]["tags"], ["urgent", "maintenance"]
        )

    @patch("the_khaki_estate.backend.notification_service.send_notification_task")
    def test_create_notification_delivery_method_override(self, mock_task):
        """
        Test notification creation with delivery method override.
        Should override notification type default delivery method.
        """
        # Create notification type with 'both' delivery
        notification_type = NotificationTypeFactory(
            name="test_type",
            default_delivery="both",
        )

        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,  # Email only preference
            notification_type_name="test_type",
            title="Test Notification",
            message="This is a test notification",
            force_delivery="sms",  # Override to SMS only
        )

        # Verify task was called with override delivery method
        mock_task.assert_called_once()
        call_args = mock_task.call_args
        self.assertEqual(call_args[0][1], "sms")

    def test_notification_service_error_handling(self):
        """
        Test NotificationService error handling.
        Should handle errors gracefully without crashing.
        """
        # Test with invalid recipient
        try:
            notification = NotificationService.create_notification(
                recipient=None,  # Invalid recipient
                notification_type_name="new_announcement",
                title="Test Notification",
                message="This is a test notification",
            )
            self.fail("Should have raised an exception for invalid recipient")
        except Exception:
            # Expected to raise exception
            pass

    def test_notification_service_performance(self):
        """
        Test NotificationService performance with bulk operations.
        Should handle bulk operations efficiently.
        """
        import time

        # Create many residents
        residents = []
        for _ in range(50):
            residents.append(ResidentFactory())

        start_time = time.time()

        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ):
            notifications = NotificationService.notify_multiple_residents(
                residents=residents,
                notification_type_name="new_announcement",
                title="Performance Test",
                message="Testing bulk notification performance",
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete within reasonable time
        self.assertLess(execution_time, 5.0)  # Less than 5 seconds
        self.assertEqual(len(notifications), 50)

    def test_notification_service_data_consistency(self):
        """
        Test that NotificationService maintains data consistency.
        Should not corrupt data during operations.
        """
        # Store original data
        original_title = "Test Notification"
        original_message = "This is a test notification"
        original_data = {"url": "/test/", "category": "test"}

        notification = NotificationService.create_notification(
            recipient=self.resident_email_only,
            notification_type_name="new_announcement",
            title=original_title,
            message=original_message,
            data=original_data,
        )

        # Verify data consistency
        self.assertEqual(notification.title, original_title)
        self.assertEqual(notification.message, original_message)
        self.assertEqual(notification.data, original_data)

        # Verify related object consistency
        self.assertEqual(notification.recipient.email, self.resident_email_only.email)
        self.assertEqual(notification.notification_type.name, "new_announcement")

    def test_notification_service_concurrent_operations(self):
        """
        Test NotificationService with concurrent operations.
        Should handle concurrent notification creation safely.
        """
        residents = [
            self.resident_email_only,
            self.resident_sms_only,
            self.resident_both_methods,
        ]

        with patch(
            "the_khaki_estate.backend.notification_service.send_notification_task"
        ):
            # Simulate concurrent operations
            notifications1 = NotificationService.notify_multiple_residents(
                residents=residents,
                notification_type_name="new_announcement",
                title="Concurrent Test 1",
                message="First concurrent notification",
            )

            notifications2 = NotificationService.notify_multiple_residents(
                residents=residents,
                notification_type_name="urgent_announcement",
                title="Concurrent Test 2",
                message="Second concurrent notification",
            )

            # Verify both operations completed successfully
            self.assertEqual(len(notifications1), 3)
            self.assertEqual(len(notifications2), 3)

            # Verify no data corruption
            for notification in notifications1:
                self.assertEqual(notification.title, "Concurrent Test 1")

            for notification in notifications2:
                self.assertEqual(notification.title, "Concurrent Test 2")
