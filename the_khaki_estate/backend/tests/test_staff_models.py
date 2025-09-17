"""
Tests for Staff model functionality and maintenance staff features.
Comprehensive testing of staff roles, permissions, and maintenance request handling.
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.utils import timezone

from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import Staff
from the_khaki_estate.backend.tests.factories import MaintenanceRequestFactory
from the_khaki_estate.backend.tests.factories import StaffFactory
from the_khaki_estate.users.tests.factories import ResidentUserFactory
from the_khaki_estate.users.tests.factories import StaffUserFactory


@pytest.mark.django_db
class TestStaffModel:
    """Test Staff model creation, validation, and methods."""

    def test_staff_creation_with_valid_data(self):
        """Test creating staff with valid data."""
        staff = StaffFactory()

        assert staff.id is not None
        assert staff.user.user_type == "staff"
        assert staff.employee_id.startswith("EMP")
        assert staff.staff_role in [choice[0] for choice in Staff.STAFF_ROLES]
        assert staff.employment_status in [
            choice[0] for choice in Staff.EMPLOYMENT_STATUS
        ]
        assert staff.is_active is True

    def test_staff_unique_employee_id(self):
        """Test that employee IDs must be unique."""
        staff1 = StaffFactory(employee_id="EMP001")

        with pytest.raises(IntegrityError):
            StaffFactory(employee_id="EMP001")

    def test_staff_role_permissions_facility_manager(self):
        """Test facility manager gets correct default permissions."""
        staff = StaffFactory(staff_role="facility_manager")

        assert staff.can_access_all_maintenance is True
        assert staff.can_assign_requests is True
        assert staff.can_close_requests is True
        assert staff.can_send_announcements is True
        assert staff.can_manage_finances is False

    def test_staff_role_permissions_accountant(self):
        """Test accountant gets correct default permissions."""
        staff = StaffFactory(staff_role="accountant")

        assert staff.can_manage_finances is True
        assert staff.can_send_announcements is True
        assert staff.can_access_all_maintenance is False
        assert staff.can_assign_requests is False
        assert staff.can_close_requests is False

    def test_staff_role_permissions_electrician(self):
        """Test electrician gets correct default permissions."""
        staff = StaffFactory(staff_role="electrician")

        assert staff.can_close_requests is True
        assert staff.can_access_all_maintenance is False
        assert staff.can_assign_requests is False
        assert staff.can_manage_finances is False
        assert staff.can_send_announcements is False

    def test_staff_helper_methods(self):
        """Test staff helper methods work correctly."""
        facility_manager = StaffFactory(staff_role="facility_manager")
        accountant = StaffFactory(staff_role="accountant")
        electrician = StaffFactory(staff_role="electrician")

        # Test is_facility_manager
        assert facility_manager.is_facility_manager() is True
        assert accountant.is_facility_manager() is False

        # Test is_accountant
        assert accountant.is_accountant() is True
        assert facility_manager.is_accountant() is False

        # Test can_handle_maintenance
        assert facility_manager.can_handle_maintenance() is True
        assert electrician.can_handle_maintenance() is True
        assert accountant.can_handle_maintenance() is False

    def test_staff_reporting_structure(self):
        """Test staff reporting relationships."""
        supervisor = StaffFactory(staff_role="maintenance_supervisor")
        subordinate = StaffFactory(
            staff_role="electrician",
            reporting_to=supervisor,
        )

        assert subordinate.reporting_to == supervisor
        assert supervisor.get_subordinate_count() == 1
        assert subordinate in supervisor.subordinates.all()

    def test_staff_string_representation(self):
        """Test staff string representation."""
        user = StaffUserFactory(name="John Doe")
        staff = StaffFactory(
            user=user,
            employee_id="EMP123",
            staff_role="facility_manager",
        )

        expected = "John Doe - Facility Manager (EMP123)"
        assert str(staff) == expected

    def test_staff_24x7_availability(self):
        """Test 24x7 availability for specific roles."""
        facility_manager = StaffFactory(staff_role="facility_manager")
        security_head = StaffFactory(staff_role="security_head")
        electrician = StaffFactory(staff_role="electrician")

        assert facility_manager.is_available_24x7 is True
        assert security_head.is_available_24x7 is True
        assert electrician.is_available_24x7 is False


@pytest.mark.django_db
class TestMaintenanceRequestStaffIntegration:
    """Test maintenance request integration with staff functionality."""

    def test_maintenance_request_staff_assignment(self):
        """Test assigning maintenance request to staff."""
        request = MaintenanceRequestFactory(status="submitted")
        staff = StaffFactory(staff_role="facility_manager")
        assigner = StaffFactory(staff_role="facility_manager")

        # Test assignment
        request.assign_to_staff(staff.user, assigner.user)

        assert request.assigned_to == staff.user
        assert request.assigned_by == assigner.user
        assert request.assigned_at is not None
        assert request.status == "assigned"

    def test_maintenance_request_can_be_assigned_to(self):
        """Test checking if request can be assigned to specific staff."""
        request = MaintenanceRequestFactory()
        facility_manager = StaffFactory(staff_role="facility_manager")
        electrician = StaffFactory(staff_role="electrician")
        accountant = StaffFactory(staff_role="accountant")

        # Facility manager can handle all requests
        assert request.can_be_assigned_to(facility_manager.user) is True

        # Electrician can handle maintenance requests
        assert request.can_be_assigned_to(electrician.user) is True

        # Accountant cannot handle maintenance requests
        assert request.can_be_assigned_to(accountant.user) is False

    def test_maintenance_request_get_suitable_staff(self):
        """Test getting suitable staff for a maintenance request."""
        request = MaintenanceRequestFactory()

        # Create various staff members
        facility_manager = StaffFactory(staff_role="facility_manager")
        electrician = StaffFactory(staff_role="electrician")
        accountant = StaffFactory(staff_role="accountant")
        inactive_staff = StaffFactory(staff_role="plumber", is_active=False)

        suitable_staff = request.get_suitable_staff()

        # Should include facility manager and electrician
        assert facility_manager in suitable_staff
        assert electrician in suitable_staff

        # Should not include accountant or inactive staff
        assert accountant not in suitable_staff
        assert inactive_staff not in suitable_staff

    def test_maintenance_request_enhanced_status_workflow(self):
        """Test enhanced maintenance request status workflow."""
        request = MaintenanceRequestFactory(status="submitted")

        # Test status progression with automatic timestamps
        request.status = "acknowledged"
        request.save()
        assert request.acknowledged_at is not None

        request.status = "assigned"
        request.save()
        assert request.assigned_at is not None

        request.status = "resolved"
        request.save()
        assert request.resolved_at is not None

        request.status = "closed"
        request.save()
        assert request.closed_at is not None

    def test_maintenance_request_cost_tracking(self):
        """Test maintenance request cost tracking functionality."""
        request = MaintenanceRequestFactory(
            estimated_cost=500.00,
            actual_cost=550.00,
            status="closed",
        )

        assert request.estimated_cost == 500.00
        assert request.actual_cost == 550.00

        # Cost overrun
        cost_difference = request.actual_cost - request.estimated_cost
        assert cost_difference == 50.00

    def test_maintenance_request_resident_feedback(self):
        """Test resident feedback and rating functionality."""
        request = MaintenanceRequestFactory(
            status="closed",
            resident_rating=5,
            resident_feedback="Excellent work, very professional!",
        )

        assert request.resident_rating == 5
        assert "Excellent work" in request.resident_feedback

    def test_maintenance_request_is_overdue(self):
        """Test overdue request detection."""
        # Create overdue request
        past_date = timezone.now() - timedelta(days=1)
        overdue_request = MaintenanceRequestFactory(
            estimated_completion=past_date,
            status="in_progress",
        )

        # Create on-time request
        future_date = timezone.now() + timedelta(days=1)
        on_time_request = MaintenanceRequestFactory(
            estimated_completion=future_date,
            status="in_progress",
        )

        # Create completed request (should not be overdue)
        completed_request = MaintenanceRequestFactory(
            estimated_completion=past_date,
            status="closed",
        )

        assert overdue_request.is_overdue() is True
        assert on_time_request.is_overdue() is False
        assert completed_request.is_overdue() is False

    def test_maintenance_request_resolution_time(self):
        """Test resolution time calculation."""
        created_time = timezone.now() - timedelta(days=2)
        resolved_time = timezone.now() - timedelta(hours=2)

        request = MaintenanceRequestFactory(
            created_at=created_time,
            resolved_at=resolved_time,
            status="resolved",
        )

        resolution_time = request.get_resolution_time()
        expected_time = resolved_time - created_time

        assert resolution_time == expected_time

    def test_maintenance_request_ordering(self):
        """Test maintenance request ordering by priority and creation date."""
        # Create requests with different priorities
        low_priority = MaintenanceRequestFactory(priority=1)
        high_priority = MaintenanceRequestFactory(priority=4)
        medium_priority = MaintenanceRequestFactory(priority=2)

        # Get ordered requests
        requests = MaintenanceRequest.objects.all()

        # Should be ordered by priority (high to low), then by creation date
        assert requests[0] == high_priority
        assert requests[2] == low_priority


@pytest.mark.django_db
class TestStaffWorkflowIntegration:
    """Test complete staff workflow integration."""

    def test_complete_maintenance_workflow(self):
        """Test complete maintenance workflow from submission to closure."""
        # Create users and staff
        resident = ResidentUserFactory()
        facility_manager = StaffFactory(staff_role="facility_manager")
        electrician = StaffFactory(staff_role="electrician")

        # 1. Resident submits request
        request = MaintenanceRequestFactory(
            resident=resident,
            status="submitted",
            title="Electrical outlet not working",
            category__name="Electrical",
        )

        # 2. Facility manager acknowledges and assigns
        request.status = "acknowledged"
        request.save()
        request.assign_to_staff(electrician.user, facility_manager.user)

        # 3. Electrician starts work
        request.status = "in_progress"
        request.save()

        # 4. Electrician completes work
        request.status = "resolved"
        request.actual_cost = 150.00
        request.save()

        # 5. Facility manager closes after resident confirmation
        request.status = "closed"
        request.resident_rating = 5
        request.resident_feedback = "Great work!"
        request.save()

        # Verify complete workflow
        assert request.acknowledged_at is not None
        assert request.assigned_to == electrician.user
        assert request.assigned_by == facility_manager.user
        assert request.assigned_at is not None
        assert request.resolved_at is not None
        assert request.closed_at is not None
        assert request.resident_rating == 5
        assert request.actual_cost == 150.00

    def test_staff_permission_based_access(self):
        """Test that staff can only access what their permissions allow."""
        facility_manager = StaffFactory(staff_role="facility_manager")
        electrician = StaffFactory(staff_role="electrician")
        accountant = StaffFactory(staff_role="accountant")

        # Create maintenance requests
        request1 = MaintenanceRequestFactory()
        request2 = MaintenanceRequestFactory()

        # Facility manager should be able to assign any request
        assert request1.can_be_assigned_to(facility_manager.user)
        assert request2.can_be_assigned_to(facility_manager.user)

        # Electrician can handle maintenance but not assign
        assert request1.can_be_assigned_to(electrician.user)
        assert not electrician.can_assign_requests

        # Accountant cannot handle maintenance requests
        assert not request1.can_be_assigned_to(accountant.user)
        assert accountant.can_manage_finances

    def test_staff_hierarchy_and_reporting(self):
        """Test staff hierarchy and reporting relationships."""
        # Create hierarchy
        facility_manager = StaffFactory(staff_role="facility_manager")
        maintenance_supervisor = StaffFactory(
            staff_role="maintenance_supervisor",
            reporting_to=facility_manager,
        )
        electrician = StaffFactory(
            staff_role="electrician",
            reporting_to=maintenance_supervisor,
        )
        plumber = StaffFactory(
            staff_role="plumber",
            reporting_to=maintenance_supervisor,
        )

        # Test hierarchy
        assert facility_manager.get_subordinate_count() == 1
        assert maintenance_supervisor.get_subordinate_count() == 2
        assert electrician.get_subordinate_count() == 0

        # Test reporting relationships
        assert electrician.reporting_to == maintenance_supervisor
        assert maintenance_supervisor.reporting_to == facility_manager
        assert facility_manager.reporting_to is None
