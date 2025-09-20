"""
Django management command to populate NotificationType table with notification types.
This command creates notification types that are used by the notification system.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from the_khaki_estate.backend.models import NotificationType


class Command(BaseCommand):
    """
    Management command to populate the NotificationType table.

    Usage: python manage.py populate_notification_types
    """

    help = "Populate NotificationType table with notification types"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing notification types before adding new ones",
        )

    def handle(self, *args, **options):
        """
        Main command handler that creates notification types.
        """

        # Define notification types
        notification_types_data = [
            # Maintenance-related notifications
            {
                "name": "new_maintenance_request",
                "template_name": "emails/maintenance_request_created.html",
                "sms_template": "New maintenance request #{ticket_number} has been submitted by {resident_name}.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "maintenance_update",
                "template_name": "emails/maintenance_request_updated.html",
                "sms_template": "Your maintenance request #{ticket_number} status has been updated to {status}.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "urgent_maintenance_request",
                "template_name": "emails/urgent_maintenance_request.html",
                "sms_template": "URGENT: Maintenance request #{ticket_number} requires immediate attention.",
                "default_delivery": "both",
                "is_urgent": True,
            },
            {
                "name": "maintenance_status_change",
                "template_name": "emails/maintenance_status_change.html",
                "sms_template": "Your maintenance request #{ticket_number} status has been updated to {status}.",
                "default_delivery": "both",
                "is_urgent": False,
            },
            {
                "name": "maintenance_resident_update",
                "template_name": "emails/maintenance_resident_update.html",
                "sms_template": "Resident has added an update to maintenance request #{ticket_number}.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            # Announcement-related notifications
            {
                "name": "new_announcement",
                "template_name": "emails/announcement_created.html",
                "sms_template": "New announcement: {title}",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "urgent_announcement",
                "template_name": "emails/urgent_announcement.html",
                "sms_template": "URGENT ANNOUNCEMENT: {title}",
                "default_delivery": "both",
                "is_urgent": True,
            },
            # Event-related notifications
            {
                "name": "event_reminder",
                "template_name": "emails/event_reminder.html",
                "sms_template": "Reminder: {event_title} is scheduled for {event_date}.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "event_cancelled",
                "template_name": "emails/event_cancelled.html",
                "sms_template": "Event cancelled: {event_title} scheduled for {event_date}.",
                "default_delivery": "both",
                "is_urgent": True,
            },
            # Booking-related notifications
            {
                "name": "booking_confirmed",
                "template_name": "emails/booking_confirmed.html",
                "sms_template": "Your booking for {area_name} on {booking_date} has been confirmed.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "booking_cancelled",
                "template_name": "emails/booking_cancelled.html",
                "sms_template": "Your booking for {area_name} on {booking_date} has been cancelled.",
                "default_delivery": "email",
                "is_urgent": False,
            },
            # General system notifications
            {
                "name": "welcome_message",
                "template_name": "emails/welcome_message.html",
                "sms_template": "Welcome to The Khaki Estate community platform!",
                "default_delivery": "email",
                "is_urgent": False,
            },
            {
                "name": "account_activated",
                "template_name": "emails/account_activated.html",
                "sms_template": "Your account has been activated. Welcome to The Khaki Estate!",
                "default_delivery": "email",
                "is_urgent": False,
            },
        ]

        try:
            with transaction.atomic():
                if options["clear"]:
                    # Clear existing notification types
                    deleted_count = NotificationType.objects.count()
                    NotificationType.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Cleared {deleted_count} existing notification types"
                        ),
                    )

                # Create notification types
                created_count = 0
                updated_count = 0

                for notif_data in notification_types_data:
                    notif_type, created = NotificationType.objects.get_or_create(
                        name=notif_data["name"],
                        defaults={
                            "template_name": notif_data["template_name"],
                            "sms_template": notif_data["sms_template"],
                            "default_delivery": notif_data["default_delivery"],
                            "is_urgent": notif_data["is_urgent"],
                        },
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            f"✅ Created: {notif_type.name} "
                            f"(Delivery: {notif_type.default_delivery}, "
                            f"Urgent: {notif_type.is_urgent})",
                        )
                    else:
                        self.stdout.write(f"⚪ Exists: {notif_type.name}")

                # Summary
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ COMPLETED: {created_count} created, {updated_count} updated",
                    ),
                )
                self.stdout.write(
                    f"Total notification types in database: {NotificationType.objects.count()}",
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error creating notification types: {e}"),
            )
            raise e

        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 Notification types have been successfully populated!",
            ),
        )
        self.stdout.write(
            "The notification system can now send emails and SMS messages.",
        )
