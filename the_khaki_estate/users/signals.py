"""
User-related Django signals for The Khaki Estate.

These signals handle automatic creation of Resident profiles
and other user-related operations.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_resident_profile(sender, instance, created, **kwargs):
    """
    Signal to create a Resident profile when a User is created.

    This acts as a backup for cases where the extended signup form
    doesn't create the Resident profile (e.g., admin-created users,
    social auth users, or legacy users).

    NOTE: This signal is disabled for staff users to prevent conflicts.
    """
    # STRICT CONDITIONS: Only create for newly created users with resident type
    if not created:
        return  # Skip for user updates

    if instance.user_type != "resident":
        return  # Skip for non-resident users

    # Import here to avoid circular imports
    from the_khaki_estate.backend.models import Resident
    from the_khaki_estate.backend.models import Staff

    # SAFETY CHECKS: Multiple conditions to prevent unwanted creation
    try:
        # Check 1: Does user already have a resident profile?
        if hasattr(instance, "resident") and instance.resident:
            return  # Already has resident profile
    except Resident.DoesNotExist:
        pass  # No resident profile, continue

    try:
        # Check 2: Does user have a staff profile? (Should never happen for residents)
        if hasattr(instance, "staff") and instance.staff:
            return  # Has staff profile, don't create resident profile
    except Staff.DoesNotExist:
        pass  # No staff profile, continue

    # Check 3: Is this being called from a signup form context?
    # If user has proper email/name, assume signup form will handle profile creation
    if instance.email and (instance.first_name or instance.last_name or instance.name):
        return  # Signup form will handle this

    # Only create for admin-created users or edge cases
    try:
        Resident.objects.create(
            user=instance,
            flat_number="0000",  # Placeholder - user needs to update
            phone_number="0000000000",  # Placeholder - user needs to update
            resident_type="owner",  # Default type
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
            is_committee_member=False,
        )
    except Exception as e:
        # Log the error but don't break user creation
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Failed to create Resident profile for user {instance.username}: {e}",
        )


@receiver(post_save, sender=User)
def update_user_name(sender, instance, created, **kwargs):
    """
    Signal to update user's name field when first_name or last_name changes.

    This ensures the 'name' field stays in sync with first_name and last_name.
    """
    if not created and (instance.first_name or instance.last_name):
        # Update name field if first_name or last_name are set
        full_name = f"{instance.first_name} {instance.last_name}".strip()
        if full_name and instance.name != full_name:
            # Avoid infinite loop by checking if name actually changed
            instance.name = full_name
            # Use update to avoid triggering signals again
            User.objects.filter(pk=instance.pk).update(name=full_name)
