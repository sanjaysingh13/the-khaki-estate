"""
Django management command to populate MaintenanceCategory table with representative categories.
This command creates common maintenance categories that residents can select from.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from the_khaki_estate.backend.models import MaintenanceCategory


class Command(BaseCommand):
    """
    Management command to populate the MaintenanceCategory table with representative categories.

    Usage: python manage.py populate_maintenance_categories
    """

    help = "Populate MaintenanceCategory table with representative categories"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing categories before adding new ones",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what categories would be created without actually creating them",
        )

    def handle(self, *args, **options):
        """
        Main command handler that creates maintenance categories.

        Categories are organized by priority level and estimated resolution time:
        - Priority 1 (Low): Routine maintenance, cosmetic issues
        - Priority 2 (Medium): Standard repairs, minor inconveniences
        - Priority 3 (High): Major issues affecting daily life
        - Priority 4 (Emergency): Safety hazards, complete system failures
        """

        # Define comprehensive list of maintenance categories
        # Each category includes: name, priority_level, estimated_resolution_hours
        categories_data = [
            # EMERGENCY CATEGORIES (Priority 4) - Immediate response required
            {
                "name": "Electrical Emergency",
                "priority_level": 4,
                "estimated_resolution_hours": 2,
            },
            {
                "name": "Plumbing Emergency",
                "priority_level": 4,
                "estimated_resolution_hours": 4,
            },
            {
                "name": "Gas Leak",
                "priority_level": 4,
                "estimated_resolution_hours": 1,
            },
            {
                "name": "Fire Safety",
                "priority_level": 4,
                "estimated_resolution_hours": 2,
            },
            {
                "name": "Security Breach",
                "priority_level": 4,
                "estimated_resolution_hours": 1,
            },
            {
                "name": "Structural Damage",
                "priority_level": 4,
                "estimated_resolution_hours": 6,
            },
            # HIGH PRIORITY CATEGORIES (Priority 3) - Major issues
            {
                "name": "Electrical Issues",
                "priority_level": 3,
                "estimated_resolution_hours": 8,
            },
            {
                "name": "Plumbing Issues",
                "priority_level": 3,
                "estimated_resolution_hours": 12,
            },
            {
                "name": "Air Conditioning",
                "priority_level": 3,
                "estimated_resolution_hours": 24,
            },
            {
                "name": "Heating System",
                "priority_level": 3,
                "estimated_resolution_hours": 24,
            },
            {
                "name": "Water Supply",
                "priority_level": 3,
                "estimated_resolution_hours": 12,
            },
            {
                "name": "Elevator Issues",
                "priority_level": 3,
                "estimated_resolution_hours": 24,
            },
            {
                "name": "Door/Window Issues",
                "priority_level": 3,
                "estimated_resolution_hours": 24,
            },
            # MEDIUM PRIORITY CATEGORIES (Priority 2) - Standard maintenance
            {
                "name": "Appliance Repair",
                "priority_level": 2,
                "estimated_resolution_hours": 48,
            },
            {
                "name": "Carpentry Work",
                "priority_level": 2,
                "estimated_resolution_hours": 72,
            },
            {
                "name": "Painting Work",
                "priority_level": 2,
                "estimated_resolution_hours": 96,
            },
            {
                "name": "Flooring Issues",
                "priority_level": 2,
                "estimated_resolution_hours": 72,
            },
            {
                "name": "Pest Control",
                "priority_level": 2,
                "estimated_resolution_hours": 24,
            },
            {
                "name": "Cleaning Services",
                "priority_level": 2,
                "estimated_resolution_hours": 8,
            },
            {
                "name": "Garden/Landscaping",
                "priority_level": 2,
                "estimated_resolution_hours": 48,
            },
            {
                "name": "Common Area Issues",
                "priority_level": 2,
                "estimated_resolution_hours": 48,
            },
            {
                "name": "Parking Issues",
                "priority_level": 2,
                "estimated_resolution_hours": 24,
            },
            # LOW PRIORITY CATEGORIES (Priority 1) - Routine maintenance
            {
                "name": "General Maintenance",
                "priority_level": 1,
                "estimated_resolution_hours": 168,  # 1 week
            },
            {
                "name": "Cosmetic Issues",
                "priority_level": 1,
                "estimated_resolution_hours": 120,
            },
            {
                "name": "Minor Repairs",
                "priority_level": 1,
                "estimated_resolution_hours": 72,
            },
            {
                "name": "Preventive Maintenance",
                "priority_level": 1,
                "estimated_resolution_hours": 168,
            },
            {
                "name": "Other",
                "priority_level": 1,
                "estimated_resolution_hours": 72,
            },
        ]

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No categories will be created"),
            )
            self.stdout.write("\nCategories that would be created:")
            for category_data in categories_data:
                self.stdout.write(
                    f"  - {category_data['name']} "
                    f"(Priority: {category_data['priority_level']}, "
                    f"Est. Resolution: {category_data['estimated_resolution_hours']}h)",
                )
            return

        try:
            with transaction.atomic():
                if options["clear"]:
                    # Clear existing categories
                    deleted_count = MaintenanceCategory.objects.count()
                    MaintenanceCategory.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING(
                            f"Cleared {deleted_count} existing categories"
                        ),
                    )

                # Create categories
                created_count = 0
                updated_count = 0

                for category_data in categories_data:
                    category, created = MaintenanceCategory.objects.get_or_create(
                        name=category_data["name"],
                        defaults={
                            "priority_level": category_data["priority_level"],
                            "estimated_resolution_hours": category_data[
                                "estimated_resolution_hours"
                            ],
                        },
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            f"✅ Created: {category.name} "
                            f"(Priority: {category.priority_level}, "
                            f"Est. Resolution: {category.estimated_resolution_hours}h)",
                        )
                    else:
                        # Update existing category if needed
                        updated = False
                        if category.priority_level != category_data["priority_level"]:
                            category.priority_level = category_data["priority_level"]
                            updated = True
                        if (
                            category.estimated_resolution_hours
                            != category_data["estimated_resolution_hours"]
                        ):
                            category.estimated_resolution_hours = category_data[
                                "estimated_resolution_hours"
                            ]
                            updated = True

                        if updated:
                            category.save()
                            updated_count += 1
                            self.stdout.write(
                                f"🔄 Updated: {category.name} "
                                f"(Priority: {category.priority_level}, "
                                f"Est. Resolution: {category.estimated_resolution_hours}h)",
                            )
                        else:
                            self.stdout.write(
                                f"⚪ Exists: {category.name}",
                            )

                # Summary
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ COMPLETED: {created_count} created, {updated_count} updated",
                    ),
                )
                self.stdout.write(
                    f"Total categories in database: {MaintenanceCategory.objects.count()}",
                )

                # Show priority breakdown
                self.stdout.write("\n📊 Categories by Priority Level:")
                for priority in range(1, 5):
                    count = MaintenanceCategory.objects.filter(
                        priority_level=priority
                    ).count()
                    priority_names = {
                        1: "Low (Routine)",
                        2: "Medium (Standard)",
                        3: "High (Major Issues)",
                        4: "Emergency (Immediate)",
                    }
                    self.stdout.write(
                        f"  Priority {priority} - {priority_names[priority]}: {count} categories"
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error creating categories: {e}"),
            )
            raise e

        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 Maintenance categories have been successfully populated!",
            ),
        )
        self.stdout.write(
            "Residents can now select from these categories when creating maintenance requests.",
        )
