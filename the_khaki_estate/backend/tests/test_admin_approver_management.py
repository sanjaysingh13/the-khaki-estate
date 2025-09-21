"""
Tests for the Django admin interface for managing approver assignments.

This test suite verifies that administrators can manage designated approvers
for common areas through the Django admin interface.
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse

from the_khaki_estate.backend.admin import ApproverAssignmentAdmin, CommonAreaAdmin
from the_khaki_estate.backend.models import ApproverAssignment, CommonArea, Resident

User = get_user_model()


class ApproverAssignmentAdminTest(TestCase):
    """
    Test the ApproverAssignment admin interface functionality.
    """

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            user_type='staff'
        )
        
        # Create residents using get_or_create to avoid duplicates
        self.resident1, _ = User.objects.get_or_create(
            username='resident1',
            defaults={
                'email': 'resident1@example.com',
                'user_type': 'resident'
            }
        )
        self.resident2, _ = User.objects.get_or_create(
            username='resident2',
            defaults={
                'email': 'resident2@example.com',
                'user_type': 'resident'
            }
        )
        
        # Create resident profiles using get_or_create to avoid duplicates
        Resident.objects.get_or_create(
            user=self.resident1,
            defaults={
                'flat_number': 'A101',
                'phone_number': '+919876543210',
                'resident_type': 'owner'
            }
        )
        
        Resident.objects.get_or_create(
            user=self.resident2,
            defaults={
                'flat_number': 'B202',
                'phone_number': '+919876543211',
                'resident_type': 'owner'
            }
        )
        
        # Create common areas
        self.common_area1 = CommonArea.objects.create(
            name='Community Hall',
            description='Large hall for events',
            capacity=100,
            booking_fee=500.00
        )
        
        self.common_area2 = CommonArea.objects.create(
            name='Garden',
            description='Outdoor garden area',
            capacity=50,
            booking_fee=200.00
        )
        
        # Set up admin
        self.site = AdminSite()
        self.admin = ApproverAssignmentAdmin(ApproverAssignment, self.site)
        self.factory = RequestFactory()

    def test_admin_list_display(self):
        """Test that the admin list display shows correct fields."""
        expected_fields = [
            'common_area',
            'approver',
            'is_active',
            'assigned_by',
            'assigned_at',
        ]
        self.assertEqual(list(self.admin.list_display), expected_fields)

    def test_admin_list_filter(self):
        """Test that the admin list filter includes correct fields."""
        expected_filters = [
            'is_active',
            'common_area',
            'assigned_at',
            'assigned_by',
        ]
        self.assertEqual(list(self.admin.list_filter), expected_filters)

    def test_admin_search_fields(self):
        """Test that the admin search fields include correct fields."""
        expected_fields = [
            'common_area__name',
            'approver__username',
            'approver__email',
            'approver__first_name',
            'approver__last_name',
            'notes',
        ]
        self.assertEqual(list(self.admin.search_fields), expected_fields)

    def test_approver_queryset_filtering(self):
        """Test that approver field only shows residents."""
        request = self.factory.get('/admin/')
        request.user = self.admin_user
        
        # Create a staff user to test filtering
        staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            user_type='staff'
        )
        
        formfield = self.admin.formfield_for_foreignkey(
            ApproverAssignment._meta.get_field('approver'),
            request
        )
        
        # Should only include residents, not staff
        self.assertIn(self.resident1, formfield.queryset)
        self.assertIn(self.resident2, formfield.queryset)
        self.assertNotIn(staff_user, formfield.queryset)
        self.assertNotIn(self.admin_user, formfield.queryset)

    def test_save_model_sets_assigned_by(self):
        """Test that save_model sets assigned_by to current user."""
        request = self.factory.post('/admin/')
        request.user = self.admin_user
        
        assignment = ApproverAssignment(
            common_area=self.common_area1,
            approver=self.resident1,
            is_active=True
        )
        
        self.admin.save_model(request, assignment, None, change=False)
        
        self.assertEqual(assignment.assigned_by, self.admin_user)
        self.assertIsNotNone(assignment.assigned_at)


class CommonAreaAdminTest(TestCase):
    """
    Test the CommonArea admin interface with inline approver assignments.
    """

    def setUp(self):
        """Set up test data."""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            user_type='staff'
        )
        
        # Create resident using get_or_create to avoid duplicates
        self.resident, _ = User.objects.get_or_create(
            username='resident',
            defaults={
                'email': 'resident@example.com',
                'user_type': 'resident'
            }
        )
        
        Resident.objects.get_or_create(
            user=self.resident,
            defaults={
                'flat_number': 'A101',
                'phone_number': '+919876543210',
                'resident_type': 'owner'
            }
        )
        
        # Create common area
        self.common_area = CommonArea.objects.create(
            name='Community Hall',
            description='Large hall for events',
            capacity=100,
            booking_fee=500.00
        )
        
        # Set up admin
        self.site = AdminSite()
        self.admin = CommonAreaAdmin(CommonArea, self.site)

    def test_admin_has_approver_inline(self):
        """Test that CommonArea admin includes ApproverAssignment inline."""
        from the_khaki_estate.backend.admin import ApproverAssignmentInline
        
        self.assertIn(ApproverAssignmentInline, self.admin.inlines)

    def test_get_current_approver_display(self):
        """Test the get_current_approver admin method."""
        # No approver assigned
        display = self.admin.get_current_approver(self.common_area)
        self.assertEqual(display, "No approver assigned")
        
        # Assign approver
        ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        display = self.admin.get_current_approver(self.common_area)
        expected = f"{self.resident.get_full_name() or self.resident.username} ({self.resident.email})"
        self.assertEqual(display, expected)


class ApproverAssignmentModelTest(TestCase):
    """
    Test the ApproverAssignment model functionality.
    """

    def setUp(self):
        """Set up test data."""
        # Create users using get_or_create to avoid duplicates
        self.resident1, _ = User.objects.get_or_create(
            username='resident1',
            defaults={
                'email': 'resident1@example.com',
                'user_type': 'resident'
            }
        )
        self.resident2, _ = User.objects.get_or_create(
            username='resident2',
            defaults={
                'email': 'resident2@example.com',
                'user_type': 'resident'
            }
        )
        self.admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'user_type': 'staff'
            }
        )
        
        # Create resident profiles using get_or_create to avoid duplicates
        Resident.objects.get_or_create(
            user=self.resident1,
            defaults={
                'flat_number': 'A101',
                'phone_number': '+919876543210',
                'resident_type': 'owner'
            }
        )
        
        Resident.objects.get_or_create(
            user=self.resident2,
            defaults={
                'flat_number': 'B202',
                'phone_number': '+919876543211',
                'resident_type': 'owner'
            }
        )
        
        # Create common area
        self.common_area = CommonArea.objects.create(
            name='Community Hall',
            description='Large hall for events',
            capacity=100,
            booking_fee=500.00
        )

    def test_approver_assignment_creation(self):
        """Test creating an approver assignment."""
        assignment = ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident1,
            is_active=True,
            assigned_by=self.admin_user,
            notes='Test assignment'
        )
        
        self.assertEqual(assignment.common_area, self.common_area)
        self.assertEqual(assignment.approver, self.resident1)
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.assigned_by, self.admin_user)
        self.assertEqual(assignment.notes, 'Test assignment')
        self.assertIsNotNone(assignment.assigned_at)

    def test_unique_together_constraint(self):
        """Test that unique_together constraint works."""
        # Create first assignment
        ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident1,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        # Try to create duplicate assignment
        with self.assertRaises(Exception):  # IntegrityError
            ApproverAssignment.objects.create(
                common_area=self.common_area,
                approver=self.resident1,
                is_active=True,
                assigned_by=self.admin_user
            )

    def test_save_deactivates_other_assignments(self):
        """Test that saving an active assignment deactivates others for same area."""
        # Create first active assignment
        assignment1 = ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident1,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        # Create second active assignment for same area
        assignment2 = ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident2,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        # Refresh from database
        assignment1.refresh_from_db()
        
        # First assignment should be deactivated
        self.assertFalse(assignment1.is_active)
        # Second assignment should be active
        self.assertTrue(assignment2.is_active)

    def test_model_string_representation(self):
        """Test the model's string representation."""
        assignment = ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident1,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        expected = f"{self.common_area.name} → {self.resident1.get_full_name() or self.resident1.username}"
        self.assertEqual(str(assignment), expected)

    def test_common_area_get_designated_approver(self):
        """Test CommonArea.get_designated_approver method."""
        # No assignment
        approver = self.common_area.get_designated_approver()
        self.assertIsNone(approver)
        
        # Create inactive assignment
        ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident1,
            is_active=False,
            assigned_by=self.admin_user
        )
        
        approver = self.common_area.get_designated_approver()
        self.assertIsNone(approver)
        
        # Create active assignment
        ApproverAssignment.objects.create(
            common_area=self.common_area,
            approver=self.resident2,
            is_active=True,
            assigned_by=self.admin_user
        )
        
        approver = self.common_area.get_designated_approver()
        self.assertEqual(approver, self.resident2)
        
        # Deactivate resident
        self.resident2.is_active = False
        self.resident2.save()
        
        approver = self.common_area.get_designated_approver()
        self.assertIsNone(approver)
