"""
Simple tests for Staff functionality that work with pytest database isolation.
These tests demonstrate the new maintenance staff features.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from the_khaki_estate.backend.models import MaintenanceCategory
from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import Resident
from the_khaki_estate.backend.models import Staff

User = get_user_model()


@pytest.mark.django_db
class TestStaffFunctionalitySimple:
    """Simple tests to demonstrate staff functionality."""

    def test_create_facility_manager(self):
        """Test creating a facility manager with correct permissions."""
        # Create user
        user = User.objects.create_user(
            username="facility_manager",
            email="fm@test.com",
            password="testpass123",
            name="John Smith",
            user_type="staff",
        )

        # Create staff profile
        staff = Staff.objects.create(
            user=user,
            employee_id="EMP001",
            staff_role="facility_manager",
            department="Management",
            phone_number="+919876543210",
            employment_status="full_time",
            hire_date=date.today(),
            can_access_all_maintenance=True,
            can_assign_requests=True,
            can_close_requests=True,
            can_send_announcements=True,
        )

        # Test assertions
        assert staff.user.user_type == "staff"
        assert staff.staff_role == "facility_manager"
        assert staff.is_facility_manager() is True
        assert staff.can_handle_maintenance() is True
        assert staff.can_access_all_maintenance is True
        assert staff.can_assign_requests is True
        assert staff.can_close_requests is True
        assert staff.can_send_announcements is True
        assert staff.can_manage_finances is False  # Should be False for FM

    def test_create_electrician(self):
        """Test creating an electrician with correct permissions."""
        user = User.objects.create_user(
            username="electrician",
            email="elec@test.com",
            password="testpass123",
            name="Mike Johnson",
            user_type="staff",
        )

        staff = Staff.objects.create(
            user=user,
            employee_id="EMP002",
            staff_role="electrician",
            department="Maintenance",
            phone_number="+919876543211",
            employment_status="full_time",
            hire_date=date.today(),
            can_close_requests=True,
        )

        # Test electrician permissions
        assert staff.staff_role == "electrician"
        assert staff.can_handle_maintenance() is True
        assert staff.can_close_requests is True
        assert staff.can_access_all_maintenance is False
        assert staff.can_assign_requests is False
        assert staff.can_manage_finances is False

    def test_create_accountant(self):
        """Test creating an accountant with correct permissions."""
        user = User.objects.create_user(
            username="accountant",
            email="acc@test.com",
            password="testpass123",
            name="Sarah Wilson",
            user_type="staff",
        )

        staff = Staff.objects.create(
            user=user,
            employee_id="EMP003",
            staff_role="accountant",
            department="Finance",
            phone_number="+919876543212",
            employment_status="full_time",
            hire_date=date.today(),
            can_manage_finances=True,
            can_send_announcements=True,
        )

        # Test accountant permissions
        assert staff.staff_role == "accountant"
        assert staff.is_accountant() is True
        assert staff.can_manage_finances is True
        assert staff.can_send_announcements is True
        assert staff.can_handle_maintenance() is False
        assert staff.can_access_all_maintenance is False

    def test_maintenance_request_workflow(self):
        """Test complete maintenance request workflow."""
        # Create users
        resident_user = User.objects.create_user(
            username="resident",
            email="resident@test.com",
            password="testpass123",
            name="Alice Cooper",
            user_type="resident",
        )

        fm_user = User.objects.create_user(
            username="facility_manager",
            email="fm@test.com",
            password="testpass123",
            name="John Smith",
            user_type="staff",
        )

        elec_user = User.objects.create_user(
            username="electrician",
            email="elec@test.com",
            password="testpass123",
            name="Mike Johnson",
            user_type="staff",
        )

        # Create profiles
        resident = Resident.objects.create(
            user=resident_user,
            flat_number="101",
            block="A",
            phone_number="+919876543210",
            resident_type="owner",
        )

        facility_manager = Staff.objects.create(
            user=fm_user,
            employee_id="EMP001",
            staff_role="facility_manager",
            department="Management",
            phone_number="+919876543211",
            employment_status="full_time",
            hire_date=date.today(),
            can_access_all_maintenance=True,
            can_assign_requests=True,
            can_close_requests=True,
        )

        electrician = Staff.objects.create(
            user=elec_user,
            employee_id="EMP002",
            staff_role="electrician",
            department="Maintenance",
            phone_number="+919876543212",
            employment_status="full_time",
            hire_date=date.today(),
            can_close_requests=True,
        )

        # Create maintenance category
        category = MaintenanceCategory.objects.create(
            name="Electrical",
            priority_level=3,
            estimated_resolution_hours=24,
        )

        # 1. Create maintenance request
        request = MaintenanceRequest.objects.create(
            resident=resident_user,
            title="Kitchen outlet not working",
            description="The main kitchen outlet stopped working",
            category=category,
            location="Flat 101",
            priority=3,
            status="submitted",
        )

        assert request.status == "submitted"
        assert request.ticket_number.startswith("MNT-")

        # 2. Acknowledge request
        request.status = "acknowledged"
        request.save()
        assert request.acknowledged_at is not None

        # 3. Assign to electrician
        request.assign_to_staff(electrician.user, facility_manager.user)
        assert request.status == "assigned"
        assert request.assigned_to == electrician.user
        assert request.assigned_by == facility_manager.user
        assert request.assigned_at is not None

        # 4. Start work
        request.status = "in_progress"
        request.estimated_cost = Decimal("200.00")
        request.save()

        # 5. Complete work
        request.status = "resolved"
        request.actual_cost = Decimal("180.00")
        request.save()
        assert request.resolved_at is not None

        # 6. Close with feedback
        request.status = "closed"
        request.resident_rating = 5
        request.resident_feedback = "Excellent work!"
        request.save()
        assert request.closed_at is not None

        # Test workflow completed successfully
        assert request.get_resolution_time() is not None
        assert request.actual_cost < request.estimated_cost

    def test_staff_assignment_logic(self):
        """Test staff assignment logic."""
        # Create users
        fm_user = User.objects.create_user(
            username="fm_test",
            email="fm@test.com",
            password="testpass123",
            name="Facility Manager",
            user_type="staff",
        )

        elec_user = User.objects.create_user(
            username="elec_test",
            email="elec@test.com",
            password="testpass123",
            name="Electrician",
            user_type="staff",
        )

        acc_user = User.objects.create_user(
            username="acc_test",
            email="acc@test.com",
            password="testpass123",
            name="Accountant",
            user_type="staff",
        )

        # Create staff profiles
        facility_manager = Staff.objects.create(
            user=fm_user,
            employee_id="FM001",
            staff_role="facility_manager",
            can_access_all_maintenance=True,
            can_assign_requests=True,
            can_close_requests=True,
        )

        electrician = Staff.objects.create(
            user=elec_user,
            employee_id="EL001",
            staff_role="electrician",
            can_close_requests=True,
        )

        accountant = Staff.objects.create(
            user=acc_user,
            employee_id="AC001",
            staff_role="accountant",
            can_manage_finances=True,
        )

        # Create maintenance request
        resident_user = User.objects.create_user(
            username="resident_assign",
            email="resident@test.com",
            password="testpass123",
            user_type="resident",
        )

        category = MaintenanceCategory.objects.create(
            name="Electrical",
            priority_level=3,
        )

        request = MaintenanceRequest.objects.create(
            resident=resident_user,
            title="Test request",
            description="Test description",
            category=category,
            location="Test location",
            priority=2,
            status="submitted",
        )

        # Test assignment capabilities
        assert request.can_be_assigned_to(facility_manager.user) is True
        assert request.can_be_assigned_to(electrician.user) is True
        assert request.can_be_assigned_to(accountant.user) is False

        # Test suitable staff query
        suitable_staff = request.get_suitable_staff()
        assert facility_manager in suitable_staff
        assert electrician in suitable_staff
        assert accountant not in suitable_staff

    def test_user_type_functionality(self):
        """Test user type methods."""
        # Create resident user
        resident_user = User.objects.create_user(
            username="test_resident",
            email="resident@test.com",
            password="testpass123",
            user_type="resident",
        )

        # Create staff user
        staff_user = User.objects.create_user(
            username="test_staff",
            email="staff@test.com",
            password="testpass123",
            user_type="staff",
        )

        # Test user type methods
        assert resident_user.is_resident() is True
        assert resident_user.is_staff_member() is False
        assert staff_user.is_staff_member() is True
        assert staff_user.is_resident() is False

        # Test default user type
        default_user = User.objects.create_user(
            username="default_user",
            email="default@test.com",
            password="testpass123",
        )
        assert default_user.user_type == "resident"
        assert default_user.is_resident() is True
