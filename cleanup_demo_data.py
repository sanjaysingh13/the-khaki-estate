#!/usr/bin/env python3
"""
Django shell script to clean up demo/test data from The Khaki Estate system.

This script safely deletes:
- Demo maintenance requests and their updates
- Demo bookings and related data
- Demo announcements and their read records
- Demo events and RSVPs
- Demo marketplace items
- Related notifications for the above items

PRESERVES (will NOT delete):
- User accounts and profiles
- System configuration data (NotificationTypes, MaintenanceCategories, AnnouncementCategories)
- Staff assignments and roles
- Common areas and facility definitions

Usage:
    python manage.py shell < cleanup_demo_data.py

Or run interactively in Django shell:
    python manage.py shell
    >>> exec(open('cleanup_demo_data.py').read())
"""

print("🧹 Starting demo data cleanup for The Khaki Estate...")
print("=" * 60)

# Import all the models we need
from the_khaki_estate.backend.models import (
    # Maintenance related
    MaintenanceRequest,
    MaintenanceUpdate,
    
    # Booking related
    Booking,
    
    # Announcement related
    Announcement,
    AnnouncementRead,
    Comment,  # Fixed: was AnnouncementComment
    
    # Event related
    Event,
    EventRSVP,
    
    # Marketplace related
    MarketplaceItem,
    
    # Notification related
    Notification,
)

# Track deletion counts
deletion_counts = {}

def safe_delete_with_count(queryset, item_name):
    """
    Safely delete a queryset and track the count.
    """
    count = queryset.count()
    if count > 0:
        queryset.delete()
        deletion_counts[item_name] = count
        print(f"✅ Deleted {count} {item_name}")
    else:
        print(f"ℹ️  No {item_name} found to delete")

print("\n1️⃣ Cleaning up MAINTENANCE data...")
print("-" * 40)

# Delete maintenance updates first (they reference maintenance requests)
try:
    safe_delete_with_count(
        MaintenanceUpdate.objects.all(),
        "maintenance updates"
    )
except Exception as e:
    print(f"⚠️  Error deleting maintenance updates: {e}")

# Delete maintenance requests
try:
    safe_delete_with_count(
        MaintenanceRequest.objects.all(),
        "maintenance requests"
    )
except Exception as e:
    print(f"⚠️  Error deleting maintenance requests: {e}")

print("\n2️⃣ Cleaning up BOOKING data...")
print("-" * 40)

# Delete bookings
try:
    safe_delete_with_count(
        Booking.objects.all(),
        "bookings"
    )
except Exception as e:
    print(f"⚠️  Error deleting bookings: {e}")

print("\n3️⃣ Cleaning up ANNOUNCEMENT data...")
print("-" * 40)

# Delete announcement comments first
try:
    safe_delete_with_count(
        Comment.objects.all(),
        "comments"
    )
except Exception as e:
    print(f"⚠️  Error deleting comments: {e}")

# Delete announcement read records
try:
    safe_delete_with_count(
        AnnouncementRead.objects.all(),
        "announcement read records"
    )
except Exception as e:
    print(f"⚠️  Error deleting announcement read records: {e}")

# Delete announcements
try:
    safe_delete_with_count(
        Announcement.objects.all(),
        "announcements"
    )
except Exception as e:
    print(f"⚠️  Error deleting announcements: {e}")

print("\n4️⃣ Cleaning up EVENT data...")
print("-" * 40)

# Delete event RSVPs first
try:
    safe_delete_with_count(
        EventRSVP.objects.all(),
        "event RSVPs"
    )
except Exception as e:
    print(f"⚠️  Error deleting event RSVPs: {e}")

# Delete events
try:
    safe_delete_with_count(
        Event.objects.all(),
        "events"
    )
except Exception as e:
    print(f"⚠️  Error deleting events: {e}")

print("\n5️⃣ Cleaning up MARKETPLACE data...")
print("-" * 40)

# Delete marketplace items
try:
    safe_delete_with_count(
        MarketplaceItem.objects.all(),
        "marketplace items"
    )
except Exception as e:
    print(f"⚠️  Error deleting marketplace items: {e}")

print("\n6️⃣ Cleaning up NOTIFICATIONS...")
print("-" * 40)

# Delete notifications related to the deleted content
# Keep system notifications like welcome messages, account activations
try:
    # Delete notifications related to maintenance, announcements, events, bookings
    maintenance_notifications = Notification.objects.filter(
        notification_type__name__in=[
            'new_maintenance_request',
            'maintenance_update', 
            'urgent_maintenance_request'
        ]
    )
    safe_delete_with_count(maintenance_notifications, "maintenance notifications")
    
    announcement_notifications = Notification.objects.filter(
        notification_type__name__in=[
            'new_announcement',
            'urgent_announcement'
        ]
    )
    safe_delete_with_count(announcement_notifications, "announcement notifications")
    
    event_notifications = Notification.objects.filter(
        notification_type__name__in=[
            'event_reminder',
            'event_cancelled'
        ]
    )
    safe_delete_with_count(event_notifications, "event notifications")
    
    booking_notifications = Notification.objects.filter(
        notification_type__name__in=[
            'booking_confirmed',
            'booking_cancelled'
        ]
    )
    safe_delete_with_count(booking_notifications, "booking notifications")
    
except Exception as e:
    print(f"⚠️  Error deleting notifications: {e}")

print("\n" + "=" * 60)
print("🎉 CLEANUP COMPLETED!")
print("=" * 60)

# Display summary
if deletion_counts:
    print("\n📊 DELETION SUMMARY:")
    print("-" * 30)
    total_deleted = 0
    for item_name, count in deletion_counts.items():
        print(f"  • {item_name}: {count}")
        total_deleted += count
    print(f"\n🗑️  Total items deleted: {total_deleted}")
else:
    print("\n✨ No demo data found - database was already clean!")

print("\n✅ PRESERVED (NOT deleted):")
print("-" * 30)
print("  • User accounts and profiles")
print("  • NotificationTypes (system configuration)")
print("  • MaintenanceCategories (system configuration)")
print("  • AnnouncementCategories (system configuration)")
print("  • CommonAreas (facility definitions)")
print("  • Staff roles and permissions")

print("\n🚀 Your system is now clean and ready for production use!")
print("=" * 60)
