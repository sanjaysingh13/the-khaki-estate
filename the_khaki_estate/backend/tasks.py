from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification


@shared_task
def send_notification_task(notification_id, delivery_method):
    """Async task to send email/SMS notifications"""
    try:
        notification = Notification.objects.get(id=notification_id)
        recipient = notification.recipient

        success = True

        # Get user's phone number from profile
        phone_number = None
        try:
            if hasattr(recipient, 'resident'):
                phone_number = recipient.resident.phone_number
            elif hasattr(recipient, 'staff'):
                phone_number = recipient.staff.phone_number
        except:
            pass

        # Send Email
        if "email" in delivery_method and recipient.email:
            try:
                context = {
                    "recipient": recipient,
                    "notification": notification,
                    "related_object": notification.get_related_object(),
                    "data": notification.data,
                }

                # For now, send simple text email since we don't have templates
                send_mail(
                    subject=notification.title,
                    message=notification.message,
                    from_email="noreply@thekhakie state.com",
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

                notification.email_sent = True
                print(f"📧 Email sent to {recipient.email}: {notification.title}")

            except Exception as e:
                success = False
                print(f"❌ Email send failed: {e}")

        # Send SMS
        if "sms" in delivery_method and phone_number:
            try:
                # Use your SMS service (Twilio, etc.)
                sms_message = (
                    notification.notification_type.sms_template.format(
                        recipient=recipient,
                        title=notification.title,
                        message=notification.message,
                    )
                    if notification.notification_type.sms_template
                    else notification.message
                )

                # SMS sending code here
                # send_sms(phone_number, sms_message)
                print(f"📱 SMS would be sent to {phone_number}: {sms_message}")

                notification.sms_sent = True

            except Exception as e:
                success = False
                print(f"SMS send failed: {e}")

        # Update notification status
        if success:
            notification.status = "delivered"
            notification.sent_at = timezone.now()
        else:
            notification.status = "failed"

        notification.save()

    except Notification.DoesNotExist:
        print(f"Notification {notification_id} not found")
