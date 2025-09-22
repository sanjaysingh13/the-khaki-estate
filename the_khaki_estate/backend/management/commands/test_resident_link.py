from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from the_khaki_estate.backend.models import Resident

User = get_user_model()


class Command(BaseCommand):
    help = 'Test linking a resident to a user account'

    def handle(self, *args, **options):
        # Find the resident
        try:
            resident = Resident.objects.get(flat_number='A-1001')
            self.stdout.write(f'Found resident: {resident}')
            self.stdout.write(f'Resident user: {resident.user}')
            self.stdout.write(f'Resident type: {resident.resident_type}')
            self.stdout.write(f'Owner name: {resident.owner_name}')
            self.stdout.write(f'Owner email: {resident.owner_email}')
        except Resident.DoesNotExist:
            self.stdout.write(self.style.ERROR('Resident A-1001 not found'))
            return

        # Create or get the user
        username = 'sanjaysingh131066'
        password = 'Decadent13'
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Found existing user: {user}')
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=resident.owner_email,
                password=password,
                first_name=resident.owner_name.split(' ')[0] if resident.owner_name else '',
                last_name=' '.join(resident.owner_name.split(' ')[1:]) if resident.owner_name and ' ' in resident.owner_name else '',
                user_type='resident'
            )
            self.stdout.write(f'Created new user: {user}')

        # Link the resident to the user
        if resident.user is None:
            resident.user = user
            resident.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully linked resident {resident.flat_number} to user {user.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Resident {resident.flat_number} is already linked to user {resident.user.username}'))

        # Verify the link
        resident.refresh_from_db()
        self.stdout.write(f'Resident user after linking: {resident.user}')
        self.stdout.write(f'User resident: {user.resident}')
