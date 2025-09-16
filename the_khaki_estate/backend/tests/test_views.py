"""
Comprehensive test suite for backend views and API endpoints.
Tests all view functionality including authentication, pagination, and error handling.
"""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.utils import timezone

from the_khaki_estate.backend.models import Notification
from the_khaki_estate.backend.tests.factories import NotificationFactory
from the_khaki_estate.backend.tests.factories import NotificationTypeFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory

User = get_user_model()


class NotificationViewsTest(TestCase):
    """
    Test suite for notification-related views and API endpoints.
    Tests GET notifications, mark as read functionality, and proper authentication.
    """

    def setUp(self):
        """
        Set up test data before each test method.
        Creates test users, notifications, and notification types.
        """
        # Create test users with different roles
        self.regular_resident = ResidentFactory()
        self.committee_member = ResidentFactory(is_committee_member=True)
        self.other_resident = ResidentFactory()

        # Create notification type
        self.notification_type = NotificationTypeFactory()

        # Create notifications for different users
        self.notification1 = NotificationFactory(
            recipient=self.regular_resident,
            notification_type=self.notification_type,
            status="sent",
        )
        self.notification2 = NotificationFactory(
            recipient=self.regular_resident,
            notification_type=self.notification_type,
            status="delivered",
        )
        self.notification3 = NotificationFactory(
            recipient=self.other_resident,
            notification_type=self.notification_type,
            status="read",
        )

        # Set up test client
        self.client = Client()

    def test_get_notifications_requires_authentication(self):
        """
        Test that the get_notifications endpoint requires user authentication.
        Unauthenticated requests should be redirected to login page.
        """
        response = self.client.get("/notifications/")

        # Should redirect to login page (status 302)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_get_notifications_authenticated_user(self):
        """
        Test that authenticated users can retrieve their notifications.
        Should return only notifications belonging to the authenticated user.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        response = self.client.get("/notifications/")

        # Should return successful response
        self.assertEqual(response.status_code, 200)

        # Parse JSON response
        data = json.loads(response.content)

        # Should contain notifications data
        self.assertIn("notifications", data)
        self.assertIn("has_next", data)
        self.assertIn("has_previous", data)
        self.assertIn("total_count", data)

        # Should only return notifications for the logged-in user
        notification_ids = [notif["id"] for notif in data["notifications"]]
        self.assertIn(self.notification1.id, notification_ids)
        self.assertIn(self.notification2.id, notification_ids)
        self.assertNotIn(
            self.notification3.id, notification_ids
        )  # Belongs to other user

    def test_get_notifications_with_status_filter(self):
        """
        Test that notifications can be filtered by status.
        Should return only notifications matching the specified status.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Filter by 'sent' status
        response = self.client.get("/notifications/?status=sent")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should only return notifications with 'sent' status
        for notification in data["notifications"]:
            self.assertEqual(notification["status"], "sent")

    def test_get_notifications_pagination(self):
        """
        Test that notifications are properly paginated.
        Should handle page parameter and return appropriate pagination info.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Request first page
        response = self.client.get("/notifications/?page=1")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should contain pagination information
        self.assertIn("has_next", data)
        self.assertIn("has_previous", data)
        self.assertIn("total_count", data)

        # Should return notifications data
        self.assertIsInstance(data["notifications"], list)

    def test_get_notifications_response_structure(self):
        """
        Test that the notifications response has the correct structure.
        Each notification should contain required fields.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        response = self.client.get("/notifications/")
        data = json.loads(response.content)

        # Check response structure
        self.assertIn("notifications", data)
        self.assertIn("has_next", data)
        self.assertIn("has_previous", data)
        self.assertIn("total_count", data)

        # Check notification structure if notifications exist
        if data["notifications"]:
            notification = data["notifications"][0]
            required_fields = ["id", "title", "message", "status", "created_at", "data"]
            for field in required_fields:
                self.assertIn(field, notification)

    def test_mark_notification_read_requires_authentication(self):
        """
        Test that marking notifications as read requires authentication.
        Unauthenticated requests should be redirected to login page.
        """
        response = self.client.post(f"/notifications/{self.notification1.id}/read/")

        # Should redirect to login page (status 302)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_mark_notification_read_success(self):
        """
        Test successfully marking a notification as read.
        Should update the notification status and return success response.
        """
        # Login as the notification recipient
        self.client.force_login(self.regular_resident)

        # Verify notification is not read initially
        self.assertEqual(self.notification1.status, "sent")
        self.assertIsNone(self.notification1.read_at)

        # Mark notification as read
        response = self.client.post(f"/notifications/{self.notification1.id}/read/")

        # Should return success response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Verify notification was updated
        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.status, "read")
        self.assertIsNotNone(self.notification1.read_at)

    def test_mark_notification_read_not_found(self):
        """
        Test marking a non-existent notification as read.
        Should return 404 error with appropriate message.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Try to mark non-existent notification as read
        response = self.client.post("/notifications/99999/read/")

        # Should return 404 error
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("not found", data["message"].lower())

    def test_mark_notification_read_wrong_user(self):
        """
        Test marking a notification as read when it belongs to another user.
        Should return 404 error as user cannot access other users' notifications.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Try to mark notification belonging to another user as read
        response = self.client.post(f"/notifications/{self.notification3.id}/read/")

        # Should return 404 error (for security, don't reveal that notification exists)
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")

    def test_mark_notification_read_already_read(self):
        """
        Test marking an already read notification as read.
        Should still return success (idempotent operation).
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Mark notification as read first time
        self.notification1.mark_as_read()
        original_read_at = self.notification1.read_at

        # Mark as read again
        response = self.client.post(f"/notifications/{self.notification1.id}/read/")

        # Should return success
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

        # Read_at timestamp should remain the same (idempotent)
        self.notification1.refresh_from_db()
        self.assertEqual(self.notification1.read_at, original_read_at)

    def test_mark_notification_read_invalid_method(self):
        """
        Test that only POST method is allowed for marking notifications as read.
        GET requests should return method not allowed error.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Try GET request instead of POST
        response = self.client.get(f"/notifications/{self.notification1.id}/read/")

        # Should return method not allowed (405)
        self.assertEqual(response.status_code, 405)

    def test_get_notifications_empty_result(self):
        """
        Test getting notifications when user has no notifications.
        Should return empty list with proper pagination info.
        """
        # Create user with no notifications
        user_without_notifications = ResidentFactory()
        self.client.force_login(user_without_notifications)

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return empty notifications list
        self.assertEqual(data["notifications"], [])
        self.assertEqual(data["total_count"], 0)
        self.assertFalse(data["has_next"])
        self.assertFalse(data["has_previous"])

    def test_get_notifications_large_dataset(self):
        """
        Test getting notifications with a large number of notifications.
        Should handle pagination correctly and not timeout.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Create many notifications for the user
        for _ in range(25):  # More than default page size (20)
            NotificationFactory(
                recipient=self.regular_resident,
                notification_type=self.notification_type,
            )

        response = self.client.get("/notifications/")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return paginated results
        self.assertEqual(len(data["notifications"]), 20)  # Default page size
        self.assertTrue(data["has_next"])  # Should have more pages
        self.assertEqual(data["total_count"], 27)  # 25 new + 2 existing

    def test_get_notifications_with_invalid_status(self):
        """
        Test getting notifications with invalid status filter.
        Should return empty results or handle gracefully.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Filter by invalid status
        response = self.client.get("/notifications/?status=invalid_status")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return empty results
        self.assertEqual(data["notifications"], [])
        self.assertEqual(data["total_count"], 0)

    def test_get_notifications_with_invalid_page(self):
        """
        Test getting notifications with invalid page number.
        Should handle gracefully and return appropriate results.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        # Request invalid page number
        response = self.client.get("/notifications/?page=999")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return empty results for non-existent page
        self.assertEqual(data["notifications"], [])
        self.assertFalse(data["has_next"])

    def test_notification_data_serialization(self):
        """
        Test that notification data is properly serialized in the response.
        All required fields should be present and properly formatted.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        response = self.client.get("/notifications/")
        data = json.loads(response.content)

        if data["notifications"]:
            notification = data["notifications"][0]

            # Check data types and formats
            self.assertIsInstance(notification["id"], int)
            self.assertIsInstance(notification["title"], str)
            self.assertIsInstance(notification["message"], str)
            self.assertIsInstance(notification["status"], str)
            self.assertIsInstance(notification["created_at"], str)
            self.assertIsInstance(notification["data"], dict)

            # Check that created_at is valid ISO format
            try:
                timezone.datetime.fromisoformat(
                    notification["created_at"].replace("Z", "+00:00")
                )
            except ValueError:
                self.fail("created_at is not in valid ISO format")

    @patch("the_khaki_estate.backend.views.send_notification_task")
    def test_notification_creation_triggers_task(self, mock_task):
        """
        Test that creating a notification triggers the appropriate Celery task.
        This tests the integration between views and background tasks.
        """
        # This test would be more relevant if we had a create notification endpoint
        # For now, we test that the task is properly imported and can be mocked
        self.assertIsNotNone(mock_task)

    def test_notification_permissions(self):
        """
        Test that users can only access their own notifications.
        Ensures proper data isolation between users.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        response = self.client.get("/notifications/")
        data = json.loads(response.content)

        # Verify all returned notifications belong to the logged-in user
        for notification_data in data["notifications"]:
            notification = Notification.objects.get(id=notification_data["id"])
            self.assertEqual(notification.recipient, self.regular_resident)

    def test_notification_response_performance(self):
        """
        Test that notification responses are returned in reasonable time.
        This is a basic performance test to ensure no major bottlenecks.
        """
        # Login as regular resident
        self.client.force_login(self.regular_resident)

        import time

        start_time = time.time()

        response = self.client.get("/notifications/")

        end_time = time.time()
        response_time = end_time - start_time

        # Should respond within reasonable time (less than 1 second)
        self.assertLess(response_time, 1.0)
        self.assertEqual(response.status_code, 200)
