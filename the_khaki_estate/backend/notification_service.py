class NotificationService:
    """Service class to handle all notification logic"""

    @staticmethod
    def create_notification(
        recipient,
        notification_type_name,
        title,
        message,
        related_object=None,
        data=None,
        force_delivery=None,
    ):
        """
        Create and optionally send notification

        Args:
            recipient: Resident object
            notification_type_name: String name of notification type
            title: Notification title
            message: Notification message
            related_object: Related model instance (optional)
            data: Additional data dict (optional)
            force_delivery: Override default delivery method (optional)
        """
        try:
            notification_type = NotificationType.objects.get(
                name=notification_type_name
            )
        except NotificationType.DoesNotExist:
            # Create default notification type
            notification_type = NotificationType.objects.create(
                name=notification_type_name,
                template_name="default_notification.html",
            )

        # Create notification record
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            related_object_type=related_object.__class__.__name__.lower()
            if related_object
            else "",
            related_object_id=related_object.id if related_object else None,
        )

        # Determine delivery method
        delivery_method = force_delivery or notification_type.default_delivery

        # Respect user preferences
        if not recipient.email_notifications and "email" in delivery_method:
            delivery_method = delivery_method.replace("email", "").replace(
                "both", "sms"
            )

        if not recipient.sms_notifications and "sms" in delivery_method:
            delivery_method = delivery_method.replace("sms", "").replace(
                "both", "email"
            )

        # Only urgent notifications if user chose urgent_only
        if recipient.urgent_only and not notification_type.is_urgent:
            delivery_method = "in_app"

        # Send notification asynchronously
        if delivery_method != "in_app":
            send_notification_task.delay(notification.id, delivery_method)

        return notification

    @staticmethod
    def notify_multiple_residents(
        residents,
        notification_type_name,
        title,
        message,
        related_object=None,
        data=None,
    ):
        """Send notification to multiple residents"""
        notifications = []
        for resident in residents:
            notification = NotificationService.create_notification(
                resident=resident,
                notification_type_name=notification_type_name,
                title=title,
                message=message,
                related_object=related_object,
                data=data,
            )
            notifications.append(notification)
        return notifications

    @staticmethod
    def notify_all_residents(
        notification_type_name,
        title,
        message,
        related_object=None,
        data=None,
        exclude_residents=None,
    ):
        """Send notification to all active residents"""
        residents = Resident.objects.filter(is_active=True)
        if exclude_residents:
            residents = residents.exclude(id__in=[r.id for r in exclude_residents])

        return NotificationService.notify_multiple_residents(
            residents,
            notification_type_name,
            title,
            message,
            related_object,
            data,
        )
