"""
Integration tests for complete maintenance workflow including notifications.
Tests the entire flow from request submission to closure with staff assignments.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import MaintenanceUpdate
from the_khaki_estate.backend.tests.factories import MaintenanceCategoryFactory
from the_khaki_estate.backend.tests.factories import MaintenanceRequestFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory
from the_khaki_estate.backend.tests.factories import StaffFactory
from the_khaki_estate.users.tests.factories import ResidentUserFactory


@pytest.mark.django_db
class TestMaintenanceWorkflowIntegration:
    """Test complete maintenance workflow integration."""

    def setup_method(self):
        """Set up test data for each test."""
        # Create users
        self.resident_user = ResidentUserFactory()
        self.resident = ResidentFactory(user=self.resident_user)

        # Create staff
        self.facility_manager = StaffFactory(staff_role="facility_manager")
        self.electrician = StaffFactory(staff_role="electrician")
        self.plumber = StaffFactory(staff_role="plumber")
        self.accountant = StaffFactory(staff_role="accountant")

        # Create maintenance category
        self.electrical_category = MaintenanceCategoryFactory(
            name="Electrical",
            priority_level=3,
            estimated_resolution_hours=24,
        )

    def test_complete_maintenance_workflow_electrical(self):
        """Test complete electrical maintenance workflow."""
        # 1. Resident submits electrical request
        request = MaintenanceRequestFactory(
            resident=self.resident_user,
            title="Kitchen outlet not working",
            description="The main kitchen outlet stopped working after power outage",
            category=self.electrical_category,
            location=f"Flat {self.resident.flat_number}",
            priority=3,
            status="submitted",
        )

        assert request.status == "submitted"
        assert request.assigned_to is None

        # 2. Facility manager acknowledges request
        request.status = "acknowledged"
        request.save()

        assert request.acknowledged_at is not None

        # 3. Facility manager assigns to electrician
        request.assign_to_staff(
            self.electrician.user,
            self.facility_manager.user,
        )

        assert request.status == "assigned"
        assert request.assigned_to == self.electrician.user
        assert request.assigned_by == self.facility_manager.user
        assert request.assigned_at is not None

        # 4. Electrician starts work
        request.status = "in_progress"
        request.estimated_completion = timezone.now() + timedelta(hours=4)
        request.estimated_cost = Decimal("200.00")
        request.save()

        # 5. Electrician completes work
        request.status = "resolved"
        request.actual_completion = timezone.now()
        request.actual_cost = Decimal("180.00")
        request.save()

        assert request.resolved_at is not None

        # 6. Resident provides feedback and facility manager closes
        request.resident_rating = 5
        request.resident_feedback = "Excellent work! Very professional and clean."
        request.status = "closed"
        request.save()

        assert request.closed_at is not None
        assert request.resident_rating == 5

        # Verify complete workflow
        resolution_time = request.get_resolution_time()
        assert resolution_time is not None
        assert request.actual_cost < request.estimated_cost  # Under budget

    def test_emergency_maintenance_workflow(self):
        """Test emergency maintenance request handling."""
        # Create emergency request
        request = MaintenanceRequestFactory(
            resident=self.resident_user,
            title="Water pipe burst in bathroom",
            description="Major water leak flooding the bathroom floor",
            priority=4,  # Emergency
            status="submitted",
        )

        # Emergency requests should be fast-tracked
        assert request.priority == 4

        # Facility manager immediately assigns to plumber
        request.assign_to_staff(self.plumber.user, self.facility_manager.user)

        # Plumber responds immediately
        request.status = "in_progress"
        request.estimated_completion = timezone.now() + timedelta(hours=2)
        request.save()

        # Quick resolution
        request.status = "resolved"
        request.actual_cost = Decimal("500.00")
        request.save()

        # Verify emergency handling
        total_time = request.get_resolution_time()
        assert total_time.total_seconds() < 7200  # Less than 2 hours

    def test_staff_assignment_based_on_expertise(self):
        """Test that requests are assigned to appropriate staff based on expertise."""
        # Create different types of requests
        electrical_request = MaintenanceRequestFactory(
            category=MaintenanceCategoryFactory(name="Electrical"),
            status="submitted",
        )

        plumbing_request = MaintenanceRequestFactory(
            category=MaintenanceCategoryFactory(name="Plumbing"),
            status="submitted",
        )

        # Test suitable staff assignment
        electrical_suitable = electrical_request.get_suitable_staff()
        plumbing_suitable = plumbing_request.get_suitable_staff()

        # Facility manager should be suitable for all
        assert self.facility_manager in electrical_suitable
        assert self.facility_manager in plumbing_suitable

        # Specialists should be suitable for their domain
        assert self.electrician in electrical_suitable
        assert self.plumber in plumbing_suitable

        # Accountant should not be suitable for maintenance
        assert self.accountant not in electrical_suitable
        assert self.accountant not in plumbing_suitable

    def test_maintenance_request_cost_management(self):
        """Test maintenance request cost tracking and management."""
        request = MaintenanceRequestFactory(
            status="assigned",
            assigned_to=self.electrician.user,
            estimated_cost=Decimal("300.00"),
        )

        # Simulate work completion with different cost scenarios

        # Scenario 1: Under budget
        request.actual_cost = Decimal("250.00")
        savings = request.estimated_cost - request.actual_cost
        assert savings == Decimal("50.00")

        # Scenario 2: Over budget
        request.actual_cost = Decimal("350.00")
        overrun = request.actual_cost - request.estimated_cost
        assert overrun == Decimal("50.00")

        # Scenario 3: On budget
        request.actual_cost = Decimal("300.00")
        difference = request.actual_cost - request.estimated_cost
        assert difference == Decimal("0.00")

    def test_maintenance_request_overdue_detection(self):
        """Test overdue request detection and handling."""
        # Create request with past estimated completion
        past_completion = timezone.now() - timedelta(days=1)
        overdue_request = MaintenanceRequestFactory(
            estimated_completion=past_completion,
            status="in_progress",
        )

        # Create request with future completion
        future_completion = timezone.now() + timedelta(days=1)
        on_time_request = MaintenanceRequestFactory(
            estimated_completion=future_completion,
            status="in_progress",
        )

        # Test overdue detection
        assert overdue_request.is_overdue() is True
        assert on_time_request.is_overdue() is False

        # Completed requests should not be overdue
        overdue_request.status = "closed"
        overdue_request.save()
        assert overdue_request.is_overdue() is False

    def test_staff_workload_balancing(self):
        """Test staff workload distribution."""
        # Create multiple requests assigned to same staff
        requests = []
        for i in range(3):
            request = MaintenanceRequestFactory(
                assigned_to=self.electrician.user,
                status="in_progress",
            )
            requests.append(request)

        # Check electrician's current workload
        active_requests = MaintenanceRequest.objects.filter(
            assigned_to=self.electrician.user,
            status__in=["assigned", "in_progress"],
        ).count()

        assert active_requests == 3

        # Complete one request
        requests[0].status = "resolved"
        requests[0].save()

        # Workload should decrease
        active_requests = MaintenanceRequest.objects.filter(
            assigned_to=self.electrician.user,
            status__in=["assigned", "in_progress"],
        ).count()

        assert active_requests == 2

    def test_resident_satisfaction_tracking(self):
        """Test resident satisfaction rating and feedback system."""
        request = MaintenanceRequestFactory(
            status="closed",
            resident_rating=4,
            resident_feedback="Good work but took longer than expected",
        )

        # Test satisfaction metrics
        assert request.resident_rating == 4
        assert "longer than expected" in request.resident_feedback

        # Test different satisfaction levels
        excellent_request = MaintenanceRequestFactory(
            status="closed",
            resident_rating=5,
            resident_feedback="Outstanding service!",
        )

        poor_request = MaintenanceRequestFactory(
            status="closed",
            resident_rating=2,
            resident_feedback="Work quality was poor, had to call again",
        )

        # Calculate average satisfaction (would be used in reporting)
        ratings = [
            request.resident_rating,
            excellent_request.resident_rating,
            poor_request.resident_rating,
        ]
        average_rating = sum(ratings) / len(ratings)
        assert average_rating == 3.67  # (4+5+2)/3 = 3.67 (rounded)

    def test_maintenance_updates_and_communication(self):
        """Test maintenance updates and communication flow."""
        request = MaintenanceRequestFactory(
            assigned_to=self.electrician.user,
            status="in_progress",
        )

        # Electrician provides update
        update1 = MaintenanceUpdate.objects.create(
            request=request,
            author=self.electrician.user,
            content="Started work, found the issue is with the circuit breaker",
            status_changed_to="in_progress",
        )

        # Facility manager provides update
        update2 = MaintenanceUpdate.objects.create(
            request=request,
            author=self.facility_manager.user,
            content="Ordered replacement parts, will complete tomorrow",
            status_changed_to="in_progress",
        )

        # Electrician completes work
        update3 = MaintenanceUpdate.objects.create(
            request=request,
            author=self.electrician.user,
            content="Work completed, circuit breaker replaced and tested",
            status_changed_to="resolved",
        )

        # Verify updates
        updates = request.updates.all()
        assert updates.count() == 3
        assert (
            update1.content
            == "Started work, found the issue is with the circuit breaker"
        )
        assert update3.status_changed_to == "resolved"

    def test_staff_performance_metrics(self):
        """Test staff performance tracking through completed requests."""
        # Create completed requests for electrician
        completed_requests = []
        for i in range(5):
            request = MaintenanceRequestFactory(
                assigned_to=self.electrician.user,
                status="closed",
                resident_rating=4 + (i % 2),  # Ratings of 4 or 5
                created_at=timezone.now() - timedelta(days=10 - i),
                resolved_at=timezone.now() - timedelta(days=9 - i),
            )
            completed_requests.append(request)

        # Calculate performance metrics
        electrician_requests = MaintenanceRequest.objects.filter(
            assigned_to=self.electrician.user,
            status="closed",
        )

        # Average resolution time
        total_resolution_time = sum(
            (req.resolved_at - req.created_at).total_seconds()
            for req in electrician_requests
        )
        avg_resolution_hours = total_resolution_time / len(electrician_requests) / 3600

        # Average satisfaction rating
        avg_rating = sum(req.resident_rating for req in electrician_requests) / len(
            electrician_requests,
        )

        assert len(electrician_requests) == 5
        assert avg_resolution_hours == 24.0  # 1 day average
        assert avg_rating == 4.4  # Average of ratings

    def test_maintenance_category_priority_handling(self):
        """Test maintenance requests are handled according to category priority."""
        # Create categories with different priorities
        emergency_category = MaintenanceCategoryFactory(
            name="Emergency",
            priority_level=4,
            estimated_resolution_hours=2,
        )

        routine_category = MaintenanceCategoryFactory(
            name="Routine",
            priority_level=1,
            estimated_resolution_hours=168,  # 1 week
        )

        # Create requests
        emergency_request = MaintenanceRequestFactory(
            category=emergency_category,
            priority=4,
        )

        routine_request = MaintenanceRequestFactory(
            category=routine_category,
            priority=1,
        )

        # Verify priority ordering
        requests = MaintenanceRequest.objects.all().order_by("-priority")
        assert requests[0] == emergency_request
        assert requests[1] == routine_request
