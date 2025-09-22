"""
Quick one-liner cleanup script for Django shell.

Usage in Django shell:
python manage.py shell

Then paste this entire block:
"""

# Quick cleanup - paste this entire block in Django shell
from the_khaki_estate.backend.models import *

print("🧹 Quick cleanup starting...")

# Delete in order (child objects first)
counts = []
try:
    counts.append(("Maintenance Updates", MaintenanceUpdate.objects.all().delete()[0]))
    counts.append(("Maintenance Requests", MaintenanceRequest.objects.all().delete()[0]))
    counts.append(("Comments", Comment.objects.all().delete()[0]))
    counts.append(("Announcement Reads", AnnouncementRead.objects.all().delete()[0]))
    counts.append(("Announcements", Announcement.objects.all().delete()[0]))
    counts.append(("Event RSVPs", EventRSVP.objects.all().delete()[0]))
    counts.append(("Events", Event.objects.all().delete()[0]))
    counts.append(("Bookings", Booking.objects.all().delete()[0]))
    counts.append(("Marketplace Items", MarketplaceItem.objects.all().delete()[0]))
    counts.append(("Related Notifications", Notification.objects.filter(notification_type__name__in=['new_maintenance_request', 'maintenance_update', 'urgent_maintenance_request', 'new_announcement', 'urgent_announcement', 'event_reminder', 'event_cancelled', 'booking_confirmed', 'booking_cancelled']).delete()[0]))
except Exception as e:
    print(f"Error: {e}")

print("✅ Cleanup completed!")
for name, count in counts:
    if count > 0:
        print(f"  • {name}: {count} deleted")

print("🎉 Demo data cleaned successfully!")
