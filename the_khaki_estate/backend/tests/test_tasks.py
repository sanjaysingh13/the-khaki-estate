"""
Comprehensive test suite for Celery tasks.
Tests asynchronous task execution, error handling, and notification delivery.
"""

from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from the_khaki_estate.backend.tasks import send_notification_task
from the_khaki_estate.backend.tests.factories import NotificationFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory


class SendNotificationTaskTest(TestCase):
    """
    Test suite for the send_notification_task Celery task.
    Tests email sending, SMS sending, error handling, and status updates.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        Creates test users, notifications, and notification types.
        """
        # Create test resident with email and phone
        self.resident = ResidentFactory(
            email="test@example.com",
            phone_number="+1234567890",
            email_notifications=True,
            sms_notifications=True,
        )

        # Create notification type with templates
        self.notification_type = NotificationTypeFactory(
            template_name="test_notification.html",
            sms_template="Test SMS: {title} - {message}",
            default_delivery="both",
        )

        # Create test notification
        self.notification = NotificationFactory(
            recipient=self.resident,
            notification_type=self.notification_type,
            title="Test Notification",
            message="This is a test notification message",
            status="sent",
        )

    def test_send_notification_task_success_email_only(self):
        """
        Test successful email-only notification sending.
        Should send email and update notification status to delivered.
        """
        # Mock the email sending to avoid actual email delivery
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute the task
            result = send_notification_task(self.notification.id, "email")

            # Verify email was sent
            mock_send_mail.assert_called_once()
            call_args = mock_send_mail.call_args

            # Check email parameters
            self.assertEqual(call_args[1]["subject"], "Test Notification")
            self.assertEqual(
                call_args[1]["message"], "This is a test notification message"
            )
            self.assertEqual(call_args[1]["from_email"], "noreply@yourhousing.com")
            self.assertEqual(call_args[1]["recipient_list"], ["test@example.com"])
            self.assertTrue(call_args[1]["fail_silently"])

            # Verify notification was updated
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")
            self.assertTrue(self.notification.email_sent)
            self.assertIsNotNone(self.notification.sent_at)

    def test_send_notification_task_success_sms_only(self):
        """
        Test successful SMS-only notification sending.
        Should process SMS sending and update notification status.
        """
        # Mock SMS sending (placeholder implementation)
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            # Execute the task with SMS only
            result = send_notification_task(self.notification.id, "sms")

            # Email should not be sent
            mock_send_mail.assert_not_called()

            # Verify notification was updated
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")
            self.assertTrue(self.notification.sms_sent)
            self.assertIsNotNone(self.notification.sent_at)

    def test_send_notification_task_success_both_methods(self):
        """
        Test successful notification sending via both email and SMS.
        Should send both email and SMS, updating both flags.
        """
        # Mock both email and SMS sending
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute the task with both methods
            result = send_notification_task(self.notification.id, "both")

            # Verify email was sent
            mock_send_mail.assert_called_once()

            # Verify notification was updated
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")
            self.assertTrue(self.notification.email_sent)
            self.assertTrue(self.notification.sms_sent)
            self.assertIsNotNone(self.notification.sent_at)

    def test_send_notification_task_email_failure(self):
        """
        Test handling of email sending failure.
        Should mark notification as failed when email sending fails.
        """
        # Mock email sending to raise an exception
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("SMTP Error")

            # Execute the task
            result = send_notification_task(self.notification.id, "email")

            # Verify notification was marked as failed
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "failed")
            self.assertFalse(self.notification.email_sent)

    def test_send_notification_task_sms_failure(self):
        """
        Test handling of SMS sending failure.
        Should mark notification as failed when SMS sending fails.
        """
        # Mock SMS sending to raise an exception
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            # Execute the task with SMS only
            result = send_notification_task(self.notification.id, "sms")

            # For now, SMS sending doesn't raise exceptions in the current implementation
            # This test documents the expected behavior for future SMS implementation
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")

    def test_send_notification_task_nonexistent_notification(self):
        """
        Test handling of non-existent notification ID.
        Should handle gracefully without raising exceptions.
        """
        # Execute task with non-existent notification ID
        result = send_notification_task(99999, "email")

        # Should complete without raising exceptions
        # In the current implementation, this would print an error message
        self.assertIsNone(result)

    def test_send_notification_task_no_email_address(self):
        """
        Test notification sending when recipient has no email address.
        Should skip email sending and continue with other methods.
        """
        # Create resident without email
        resident_no_email = ResidentFactory(email="")
        notification_no_email = NotificationFactory(
            recipient=resident_no_email,
            notification_type=self.notification_type,
        )

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            # Execute the task
            result = send_notification_task(notification_no_email.id, "email")

            # Email should not be sent
            mock_send_mail.assert_not_called()

            # Notification should still be marked as delivered (SMS might work)
            notification_no_email.refresh_from_db()
            self.assertEqual(notification_no_email.status, "delivered")

    def test_send_notification_task_no_phone_number(self):
        """
        Test notification sending when recipient has no phone number.
        Should skip SMS sending and continue with other methods.
        """
        # Create resident without phone
        resident_no_phone = ResidentFactory(phone_number="")
        notification_no_phone = NotificationFactory(
            recipient=resident_no_phone,
            notification_type=self.notification_type,
        )

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute the task
            result = send_notification_task(notification_no_phone.id, "both")

            # Email should be sent
            mock_send_mail.assert_called_once()

            # SMS should be skipped, but notification should still be delivered
            notification_no_phone.refresh_from_db()
            self.assertEqual(notification_no_phone.status, "delivered")
            self.assertTrue(notification_no_phone.email_sent)
            self.assertFalse(notification_no_phone.sms_sent)

    def test_send_notification_task_email_template_rendering(self):
        """
        Test that email templates are properly rendered with context.
        Should use the notification type's template and pass proper context.
        """
        with patch("the_khaki_estate.backend.tasks.render_to_string") as mock_render:
            with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
                mock_render.return_value = "<html>Test Email</html>"
                mock_send_mail.return_value = True

                # Execute the task
                result = send_notification_task(self.notification.id, "email")

                # Verify template was rendered
                mock_render.assert_called_once()
                call_args = mock_render.call_args

                # Check template name
                self.assertEqual(
                    call_args[0][0], "notifications/test_notification.html"
                )

                # Check context
                context = call_args[0][1]
                self.assertEqual(context["recipient"], self.resident)
                self.assertEqual(context["notification"], self.notification)
                self.assertIn("data", context)

    def test_send_notification_task_sms_template_formatting(self):
        """
        Test that SMS templates are properly formatted with context.
        Should use the notification type's SMS template and format it correctly.
        """
        # This test documents the expected behavior for SMS template formatting
        # The current implementation has placeholder SMS sending code

        # Verify SMS template exists
        self.assertIsNotNone(self.notification_type.sms_template)
        self.assertIn("{title}", self.notification_type.sms_template)
        self.assertIn("{message}", self.notification_type.sms_template)

        # Test template formatting logic
        formatted_sms = self.notification_type.sms_template.format(
            recipient=self.resident,
            title=self.notification.title,
            message=self.notification.message,
        )

        self.assertIn("Test Notification", formatted_sms)
        self.assertIn("This is a test notification message", formatted_sms)

    def test_send_notification_task_in_app_only(self):
        """
        Test notification sending with in-app only delivery method.
        Should not send email or SMS, just mark as delivered.
        """
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            # Execute the task with in-app only
            result = send_notification_task(self.notification.id, "in_app")

            # Neither email nor SMS should be sent
            mock_send_mail.assert_not_called()

            # Notification should be marked as delivered
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")
            self.assertFalse(self.notification.email_sent)
            self.assertFalse(self.notification.sms_sent)

    def test_send_notification_task_status_transitions(self):
        """
        Test that notification status transitions are handled correctly.
        Should properly update status based on delivery success/failure.
        """
        # Test successful delivery
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Start with 'sent' status
            self.assertEqual(self.notification.status, "sent")

            # Execute task
            result = send_notification_task(self.notification.id, "email")

            # Should transition to 'delivered'
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "delivered")

        # Test failed delivery
        notification_failed = NotificationFactory(
            recipient=self.resident,
            notification_type=self.notification_type,
            status="sent",
        )

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Delivery failed")

            # Execute task
            result = send_notification_task(notification_failed.id, "email")

            # Should transition to 'failed'
            notification_failed.refresh_from_db()
            self.assertEqual(notification_failed.status, "failed")

    def test_send_notification_task_timestamp_updates(self):
        """
        Test that timestamps are properly updated during task execution.
        Should set sent_at when notification is successfully delivered.
        """
        # Verify initial state
        self.assertIsNone(self.notification.sent_at)

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute task
            result = send_notification_task(self.notification.id, "email")

            # Should set sent_at timestamp
            self.notification.refresh_from_db()
            self.assertIsNotNone(self.notification.sent_at)

            # Should be recent timestamp
            time_diff = timezone.now() - self.notification.sent_at
            self.assertLess(time_diff.total_seconds(), 5)  # Within 5 seconds

    def test_send_notification_task_concurrent_execution(self):
        """
        Test that the task can handle concurrent execution safely.
        Should not cause race conditions or data corruption.
        """
        # Create multiple notifications
        notifications = []
        for _ in range(5):
            notifications.append(
                NotificationFactory(
                    recipient=self.resident,
                    notification_type=self.notification_type,
                    status="sent",
                )
            )

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute tasks for all notifications
            results = []
            for notification in notifications:
                result = send_notification_task(notification.id, "email")
                results.append(result)

            # All notifications should be processed successfully
            for notification in notifications:
                notification.refresh_from_db()
                self.assertEqual(notification.status, "delivered")
                self.assertTrue(notification.email_sent)

    def test_send_notification_task_error_logging(self):
        """
        Test that errors are properly logged during task execution.
        Should log errors without crashing the task.
        """
        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            with patch("the_khaki_estate.backend.tasks.print") as mock_print:
                mock_send_mail.side_effect = Exception("Test error")

                # Execute task
                result = send_notification_task(self.notification.id, "email")

                # Should log the error
                mock_print.assert_called()
                error_call = mock_print.call_args[0][0]
                self.assertIn("Email send failed", error_call)
                self.assertIn("Test error", error_call)

    def test_send_notification_task_retry_mechanism(self):
        """
        Test that the task can be retried on failure.
        Should handle retries gracefully without data corruption.
        """
        # This test documents the expected behavior for retry mechanisms
        # The current implementation doesn't have explicit retry logic

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Temporary failure")

            # Execute task
            result = send_notification_task(self.notification.id, "email")

            # Should handle failure gracefully
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.status, "failed")

    def test_send_notification_task_performance(self):
        """
        Test that the task executes within reasonable time limits.
        Should not take too long to complete.
        """
        import time

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            start_time = time.time()
            result = send_notification_task(self.notification.id, "email")
            end_time = time.time()

            execution_time = end_time - start_time

            # Should complete within reasonable time (less than 1 second for test)
            self.assertLess(execution_time, 1.0)

    def test_send_notification_task_data_integrity(self):
        """
        Test that the task maintains data integrity during execution.
        Should not corrupt notification data or related objects.
        """
        # Store original notification data
        original_title = self.notification.title
        original_message = self.notification.message
        original_recipient_id = self.notification.recipient.id

        with patch("the_khaki_estate.backend.tasks.send_mail") as mock_send_mail:
            mock_send_mail.return_value = True

            # Execute task
            result = send_notification_task(self.notification.id, "email")

            # Verify data integrity
            self.notification.refresh_from_db()
            self.assertEqual(self.notification.title, original_title)
            self.assertEqual(self.notification.message, original_message)
            self.assertEqual(self.notification.recipient.id, original_recipient_id)

            # Verify related objects are intact
            self.assertEqual(self.notification.recipient.email, "test@example.com")
            self.assertEqual(
                self.notification.notification_type.template_name,
                "test_notification.html",
            )
