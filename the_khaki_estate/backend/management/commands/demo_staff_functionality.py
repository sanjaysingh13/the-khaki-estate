"""
Django management command to demonstrate the new maintenance staff functionality.
Usage: uv run python manage.py demo_staff_functionality
"""

from datetime import date
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from the_khaki_estate.backend.models import MaintenanceCategory
from the_khaki_estate.backend.models import MaintenanceRequest
from the_khaki_estate.backend.models import Resident
from the_khaki_estate.backend.models import Staff

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to demonstrate maintenance staff functionality.
    Creates sample users, staff, and maintenance requests to show the workflow.
    """

    help = "Demonstrates the new maintenance staff functionality"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="Clean up demo data after running",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(
            self.style.SUCCESS("🚀 Demonstrating Maintenance Staff Functionality"),
        )
        self.stdout.write("=" * 60)

        try:
            self.create_staff_members()
            self.create_test_resident()
            self.create_maintenance_categories()
            self.demonstrate_maintenance_workflow()
            self.show_staff_capabilities()

            self.stdout.write(
                self.style.SUCCESS("\n✅ Demonstration completed successfully!"),
            )

            if options["cleanup"]:
                self.cleanup_demo_data()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error during demonstration: {e}"),
            )
            import traceback

            self.stdout.write(traceback.format_exc())

    def create_staff_members(self):
        """Create different types of staff members."""
        self.stdout.write("\n🔧 Creating Staff Members...")

        # Create facility manager
        fm_user, created = User.objects.get_or_create(
            username="demo_facility_manager",
            defaults={
                "email": "fm@khakiestate.com",
                "name": "John Smith",
                "user_type": "staff",
            },
        )
        if created:
            fm_user.set_password("demo123")
            fm_user.save()

        self.facility_manager, created = Staff.objects.get_or_create(
            user=fm_user,
            defaults={
                "employee_id": "DEMO_FM001",
                "staff_role": "facility_manager",
                "department": "Management",
                "phone_number": "+919876543210",
                "employment_status": "full_time",
                "hire_date": date.today(),
                "can_access_all_maintenance": True,
                "can_assign_requests": True,
                "can_close_requests": True,
                "can_send_announcements": True,
                "work_schedule": "Mon-Fri 9AM-6PM, On-call weekends",
                "is_available_24x7": True,
            },
        )

        # Create electrician
        elec_user, created = User.objects.get_or_create(
            username="demo_electrician",
            defaults={
                "email": "electrician@khakiestate.com",
                "name": "Mike Johnson",
                "user_type": "staff",
            },
        )
        if created:
            elec_user.set_password("demo123")
            elec_user.save()

        self.electrician, created = Staff.objects.get_or_create(
            user=elec_user,
            defaults={
                "employee_id": "DEMO_EL001",
                "staff_role": "electrician",
                "department": "Maintenance",
                "phone_number": "+919876543211",
                "employment_status": "full_time",
                "hire_date": date.today(),
                "can_close_requests": True,
                "work_schedule": "Mon-Fri 8AM-5PM, Emergency on-call",
            },
        )

        # Create accountant
        acc_user, created = User.objects.get_or_create(
            username="demo_accountant",
            defaults={
                "email": "accountant@khakiestate.com",
                "name": "Sarah Wilson",
                "user_type": "staff",
            },
        )
        if created:
            acc_user.set_password("demo123")
            acc_user.save()

        self.accountant, created = Staff.objects.get_or_create(
            user=acc_user,
            defaults={
                "employee_id": "DEMO_AC001",
                "staff_role": "accountant",
                "department": "Finance",
                "phone_number": "+919876543212",
                "employment_status": "full_time",
                "hire_date": date.today(),
                "can_manage_finances": True,
                "can_send_announcements": True,
                "work_schedule": "Mon-Fri 9AM-5PM",
            },
        )

        self.stdout.write(f"   ✅ Facility Manager: {self.facility_manager}")
        self.stdout.write(f"   ✅ Electrician: {self.electrician}")
        self.stdout.write(f"   ✅ Accountant: {self.accountant}")

    def create_test_resident(self):
        """Create a test resident."""
        self.stdout.write("\n🏠 Creating Test Resident...")

        resident_user, created = User.objects.get_or_create(
            username="demo_resident",
            defaults={
                "email": "resident@khakiestate.com",
                "name": "Alice Cooper",
                "user_type": "resident",
            },
        )
        if created:
            resident_user.set_password("demo123")
            resident_user.save()

        self.resident, created = Resident.objects.get_or_create(
            user=resident_user,
            defaults={
                "flat_number": "101",
                "block": "A",
                "phone_number": "+919876543213",
                "resident_type": "owner",
                "move_in_date": date.today() - timedelta(days=365),
            },
        )

        self.stdout.write(f"   ✅ Resident: {self.resident}")

    def create_maintenance_categories(self):
        """Create maintenance categories."""
        self.stdout.write("\n🏷️  Creating Maintenance Categories...")

        self.electrical_category, created = MaintenanceCategory.objects.get_or_create(
            name="Electrical",
            defaults={
                "priority_level": 3,
                "estimated_resolution_hours": 24,
            },
        )

        self.plumbing_category, created = MaintenanceCategory.objects.get_or_create(
            name="Plumbing",
            defaults={
                "priority_level": 3,
                "estimated_resolution_hours": 12,
            },
        )

        self.stdout.write("   ✅ Created categories: Electrical, Plumbing")

    def demonstrate_maintenance_workflow(self):
        """Demonstrate complete maintenance workflow."""
        self.stdout.write("\n🔧 Demonstrating Maintenance Workflow...")

        # 1. Create maintenance request
        request = MaintenanceRequest.objects.create(
            resident=self.resident.user,
            title="Kitchen outlet not working",
            description="The main kitchen outlet stopped working after power outage",
            category=self.electrical_category,
            location=f"Flat {self.resident.flat_number}",
            priority=3,
            status="submitted",
        )

        self.stdout.write(f"   1️⃣  Request created: {request.ticket_number}")

        # 2. Facility manager acknowledges
        request.status = "acknowledged"
        request.save()
        self.stdout.write(f"   2️⃣  Request acknowledged at: {request.acknowledged_at}")

        # 3. Check suitable staff
        suitable_staff = request.get_suitable_staff()
        self.stdout.write(
            f"   🔍 Suitable staff: {suitable_staff.count()} staff members",
        )

        # 4. Assign to electrician
        request.assign_to_staff(self.electrician.user, self.facility_manager.user)
        self.stdout.write(f"   3️⃣  Assigned to: {request.assigned_to.name}")
        self.stdout.write(f"   3️⃣  Assigned by: {request.assigned_by.name}")
        self.stdout.write(f"   3️⃣  Status: {request.status}")

        # 5. Start work
        request.status = "in_progress"
        request.estimated_cost = Decimal("200.00")
        request.save()
        self.stdout.write(
            f"   4️⃣  Work started, estimated cost: ₹{request.estimated_cost}",
        )

        # 6. Complete work
        request.status = "resolved"
        request.actual_cost = Decimal("180.00")
        request.save()
        self.stdout.write(f"   5️⃣  Work completed, actual cost: ₹{request.actual_cost}")
        self.stdout.write(
            f"   5️⃣  Savings: ₹{request.estimated_cost - request.actual_cost}",
        )

        # 7. Close with feedback
        request.status = "closed"
        request.resident_rating = 5
        request.resident_feedback = "Excellent work! Very professional and clean."
        request.save()
        self.stdout.write(f"   6️⃣  Request closed with {request.resident_rating} stars")

        # Show resolution time
        resolution_time = request.get_resolution_time()
        self.stdout.write(f"   📊 Total resolution time: {resolution_time}")

        self.request = request

    def show_staff_capabilities(self):
        """Show different staff capabilities."""
        self.stdout.write("\n👥 Staff Capabilities Summary...")

        self.stdout.write(
            f"\n🏢 Facility Manager ({self.facility_manager.employee_id}):",
        )
        self.stdout.write(
            f"   ✅ Can access all maintenance: {self.facility_manager.can_access_all_maintenance}",
        )
        self.stdout.write(
            f"   ✅ Can assign requests: {self.facility_manager.can_assign_requests}",
        )
        self.stdout.write(
            f"   ✅ Can close requests: {self.facility_manager.can_close_requests}",
        )
        self.stdout.write(
            f"   ✅ Can send announcements: {self.facility_manager.can_send_announcements}",
        )
        self.stdout.write(
            f"   ❌ Can manage finances: {self.facility_manager.can_manage_finances}",
        )

        self.stdout.write(f"\n⚡ Electrician ({self.electrician.employee_id}):")
        self.stdout.write(
            f"   ✅ Can handle maintenance: {self.electrician.can_handle_maintenance()}",
        )
        self.stdout.write(
            f"   ✅ Can close requests: {self.electrician.can_close_requests}",
        )
        self.stdout.write(
            f"   ❌ Can access all maintenance: {self.electrician.can_access_all_maintenance}",
        )
        self.stdout.write(
            f"   ❌ Can assign requests: {self.electrician.can_assign_requests}",
        )

        self.stdout.write(f"\n💰 Accountant ({self.accountant.employee_id}):")
        self.stdout.write(
            f"   ✅ Can manage finances: {self.accountant.can_manage_finances}",
        )
        self.stdout.write(
            f"   ✅ Can send announcements: {self.accountant.can_send_announcements}",
        )
        self.stdout.write(
            f"   ❌ Can handle maintenance: {self.accountant.can_handle_maintenance()}",
        )
        self.stdout.write(
            f"   ❌ Can assign requests: {self.accountant.can_assign_requests}",
        )

        # Show user type functionality
        self.stdout.write("\n👤 User Type Verification:")
        self.stdout.write(
            f"   Staff user is staff: {self.facility_manager.user.is_staff_member()}",
        )
        self.stdout.write(
            f"   Staff user is resident: {self.facility_manager.user.is_resident()}",
        )
        self.stdout.write(
            f"   Resident user is resident: {self.resident.user.is_resident()}",
        )
        self.stdout.write(
            f"   Resident user is staff: {self.resident.user.is_staff_member()}",
        )

    def cleanup_demo_data(self):
        """Clean up demo data."""
        self.stdout.write("\n🧹 Cleaning up demo data...")

        # Delete in proper order to avoid foreign key constraints
        MaintenanceRequest.objects.filter(ticket_number__contains="MNT-").delete()
        Staff.objects.filter(employee_id__startswith="DEMO_").delete()
        Resident.objects.filter(flat_number="101").delete()
        User.objects.filter(username__startswith="demo_").delete()
        MaintenanceCategory.objects.filter(name__in=["Electrical", "Plumbing"]).delete()

        self.stdout.write("   ✅ Demo data cleaned up")
