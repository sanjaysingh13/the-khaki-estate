"""
Management command to create designated residents for booking approvals.

This command creates the stub users required for the booking approval system:
- sanjaysingh13: Designated for Community Hall approvals
- ajoykumar: Designated for Garden approvals

These users follow the requirement specified in the user query.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from the_khaki_estate.backend.models import Resident

User = get_user_model()


class Command(BaseCommand):
    """
    Create designated residents for booking approval workflow.
    
    This command creates the specific residents mentioned in the requirements:
    - sanjaysingh13: Handles Community Hall bookings
    - ajoykumar: Handles Garden bookings
    """
    help = 'Create designated residents for booking approval workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if users already exist',
        )

    def handle(self, *args, **options):
        """
        Create the designated residents with proper profiles and settings.
        
        The command creates:
        1. User accounts with resident type
        2. Resident profiles with appropriate settings
        3. Notification preferences for booking approvals
        """
        force = options['force']
        
        # Define the designated residents as specified in requirements
        designated_residents = [
            {
                'username': 'sanjaysingh13',
                'email': 'sanjaysingh13@example.com',
                'first_name': 'Sanjay',
                'last_name': 'Singh',
                'name': 'Sanjay Singh',
                'areas_responsible': ['Community Hall', 'Community Center'],
                'flat_number': 'A101',
                'phone_number': '+919876543210',
                'resident_type': 'owner',
                'is_committee_member': True,  # Give committee access for oversight
            },
            {
                'username': 'ajoykumar',
                'email': 'ajoykumar@example.com',
                'first_name': 'Ajoy',
                'last_name': 'Kumar',
                'name': 'Ajoy Kumar',
                'areas_responsible': ['Garden', 'Garden Area'],
                'flat_number': 'B205',
                'phone_number': '+919876543211',
                'resident_type': 'owner',
                'is_committee_member': True,  # Give committee access for oversight
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for resident_data in designated_residents:
            username = resident_data['username']
            areas = resident_data.pop('areas_responsible')
            
            try:
                with transaction.atomic():
                    # Check if user already exists
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': resident_data['email'],
                            'first_name': resident_data['first_name'],
                            'last_name': resident_data['last_name'],
                            'name': resident_data['name'],
                            'user_type': 'resident',
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ Created user: {username}")
                        )
                    else:
                        if force:
                            # Update existing user
                            user.email = resident_data['email']
                            user.first_name = resident_data['first_name']
                            user.last_name = resident_data['last_name']
                            user.name = resident_data['name']
                            user.user_type = 'resident'
                            user.is_active = True
                            user.save()
                            updated_count += 1
                            self.stdout.write(
                                self.style.WARNING(f"🔄 Updated user: {username}")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"⚠️  User already exists: {username}")
                            )
                            continue
                    
                    # Create or update resident profile
                    resident_profile, profile_created = Resident.objects.get_or_create(
                        user=user,
                        defaults={
                            'flat_number': resident_data['flat_number'],
                            'phone_number': resident_data['phone_number'],
                            'resident_type': resident_data['resident_type'],
                            'is_committee_member': resident_data['is_committee_member'],
                            'email_notifications': True,
                            'sms_notifications': True,
                            'urgent_only': False,
                        }
                    )
                    
                    if not profile_created and force:
                        # Update existing profile
                        resident_profile.flat_number = resident_data['flat_number']
                        resident_profile.phone_number = resident_data['phone_number']
                        resident_profile.resident_type = resident_data['resident_type']
                        resident_profile.is_committee_member = resident_data['is_committee_member']
                        resident_profile.email_notifications = True
                        resident_profile.sms_notifications = True
                        resident_profile.urgent_only = False
                        resident_profile.save()
                    
                    # Display areas of responsibility
                    areas_str = ', '.join(areas)
                    self.stdout.write(
                        f"   📍 Areas responsible: {areas_str}"
                    )
                    self.stdout.write(
                        f"   🏠 Flat: {resident_data['flat_number']}"
                    )
                    self.stdout.write(
                        f"   📧 Email: {resident_data['email']}"
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating {username}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"✅ Designated residents setup complete!"))
        self.stdout.write(f"   Created: {created_count} users")
        self.stdout.write(f"   Updated: {updated_count} users")
        self.stdout.write("\n📋 Booking Approval Areas:")
        self.stdout.write("   • sanjaysingh13 → Community Hall, Community Center")
        self.stdout.write("   • ajoykumar → Garden, Garden Area")
        self.stdout.write("\n🔔 Both users have:")
        self.stdout.write("   • Email notifications enabled")
        self.stdout.write("   • SMS notifications enabled")
        self.stdout.write("   • Committee member access")
        self.stdout.write("   • Owner resident type")
        
        # Test the setup
        self.stdout.write("\n🧪 Testing designated approver logic...")
        from the_khaki_estate.backend.models import CommonArea, Booking
        from datetime import date, time
        
        # Create test common areas if they don't exist
        test_areas = [
            {'name': 'Community Hall', 'description': 'Large hall for events'},
            {'name': 'Garden', 'description': 'Outdoor garden area'},
        ]
        
        for area_data in test_areas:
            area, created = CommonArea.objects.get_or_create(
                name=area_data['name'],
                defaults=area_data
            )
            if created:
                self.stdout.write(f"   📍 Created test area: {area.name}")
        
        # Test the booking model logic
        community_hall = CommonArea.objects.filter(name='Community Hall').first()
        garden = CommonArea.objects.filter(name='Garden').first()
        
        if community_hall and garden:
            # Test designated approver assignment
            test_booking = Booking(
                common_area=community_hall,
                resident=User.objects.get(username='sanjaysingh13'),
                booking_date=date.today(),
                start_time=time(10, 0),
                end_time=time(12, 0),
                purpose='Test booking'
            )
            
            approver = test_booking.get_designated_approver()
            if approver and approver.username == 'sanjaysingh13':
                self.stdout.write("   ✅ Community Hall → sanjaysingh13 (correct)")
            else:
                self.stdout.write("   ❌ Community Hall → approver assignment failed")
            
            test_booking.common_area = garden
            approver = test_booking.get_designated_approver()
            if approver and approver.username == 'ajoykumar':
                self.stdout.write("   ✅ Garden → ajoykumar (correct)")
            else:
                self.stdout.write("   ❌ Garden → approver assignment failed")
        
        self.stdout.write("\n🎉 Designated residents are ready for booking approvals!")
