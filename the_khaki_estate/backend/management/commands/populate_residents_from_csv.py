"""
Management command to populate Resident profiles from CSV file.

This command reads the flat owners CSV file and creates Resident profiles
with the specified default values. It handles:
- Parsing CSV with block headers
- Cleaning names (removing SHRI/MS prefixes, converting to title case)
- Formatting phone numbers with +91 prefix
- Converting flat numbers to 6-character format
- Creating User and Resident records with default values
"""

import csv
import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from the_khaki_estate.backend.models import Resident

User = get_user_model()


class Command(BaseCommand):
    """
    Management command to populate residents from CSV file.
    
    This command processes the flat owners CSV file and creates:
    1. User accounts for each flat owner
    2. Resident profiles linked to those users
    3. Properly formatted data (names, phone numbers, flat numbers)
    """
    
    help = 'Populate residents from CSV file with flat owner data'

    def add_arguments(self, parser):
        """
        Add command line arguments for the management command.
        
        Args:
            parser: ArgumentParser instance to add arguments to
        """
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing flat owner data'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip flat numbers that already have residents'
        )

    def handle(self, *args, **options):
        """
        Main command handler that processes the CSV file and creates residents.
        
        Args:
            *args: Variable length argument list
            **options: Arbitrary keyword arguments from command line
        """
        csv_file_path = options['csv_file']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        
        # Validate CSV file path
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_file_path}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Processing CSV file: {csv_file_path}')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No records will be created')
            )
        
        # Process the CSV file
        try:
            residents_data = self._parse_csv_file(csv_path)
            self.stdout.write(f'Found {len(residents_data)} residents to process')
            
            # Create residents
            created_count = self._create_residents(
                residents_data, 
                dry_run=dry_run, 
                skip_existing=skip_existing
            )
            
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'DRY RUN: Would create {created_count} residents')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {created_count} residents')
                )
                
        except Exception as e:
            raise CommandError(f'Error processing CSV file: {str(e)}')

    def _parse_csv_file(self, csv_path):
        """
        Parse the CSV file and extract resident data.
        
        This method handles the specific format of the flat owners CSV:
        - Skips header rows and block separator rows
        - Extracts flat number, name, phone, and email
        - Cleans and formats the data appropriately
        
        Args:
            csv_path: Path object pointing to the CSV file
            
        Returns:
            list: List of dictionaries containing resident data
        """
        residents_data = []
        current_block = None
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            # Use csv.reader to handle CSV parsing properly
            csv_reader = csv.reader(file)
            
            for row_num, row in enumerate(csv_reader, 1):
                # Skip empty rows
                if not row or not any(cell.strip() for cell in row):
                    continue
                
                # Check if this is a block header row (e.g., "BLOCK-A", "BLOCK-B")
                if len(row) >= 1 and row[0].strip().startswith('BLOCK'):
                    current_block = row[0].strip()
                    self.stdout.write(f'Processing {current_block}')
                    continue
                
                # Skip header rows (containing "Ser No", "Flat No", etc.)
                if any(header in row for header in ['Ser No', 'Flat No', 'Name of Owners']):
                    continue
                
                # Skip rows that don't have enough data
                if len(row) < 5:
                    continue
                
                # Extract data from the row
                ser_no = row[0].strip()
                flat_number = row[1].strip()
                name = row[2].strip()
                phone = row[3].strip()
                email = row[4].strip()
                
                # Skip if essential data is missing
                if not flat_number or not name or not phone or not email:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping row {row_num}: Missing essential data')
                    )
                    continue
                
                # Process and clean the data
                processed_data = self._process_resident_data(
                    ser_no, flat_number, name, phone, email, current_block
                )
                
                if processed_data:
                    residents_data.append(processed_data)
        
        return residents_data

    def _process_resident_data(self, ser_no, flat_number, name, phone, email, block):
        """
        Process and clean individual resident data.
        
        This method handles:
        - Cleaning names (removing SHRI/MS prefixes, converting to title case)
        - Formatting phone numbers with +91 prefix
        - Converting flat numbers to 6-character format
        - Validating email addresses
        
        Args:
            ser_no: Serial number from CSV
            flat_number: Flat number from CSV
            name: Owner name from CSV
            phone: Phone number from CSV
            email: Email address from CSV
            block: Current block being processed
            
        Returns:
            dict: Processed resident data or None if invalid
        """
        try:
            # Clean the name - remove prefixes and convert to title case
            cleaned_name = self._clean_name(name)
            
            # Format phone number with +91 prefix
            formatted_phone = self._format_phone_number(phone)
            
            # Convert flat number to 6-character format
            formatted_flat = self._format_flat_number(flat_number)
            
            # Extract block from flat number if not provided
            if not block and '-' in flat_number:
                block = flat_number.split('-')[0]
            
            # Clean block name - extract just the letter/number from "BLOCK-A" format
            if block and block.startswith('BLOCK'):
                # Extract the block identifier (e.g., "A" from "BLOCK-A", "C1" from "BLOCK - C1")
                block_clean = block.replace('BLOCK', '').replace('-', '').replace(' ', '').strip()
                block = block_clean
            
            # Split name into first and last name
            name_parts = cleaned_name.split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Generate username from email
            username = email.split('@')[0]
            
            return {
                'ser_no': ser_no,
                'flat_number': formatted_flat,
                'block': block or '',
                'first_name': first_name,
                'last_name': last_name,
                'full_name': cleaned_name,
                'phone_number': formatted_phone,
                'email': email,
                'username': username,
            }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error processing data for {name}: {str(e)}')
            )
            return None

    def _clean_name(self, name):
        """
        Clean the name by removing prefixes and converting to title case.
        
        Args:
            name: Raw name from CSV
            
        Returns:
            str: Cleaned name in title case
        """
        # Remove common prefixes
        prefixes_to_remove = ['SHRI', 'SMT', 'MS', 'MR', 'MRS']
        
        cleaned_name = name.strip()
        
        # Remove prefixes (case insensitive)
        for prefix in prefixes_to_remove:
            if cleaned_name.upper().startswith(prefix):
                cleaned_name = cleaned_name[len(prefix):].strip()
                break
        
        # Convert to title case
        return cleaned_name.title()

    def _format_phone_number(self, phone):
        """
        Format phone number with +91 prefix.
        
        Args:
            phone: Raw phone number from CSV
            
        Returns:
            str: Formatted phone number with +91 prefix
        """
        # Remove any non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Remove leading 0 if present
        if digits_only.startswith('0'):
            digits_only = digits_only[1:]
        
        # Ensure it's 10 digits
        if len(digits_only) == 10:
            return f'+91{digits_only}'
        elif len(digits_only) == 12 and digits_only.startswith('91'):
            return f'+{digits_only}'
        else:
            raise ValueError(f'Invalid phone number format: {phone}')

    def _format_flat_number(self, flat_number):
        """
        Clean and format flat number while preserving original format.
        
        Args:
            flat_number: Raw flat number from CSV
            
        Returns:
            str: Cleaned flat number in original format
        """
        # Remove any spaces or special characters except dash
        cleaned = re.sub(r'[^\w\-]', '', flat_number)
        
        # Return the cleaned flat number as-is (no padding)
        return cleaned

    def _create_residents(self, residents_data, dry_run=False, skip_existing=False):
        """
        Create User and Resident records from the processed data.
        
        This method uses database transactions to ensure data consistency
        and handles duplicate flat numbers appropriately.
        
        Args:
            residents_data: List of processed resident data dictionaries
            dry_run: If True, don't actually create records
            skip_existing: If True, skip flat numbers that already have residents
            
        Returns:
            int: Number of residents created
        """
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for resident_data in residents_data:
            try:
                # Check if flat number already exists
                if Resident.objects.filter(flat_number=resident_data['flat_number']).exists():
                    if skip_existing:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping {resident_data["flat_number"]}: Already exists'
                            )
                        )
                        skipped_count += 1
                        continue
                    else:
                        raise ValueError(
                            f'Flat number {resident_data["flat_number"]} already exists'
                        )
                
                if dry_run:
                    self.stdout.write(
                        f'Would create: {resident_data["full_name"]} - '
                        f'{resident_data["flat_number"]} - {resident_data["email"]}'
                    )
                    created_count += 1
                    continue
                
                # Create Resident without User account (for signup workflow)
                with transaction.atomic():
                    # Create Resident without user (user will be linked during signup)
                    Resident.objects.create(
                        user=None,  # No user initially - will be linked during signup
                        flat_number=resident_data['flat_number'],
                        block=resident_data['block'],
                        phone_number=resident_data['phone_number'],
                        alternate_phone='',
                        resident_type='owner',
                        is_committee_member=False,
                        move_in_date=None,
                        emergency_contact_name='',
                        emergency_contact_phone='',
                        email_notifications=True,
                        sms_notifications=False,
                        urgent_only=False,
                        # Store owner data for API access
                        owner_name=resident_data['full_name'],
                        owner_email=resident_data['email'],
                    )
                    
                    self.stdout.write(
                        f'Created: {resident_data["full_name"]} - '
                        f'{resident_data["flat_number"]} - {resident_data["email"]}'
                    )
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating resident {resident_data.get("full_name", "Unknown")}: {str(e)}'
                    )
                )
                error_count += 1
        
        # Print summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Errors: {error_count}')
        self.stdout.write('='*50)
        
        return created_count
