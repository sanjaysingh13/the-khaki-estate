import json
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Announcement
from .models import AnnouncementCategory
from .models import AnnouncementRead
from .models import Booking
from .models import Comment
from .models import CommonArea
from .models import Event
from .models import EventRSVP
from .models import GalleryComment
from .models import GalleryLike
from .models import GalleryPhoto
from .models import MaintenanceCategory
from .models import MaintenanceRequest
from .models import MaintenanceUpdate
from .models import MarketplaceItem
from .models import Notification

# Import all models from the backend app
from .models import Resident

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_resident_profile(user):
    """
    Get the resident profile for a user, creating one if it doesn't exist
    """
    try:
        return user.resident
    except Resident.DoesNotExist:
        # Create a resident profile for the user
        return Resident.objects.create(
            user=user,
            flat_number="0000",  # Default value, should be updated
            phone_number="0000000000",  # Default value, should be updated
            resident_type="owner",
        )


def is_committee_member(user):
    """
    Check if user is a committee member
    """
    try:
        resident = get_resident_profile(user)
    except (Resident.DoesNotExist, AttributeError):
        return False
    else:
        return resident.is_committee_member


def is_staff_member(user):
    """
    Check if user is a staff member
    """
    try:
        staff = user.staff
        return staff.is_active
    except:
        return False


def can_manage_maintenance(user):
    """
    Check if user can manage maintenance requests
    (either committee member or staff with appropriate permissions)
    """
    # Check if user is committee member
    if is_committee_member(user):
        return True

    # Check if user is staff with maintenance permissions
    try:
        staff = user.staff
        return staff.is_active and (
            staff.can_access_all_maintenance
            or staff.can_assign_requests
            or staff.staff_role in ["facility_manager", "maintenance_supervisor"]
        )
    except:
        return False


# ============================================================================
# DASHBOARD VIEWS - Main landing pages for residents and management
# ============================================================================


@login_required
def dashboard(request):
    """
    Main dashboard view that shows different content based on user type
    - Residents see: recent announcements, their maintenance requests, upcoming events
    - Committee members see: management dashboard with analytics and pending tasks
    """
    user = request.user

    # Get recent announcements (last 7 days)
    recent_announcements = Announcement.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7),
    ).order_by("-is_pinned", "-is_urgent", "-created_at")[:5]

    # Get user's unread notifications count
    unread_notifications = Notification.objects.filter(
        recipient=user,
        status__in=["sent", "delivered"],
    ).count()

    if is_committee_member(user) or can_manage_maintenance(user):
        # Management dashboard - show management data for committee members and staff
        pending_maintenance = MaintenanceRequest.objects.filter(
            status__in=["submitted", "acknowledged"],
        ).count()

        upcoming_events = Event.objects.filter(
            start_datetime__gte=timezone.now(),
        ).order_by("start_datetime")[:3]

        recent_bookings = Booking.objects.filter(
            booking_date__gte=timezone.now().date(),
        ).order_by("booking_date", "start_time")[:5]

        # Staff-specific data
        staff_info = None
        if is_staff_member(user):
            try:
                staff = user.staff
                staff_info = {
                    "role": staff.get_staff_role_display(),
                    "department": staff.department,
                    "can_access_all_maintenance": staff.can_access_all_maintenance,
                    "can_assign_requests": staff.can_assign_requests,
                    "can_close_requests": staff.can_close_requests,
                }
            except:
                staff_info = None

        context = {
            "user": user,
            "recent_announcements": recent_announcements,
            "unread_notifications": unread_notifications,
            "pending_maintenance": pending_maintenance,
            "upcoming_events": upcoming_events,
            "recent_bookings": recent_bookings,
            "is_committee": is_committee_member(user),
            "is_staff": is_staff_member(user),
            "staff_info": staff_info,
            "can_manage_maintenance": can_manage_maintenance(user),
        }
    else:
        # Regular resident dashboard
        user_maintenance_requests = MaintenanceRequest.objects.filter(
            resident=user,
        ).order_by("-created_at")[:3]

        upcoming_events = Event.objects.filter(
            start_datetime__gte=timezone.now(),
        ).order_by("start_datetime")[:3]

        user_bookings = Booking.objects.filter(
            resident=user,
            booking_date__gte=timezone.now().date(),
        ).order_by("booking_date", "start_time")[:3]

        context = {
            "user": user,
            "recent_announcements": recent_announcements,
            "unread_notifications": unread_notifications,
            "user_maintenance_requests": user_maintenance_requests,
            "upcoming_events": upcoming_events,
            "user_bookings": user_bookings,
            "is_committee": False,
        }

    return render(request, "backend/dashboard.html", context)


# ============================================================================
# ANNOUNCEMENT VIEWS - Communication workflow implementation
# ============================================================================


@login_required
def announcement_list(request):
    """
    Display all announcements with filtering and search capabilities
    Supports filtering by category, urgency, and read status
    """
    announcements = Announcement.objects.all().order_by(
        "-is_pinned",
        "-is_urgent",
        "-created_at",
    )

    # Filter by category if specified
    category_id = request.GET.get("category")
    if category_id:
        announcements = announcements.filter(category_id=category_id)

    # Filter by urgency if specified
    urgent_only = request.GET.get("urgent")
    if urgent_only == "true":
        announcements = announcements.filter(is_urgent=True)

    # Filter by read status
    read_status = request.GET.get("read")
    if read_status == "unread":
        read_announcements = AnnouncementRead.objects.filter(
            resident=request.user,
        ).values_list("announcement_id", flat=True)
        announcements = announcements.exclude(id__in=read_announcements)
    elif read_status == "read":
        read_announcements = AnnouncementRead.objects.filter(
            resident=request.user,
        ).values_list("announcement_id", flat=True)
        announcements = announcements.filter(id__in=read_announcements)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        announcements = announcements.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query),
        )

    # Pagination
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter dropdown
    categories = AnnouncementCategory.objects.all()

    # Mark announcements as read when viewed
    for announcement in page_obj:
        AnnouncementRead.objects.get_or_create(
            announcement=announcement,
            resident=request.user,
        )

    context = {
        "announcements": page_obj,
        "categories": categories,
        "current_category": category_id,
        "current_urgent": urgent_only,
        "current_read": read_status,
        "search_query": search_query,
    }

    return render(request, "backend/announcements/list.html", context)


@login_required
def announcement_detail(request, announcement_id):
    """
    Display individual announcement with comments and interaction options
    Allows residents to comment and committee members to edit
    """
    announcement = get_object_or_404(Announcement, id=announcement_id)

    # Mark as read
    AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        resident=request.user,
    )

    # Get comments (including replies)
    comments = Comment.objects.filter(announcement=announcement, parent=None).order_by(
        "created_at",
    )

    # Get read statistics for committee members
    read_stats = None
    if is_committee_member(request.user):
        total_residents = Resident.objects.filter(user__is_active=True).count()
        read_count = AnnouncementRead.objects.filter(announcement=announcement).count()
        read_stats = {
            "read_count": read_count,
            "total_residents": total_residents,
            "read_percentage": (read_count / total_residents * 100)
            if total_residents > 0
            else 0,
        }

    context = {
        "announcement": announcement,
        "comments": comments,
        "read_stats": read_stats,
        "can_edit": is_committee_member(request.user),
    }

    return render(request, "backend/announcements/detail.html", context)


@login_required
def announcement_create(request):
    """
    Create new announcement - only accessible to committee members
    Handles form submission and automatic notification sending
    """
    if not is_committee_member(request.user):
        messages.error(request, "Only committee members can create announcements.")
        return redirect("backend:dashboard")

    if request.method == "POST":
        # Extract form data
        title = request.POST.get("title")
        content = request.POST.get("content")
        category_id = request.POST.get("category")
        is_urgent = request.POST.get("is_urgent") == "on"
        is_pinned = request.POST.get("is_pinned") == "on"
        valid_until = request.POST.get("valid_until")

        # Validate required fields
        if not title or not content or not category_id:
            messages.error(request, "Please fill in all required fields.")
            return redirect("backend:announcement_create")

        try:
            category = AnnouncementCategory.objects.get(id=category_id)

            # Create announcement
            announcement = Announcement.objects.create(
                title=title,
                content=content,
                category=category,
                author=request.user,
                is_urgent=is_urgent,
                is_pinned=is_pinned,
                valid_until=datetime.fromisoformat(valid_until)
                if valid_until
                else None,
            )

            # Handle file attachment if provided
            if "attachment" in request.FILES:
                announcement.attachment = request.FILES["attachment"]
                announcement.save()

            # Send notifications to all residents
            # TODO: Implement notification sending

            messages.success(request, f'Announcement "{title}" created successfully!')
            return redirect(
                "backend:announcement_detail",
                announcement_id=announcement.id,
            )

        except AnnouncementCategory.DoesNotExist:
            messages.error(request, "Invalid category selected.")
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Error creating announcement: {e!s}")

    # GET request - show form
    categories = AnnouncementCategory.objects.all()
    context = {
        "categories": categories,
    }

    return render(request, "backend/announcements/create.html", context)


@login_required
def announcement_edit(request, announcement_id):
    """
    Edit existing announcement - only accessible to committee members
    """
    announcement = get_object_or_404(Announcement, id=announcement_id)

    if not is_committee_member(request.user):
        messages.error(request, "Only committee members can edit announcements.")
        return redirect("backend:announcement_detail", announcement_id=announcement_id)

    if request.method == "POST":
        # Update announcement fields
        announcement.title = request.POST.get("title")
        announcement.content = request.POST.get("content")
        announcement.category_id = request.POST.get("category")
        announcement.is_urgent = request.POST.get("is_urgent") == "on"
        announcement.is_pinned = request.POST.get("is_pinned") == "on"

        valid_until = request.POST.get("valid_until")
        announcement.valid_until = (
            datetime.fromisoformat(valid_until) if valid_until else None
        )

        # Handle file attachment
        if "attachment" in request.FILES:
            announcement.attachment = request.FILES["attachment"]

        announcement.save()

        messages.success(request, "Announcement updated successfully!")
        return redirect("backend:announcement_detail", announcement_id=announcement.id)

    # GET request - show edit form
    categories = AnnouncementCategory.objects.all()
    context = {
        "announcement": announcement,
        "categories": categories,
    }

    return render(request, "backend/announcements/edit.html", context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, announcement_id):
    """
    Add comment to announcement - AJAX endpoint
    Supports threaded comments (replies)
    """
    announcement = get_object_or_404(Announcement, id=announcement_id)

    content = request.POST.get("content")
    parent_id = request.POST.get("parent_id")

    if not content:
        return JsonResponse(
            {"status": "error", "message": "Comment content is required"},
        )

    try:
        parent = None
        if parent_id:
            parent = Comment.objects.get(id=parent_id, announcement=announcement)

        comment = Comment.objects.create(
            announcement=announcement,
            author=request.user,
            content=content,
            parent=parent,
        )

        return JsonResponse(
            {
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "content": comment.content,
                    "author": comment.author.get_full_name(),
                    "created_at": comment.created_at.isoformat(),
                    "parent_id": parent.id if parent else None,
                },
            },
        )

    except Comment.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Parent comment not found"})
    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


# ============================================================================
# MAINTENANCE REQUEST VIEWS - Complete maintenance workflow
# ============================================================================


@login_required
def maintenance_request_list(request):
    """
    Display maintenance requests with filtering and status management
    Different views for residents (their requests) and committee (all requests)
    """
    if can_manage_maintenance(request.user):
        # Committee members and authorized staff see all requests
        requests = MaintenanceRequest.objects.all().order_by("-created_at")

        # Filter by status
        status_filter = request.GET.get("status")
        if status_filter:
            requests = requests.filter(status=status_filter)

        # Filter by priority
        priority_filter = request.GET.get("priority")
        if priority_filter:
            requests = requests.filter(priority=priority_filter)

        # Filter by category
        category_filter = request.GET.get("category")
        if category_filter:
            requests = requests.filter(category_id=category_filter)

    else:
        # Residents see only their requests
        requests = MaintenanceRequest.objects.filter(resident=request.user).order_by(
            "-created_at",
        )

    # Pagination
    paginator = Paginator(requests, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options
    categories = MaintenanceCategory.objects.all()

    context = {
        "requests": page_obj,
        "categories": categories,
        "is_committee": is_committee_member(request.user),
        "current_status": request.GET.get("status"),
        "current_priority": request.GET.get("priority"),
        "current_category": request.GET.get("category"),
    }

    return render(request, "backend/maintenance/list.html", context)


@login_required
def maintenance_request_detail(request, request_id):
    """
    Display maintenance request details with updates and status management
    """
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # Check if user has permission to view this request
    if (
        not can_manage_maintenance(request.user)
        and maintenance_request.resident != request.user
    ):
        messages.error(request, "You do not have permission to view this request.")
        return redirect("backend:maintenance_list")

    # Get all updates for this request
    updates = MaintenanceUpdate.objects.filter(request=maintenance_request).order_by(
        "created_at",
    )

    # Get available staff for assignment (committee members)
    available_staff = Resident.objects.filter(
        is_committee_member=True,
        user__is_active=True,
    )

    context = {
        "maintenance_request": maintenance_request,
        "updates": updates,
        "available_staff": available_staff,
        "can_manage": can_manage_maintenance(request.user),
        "is_owner": maintenance_request.resident == request.user,
    }

    return render(request, "backend/maintenance/detail.html", context)


@login_required
def maintenance_request_create(request):
    """
    Create new maintenance request with automatic ticket generation
    """
    if request.method == "POST":
        # Extract form data
        title = request.POST.get("title")
        description = request.POST.get("description")
        category_id = request.POST.get("category")
        location = request.POST.get("location")
        priority = int(request.POST.get("priority", 2))

        # Validate required fields
        if not all([title, description, category_id, location]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("backend:maintenance_create")

        try:
            category = MaintenanceCategory.objects.get(id=category_id)

            # Create maintenance request (ticket number auto-generated in save method)
            maintenance_request = MaintenanceRequest.objects.create(
                title=title,
                description=description,
                category=category,
                resident=request.user,
                location=location,
                priority=priority,
            )

            # Handle image attachment if provided
            if "attachment" in request.FILES:
                maintenance_request.attachment = request.FILES["attachment"]
                maintenance_request.save()

            # Send notifications to committee members
            # TODO: Implement notification sending

            messages.success(
                request,
                f"Maintenance request {maintenance_request.ticket_number} created successfully!",
            )
            return redirect(
                "backend:maintenance_detail",
                request_id=maintenance_request.id,
            )

        except MaintenanceCategory.DoesNotExist:
            messages.error(request, "Invalid category selected.")
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Error creating maintenance request: {e!s}")

    # GET request - show form
    categories = MaintenanceCategory.objects.all()
    context = {
        "categories": categories,
    }

    return render(request, "backend/maintenance/create.html", context)


@login_required
@require_http_methods(["POST"])
def update_maintenance_status(request, request_id):
    """
    Update maintenance request status - committee members only
    """
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    if not can_manage_maintenance(request.user):
        return JsonResponse({"status": "error", "message": "Permission denied"})

    new_status = request.POST.get("status")
    assigned_to_id = request.POST.get("assigned_to")
    comment = request.POST.get("comment", "")

    if new_status not in [choice[0] for choice in MaintenanceRequest.STATUS_CHOICES]:
        return JsonResponse({"status": "error", "message": "Invalid status"})

    try:
        # Update status
        maintenance_request.status = new_status

        # Update assignment if provided
        if assigned_to_id:
            assigned_user = Resident.objects.get(
                id=assigned_to_id,
                is_committee_member=True,
            )
            maintenance_request.assigned_to = assigned_user

        # Set resolved timestamp if status is resolved
        if new_status == "resolved":
            maintenance_request.resolved_at = timezone.now()

        maintenance_request.save()

        # Create update record
        if comment:
            MaintenanceUpdate.objects.create(
                request=maintenance_request,
                author=request.user,
                content=comment,
                status_changed_to=new_status,
            )

        # Send notification to resident about status change
        from .notification_service import NotificationService

        status_messages = {
            "submitted": "Your maintenance request has been submitted",
            "acknowledged": "Your maintenance request has been acknowledged and is being reviewed",
            "assigned": "Your maintenance request has been assigned to our team",
            "in_progress": "Work has started on your maintenance request",
            "resolved": "Your maintenance request has been completed! Please check and confirm.",
            "closed": "Your maintenance request has been closed",
            "cancelled": "Your maintenance request has been cancelled",
        }

        status_message = status_messages.get(
            new_status, f"Status updated to {new_status}"
        )

        NotificationService.create_notification(
            recipient=maintenance_request.resident,
            notification_type_name="maintenance_status_change",
            title=f"Status Update: {maintenance_request.ticket_number}",
            message=status_message,
            related_object=maintenance_request,
            data={
                "url": f"/backend/maintenance/{maintenance_request.id}/",
                "request_id": maintenance_request.id,
                "old_status": maintenance_request.status,
                "new_status": new_status,
            },
        )

        return JsonResponse(
            {"status": "success", "message": "Status updated successfully"},
        )

    except Resident.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Invalid staff member"})
    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


@login_required
@require_http_methods(["POST"])
def add_maintenance_update(request, request_id):
    """
    Add update/comment to maintenance request
    """
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # Check permissions - allow staff with maintenance permissions or the resident who owns the request
    if (
        not can_manage_maintenance(request.user)
        and maintenance_request.resident != request.user
    ):
        return JsonResponse({"status": "error", "message": "Permission denied"})

    content = request.POST.get("content")
    if not content:
        return JsonResponse(
            {"status": "error", "message": "Update content is required"},
        )

    try:
        update = MaintenanceUpdate.objects.create(
            request=maintenance_request,
            author=request.user,
            content=content,
        )

        # Handle image attachment if provided
        if "attachment" in request.FILES:
            update.attachment = request.FILES["attachment"]
            update.save()

        # Send notification based on who added the update
        from .notification_service import NotificationService

        if can_manage_maintenance(request.user):
            # Staff member added update, notify the resident who created the request
            NotificationService.create_notification(
                recipient=maintenance_request.resident,
                notification_type_name="maintenance_update",
                title=f"Update on your maintenance request {maintenance_request.ticket_number}",
                message=f"New update: {content[:100]}{'...' if len(content) > 100 else ''}",
                related_object=maintenance_request,
                data={
                    "url": f"/backend/maintenance/{maintenance_request.id}/",
                    "request_id": maintenance_request.id,
                    "update_id": update.id,
                },
            )
        elif maintenance_request.resident == request.user:
            # Resident added update to their own request, notify staff members who can manage maintenance
            from .models import Staff

            # Notify all active staff members who can handle maintenance
            staff_members = Staff.objects.filter(
                is_active=True,
                can_access_all_maintenance=True,
            ).select_related("user")

            for staff in staff_members:
                if staff.user.is_active:
                    NotificationService.create_notification(
                        recipient=staff.user,
                        notification_type_name="maintenance_resident_update",
                        title=f"Resident update on {maintenance_request.ticket_number}",
                        message=f"{maintenance_request.resident.get_full_name()}: {content[:100]}{'...' if len(content) > 100 else ''}",
                        related_object=maintenance_request,
                        data={
                            "url": f"/backend/maintenance/{maintenance_request.id}/",
                            "request_id": maintenance_request.id,
                            "update_id": update.id,
                        },
                    )

        return JsonResponse(
            {
                "status": "success",
                "update": {
                    "id": update.id,
                    "content": update.content,
                    "author": update.author.get_full_name(),
                    "created_at": update.created_at.isoformat(),
                    "has_attachment": bool(update.attachment),
                },
            },
        )

    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


# ============================================================================
# FACILITY BOOKING VIEWS - Complete booking workflow
# ============================================================================


@login_required
def booking_list(request):
    """
    Display bookings with calendar view and filtering options
    """
    bookings = Booking.objects.filter(booking_date__gte=timezone.now().date()).order_by(
        "booking_date",
        "start_time",
    )

    # Filter by common area
    area_filter = request.GET.get("area")
    if area_filter:
        bookings = bookings.filter(common_area_id=area_filter)

    # Filter by status
    status_filter = request.GET.get("status")
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # Filter by user permissions
    if is_committee_member(request.user):
        # Committee members can see all bookings
        pass
    else:
        # Regular users see their own bookings or bookings they need to approve
        bookings = bookings.filter(
            Q(resident=request.user) |  # Their own bookings
            Q(designated_approver=request.user)  # Bookings they need to approve
        )

    # Pagination
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get filter options
    common_areas = CommonArea.objects.filter(is_active=True)

    # Get pending bookings for designated approvers
    pending_approvals = []
    if not is_committee_member(request.user):
        pending_approvals = Booking.objects.filter(
            designated_approver=request.user,
            status="pending"
        ).count()

    context = {
        "bookings": page_obj,
        "common_areas": common_areas,
        "current_area": area_filter,
        "current_status": status_filter,
        "is_committee": is_committee_member(request.user),
        "pending_approvals": pending_approvals,
    }

    return render(request, "backend/bookings/list.html", context)


@login_required
def booking_calendar(request):
    """
    Enhanced calendar view for facility bookings with proper data serialization.
    Shows current bookings so residents can plan their requests accordingly.
    """
    # Get filter parameters from request
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = timezone.now().month
        year = timezone.now().year
    
    # Create date range for the requested month
    start_of_month = date(year, month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get all common areas
    common_areas = CommonArea.objects.filter(is_active=True)
    
    # Get bookings for the month - include all statuses except cancelled for visibility
    bookings = Booking.objects.filter(
        booking_date__range=[start_of_month, end_of_month],
        status__in=["pending", "approved", "confirmed", "completed"]
    ).select_related(
        'common_area', 'resident', 'resident__resident'
    ).order_by("booking_date", "start_time")
    
    # Filter based on user permissions
    if not is_committee_member(request.user):
        # Regular residents see all bookings (for planning) but with limited details
        # They can see their own bookings with full details
        pass  # Show all bookings for planning purposes
    
    # Serialize bookings data for JavaScript consumption
    bookings_data = []
    for booking in bookings:
        # Determine what details to show based on user permissions
        if booking.resident == request.user or is_committee_member(request.user):
            # Full details for own bookings or committee members
            booking_data = {
                'id': booking.id,
                'booking_number': booking.booking_number,
                'common_area_id': booking.common_area.id,
                'common_area_name': booking.common_area.name,
                'booking_date': booking.booking_date.isoformat(),
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'purpose': booking.purpose,
                'status': booking.status,
                'guests_count': booking.guests_count,
                'total_fee': float(booking.total_fee) if booking.total_fee else 0,
                'resident_name': booking.resident.get_full_name(),
                'resident_flat': getattr(booking.resident.resident, 'flat_number', 'N/A') if hasattr(booking.resident, 'resident') else 'N/A',
                'is_own_booking': booking.resident == request.user
            }
        else:
            # Limited details for other residents' bookings (for planning purposes)
            booking_data = {
                'id': booking.id,
                'common_area_id': booking.common_area.id,
                'common_area_name': booking.common_area.name,
                'booking_date': booking.booking_date.isoformat(),
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'status': booking.status,
                'purpose': 'Private Event',  # Generic purpose for privacy
                'resident_name': 'Resident',  # Anonymous for privacy
                'is_own_booking': False
            }
        bookings_data.append(booking_data)
    
    # Group bookings by area for easier frontend processing
    bookings_by_area = {}
    for area in common_areas:
        area_bookings = [b for b in bookings_data if b['common_area_id'] == area.id]
        bookings_by_area[str(area.id)] = area_bookings
    
    context = {
        "common_areas": common_areas,
        "bookings_by_area": json.dumps(bookings_by_area),  # Properly serialize for JavaScript
        "current_month": start_of_month.strftime("%B %Y"),
        "current_month_number": month,
        "current_year": year,
        "is_committee": is_committee_member(request.user),
        "today": timezone.now().date().isoformat(),
    }

    return render(request, "backend/bookings/calendar.html", context)


@login_required
def booking_calendar_api(request):
    """
    API endpoint for dynamic calendar data loading.
    Returns booking data for a specific month/year as JSON.
    """
    # Get parameters from request
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    area_filter = request.GET.get('area', '')
    
    try:
        month = int(month)
        year = int(year)
        area_filter = int(area_filter) if area_filter else None
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)
    
    # Create date range for the requested month
    start_of_month = date(year, month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Build query for bookings
    bookings_query = Booking.objects.filter(
        booking_date__range=[start_of_month, end_of_month],
        status__in=["pending", "approved", "confirmed", "completed"]
    ).select_related('common_area', 'resident', 'resident__resident')
    
    # Apply area filter if specified
    if area_filter:
        bookings_query = bookings_query.filter(common_area_id=area_filter)
    
    bookings = bookings_query.order_by("booking_date", "start_time")
    
    # Serialize bookings data
    bookings_data = []
    for booking in bookings:
        # Privacy controls: show limited info for other residents' bookings
        if booking.resident == request.user or is_committee_member(request.user):
            booking_data = {
                'id': booking.id,
                'booking_number': booking.booking_number,
                'common_area_id': booking.common_area.id,
                'common_area_name': booking.common_area.name,
                'booking_date': booking.booking_date.isoformat(),
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'purpose': booking.purpose,
                'status': booking.status,
                'guests_count': getattr(booking, 'guests_count', 0),
                'total_fee': float(getattr(booking, 'total_fee', 0)) if hasattr(booking, 'total_fee') else 0,
                'resident_name': booking.resident.get_full_name(),
                'resident_flat': getattr(booking.resident.resident, 'flat_number', 'N/A') if hasattr(booking.resident, 'resident') else 'N/A',
                'is_own_booking': True
            }
        else:
            # Limited info for privacy
            booking_data = {
                'id': booking.id,
                'common_area_id': booking.common_area.id,
                'common_area_name': booking.common_area.name,
                'booking_date': booking.booking_date.isoformat(),
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'status': booking.status,
                'purpose': 'Private Event',
                'resident_name': 'Resident',
                'is_own_booking': False
            }
        bookings_data.append(booking_data)
    
    return JsonResponse({
        'bookings': bookings_data,
        'month': month,
        'year': year,
        'month_name': start_of_month.strftime("%B %Y"),
        'success': True
    })


@login_required
def booking_create(request):
    """
    Create new facility booking with availability checking
    """
    if request.method == "POST":
        # Extract form data
        common_area_id = request.POST.get("common_area")
        booking_date = request.POST.get("booking_date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        purpose = request.POST.get("purpose")
        guests_count = int(request.POST.get("guests_count", 0))

        # Validate required fields
        if not all([common_area_id, booking_date, start_time, end_time, purpose]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("backend:booking_create")

        try:
            common_area = CommonArea.objects.get(id=common_area_id, is_active=True)

            # Parse dates and times
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time, "%H:%M").time()
            end_time = datetime.strptime(end_time, "%H:%M").time()

            # Check availability
            conflicting_bookings = Booking.objects.filter(
                common_area=common_area,
                booking_date=booking_date,
                status__in=["confirmed", "pending"],
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if conflicting_bookings.exists():
                messages.error(request, "The selected time slot is already booked.")
                return redirect("backend:booking_create")

            # Calculate fee
            hours = (
                datetime.combine(booking_date, end_time)
                - datetime.combine(booking_date, start_time)
            ).total_seconds() / 3600
            total_fee = float(common_area.booking_fee) * hours

            # Create booking (booking number auto-generated in save method)
            # The designated approver will be set automatically via the signal handler
            booking = Booking.objects.create(
                common_area=common_area,
                resident=request.user,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                purpose=purpose,
                guests_count=guests_count,
                total_fee=total_fee,
                status="pending",  # Requires designated resident approval
            )

            # The signal handler will automatically:
            # 1. Set the designated approver based on common area
            # 2. Send notification to the designated approver

            # Get the designated approver for user feedback
            approver = booking.get_designated_approver()
            approver_name = approver.get_full_name() if approver else "designated approver"
            
            messages.success(
                request,
                f"Booking {booking.booking_number} created successfully! "
                f"It has been sent to {approver_name} for approval.",
            )
            return redirect("backend:booking_detail", booking_id=booking.id)

        except CommonArea.DoesNotExist:
            messages.error(request, "Invalid facility selected.")
        except ValueError as e:
            messages.error(request, f"Invalid date/time format: {e!s}")
        except IntegrityError as e:
            messages.error(request, f"Error creating booking: {e!s}")

    # GET request - show form
    common_areas = CommonArea.objects.filter(is_active=True)
    
    # Check if date is pre-filled from calendar
    prefilled_date = request.GET.get('date', '')
    if prefilled_date:
        try:
            # Validate the date format
            datetime.strptime(prefilled_date, '%Y-%m-%d')
        except ValueError:
            prefilled_date = ''  # Invalid date format, clear it
    
    context = {
        "common_areas": common_areas,
        "prefilled_date": prefilled_date,
    }

    return render(request, "backend/bookings/create.html", context)


@login_required
def booking_detail(request, booking_id):
    """
    Display booking details with management options
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # Check permissions - allow designated approver, owner, and committee members
    can_view = (
        booking.resident == request.user or  # Booking owner
        booking.designated_approver == request.user or  # Designated approver
        is_committee_member(request.user)  # Committee members
    )
    
    if not can_view:
        messages.error(request, "You do not have permission to view this booking.")
        return redirect("backend:booking_list")

    # Check if user can approve this booking
    can_approve = booking.can_be_approved_by(request.user)
    
    # Check if user is the designated approver
    is_designated_approver = booking.designated_approver == request.user

    context = {
        "booking": booking,
        "can_manage": can_manage_maintenance(request.user),
        "can_approve": can_approve,
        "is_designated_approver": is_designated_approver,
        "is_owner": booking.resident == request.user,
    }

    return render(request, "backend/bookings/detail.html", context)


@login_required
@require_http_methods(["POST"])
def approve_booking(request, booking_id):
    """
    Approve or reject a booking - designated resident approvers only
    
    This view handles the new approval workflow where designated residents
    (instead of facility managers) approve bookings for their assigned areas.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if user can approve this booking
    if not booking.can_be_approved_by(request.user):
        return JsonResponse({
            "status": "error", 
            "message": "You are not authorized to approve this booking"
        })
    
    action = request.POST.get("action")  # 'approve' or 'reject'
    rejection_reason = request.POST.get("rejection_reason", "").strip()
    
    if action not in ["approve", "reject"]:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid action. Must be 'approve' or 'reject'"
        })
    
    # Validate rejection reason if rejecting
    if action == "reject" and not rejection_reason:
        return JsonResponse({
            "status": "error", 
            "message": "Rejection reason is required when rejecting a booking"
        })
    
    try:
        # Use the model's approval method for proper workflow
        approved = (action == "approve")
        booking.approve_booking(
            approver=request.user,
            approved=approved,
            rejection_reason=rejection_reason if not approved else None
        )
        
        # Manually trigger notifications since signal handler has issues
        from .signals import _notify_booking_approved, _notify_booking_rejected
        
        if approved:
            _notify_booking_approved(booking)
        else:
            _notify_booking_rejected(booking)
        
        action_message = "approved" if approved else "rejected"
        return JsonResponse({
            "status": "success", 
            "message": f"Booking {booking.booking_number} has been {action_message} successfully"
        })
        
    except ValueError as e:
        return JsonResponse({"status": "error", "message": str(e)})
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"})


@login_required
@require_http_methods(["POST"])
def update_booking_status(request, booking_id):
    """
    Update booking status - committee members and designated approvers
    
    This view handles general status updates (confirmed, cancelled, completed)
    for users who have permission to manage bookings.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check permissions - committee members or designated approvers
    can_manage = (
        is_committee_member(request.user) or 
        booking.designated_approver == request.user or
        can_manage_maintenance(request.user)
    )
    
    if not can_manage:
        return JsonResponse({
            "status": "error", 
            "message": "Permission denied"
        })
    
    new_status = request.POST.get("status")
    
    if new_status not in [choice[0] for choice in Booking.STATUS_CHOICES]:
        return JsonResponse({
            "status": "error", 
            "message": "Invalid status"
        })
    
    # Validate status transitions
    valid_transitions = {
        'pending': ['approved', 'rejected', 'cancelled'],
        'approved': ['confirmed', 'cancelled'],
        'confirmed': ['completed', 'cancelled'],
        'rejected': ['cancelled'],
        'cancelled': [],  # Terminal state
        'completed': [],  # Terminal state
    }
    
    if new_status not in valid_transitions.get(booking.status, []):
        return JsonResponse({
            "status": "error", 
            "message": f"Cannot transition from {booking.status} to {new_status}"
        })
    
    try:
        # Update status with audit trail
        from django.utils import timezone
        
        old_status = booking.status
        booking.status = new_status
        booking.status_changed_at = timezone.now()
        booking.status_changed_by = request.user
        booking.save()
        
        # Manually trigger notifications for specific status changes
        from .signals import _notify_booking_confirmed, _notify_booking_cancelled
        
        if new_status == "confirmed":
            _notify_booking_confirmed(booking)
        elif new_status == "cancelled":
            _notify_booking_cancelled(booking)
        
        return JsonResponse({
            "status": "success", 
            "message": f"Booking status updated from {old_status} to {new_status} successfully"
        })
        
    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


# ============================================================================
# EVENT MANAGEMENT VIEWS - Community engagement workflow
# ============================================================================


@login_required
def event_list(request):
    """
    Display upcoming events with RSVP functionality
    """
    events = Event.objects.filter(start_datetime__gte=timezone.now()).order_by(
        "start_datetime",
    )

    # Filter by event type
    event_type = request.GET.get("type")
    if event_type:
        events = events.filter(event_type=event_type)

    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Get RSVP status for each event
    event_rsvps = {}
    for event in page_obj:
        try:
            rsvp = EventRSVP.objects.get(event=event, resident=request.user)
            event_rsvps[event.id] = rsvp.response
        except EventRSVP.DoesNotExist:
            event_rsvps[event.id] = None

    context = {
        "events": page_obj,
        "event_rsvps": event_rsvps,
        "current_type": event_type,
        "event_types": Event.EVENT_TYPES,
    }

    return render(request, "backend/events/list.html", context)


@login_required
def event_detail(request, event_id):
    """
    Display event details with RSVP functionality and attendee list
    """
    event = get_object_or_404(Event, id=event_id)

    # Get user's RSVP status
    user_rsvp = None
    from contextlib import suppress

    with suppress(EventRSVP.DoesNotExist):
        user_rsvp = EventRSVP.objects.get(event=event, resident=request.user)

    # Get all RSVPs for this event
    rsvps = EventRSVP.objects.filter(event=event).order_by("response", "created_at")

    # Count RSVP responses
    rsvp_counts = rsvps.values("response").annotate(count=Count("response"))
    rsvp_summary = {item["response"]: item["count"] for item in rsvp_counts}

    # Calculate total attendees (including guests)
    total_attendees = sum(
        rsvp.guests_count + 1 for rsvp in rsvps if rsvp.response == "yes"
    )

    # Calculate capacity percentage for progress bar
    capacity_percentage = 0
    if event.max_attendees and event.max_attendees > 0:
        capacity_percentage = min(100, (total_attendees / event.max_attendees) * 100)

    context = {
        "event": event,
        "user_rsvp": user_rsvp,
        "rsvps": rsvps,
        "rsvp_summary": rsvp_summary,
        "total_attendees": total_attendees,
        "capacity_percentage": capacity_percentage,
        "can_edit": is_committee_member(request.user)
        or event.organizer == request.user,
    }

    return render(request, "backend/events/detail.html", context)


@login_required
def event_create(request):
    """
    Create new event - accessible to committee members and residents
    """
    if request.method == "POST":
        # Extract form data
        title = request.POST.get("title")
        description = request.POST.get("description")
        event_type = request.POST.get("event_type")
        start_datetime = request.POST.get("start_datetime")
        end_datetime = request.POST.get("end_datetime")
        location = request.POST.get("location")
        max_attendees = request.POST.get("max_attendees")
        is_rsvp_required = request.POST.get("is_rsvp_required") == "on"

        # Validate required fields
        if not all(
            [title, description, event_type, start_datetime, end_datetime, location],
        ):
            messages.error(request, "Please fill in all required fields.")
            return redirect("backend:event_create")

        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start_datetime.replace("T", " "))
            end_dt = datetime.fromisoformat(end_datetime.replace("T", " "))

            # Create event
            event = Event.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                start_datetime=start_dt,
                end_datetime=end_dt,
                location=location,
                max_attendees=int(max_attendees) if max_attendees else None,
                is_rsvp_required=is_rsvp_required,
                organizer=request.user,
            )

            # Send notifications to all residents
            # TODO: Implement notification sending

            messages.success(request, f'Event "{title}" created successfully!')
            return redirect("backend:event_detail", event_id=event.id)

        except ValueError as e:
            messages.error(request, f"Invalid date/time format: {e!s}")
        except IntegrityError as e:
            messages.error(request, f"Error creating event: {e!s}")

    # GET request - show form
    context = {
        "event_types": Event.EVENT_TYPES,
    }

    return render(request, "backend/events/create.html", context)


@login_required
@require_http_methods(["POST"])
def event_rsvp(request, event_id):
    """
    Handle RSVP responses for events
    """
    event = get_object_or_404(Event, id=event_id)

    response = request.POST.get("response")
    guests_count = int(request.POST.get("guests_count", 0))
    comment = request.POST.get("comment", "")

    if response not in [choice[0] for choice in EventRSVP.RESPONSE_CHOICES]:
        return JsonResponse({"status": "error", "message": "Invalid response"})

    try:
        # Create or update RSVP
        _rsvp, created = EventRSVP.objects.update_or_create(
            event=event,
            resident=request.user,
            defaults={
                "response": response,
                "guests_count": guests_count,
                "comment": comment,
            },
        )

        # Send notification to organizer
        # TODO: Implement notification sending

        return JsonResponse(
            {
                "status": "success",
                "message": "RSVP updated successfully",
                "created": created,
            },
        )

    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


# ============================================================================
# MARKETPLACE VIEWS - Community marketplace functionality
# ============================================================================


@login_required
def marketplace_list(request):
    """
    Display marketplace items with filtering and search
    """
    items = MarketplaceItem.objects.filter(
        status="active",
        expires_at__gt=timezone.now(),
    ).order_by("-created_at")

    # Filter by item type
    item_type = request.GET.get("type")
    if item_type:
        items = items.filter(item_type=item_type)

    # Search functionality
    search_query = request.GET.get("search")
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query),
        )

    # Pagination
    paginator = Paginator(items, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "items": page_obj,
        "item_types": MarketplaceItem.ITEM_TYPES,
        "current_type": item_type,
        "search_query": search_query,
    }

    return render(request, "backend/marketplace/list.html", context)


@login_required
def marketplace_detail(request, item_id):
    """
    Display marketplace item details with contact options
    """
    item = get_object_or_404(MarketplaceItem, id=item_id)

    # Check if item is still active
    if item.status != "active" or item.expires_at <= timezone.now():
        messages.error(request, "This item is no longer available.")
        return redirect("backend:marketplace_list")

    context = {
        "item": item,
        "is_owner": item.seller == request.user,
    }

    return render(request, "backend/marketplace/detail.html", context)


@login_required
def marketplace_create(request):
    """
    Create new marketplace item
    """
    if request.method == "POST":
        # Extract form data
        title = request.POST.get("title")
        description = request.POST.get("description")
        item_type = request.POST.get("item_type")
        price = request.POST.get("price")
        contact_phone = request.POST.get("contact_phone")
        expires_days = int(request.POST.get("expires_days", 30))

        # Validate required fields
        if not all([title, description, item_type]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("backend:marketplace_create")

        try:
            # Calculate expiry date
            expires_at = timezone.now() + timedelta(days=expires_days)

            # Create marketplace item
            item = MarketplaceItem.objects.create(
                title=title,
                description=description,
                item_type=item_type,
                price=float(price) if price else None,
                seller=request.user,
                contact_phone=contact_phone or request.user.phone_number,
                expires_at=expires_at,
            )

            # Handle image uploads
            for i in range(1, 4):
                image_field = f"image{i}"
                if image_field in request.FILES:
                    setattr(item, image_field, request.FILES[image_field])

            item.save()

            messages.success(request, f'Item "{title}" posted successfully!')
            return redirect("backend:marketplace_detail", item_id=item.id)

        except ValueError as e:
            messages.error(request, f"Invalid price format: {e!s}")
        except IntegrityError as e:
            messages.error(request, f"Error creating item: {e!s}")

    # GET request - show form
    context = {
        "item_types": MarketplaceItem.ITEM_TYPES,
    }

    return render(request, "backend/marketplace/create.html", context)


@login_required
@require_http_methods(["POST"])
def marketplace_update_status(request, item_id):
    """
    Update marketplace item status (mark as sold, etc.)
    """
    item = get_object_or_404(MarketplaceItem, id=item_id)

    if item.seller != request.user:
        return JsonResponse({"status": "error", "message": "Permission denied"})

    new_status = request.POST.get("status")

    if new_status not in [choice[0] for choice in MarketplaceItem.STATUS_CHOICES]:
        return JsonResponse({"status": "error", "message": "Invalid status"})

    try:
        item.status = new_status
        item.save()

        return JsonResponse(
            {"status": "success", "message": "Item status updated successfully"},
        )

    except (ValueError, IntegrityError) as e:
        return JsonResponse({"status": "error", "message": str(e)})


# ============================================================================
# NOTIFICATION VIEWS - Notification management
# ============================================================================


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """Get user's notifications - supports both HTML and JSON responses"""
    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )

    # Filter by status if requested
    status = request.GET.get("status")
    if status:
        notifications = notifications.filter(status=status)

    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Check if JSON response is requested
    if (
        request.headers.get("Accept") == "application/json"
        or request.GET.get("format") == "json"
    ):
        notifications_data = [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "status": notification.status,
                "created_at": notification.created_at.isoformat(),
                "data": notification.data,
            }
            for notification in page_obj
        ]

        return JsonResponse(
            {
                "notifications": notifications_data,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "total_count": paginator.count,
            },
        )

    # For HTML requests (when user actually visits notification center),
    # automatically mark all unread notifications as read
    if not status:  # Only when viewing all notifications, not filtered views
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            status__in=[
                "sent",
                "delivered",
            ],  # Both 'sent' and 'delivered' are considered unread
        )
        unread_notifications.update(
            status="read",
            read_at=timezone.now(),
        )

        # Refresh the queryset to show updated status
        notifications = Notification.objects.filter(recipient=request.user).order_by(
            "-created_at"
        )
        paginator = Paginator(notifications, 20)
        page_obj = paginator.get_page(page_number)

    # HTML response for browser navigation
    context = {
        "notifications": page_obj,
        "status_filter": status,
        "total_count": paginator.count,
    }
    return render(request, "backend/notifications/list.html", context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user,
        )
        notification.mark_as_read()
        return JsonResponse({"status": "success"})
    except Notification.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Notification not found"},
            status=404,
        )


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Mark all unread notifications as read for the current user.
    This endpoint is called when the user opens their notification center.
    """
    try:
        # Mark all unread notifications (sent/delivered) as read
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            status__in=["sent", "delivered"],
        )

        updated_count = unread_notifications.update(
            status="read",
            read_at=timezone.now(),
        )

        return JsonResponse(
            {
                "status": "success",
                "marked_count": updated_count,
                "message": f"{updated_count} notifications marked as read",
            }
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500,
        )


# ============================================================================
# API ENDPOINTS FOR SIGNUP FORM
# ============================================================================

@require_http_methods(["GET"])
def get_available_flats(request):
    """
    API endpoint to get available flats for owner signup.
    
    Returns flats that don't have associated users yet, formatted for
    the signup form autocomplete functionality.
    """
    try:
        # Get all residents that don't have associated users
        # These are residents created from CSV but not yet linked to user accounts
        available_residents = Resident.objects.filter(
            user__isnull=True,
            resident_type='owner'
        ).order_by('flat_number')
        
        # Format data for frontend
        flats_data = []
        for resident in available_residents:
            flats_data.append({
                'id': resident.id,
                'flat_number': resident.flat_number,
                'block': resident.block,
                'owner_name': resident.owner_name or f'Owner of {resident.flat_number}',
                'email': resident.owner_email or '',
                'phone': resident.phone_number,
            })
        
        return JsonResponse({
            'status': 'success',
            'flats': flats_data,
            'count': len(flats_data)
        })
        
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=500
        )


# ============================================================================
# CELERY TASK IMPORTS - Background task functions
# ============================================================================

# Import Celery tasks (these would be defined in tasks.py)
# TODO: Import notification tasks when implemented


# ============================================================================
# GALLERY VIEWS - Photo sharing and community interaction
# ============================================================================

@login_required
def gallery_list(request):
    """
    Display the gallery photo wall with timeline view.
    
    Shows all approved photos in chronological order (latest first)
    with like counts, comment counts, and interaction capabilities.
    """
    # Get all approved photos with related data
    photos = GalleryPhoto.objects.filter(
        is_approved=True
    ).select_related('author').prefetch_related(
        'likes', 'comments'
    ).order_by('-created_at')
    
    # Pagination for better performance
    paginator = Paginator(photos, 12)  # 12 photos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Add interaction data for each photo
    for photo in page_obj:
        photo.like_count = photo.get_like_count()
        photo.comment_count = photo.get_comment_count()
        photo.is_liked = photo.is_liked_by(request.user)
        photo.recent_comments = photo.get_recent_comments(3)
    
    context = {
        'page_obj': page_obj,
        'photos': page_obj,
        'user': request.user,
    }
    
    return render(request, 'backend/gallery/list.html', context)


@login_required
def gallery_create(request):
    """
    Handle photo upload to the gallery.
    
    Allows residents to upload photos with captions to share with
    the community. Includes file validation and error handling.
    """
    if request.method == 'POST':
        # Import the form here to avoid circular imports
        from .gallery_forms import GalleryPhotoForm
        
        form = GalleryPhotoForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                photo = form.save()
                messages.success(
                    request,
                    f"Photo uploaded successfully! "
                    f"Thank you for sharing with the community."
                )
                return redirect('backend:gallery_detail', photo_id=photo.id)
            except Exception as e:
                messages.error(
                    request,
                    f"Error uploading photo: {str(e)}"
                )
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        from .gallery_forms import GalleryPhotoForm
        form = GalleryPhotoForm(user=request.user)
    
    context = {
        'form': form,
        'user': request.user,
    }
    
    return render(request, 'backend/gallery/create.html', context)


@login_required
def gallery_detail(request, photo_id):
    """
    Display detailed view of a single photo with full comments.
    
    Shows the photo with all comments, like/unlike functionality,
    and comment form for user interaction.
    """
    photo = get_object_or_404(
        GalleryPhoto.objects.select_related('author').prefetch_related(
            'likes', 'comments__author', 'comments__replies__author'
        ),
        id=photo_id,
        is_approved=True
    )
    
    # Get all comments for this photo (including replies)
    comments = photo.comments.filter(
        is_approved=True,
        parent__isnull=True  # Only top-level comments
    ).order_by('created_at')
    
    # Add interaction data
    photo.like_count = photo.get_like_count()
    photo.comment_count = photo.get_comment_count()
    photo.is_liked = photo.is_liked_by(request.user)
    
    # Prepare comment form
    from .gallery_forms import GalleryCommentForm
    comment_form = GalleryCommentForm(user=request.user, photo=photo)
    
    context = {
        'photo': photo,
        'comments': comments,
        'comment_form': comment_form,
        'user': request.user,
    }
    
    return render(request, 'backend/gallery/detail.html', context)


@login_required
@require_http_methods(["POST"])
def gallery_like_toggle(request, photo_id):
    """
    AJAX endpoint to like/unlike a photo.
    
    Handles the like/unlike functionality via AJAX requests.
    Returns JSON response with updated like count and status.
    """
    photo = get_object_or_404(GalleryPhoto, id=photo_id, is_approved=True)
    
    try:
        # Check if user already liked this photo
        like, created = GalleryLike.objects.get_or_create(
            photo=photo,
            user=request.user
        )
        
        if not created:
            # User already liked, so unlike (delete the like)
            like.delete()
            is_liked = False
            message = "Photo unliked"
        else:
            # User liked the photo
            is_liked = True
            message = "Photo liked"
        
        # Get updated like count
        like_count = photo.get_like_count()
        
        return JsonResponse({
            'status': 'success',
            'is_liked': is_liked,
            'like_count': like_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f"Error updating like: {str(e)}"
        }, status=500)


@login_required
@require_http_methods(["POST"])
def gallery_comment_add(request, photo_id):
    """
    AJAX endpoint to add a comment to a photo.
    
    Handles comment submission via AJAX and returns the new comment
    as HTML for dynamic insertion into the page.
    """
    photo = get_object_or_404(GalleryPhoto, id=photo_id, is_approved=True)
    
    try:
        # Get parent comment if this is a reply
        parent_comment_id = request.POST.get('parent_comment_id')
        parent_comment = None
        if parent_comment_id:
            parent_comment = get_object_or_404(
                GalleryComment,
                id=parent_comment_id,
                photo=photo
            )
        
        # Import the form here to avoid circular imports
        from .gallery_forms import GalleryCommentForm
        
        form = GalleryCommentForm(
            request.POST,
            user=request.user,
            photo=photo,
            parent_comment=parent_comment
        )
        
        if form.is_valid():
            comment = form.save()
            
            # Return the new comment as HTML
            comment_html = render_to_string(
                'backend/gallery/partials/comment.html',
                {'comment': comment, 'user': request.user}
            )
            
            return JsonResponse({
                'status': 'success',
                'comment_html': comment_html,
                'comment_count': photo.get_comment_count(),
                'message': 'Comment added successfully'
            })
        else:
            # Return form errors
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            
            return JsonResponse({
                'status': 'error',
                'message': '; '.join(errors)
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f"Error adding comment: {str(e)}"
        }, status=500)


@login_required
def gallery_my_photos(request):
    """
    Display user's own photos for management.
    
    Shows all photos uploaded by the current user, including
    unapproved ones, with edit/delete options.
    """
    photos = GalleryPhoto.objects.filter(
        author=request.user
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(photos, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'photos': page_obj,
        'user': request.user,
    }
    
    return render(request, 'backend/gallery/my_photos.html', context)


@login_required
@require_http_methods(["POST"])
def gallery_photo_delete(request, photo_id):
    """
    Delete a photo (only by the author).
    
    Allows users to delete their own photos with confirmation.
    """
    photo = get_object_or_404(GalleryPhoto, id=photo_id, author=request.user)
    
    try:
        photo.delete()
        messages.success(request, "Photo deleted successfully.")
        return redirect('backend:gallery_my_photos')
    except Exception as e:
        messages.error(request, f"Error deleting photo: {str(e)}")
        return redirect('backend:gallery_detail', photo_id=photo_id)
