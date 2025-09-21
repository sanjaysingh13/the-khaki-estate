from django.urls import path

from . import views

app_name = "backend"

# ============================================================================
# URL PATTERNS FOR HOUSING COMPLEX MANAGEMENT SYSTEM
# ============================================================================

urlpatterns = [
    # Dashboard - Main landing page
    path("", views.dashboard, name="dashboard"),
    # ============================================================================
    # ANNOUNCEMENT URLS - Communication workflow
    # ============================================================================
    path("announcements/", views.announcement_list, name="announcement_list"),
    path(
        "announcements/create/",
        views.announcement_create,
        name="announcement_create",
    ),
    path(
        "announcements/<int:announcement_id>/",
        views.announcement_detail,
        name="announcement_detail",
    ),
    path(
        "announcements/<int:announcement_id>/edit/",
        views.announcement_edit,
        name="announcement_edit",
    ),
    path(
        "announcements/<int:announcement_id>/comment/",
        views.add_comment,
        name="add_comment",
    ),
    # ============================================================================
    # MAINTENANCE REQUEST URLS - Maintenance workflow
    # ============================================================================
    path("maintenance/", views.maintenance_request_list, name="maintenance_list"),
    path(
        "maintenance/create/",
        views.maintenance_request_create,
        name="maintenance_create",
    ),
    path(
        "maintenance/<int:request_id>/",
        views.maintenance_request_detail,
        name="maintenance_detail",
    ),
    path(
        "maintenance/<int:request_id>/update-status/",
        views.update_maintenance_status,
        name="update_maintenance_status",
    ),
    path(
        "maintenance/<int:request_id>/add-update/",
        views.add_maintenance_update,
        name="add_maintenance_update",
    ),
    # ============================================================================
    # FACILITY BOOKING URLS - Booking workflow
    # ============================================================================
    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/calendar/", views.booking_calendar, name="booking_calendar"),
    path("bookings/calendar/api/", views.booking_calendar_api, name="booking_calendar_api"),
    path("bookings/create/", views.booking_create, name="booking_create"),
    path("bookings/<int:booking_id>/", views.booking_detail, name="booking_detail"),
    path(
        "bookings/<int:booking_id>/approve/",
        views.approve_booking,
        name="approve_booking",
    ),
    path(
        "bookings/<int:booking_id>/update-status/",
        views.update_booking_status,
        name="update_booking_status",
    ),
    # ============================================================================
    # EVENT MANAGEMENT URLS - Community engagement
    # ============================================================================
    path("events/", views.event_list, name="event_list"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("events/<int:event_id>/rsvp/", views.event_rsvp, name="event_rsvp"),
    # ============================================================================
    # MARKETPLACE URLS - Community marketplace
    # ============================================================================
    path("marketplace/", views.marketplace_list, name="marketplace_list"),
    path("marketplace/create/", views.marketplace_create, name="marketplace_create"),
    path(
        "marketplace/<int:item_id>/",
        views.marketplace_detail,
        name="marketplace_detail",
    ),
    path(
        "marketplace/<int:item_id>/update-status/",
        views.marketplace_update_status,
        name="marketplace_update_status",
    ),
    # ============================================================================
    # NOTIFICATION URLS - Notification management
    # ============================================================================
    path("notifications/", views.get_notifications, name="get_notifications"),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
]
