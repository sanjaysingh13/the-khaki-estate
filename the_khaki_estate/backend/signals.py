from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import models to avoid circular imports in signal functions
from .models import Announcement
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
            is_committee_member=True, user__is_active=True
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
