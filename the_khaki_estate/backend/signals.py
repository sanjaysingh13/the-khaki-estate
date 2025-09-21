from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import models to avoid circular imports in signal functions
from .models import Announcement
from .models import Booking
from .models import MaintenanceRequest
from .models import Resident
from .models import Staff
from .notification_service import NotificationService


@receiver(post_save, sender=Announcement)
def announcement_created(sender, instance, created, **kwargs):
    """Auto-notify residents about new announcements"""
    if created:
        # Determine notification urgency
        notification_type = (
            "urgent_announcement" if instance.is_urgent else "new_announcement"
        )

        NotificationService.notify_all_residents(
            notification_type_name=notification_type,
            title=f"New Announcement: {instance.title}",
            message=f"{instance.content[:100]}..."
            if len(instance.content) > 100
            else instance.content,
            related_object=instance,
            data={
                "url": f"/announcements/{instance.id}/",
                "category": instance.category.name,
            },
        )


@receiver(post_save, sender=MaintenanceRequest)
def maintenance_request_updated(sender, instance, created, **kwargs):
    """Notify on maintenance request updates"""
    if created:
        # Notify management about new request - both committee members and staff
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get committee members (residents)
        committee_members = Resident.objects.filter(
            is_committee_member=True,
            user__is_active=True,
        )

        # Get staff members who can handle maintenance
        maintenance_staff = Staff.objects.filter(
            is_active=True,
            user__is_active=True,
        ).filter(
            models.Q(can_access_all_maintenance=True)
            | models.Q(staff_role__in=["facility_manager", "maintenance_supervisor"]),
        )

        # Notify staff members only (committee members will see in dashboard for awareness)
        for staff in maintenance_staff:
            NotificationService.create_notification(
                recipient=staff.user,
                notification_type_name="new_maintenance_request",
                title=f"New Maintenance Request: {instance.ticket_number}",
                message=f"From: {instance.resident.get_full_name()} - {instance.title}",
                related_object=instance,
                data={"url": f"/backend/maintenance/{instance.id}/"},
            )
    else:
        # Notify resident about status change
        NotificationService.create_notification(
            recipient=instance.resident,
            notification_type_name="maintenance_update",
            title=f"Maintenance Update: {instance.ticket_number}",
            message=f"Status changed to: {instance.get_status_display()}",
            related_object=instance,
            data={"url": f"/maintenance/{instance.id}/"},
        )


@receiver(post_save, sender=Booking)
def booking_workflow_handler(sender, instance, created, **kwargs):
    """
    Handle booking workflow notifications for the designated resident approval system.
    
    This signal handler manages the complete booking workflow:
    1. New booking creation → Notify designated approver
    2. Status changes → Notify relevant parties
    3. Approval/rejection → Notify booking resident
    
    The workflow mirrors the maintenance system but uses designated residents
    instead of facility managers for approvals.
    """
    if created:
        # NEW BOOKING: Set designated approver and notify them
        _handle_new_booking(instance)
    else:
        # STATUS CHANGE: Handle various status transitions
        _handle_booking_status_change(instance)


def _handle_new_booking(booking):
    """
    Handle new booking creation workflow.
    
    Actions:
    1. Set the designated approver based on common area
    2. Send notification to designated approver
    3. Create audit trail entry
    """
    # Set designated approver based on common area
    approver = booking.set_designated_approver()
    
    # Save the booking to persist the designated_approver field
    if approver:
        booking.save()
    
    if approver:
        # Notify designated approver about new booking request
        NotificationService.create_notification(
            recipient=approver,
            notification_type_name="booking_pending_approval",
            title=f"New Booking Request: {booking.booking_number}",
            message=f"Booking request for {booking.common_area.name} on {booking.booking_date} requires your approval",
            related_object=booking,
            data={
                "url": f"/backend/bookings/{booking.id}/",
                "booking_number": booking.booking_number,
                "area_name": booking.common_area.name,
                "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
                "purpose": booking.purpose,
                "resident_name": booking.resident.get_full_name(),
            },
        )
    else:
        # Log warning if no designated approver found
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"No designated approver found for booking {booking.booking_number} in area {booking.common_area.name}")


def _handle_booking_status_change(booking):
    """
    Handle booking status changes and send appropriate notifications.
    
    Status transitions:
    - pending → approved: Notify resident of approval
    - pending → rejected: Notify resident of rejection
    - approved → confirmed: Notify resident of confirmation
    - any → cancelled: Notify designated approver if resident cancelled
    """
    # Get the previous status from the database to detect changes
    try:
        old_booking = Booking.objects.get(pk=booking.pk)
        # We need to track status changes manually since we don't have pre_save
        # For now, we'll handle this in the view when status is explicitly changed
        return
    except Booking.DoesNotExist:
        return
    
    # Handle specific status changes
    if booking.status == "approved":
        _notify_booking_approved(booking)
    elif booking.status == "rejected":
        _notify_booking_rejected(booking)
    elif booking.status == "confirmed":
        _notify_booking_confirmed(booking)
    elif booking.status == "cancelled":
        _notify_booking_cancelled(booking)


def _notify_booking_approved(booking):
    """Notify resident that their booking has been approved."""
    NotificationService.create_notification(
        recipient=booking.resident,
        notification_type_name="booking_approved",
        title=f"Booking Approved: {booking.booking_number}",
        message=f"Your booking for {booking.common_area.name} on {booking.booking_date} has been approved",
        related_object=booking,
        data={
            "url": f"/backend/bookings/{booking.id}/",
            "booking_number": booking.booking_number,
            "area_name": booking.common_area.name,
            "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
        },
    )


def _notify_booking_rejected(booking):
    """Notify resident that their booking has been rejected."""
    NotificationService.create_notification(
        recipient=booking.resident,
        notification_type_name="booking_rejected",
        title=f"Booking Rejected: {booking.booking_number}",
        message=f"Your booking for {booking.common_area.name} on {booking.booking_date} has been rejected",
        related_object=booking,
        data={
            "url": f"/backend/bookings/{booking.id}/",
            "booking_number": booking.booking_number,
            "area_name": booking.common_area.name,
            "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
            "rejection_reason": booking.rejection_reason,
        },
    )


def _notify_booking_confirmed(booking):
    """Notify resident that their booking has been confirmed."""
    NotificationService.create_notification(
        recipient=booking.resident,
        notification_type_name="booking_confirmed",
        title=f"Booking Confirmed: {booking.booking_number}",
        message=f"Your booking for {booking.common_area.name} on {booking.booking_date} has been confirmed",
        related_object=booking,
        data={
            "url": f"/backend/bookings/{booking.id}/",
            "booking_number": booking.booking_number,
            "area_name": booking.common_area.name,
            "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
        },
    )


def _notify_booking_cancelled(booking):
    """Notify designated approver when resident cancels their booking."""
    if booking.designated_approver:
        NotificationService.create_notification(
            recipient=booking.designated_approver,
            notification_type_name="booking_cancelled_by_resident",
            title=f"Booking Cancelled: {booking.booking_number}",
            message=f"Booking for {booking.common_area.name} on {booking.booking_date} has been cancelled by {booking.resident.get_full_name()}",
            related_object=booking,
            data={
                "url": f"/backend/bookings/{booking.id}/",
                "booking_number": booking.booking_number,
                "area_name": booking.common_area.name,
                "booking_date": booking.booking_date.strftime("%Y-%m-%d"),
                "resident_name": booking.resident.get_full_name(),
            },
        )
