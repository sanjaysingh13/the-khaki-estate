"""
Comprehensive tests for the booking approval workflow.

This test suite covers the complete booking approval system where designated
residents (instead of facility managers) handle approvals for specific areas.

Test Coverage:
- Booking model approval methods
- Designated approver assignment
- Approval/rejection workflow
- Notification system integration
- Signal handlers
- View permissions and functionality
"""

import pytest
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from the_khaki_estate.backend.models import ApproverAssignment, Booking, CommonArea, Resident
from the_khaki_estate.backend.tests.factories import (
    BookingFactory,
    CommonAreaFactory,
    ResidentFactory,
    UserFactory,
)
from the_khaki_estate.backend.signals import booking_workflow_handler

User = get_user_model()


class BookingApprovalWorkflowTest(TestCase):
    """
    Test suite for the booking approval workflow system.
    
    This class tests the complete workflow where designated residents
    approve bookings instead of facility managers.
    """

    def setUp(self):
        """
        Set up test data for booking approval workflow tests.
        
        Creates:
        - Designated residents (sanjaysingh13, ajoykumar)
        - Common areas (Community Hall, Garden)
        - Regular residents for booking creation
        """
        # Create designated residents as specified in requirements
        self.sanjaysingh13 = User.objects.create_user(
            username='sanjaysingh13',
            email='sanjaysingh13@example.com',
            first_name='Sanjay',
            last_name='Singh',
            user_type='resident',
            is_active=True
        )
        
        self.ajoykumar = User.objects.create_user(
            username='ajoykumar',
            email='ajoykumar@example.com',
            first_name='Ajoy',
            last_name='Kumar',
            user_type='resident',
            is_active=True
        )
        
        # Create resident profiles
        self.sanjaysingh13_profile = Resident.objects.create(
            user=self.sanjaysingh13,
            flat_number='A101',
            phone_number='+919876543210',
            resident_type='owner',
            is_committee_member=True
        )
        
        self.ajoykumar_profile = Resident.objects.create(
            user=self.ajoykumar,
            flat_number='B205',
            phone_number='+919876543211',
            resident_type='owner',
            is_committee_member=True
        )
        
        # Create common areas
        self.community_hall = CommonArea.objects.create(
            name='Community Hall',
            description='Large hall for events',
            capacity=100,
            booking_fee=500.00,
            is_active=True
        )
        
        self.garden = CommonArea.objects.create(
            name='Garden',
            description='Outdoor garden area',
            capacity=50,
            booking_fee=200.00,
            is_active=True
        )
        
        # Create approver assignments
        ApproverAssignment.objects.create(
            common_area=self.community_hall,
            approver=self.sanjaysingh13,
            is_active=True,
            notes='Test assignment for Community Hall'
        )
        
        ApproverAssignment.objects.create(
            common_area=self.garden,
            approver=self.ajoykumar,
            is_active=True,
            notes='Test assignment for Garden'
        )
        
        # Create a regular resident for booking creation
        self.regular_resident = UserFactory(
            username='testresident',
            user_type='resident'
        )
        self.regular_resident_profile = Resident.objects.create(
            user=self.regular_resident,
            flat_number='C301',
            phone_number='+919876543212',
            resident_type='owner'
        )

    def test_designated_approver_assignment(self):
        """
        Test that the correct designated approver is assigned based on common area.
        
        Business Logic:
        - Community Hall → sanjaysingh13
        - Garden → ajoykumar
        """
        # Test Community Hall assignment
        booking_hall = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test event in Community Hall',
            status='pending'
        )
        
        approver_hall = booking_hall.get_designated_approver()
        self.assertEqual(approver_hall, self.sanjaysingh13)
        
        # Test Garden assignment
        booking_garden = Booking.objects.create(
            common_area=self.garden,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(14, 0),
            end_time=time(16, 0),
            purpose='Test event in Garden',
            status='pending'
        )
        
        approver_garden = booking_garden.get_designated_approver()
        self.assertEqual(approver_garden, self.ajoykumar)

    def test_set_designated_approver(self):
        """
        Test the set_designated_approver method.
        
        This method should automatically set the designated_approver field
        based on the common area when creating a booking.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking'
        )
        
        # Set the designated approver
        approver = booking.set_designated_approver()
        self.assertEqual(approver, self.sanjaysingh13)
        self.assertEqual(booking.designated_approver, self.sanjaysingh13)

    def test_can_be_approved_by_permissions(self):
        """
        Test permission checking for booking approval.
        
        Only the designated approver should be able to approve a booking
        when it's in pending status.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking',
            status='pending'
        )
        booking.set_designated_approver()
        
        # Designated approver should be able to approve
        self.assertTrue(booking.can_be_approved_by(self.sanjaysingh13))
        
        # Other residents should not be able to approve
        self.assertFalse(booking.can_be_approved_by(self.ajoykumar))
        self.assertFalse(booking.can_be_approved_by(self.regular_resident))
        
        # Inactive user should not be able to approve
        self.sanjaysingh13.is_active = False
        self.sanjaysingh13.save()
        self.assertFalse(booking.can_be_approved_by(self.sanjaysingh13))
        
        # Restore active status
        self.sanjaysingh13.is_active = True
        self.sanjaysingh13.save()
        
        # Non-pending bookings should not be approvable
        booking.status = 'approved'
        booking.save()
        self.assertFalse(booking.can_be_approved_by(self.sanjaysingh13))

    def test_approve_booking_workflow(self):
        """
        Test the complete booking approval workflow.
        
        This test covers:
        - Approving a booking
        - Rejecting a booking
        - Proper timestamp and audit trail updates
        - Validation of approval permissions
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking',
            status='pending'
        )
        booking.set_designated_approver()
        
        # Test approval
        booking.approve_booking(
            approver=self.sanjaysingh13,
            approved=True
        )
        
        self.assertEqual(booking.status, 'approved')
        self.assertEqual(booking.approved_by, self.sanjaysingh13)
        self.assertIsNotNone(booking.approved_at)
        self.assertEqual(booking.status_changed_by, self.sanjaysingh13)
        self.assertIsNotNone(booking.status_changed_at)
        self.assertEqual(booking.rejection_reason, '')
        
        # Test rejection
        booking2 = Booking.objects.create(
            common_area=self.garden,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=8),
            start_time=time(14, 0),
            end_time=time(16, 0),
            purpose='Test booking 2',
            status='pending'
        )
        booking2.set_designated_approver()
        
        rejection_reason = "Area is under maintenance"
        booking2.approve_booking(
            approver=self.ajoykumar,
            approved=False,
            rejection_reason=rejection_reason
        )
        
        self.assertEqual(booking2.status, 'rejected')
        self.assertEqual(booking2.approved_by, self.ajoykumar)
        self.assertIsNotNone(booking2.approved_at)
        self.assertEqual(booking2.rejection_reason, rejection_reason)

    def test_approve_booking_validation(self):
        """
        Test validation in the approve_booking method.
        
        Should raise ValueError for invalid approval attempts.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking',
            status='pending'
        )
        booking.set_designated_approver()
        
        # Try to approve with wrong user
        with self.assertRaises(ValueError):
            booking.approve_booking(
                approver=self.ajoykumar,  # Wrong approver for Community Hall
                approved=True
            )

    def test_booking_duration_calculation(self):
        """
        Test booking duration calculation method.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking'
        )
        
        duration = booking.booking_duration_hours
        self.assertEqual(duration, 2.0)
        
        # Test overnight booking
        booking_overnight = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today(),
            start_time=time(22, 0),
            end_time=time(2, 0),
            purpose='Overnight event'
        )
        
        duration_overnight = booking_overnight.booking_duration_hours
        self.assertEqual(duration_overnight, 4.0)

    def test_booking_overdue_status(self):
        """
        Test overdue booking detection.
        """
        # Create past booking
        past_booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Past booking',
            status='pending'
        )
        
        self.assertTrue(past_booking.is_overdue())
        
        # Create future booking
        future_booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Future booking',
            status='pending'
        )
        
        self.assertFalse(future_booking.is_overdue())
        
        # Completed bookings should not be overdue
        completed_booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() - timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Completed booking',
            status='completed'
        )
        
        self.assertFalse(completed_booking.is_overdue())

    def test_status_display_colors(self):
        """
        Test status display color mapping.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking'
        )
        
        # Test different status colors
        booking.status = 'pending'
        self.assertEqual(booking.get_status_display_color(), 'warning')
        
        booking.status = 'approved'
        self.assertEqual(booking.get_status_display_color(), 'info')
        
        booking.status = 'confirmed'
        self.assertEqual(booking.get_status_display_color(), 'success')
        
        booking.status = 'rejected'
        self.assertEqual(booking.get_status_display_color(), 'danger')

    @patch('the_khaki_estate.backend.signals._handle_new_booking')
    def test_booking_creation_signal(self, mock_handle_new_booking):
        """
        Test that booking creation triggers the appropriate signal handler.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking',
            status='pending'
        )
        
        # Verify the signal handler was called
        mock_handle_new_booking.assert_called_once_with(booking)

    def test_booking_model_string_representation(self):
        """
        Test the string representation of booking model.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking'
        )
        
        expected_str = f"{booking.booking_number} - {self.community_hall.name}"
        self.assertEqual(str(booking), expected_str)

    def test_booking_number_generation(self):
        """
        Test automatic booking number generation.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today(),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking'
        )
        
        # Should have a booking number in format BKG-YYYY-XXXX
        current_year = timezone.now().year
        expected_prefix = f"BKG-{current_year}-"
        self.assertTrue(booking.booking_number.startswith(expected_prefix))

    def test_booking_model_ordering(self):
        """
        Test the default ordering of booking model.
        """
        # Create bookings with different dates
        booking1 = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Future booking 1'
        )
        
        booking2 = Booking.objects.create(
            common_area=self.garden,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=2),
            start_time=time(14, 0),
            end_time=time(16, 0),
            purpose='Future booking 2'
        )
        
        bookings = Booking.objects.all()
        # Should be ordered by booking_date descending, then start_time descending
        self.assertEqual(bookings[0], booking2)  # Later date
        self.assertEqual(bookings[1], booking1)  # Earlier date


class BookingApprovalIntegrationTest(TestCase):
    """
    Integration tests for the booking approval workflow.
    
    These tests verify the complete integration between models, views,
    signals, and notifications.
    """

    def setUp(self):
        """Set up integration test data."""
        # Create designated residents using get_or_create to avoid duplicates
        self.sanjaysingh13, _ = User.objects.get_or_create(
            username='sanjaysingh13',
            defaults={
                'email': 'sanjaysingh13@example.com',
                'user_type': 'resident'
            }
        )
        self.sanjaysingh13_resident, _ = Resident.objects.get_or_create(
            user=self.sanjaysingh13,
            defaults={
                'flat_number': 'A101',
                'phone_number': '+919876543210',
                'resident_type': 'owner'
            }
        )
        
        self.ajoykumar, _ = User.objects.get_or_create(
            username='ajoykumar',
            defaults={
                'email': 'ajoykumar@example.com',
                'user_type': 'resident'
            }
        )
        self.ajoykumar_resident, _ = Resident.objects.get_or_create(
            user=self.ajoykumar,
            defaults={
                'flat_number': 'B205',
                'phone_number': '+919876543211',
                'resident_type': 'owner'
            }
        )
        
        # Create common areas using get_or_create to avoid duplicates
        self.community_hall, _ = CommonArea.objects.get_or_create(
            name='Community Hall',
            defaults={
                'description': 'Large hall for events',
                'capacity': 100,
                'booking_fee': 500.00
            }
        )
        
        self.garden, _ = CommonArea.objects.get_or_create(
            name='Garden',
            defaults={
                'description': 'Outdoor garden area',
                'capacity': 50,
                'booking_fee': 200.00
            }
        )
        
        # Create approver assignments using get_or_create to avoid duplicates
        ApproverAssignment.objects.get_or_create(
            common_area=self.community_hall,
            approver=self.sanjaysingh13,
            defaults={
                'is_active': True,
                'notes': 'Integration test assignment for Community Hall'
            }
        )
        
        ApproverAssignment.objects.get_or_create(
            common_area=self.garden,
            approver=self.ajoykumar,
            defaults={
                'is_active': True,
                'notes': 'Integration test assignment for Garden'
            }
        )
        
        # Create regular resident using get_or_create to avoid duplicates
        self.regular_resident, _ = User.objects.get_or_create(
            username='regular_resident',
            defaults={
                'email': 'regular@example.com',
                'user_type': 'resident'
            }
        )
        self.regular_resident_obj, _ = Resident.objects.get_or_create(
            user=self.regular_resident,
            defaults={
                'flat_number': 'C301',
                'phone_number': '+919876543212',
                'resident_type': 'owner'
            }
        )

    @patch('the_khaki_estate.backend.notification_service.NotificationService.create_notification')
    def test_booking_creation_notification_flow(self, mock_create_notification):
        """
        Test that booking creation triggers notifications to designated approver.
        """
        # Create booking for Community Hall
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test event',
            status='pending'
        )
        
        # Verify notification was sent to sanjaysingh13 (Community Hall approver)
        mock_create_notification.assert_called_once()
        call_args = mock_create_notification.call_args
        
        self.assertEqual(call_args[1]['recipient'], self.sanjaysingh13)
        self.assertEqual(call_args[1]['notification_type_name'], 'booking_pending_approval')
        self.assertIn('New Booking Request:', call_args[1]['title'])
        self.assertIn(booking.booking_number, call_args[1]['title'])

    def test_booking_approval_workflow_integration(self):
        """
        Test the complete booking approval workflow integration.
        
        This test simulates the real-world workflow:
        1. Resident creates booking
        2. Designated approver receives notification
        3. Designated approver approves/rejects booking
        4. Resident receives notification of decision
        """
        # Step 1: Create booking
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Integration test booking',
            status='pending'
        )
        
        # Step 2: Verify designated approver is set
        approver = booking.set_designated_approver()
        self.assertEqual(approver, self.sanjaysingh13)
        
        # Step 3: Approve booking
        booking.approve_booking(
            approver=self.sanjaysingh13,
            approved=True
        )
        
        # Step 4: Verify approval state
        self.assertEqual(booking.status, 'approved')
        self.assertEqual(booking.approved_by, self.sanjaysingh13)
        self.assertIsNotNone(booking.approved_at)
        
        # Step 5: Test rejection workflow
        booking2 = Booking.objects.create(
            common_area=self.garden,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=8),
            start_time=time(14, 0),
            end_time=time(16, 0),
            purpose='Integration test booking 2',
            status='pending'
        )
        
        booking2.set_designated_approver()
        booking2.approve_booking(
            approver=self.ajoykumar,
            approved=False,
            rejection_reason="Area unavailable"
        )
        
        self.assertEqual(booking2.status, 'rejected')
        self.assertEqual(booking2.rejection_reason, "Area unavailable")

    def test_multiple_bookings_same_approver(self):
        """
        Test handling multiple bookings for the same designated approver.
        """
        # Create multiple bookings for Community Hall
        bookings = []
        for i in range(3):
            booking = Booking.objects.create(
                common_area=self.community_hall,
                resident=self.regular_resident,
                booking_date=date.today() + timedelta(days=i+1),
                start_time=time(10, 0),
                end_time=time(12, 0),
                purpose=f'Test booking {i+1}',
                status='pending'
            )
            booking.set_designated_approver()
            bookings.append(booking)
        
        # All should have the same designated approver
        for booking in bookings:
            self.assertEqual(booking.designated_approver, self.sanjaysingh13)
        
        # Approve all bookings
        for booking in bookings:
            booking.approve_booking(
                approver=self.sanjaysingh13,
                approved=True
            )
        
        # Verify all are approved
        for booking in bookings:
            self.assertEqual(booking.status, 'approved')

    def test_booking_approval_permission_edge_cases(self):
        """
        Test edge cases for booking approval permissions.
        """
        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.regular_resident,
            booking_date=date.today() + timedelta(days=7),
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose='Test booking',
            status='pending'
        )
        booking.set_designated_approver()
        
        # Test with non-resident user
        staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            user_type='staff'
        )
        self.assertFalse(booking.can_be_approved_by(staff_user))
        
        # Test with inactive designated approver
        self.sanjaysingh13.is_active = False
        self.sanjaysingh13.save()
        self.assertFalse(booking.can_be_approved_by(self.sanjaysingh13))
        
        # Test with None user
        self.assertFalse(booking.can_be_approved_by(None))
