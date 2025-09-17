"""
Tests for Staff registration forms and user type functionality.
Comprehensive testing of StaffSignupForm and user type validation.
"""

from datetime import date

import pytest
from django.contrib.auth import get_user_model

from the_khaki_estate.backend.models import Staff
from the_khaki_estate.backend.tests.factories import StaffFactory
from the_khaki_estate.users.forms import StaffSignupForm

User = get_user_model()


@pytest.mark.django_db
class TestStaffSignupForm:
    """Test StaffSignupForm functionality."""

    def test_staff_form_valid_data(self):
        """Test form with valid staff data."""
        form_data = {
            "username": "facility_manager_1",
            "email": "fm1@khakiestate.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "employee_id": "EMP001",
            "staff_role": "facility_manager",
            "department": "Management",
            "employment_status": "full_time",
            "phone_number": "+919876543210",
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert form.is_valid()

    def test_staff_form_creates_user_and_staff(self):
        """Test that form creates both User and Staff objects."""
        form_data = {
            "username": "electrician_1",
            "email": "elec1@khakiestate.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Mike",
            "last_name": "Johnson",
            "employee_id": "EMP002",
            "staff_role": "electrician",
            "department": "Maintenance",
            "employment_status": "full_time",
            "phone_number": "+919876543211",
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert form.is_valid()

        # Mock request object
        class MockRequest:
            pass

        user = form.save(MockRequest())

        # Check user creation
        assert user.username == "electrician_1"
        assert user.email == "elec1@khakiestate.com"
        assert user.name == "Mike Johnson"
        assert user.user_type == "staff"

        # Check staff profile creation
        staff = Staff.objects.get(user=user)
        assert staff.employee_id == "EMP002"
        assert staff.staff_role == "electrician"
        assert staff.department == "Maintenance"
        assert staff.employment_status == "full_time"
        assert staff.phone_number == "+919876543211"

    def test_staff_form_sets_role_based_permissions(self):
        """Test that form sets permissions based on staff role."""
        # Test facility manager permissions
        form_data = {
            "username": "fm_test",
            "email": "fm@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "FM",
            "employee_id": "EMP003",
            "staff_role": "facility_manager",
            "employment_status": "full_time",
            "phone_number": "+919876543212",
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert form.is_valid()

        class MockRequest:
            pass

        user = form.save(MockRequest())
        staff = Staff.objects.get(user=user)

        # Facility manager should have these permissions
        assert staff.can_access_all_maintenance is True
        assert staff.can_assign_requests is True
        assert staff.can_close_requests is True
        assert staff.can_send_announcements is True
        assert staff.can_manage_finances is False

    def test_staff_form_accountant_permissions(self):
        """Test accountant gets correct permissions."""
        form_data = {
            "username": "accountant_test",
            "email": "acc@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Accountant",
            "employee_id": "EMP004",
            "staff_role": "accountant",
            "employment_status": "full_time",
            "phone_number": "+919876543213",
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert form.is_valid()

        class MockRequest:
            pass

        user = form.save(MockRequest())
        staff = Staff.objects.get(user=user)

        # Accountant should have these permissions
        assert staff.can_manage_finances is True
        assert staff.can_send_announcements is True
        assert staff.can_access_all_maintenance is False
        assert staff.can_assign_requests is False
        assert staff.can_close_requests is False

    def test_staff_form_duplicate_employee_id(self):
        """Test form validation for duplicate employee ID."""
        # Create existing staff
        StaffFactory(employee_id="EMP005")

        form_data = {
            "username": "duplicate_test",
            "email": "dup@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Duplicate",
            "employee_id": "EMP005",  # Duplicate
            "staff_role": "electrician",
            "employment_status": "full_time",
            "phone_number": "+919876543214",
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert not form.is_valid()
        assert "employee_id" in form.errors

    def test_staff_form_invalid_phone_format(self):
        """Test form validation for invalid phone number format."""
        form_data = {
            "username": "phone_test",
            "email": "phone@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Phone",
            "employee_id": "EMP006",
            "staff_role": "plumber",
            "employment_status": "full_time",
            "phone_number": "1234567890",  # Invalid format
            "hire_date": date.today(),
        }

        form = StaffSignupForm(data=form_data)
        assert not form.is_valid()
        assert "phone_number" in form.errors

    def test_staff_form_optional_fields(self):
        """Test form with optional fields."""
        form_data = {
            "username": "optional_test",
            "email": "opt@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Optional",
            "employee_id": "EMP007",
            "staff_role": "gardener",
            "department": "Landscaping",
            "employment_status": "part_time",
            "phone_number": "+919876543215",
            "alternate_phone": "+919876543216",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+919876543217",
            "hire_date": date.today(),
            "work_schedule": "Mon-Fri 7AM-3PM",
            "is_available_24x7": False,
        }

        form = StaffSignupForm(data=form_data)
        assert form.is_valid()

        class MockRequest:
            pass

        user = form.save(MockRequest())
        staff = Staff.objects.get(user=user)

        assert staff.alternate_phone == "+919876543216"
        assert staff.emergency_contact_name == "Jane Doe"
        assert staff.emergency_contact_phone == "+919876543217"
        assert staff.work_schedule == "Mon-Fri 7AM-3PM"
        assert staff.is_available_24x7 is False

    def test_staff_form_all_role_types(self):
        """Test form works with all staff role types."""
        roles = [
            "facility_manager",
            "accountant",
            "security_head",
            "maintenance_supervisor",
            "electrician",
            "plumber",
            "cleaner",
            "gardener",
        ]

        for i, role in enumerate(roles):
            form_data = {
                "username": f"role_test_{i}",
                "email": f"role{i}@test.com",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
                "first_name": "Test",
                "last_name": f"Role{i}",
                "employee_id": f"EMP{100 + i}",
                "staff_role": role,
                "employment_status": "full_time",
                "phone_number": f"+91987654{3220 + i}",
                "hire_date": date.today(),
            }

            form = StaffSignupForm(data=form_data)
            assert form.is_valid(), f"Form invalid for role {role}: {form.errors}"

            class MockRequest:
                pass

            user = form.save(MockRequest())
            staff = Staff.objects.get(user=user)
            assert staff.staff_role == role

    def test_staff_form_missing_required_fields(self):
        """Test form validation with missing required fields."""
        form_data = {
            "username": "missing_test",
            "email": "missing@test.com",
            "password1": "TestPass123!",
            "password2": "TestPass123!",
            # Missing required fields: first_name, last_name, employee_id, etc.
        }

        form = StaffSignupForm(data=form_data)
        assert not form.is_valid()

        required_fields = [
            "first_name",
            "last_name",
            "employee_id",
            "staff_role",
            "phone_number",
            "hire_date",
        ]

        for field in required_fields:
            assert field in form.errors

    def test_staff_form_employment_status_choices(self):
        """Test all employment status choices work."""
        statuses = ["full_time", "part_time", "contract", "consultant"]

        for i, status in enumerate(statuses):
            form_data = {
                "username": f"status_test_{i}",
                "email": f"status{i}@test.com",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
                "first_name": "Test",
                "last_name": f"Status{i}",
                "employee_id": f"EMP{200 + i}",
                "staff_role": "cleaner",
                "employment_status": status,
                "phone_number": f"+91987654{3230 + i}",
                "hire_date": date.today(),
            }

            form = StaffSignupForm(data=form_data)
            assert form.is_valid()

            class MockRequest:
                pass

            user = form.save(MockRequest())
            staff = Staff.objects.get(user=user)
            assert staff.employment_status == status


@pytest.mark.django_db
class TestUserTypeIntegration:
    """Test User model user_type functionality."""

    def test_user_type_methods(self):
        """Test user type helper methods."""
        resident_user = User.objects.create_user(
            username="resident_test",
            email="resident@test.com",
            password="testpass",
            user_type="resident",
        )

        staff_user = User.objects.create_user(
            username="staff_test",
            email="staff@test.com",
            password="testpass",
            user_type="staff",
        )

        # Test resident methods
        assert resident_user.is_resident() is True
        assert resident_user.is_staff_member() is False

        # Test staff methods
        assert staff_user.is_staff_member() is True
        assert staff_user.is_resident() is False

    def test_user_type_default_value(self):
        """Test user_type defaults to resident."""
        user = User.objects.create_user(
            username="default_test",
            email="default@test.com",
            password="testpass",
        )

        assert user.user_type == "resident"
        assert user.is_resident() is True

    def test_user_type_choices_validation(self):
        """Test user_type only accepts valid choices."""
        # Valid choices should work
        user1 = User.objects.create_user(
            username="valid1",
            email="valid1@test.com",
            password="testpass",
            user_type="resident",
        )

        user2 = User.objects.create_user(
            username="valid2",
            email="valid2@test.com",
            password="testpass",
            user_type="staff",
        )

        assert user1.user_type == "resident"
        assert user2.user_type == "staff"
