"""
Management command to create Resident profiles for existing users.

This command is useful for:
1. Migrating existing users to the new system
2. Creating profiles for admin-created users
3. Fixing missing resident profiles

Usage:
    python manage.py create_resident_profiles
    python manage.py create_resident_profiles --update-existing
    python manage.py create_resident_profiles --dry-run
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from the_khaki_estate.backend.models import Resident

User = get_user_model()


class Command(BaseCommand):
    help = "Create Resident profiles for users who don't have them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating profiles",
        )
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update existing resident profiles with placeholder data",
        )
        parser.add_argument(
            "--flat-prefix",
            type=str,
            default="0",
            help="Prefix for auto-generated flat numbers (default: 0)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        update_existing = options["update_existing"]
        flat_prefix = options["flat_prefix"]

        self.stdout.write(self.style.SUCCESS("Starting Resident profile creation..."))

        # Find users without resident profiles
        users_without_profiles = []
        users_with_placeholder_profiles = []

        for user in User.objects.all():
            try:
                resident = user.resident
                # Check if this is a placeholder profile
                if (
                    resident.flat_number == "0000"
                    or resident.phone_number == "0000000000"
                ):
                    users_with_placeholder_profiles.append(user)
            except Resident.DoesNotExist:
                users_without_profiles.append(user)

        self.stdout.write(
            f"Found {len(users_without_profiles)} users without resident profiles",
        )
        self.stdout.write(
            f"Found {len(users_with_placeholder_profiles)} users with placeholder profiles",
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made")
            )

        # Create profiles for users without them
        created_count = 0
        with transaction.atomic():
            for i, user in enumerate(users_without_profiles, 1):
                flat_number = f"{flat_prefix}{i:03d}"  # e.g., 0001, 0002, etc.

                if dry_run:
                    self.stdout.write(
                        f"Would create profile for {user.username} "
                        f"(flat: {flat_number})",
                    )
                else:
                    try:
                        Resident.objects.create(
                            user=user,
                            flat_number=flat_number,
                            phone_number="0000000000",  # Placeholder
                            resident_type="owner",  # Default
                            email_notifications=True,
                            sms_notifications=False,
                            urgent_only=False,
                            is_committee_member=False,
                        )
                        created_count += 1
                        self.stdout.write(
                            f"Created profile for {user.username} "
                            f"(flat: {flat_number})",
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to create profile for {user.username}: {e}",
                            ),
                        )

        # Update placeholder profiles if requested
        updated_count = 0
        if update_existing and users_with_placeholder_profiles:
            self.stdout.write("\nUpdating placeholder profiles...")

            for i, user in enumerate(users_with_placeholder_profiles, 1):
                new_flat_number = f"{flat_prefix}{i + len(users_without_profiles):03d}"

                if dry_run:
                    self.stdout.write(
                        f"Would update profile for {user.username} "
                        f"(new flat: {new_flat_number})",
                    )
                else:
                    try:
                        resident = user.resident
                        if resident.flat_number == "0000":
                            resident.flat_number = new_flat_number
                        if resident.phone_number == "0000000000":
                            resident.phone_number = "0000000000"  # Keep placeholder
                        resident.save()
                        updated_count += 1
                        self.stdout.write(
                            f"Updated profile for {user.username} "
                            f"(flat: {resident.flat_number})",
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to update profile for {user.username}: {e}",
                            ),
                        )

        # Summary
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nCompleted! Created {created_count} new profiles, "
                    f"updated {updated_count} existing profiles.",
                ),
            )
            if created_count > 0 or updated_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "\nIMPORTANT: Users with placeholder data (flat: 0xxx, "
                        "phone: 0000000000) need to update their profiles!",
                    ),
                )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nDRY RUN COMPLETE: Would create {len(users_without_profiles)} "
                    f"profiles and update {len(users_with_placeholder_profiles) if update_existing else 0} profiles.",
                ),
            )
