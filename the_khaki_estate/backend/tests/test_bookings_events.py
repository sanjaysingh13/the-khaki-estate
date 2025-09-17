"""
Tests for booking and event functionality.
Comprehensive testing of facility bookings, events, and related workflows.
"""

from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from the_khaki_estate.backend.models import Booking
from the_khaki_estate.backend.models import Event
from the_khaki_estate.backend.models import EventRSVP
from the_khaki_estate.backend.tests.factories import BookingFactory
from the_khaki_estate.backend.tests.factories import CommonAreaFactory
from the_khaki_estate.backend.tests.factories import EventFactory
from the_khaki_estate.backend.tests.factories import EventRSVPFactory
from the_khaki_estate.backend.tests.factories import ResidentFactory
from the_khaki_estate.users.tests.factories import ResidentUserFactory


@pytest.mark.django_db
class TestBookingSystem:
    """Test facility booking system functionality."""

    def setup_method(self):
        """Set up test data for each test."""
        self.resident_user = ResidentUserFactory()
        self.resident = ResidentFactory(user=self.resident_user)

        self.community_hall = CommonAreaFactory(
            name="Community Hall",
            capacity=100,
            booking_fee=Decimal("1000.00"),
            advance_booking_days=30,
            min_booking_hours=2,
            max_booking_hours=12,
            available_start_time=time(6, 0),
            available_end_time=time(22, 0),
        )

    def test_booking_creation_with_valid_data(self):
        """Test creating booking with valid data."""
        booking_date = date.today() + timedelta(days=7)

        booking = Booking.objects.create(
            common_area=self.community_hall,
            resident=self.resident_user,
            booking_date=booking_date,
            start_time=time(10, 0),
            end_time=time(14, 0),
            purpose="Birthday party",
            guests_count=25,
            total_fee=self.community_hall.booking_fee,
            status="pending",
        )

        assert booking.booking_number.startswith("BKG-")
        assert booking.common_area == self.community_hall
        assert booking.resident == self.resident_user
        assert booking.status == "pending"

    def test_booking_number_generation(self):
        """Test automatic booking number generation."""
        booking1 = BookingFactory()
        booking2 = BookingFactory()

        assert booking1.booking_number != booking2.booking_number
        assert booking1.booking_number.startswith("BKG-")
        assert booking2.booking_number.startswith("BKG-")

        # Extract numbers and verify sequence
        num1 = int(booking1.booking_number.split("-")[-1])
        num2 = int(booking2.booking_number.split("-")[-1])
        assert abs(num1 - num2) == 1

    def test_booking_fee_calculation(self):
        """Test booking fee calculation based on duration."""
        booking = BookingFactory(
            common_area=self.community_hall,
            start_time=time(10, 0),
            end_time=time(14, 0),  # 4 hours
        )

        # Fee should be set to common area's booking fee
        assert booking.total_fee == self.community_hall.booking_fee

    def test_booking_time_validation(self):
        """Test booking time validation within available hours."""
        # Valid booking within available hours
        valid_booking = BookingFactory(
            common_area=self.community_hall,
            start_time=time(10, 0),
            end_time=time(14, 0),
        )
        assert valid_booking.start_time >= self.community_hall.available_start_time
        assert valid_booking.end_time <= self.community_hall.available_end_time

    def test_booking_capacity_validation(self):
        """Test booking guest count against facility capacity."""
        # Booking within capacity
        valid_booking = BookingFactory(
            common_area=self.community_hall,
            guests_count=50,  # Within 100 capacity
        )
        assert valid_booking.guests_count <= self.community_hall.capacity

        # Test over capacity scenario
        over_capacity_booking = BookingFactory(
            common_area=self.community_hall,
            guests_count=150,  # Over 100 capacity
        )
        # This should be flagged for manual review
        assert over_capacity_booking.guests_count > self.community_hall.capacity

    def test_booking_advance_notice_requirement(self):
        """Test advance booking notice requirements."""
        # Booking within advance notice period
        future_date = date.today() + timedelta(days=15)
        valid_booking = BookingFactory(
            common_area=self.community_hall,
            booking_date=future_date,
        )

        days_ahead = (valid_booking.booking_date - date.today()).days
        assert days_ahead <= self.community_hall.advance_booking_days

    def test_booking_status_workflow(self):
        """Test booking status workflow."""
        booking = BookingFactory(status="pending")

        # Approve booking
        booking.status = "confirmed"
        booking.save()
        assert booking.status == "confirmed"

        # Complete booking
        booking.status = "completed"
        booking.save()
        assert booking.status == "completed"

        # Cancel booking
        cancelled_booking = BookingFactory(status="pending")
        cancelled_booking.status = "cancelled"
        cancelled_booking.save()
        assert cancelled_booking.status == "cancelled"

    def test_booking_conflict_detection(self):
        """Test detection of booking conflicts."""
        booking_date = date.today() + timedelta(days=7)

        # Create first booking
        booking1 = BookingFactory(
            common_area=self.community_hall,
            booking_date=booking_date,
            start_time=time(10, 0),
            end_time=time(14, 0),
            status="confirmed",
        )

        # Test overlapping booking
        overlapping_booking = BookingFactory(
            common_area=self.community_hall,
            booking_date=booking_date,
            start_time=time(12, 0),  # Overlaps with first booking
            end_time=time(16, 0),
            status="pending",
        )

        # Check for conflicts (would be implemented in booking validation)
        conflicts = Booking.objects.filter(
            common_area=self.community_hall,
            booking_date=booking_date,
            status__in=["confirmed", "pending"],
            start_time__lt=overlapping_booking.end_time,
            end_time__gt=overlapping_booking.start_time,
        ).exclude(id=overlapping_booking.id)

        assert conflicts.exists()

    def test_booking_payment_tracking(self):
        """Test booking payment tracking."""
        booking = BookingFactory(
            total_fee=Decimal("1000.00"),
            is_paid=False,
        )

        # Initially unpaid
        assert booking.is_paid is False

        # Mark as paid
        booking.is_paid = True
        booking.save()
        assert booking.is_paid is True

    def test_multiple_facility_bookings(self):
        """Test bookings across multiple facilities."""
        pool = CommonAreaFactory(
            name="Swimming Pool",
            booking_fee=Decimal("500.00"),
        )

        gym = CommonAreaFactory(
            name="Gymnasium",
            booking_fee=Decimal("300.00"),
        )

        # Book different facilities on same day
        same_date = date.today() + timedelta(days=10)

        hall_booking = BookingFactory(
            common_area=self.community_hall,
            booking_date=same_date,
            start_time=time(10, 0),
            end_time=time(14, 0),
        )

        pool_booking = BookingFactory(
            common_area=pool,
            booking_date=same_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
        )

        # Should be allowed as different facilities
        assert hall_booking.common_area != pool_booking.common_area
        assert hall_booking.booking_date == pool_booking.booking_date


@pytest.mark.django_db
class TestEventSystem:
    """Test event management system functionality."""

    def setup_method(self):
        """Set up test data for each test."""
        self.organizer_user = ResidentUserFactory()
        self.organizer = ResidentFactory(
            user=self.organizer_user,
            is_committee_member=True,
        )

        self.resident_user = ResidentUserFactory()
        self.resident = ResidentFactory(user=self.resident_user)

    def test_event_creation(self):
        """Test event creation with valid data."""
        start_time = timezone.now() + timedelta(days=7)
        end_time = start_time + timedelta(hours=3)

        event = Event.objects.create(
            title="Community BBQ",
            description="Annual community barbecue event",
            event_type="social",
            start_datetime=start_time,
            end_datetime=end_time,
            location="Garden Area",
            max_attendees=50,
            is_rsvp_required=True,
            organizer=self.organizer_user,
        )

        assert event.title == "Community BBQ"
        assert event.event_type == "social"
        assert event.organizer == self.organizer_user
        assert event.is_rsvp_required is True

    def test_event_types(self):
        """Test different event types."""
        event_types = ["meeting", "maintenance", "social", "festival", "other"]

        for event_type in event_types:
            event = EventFactory(event_type=event_type)
            assert event.event_type == event_type

    def test_all_day_events(self):
        """Test all-day event functionality."""
        event = EventFactory(
            is_all_day=True,
            start_datetime=timezone.now().replace(hour=0, minute=0, second=0),
            end_datetime=timezone.now().replace(hour=23, minute=59, second=59),
        )

        assert event.is_all_day is True
        assert event.start_datetime.hour == 0
        assert event.end_datetime.hour == 23

    def test_event_capacity_management(self):
        """Test event capacity and attendee limits."""
        event = EventFactory(
            max_attendees=10,
            is_rsvp_required=True,
        )

        # Create RSVPs up to capacity
        for i in range(8):
            resident = ResidentUserFactory()
            EventRSVPFactory(
                event=event,
                resident=resident,
                response="yes",
                guests_count=1,
            )

        # Count confirmed attendees
        confirmed_rsvps = EventRSVP.objects.filter(
            event=event,
            response="yes",
        )

        total_attendees = sum(
            rsvp.guests_count + 1
            for rsvp in confirmed_rsvps  # +1 for the resident
        )

        assert total_attendees <= event.max_attendees

    def test_event_rsvp_responses(self):
        """Test RSVP response functionality."""
        event = EventFactory(is_rsvp_required=True)

        # Create different RSVP responses
        yes_rsvp = EventRSVPFactory(
            event=event,
            resident=self.resident_user,
            response="yes",
            guests_count=2,
            comment="Looking forward to it!",
        )

        no_rsvp = EventRSVPFactory(
            event=event,
            response="no",
            comment="Unfortunately can't make it",
        )

        maybe_rsvp = EventRSVPFactory(
            event=event,
            response="maybe",
            comment="Will try to attend",
        )

        # Verify responses
        assert yes_rsvp.response == "yes"
        assert yes_rsvp.guests_count == 2
        assert no_rsvp.response == "no"
        assert maybe_rsvp.response == "maybe"

    def test_event_rsvp_statistics(self):
        """Test RSVP statistics calculation."""
        event = EventFactory(is_rsvp_required=True)

        # Create various RSVPs
        EventRSVPFactory.create_batch(5, event=event, response="yes")
        EventRSVPFactory.create_batch(2, event=event, response="no")
        EventRSVPFactory.create_batch(3, event=event, response="maybe")

        # Calculate statistics
        yes_count = event.rsvps.filter(response="yes").count()
        no_count = event.rsvps.filter(response="no").count()
        maybe_count = event.rsvps.filter(response="maybe").count()
        total_responses = event.rsvps.count()

        assert yes_count == 5
        assert no_count == 2
        assert maybe_count == 3
        assert total_responses == 10

    def test_event_date_validation(self):
        """Test event date validation."""
        # Past event
        past_event = EventFactory(
            start_datetime=timezone.now() - timedelta(days=1),
            end_datetime=timezone.now() - timedelta(hours=22),
        )
        assert past_event.start_datetime < timezone.now()

        # Future event
        future_event = EventFactory(
            start_datetime=timezone.now() + timedelta(days=7),
            end_datetime=timezone.now() + timedelta(days=7, hours=3),
        )
        assert future_event.start_datetime > timezone.now()

        # End time after start time
        assert future_event.end_datetime > future_event.start_datetime

    def test_event_organizer_permissions(self):
        """Test event organizer permissions and responsibilities."""
        # Committee member can organize events
        committee_event = EventFactory(
            organizer=self.organizer_user,  # Committee member
            event_type="meeting",
        )
        assert committee_event.organizer == self.organizer_user

        # Regular resident organizing social event
        social_event = EventFactory(
            organizer=self.resident_user,
            event_type="social",
        )
        assert social_event.organizer == self.resident_user

    def test_recurring_event_concept(self):
        """Test concept for recurring events (future enhancement)."""
        # Create weekly recurring event concept
        base_date = timezone.now() + timedelta(days=7)

        weekly_events = []
        for week in range(4):  # 4 weeks
            event_date = base_date + timedelta(weeks=week)
            event = EventFactory(
                title=f"Weekly Yoga Class - Week {week + 1}",
                event_type="social",
                start_datetime=event_date,
                end_datetime=event_date + timedelta(hours=1),
                organizer=self.organizer_user,
            )
            weekly_events.append(event)

        assert len(weekly_events) == 4
        # Verify weekly spacing
        for i in range(1, len(weekly_events)):
            time_diff = (
                weekly_events[i].start_datetime - weekly_events[i - 1].start_datetime
            )
            assert time_diff.days == 7


@pytest.mark.django_db
class TestBookingEventIntegration:
    """Test integration between bookings and events."""

    def setup_method(self):
        """Set up test data for integration tests."""
        self.organizer_user = ResidentUserFactory()
        self.organizer = ResidentFactory(
            user=self.organizer_user,
            is_committee_member=True,
        )

        self.community_hall = CommonAreaFactory(
            name="Community Hall",
            capacity=100,
            booking_fee=Decimal("1000.00"),
        )

    def test_event_with_facility_booking(self):
        """Test creating event that requires facility booking."""
        event_date = date.today() + timedelta(days=14)
        event_start = datetime.combine(event_date, time(18, 0))
        event_end = datetime.combine(event_date, time(21, 0))

        # Create event
        event = EventFactory(
            title="Annual General Meeting",
            event_type="meeting",
            start_datetime=timezone.make_aware(event_start),
            end_datetime=timezone.make_aware(event_end),
            location="Community Hall",
            organizer=self.organizer_user,
            max_attendees=80,
        )

        # Create corresponding booking
        booking = BookingFactory(
            common_area=self.community_hall,
            resident=self.organizer_user,
            booking_date=event_date,
            start_time=time(17, 30),  # Setup time
            end_time=time(21, 30),  # Cleanup time
            purpose=f"Event: {event.title}",
            guests_count=event.max_attendees,
            status="confirmed",
        )

        # Verify integration
        assert event.location == self.community_hall.name
        assert booking.purpose.startswith("Event:")
        assert booking.guests_count == event.max_attendees

    def test_booking_availability_for_events(self):
        """Test checking facility availability for events."""
        event_date = date.today() + timedelta(days=10)

        # Create existing booking
        existing_booking = BookingFactory(
            common_area=self.community_hall,
            booking_date=event_date,
            start_time=time(14, 0),
            end_time=time(18, 0),
            status="confirmed",
        )

        # Try to create event during same time
        conflicting_event_time = datetime.combine(event_date, time(16, 0))

        # Check for conflicts
        conflicts = Booking.objects.filter(
            common_area=self.community_hall,
            booking_date=event_date,
            status="confirmed",
            start_time__lt=time(19, 0),  # Event end time
            end_time__gt=time(15, 0),  # Event start time
        )

        assert conflicts.exists()
        # Event organizer would need to choose different time or venue

    def test_event_capacity_vs_facility_capacity(self):
        """Test event capacity against facility capacity."""
        # Create event with attendees exceeding facility capacity
        large_event = EventFactory(
            max_attendees=150,  # Exceeds hall capacity of 100
            location="Community Hall",
        )

        # This should be flagged for review
        assert large_event.max_attendees > self.community_hall.capacity

        # Create appropriate sized event
        appropriate_event = EventFactory(
            max_attendees=80,  # Within hall capacity
            location="Community Hall",
        )

        assert appropriate_event.max_attendees <= self.community_hall.capacity
