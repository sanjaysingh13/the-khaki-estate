/* Project specific Javascript goes here. */
$(document).ready(function() {

    // Load unread notification count for authenticated users
    function loadNotificationCount() {
        if ($('#notification-badge').length > 0) {
            $.ajax({
                url: '/backend/notifications/?format=json',
                method: 'GET',
                dataType: 'json',
                success: function(data) {
                    try {
                        let unreadCount = 0;

                        // Count unread notifications (both 'sent' and 'delivered' are considered unread)
                        if (data && data.notifications && Array.isArray(data.notifications)) {
                            unreadCount = data.notifications.filter(function(notification) {
                                return notification.status === 'sent' || notification.status === 'delivered';
                            }).length;
                        }

                        console.log('Notification count loaded:', unreadCount);

                        const badge = $('#notification-badge');
                        if (unreadCount > 0) {
                            badge.text(unreadCount).show();
                        } else {
                            badge.hide();
                        }
                    } catch (e) {
                        console.log('Error parsing notification count:', e);
                    }
                },
                error: function(xhr, status, error) {
                    console.log('Failed to load notification count:', error);
                }
            });
        }
    }

    // Load notification count on page load
    loadNotificationCount();

    // Refresh notification count every 30 seconds
    setInterval(loadNotificationCount, 30000);

    /**
     * Enhanced notification handling - Auto-mark as read when notification center is accessed
     * This provides a better UX by automatically clearing the notification badge
     * when users visit their notification center
     */

    // Function to mark all notifications as read and clear the badge
    function markAllNotificationsRead() {
        return fetch('/backend/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Immediately clear the notification badge
                    $('#notification-badge').hide();
                    console.log('Notifications marked as read:', data.marked_count);
                } else {
                    console.log('Failed to mark notifications as read:', data.message);
                }
                return data;
            })
            .catch(error => {
                console.log('Error marking notifications as read:', error);
            });
    }

    // CSRF token not needed for mark-all-read endpoint (uses @csrf_exempt)

    // Auto-mark notifications as read when user clicks on notification bell/link
    $(document).on('click', 'a[href*="/backend/notifications"]', function(e) {
        // Only auto-mark for the main notifications page, not filtered views
        const href = $(this).attr('href');
        if (href === '/backend/notifications/' || href.endsWith('/backend/notifications/')) {
            markAllNotificationsRead();
        }
    });

    // If we're currently on the notifications page, mark all as read immediately
    if (window.location.pathname === '/backend/notifications/' ||
        window.location.pathname.endsWith('/backend/notifications/')) {
        // Small delay to ensure page is fully loaded
        setTimeout(function() {
            markAllNotificationsRead();
        }, 500);
    }


});