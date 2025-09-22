# The Khaki Estate - Technical Documentation

**IMPORTANT: This project uses `uv` as the Python package manager for all dependency management and virtual environment operations.**

**TESTING: This project uses `pytest` for all testing operations instead of Django's built-in test runner.**

## 🚀 Quick Start

### Package Manager
- **Primary Tool**: `uv` (modern Python package manager)
- **Virtual Environment**: Managed by `uv`
- **Dependencies**: `uv.lock` file for reproducible builds

### Development Commands
```bash
# Start development server
uv run python manage.py runserver 8001

# Run migrations
uv run python manage.py migrate

# Run tests
uv run pytest -v

# Install dependencies
uv sync

# Add new dependency
uv add package-name
```

**Version**: 2.3
**Last Updated**: 22nd September, 2025
**Target Audience**: Developers, System Architects, Technical Teams

---

## 📋 Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Enhanced Owner Signup Workflow](#enhanced-owner-signup-workflow-v23)
3. [Database Schema & Models](#database-schema--models)
4. [User Management System](#user-management-system)
5. [Maintenance Staff Architecture](#maintenance-staff-architecture)
6. [Maintenance Request Workflow](#maintenance-request-workflow)
7. [Booking Approval Workflow](#booking-approval-workflow)
8. [Permission & Access Control](#permission--access-control)
9. [Forms & Validation](#forms--validation)
10. [Views & URL Patterns](#views--url-patterns)
11. [Tasks & Background Processing](#tasks--background-processing)
12. [Signals & Event Handling](#signals--event-handling)
13. [Admin Interface](#admin-interface)
14. [Testing Strategy](#testing-strategy)
15. [API Design Patterns](#api-design-patterns)
16. [Performance Considerations](#performance-considerations)
17. [Deployment & Migration Guide](#deployment--migration-guide)

---

## 🏗️ System Architecture Overview

### Technology Stack
- **Backend Framework**: Django 5.2.6
- **Database**: PostgreSQL with Neo4j integration (database: 'cdranalysis')
- **Task Queue**: Celery with Redis
- **Package Manager**: uv (modern Python package management)
- **Testing**: pytest with factory_boy
- **Admin Interface**: Enhanced Django Admin
- **Frontend**: Bootstrap 5, Font Awesome, JavaScript

### Core Components
```
┌─────────────────────────────────────────────────────────────┐
│                    THE KHAKI ESTATE                         │
│                 Management System v2.0                     │
├─────────────────────────────────────────────────────────────┤
│  Users Module          │  Backend Module                    │
│  ├── User (Enhanced)   │  ├── Resident                     │
│  ├── Staff (NEW)       │  ├── Staff (NEW)                  │
│  └── Forms             │  ├── MaintenanceRequest (Enhanced) │
│                        │  ├── Announcement                  │
│                        │  ├── Booking                       │
│                        │  ├── Event                         │
│                        │  └── Notification                  │
├─────────────────────────────────────────────────────────────┤
│  Admin Interface       │  Tasks & Signals                   │
│  ├── UserAdmin         │  ├── notification_tasks.py         │
│  ├── StaffAdmin (NEW)  │  ├── maintenance_signals.py        │
│  └── Enhanced Models   │  └── celery_app.py                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 👤 Enhanced Owner Signup Workflow (v2.3)

### **CSV-Based Owner Registration System**

**Key Design Principles:**
- **Pre-populated Owner Data**: Owners are imported from CSV before user account creation
- **Dynamic Form Behavior**: Signup form adapts based on user type and resident type selections
- **Auto-population**: Owner details are automatically filled when flat number is selected
- **Seamless Linking**: New user accounts are linked to existing owner records from CSV

### **CSV Data Import Process**

```python
# Management Command: populate_residents_from_csv
class Command(BaseCommand):
    """
    Import owner data from CSV file and create Resident records without User accounts.
    
    Workflow:
    1. Parse CSV with interleaved block headers
    2. Clean and normalize data (names, phone numbers, flat numbers)
    3. Create Resident records with user=None
    4. Store owner_name and owner_email for later linking
    """
    
    def _process_resident_data(self, ser_no, flat_number, name, phone, email, block):
        """Clean and normalize resident data from CSV."""
        # Clean name - remove appellations (SHRI, MS) and normalize case
        cleaned_name = self._clean_name(name)
        
        # Format phone number - add +91 prefix
        formatted_phone = self._format_phone_number(phone)
        
        # Extract block identifier from "BLOCK-A" format
        block_clean = block.replace('BLOCK', '').replace('-', '').replace(' ', '').strip()
        
        return {
            'flat_number': flat_number,  # Keep original format (A-101, C1-201)
            'full_name': cleaned_name,
            'phone_number': formatted_phone,
            'email': email.lower(),
            'block': block_clean,
        }
    
    def _create_residents(self, residents_data, dry_run=False):
        """Create Resident records without User accounts."""
        for resident_data in residents_data:
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
```

### **Enhanced Resident Model**

```python
class Resident(models.Model):
    """
    Enhanced Resident model supporting CSV-imported owners and dynamic user linking.
    """
    
    # Core relationship - nullable to support CSV-imported owners
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name="resident", 
        null=True, 
        blank=True
    )
    
    # Property details
    flat_number = models.CharField(max_length=10)  # Supports A-101, C1-201 formats
    block = models.CharField(max_length=5, blank=True)  # Supports A, C1 formats
    
    # Contact information
    phone_number = models.CharField(max_length=13)
    alternate_phone = models.CharField(max_length=13, blank=True)
    
    # Owner data fields for CSV-created residents (before user association)
    owner_name = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Owner name from CSV data"
    )
    owner_email = models.EmailField(
        blank=True, 
        help_text="Owner email from CSV data"
    )
    
    # Resident classification
    resident_type = models.CharField(
        max_length=10,
        choices=RESIDENT_TYPES,
        default="owner",
    )
    
    # Additional fields
    is_committee_member = models.BooleanField(default=False)
    move_in_date = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=13, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    urgent_only = models.BooleanField(default=False)
    
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} - {self.flat_number}"
        else:
            return f"{self.owner_name or 'Unknown'} - {self.flat_number}"
```

### **Dynamic Signup Form Architecture**

```python
class NewUserSignupForm(SignupForm):
    """
    Enhanced signup form with dynamic field behavior for owner registration.
    
    Workflow:
    1. User selects "Resident" → "Owner"
    2. Flat number field appears with autocomplete
    3. User selects flat → Owner details auto-populate
    4. User fills remaining fields and submits
    5. User account created and linked to existing Resident record
    """
    
    # Field ordering optimized for workflow
    field_order = [
        'user_type', 'resident_type', 'flat_number', 'email', 
        'first_name', 'last_name', 'block', 'phone_number',
        'emergency_contact_name', 'emergency_contact_phone', 
        'move_in_date', 'username', 'password1', 'password2'
    ]
    
    # Hidden field to store resident_id for existing owners
    resident_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_resident_id'}),
    )
    
    def clean_flat_number(self):
        """Validate flat number and handle existing owner linking."""
        user_type = self.cleaned_data.get("user_type")
        resident_type = self.cleaned_data.get("resident_type")
        flat_number = self.cleaned_data.get("flat_number")
        
        if user_type == "resident":
            if not flat_number:
                raise forms.ValidationError("Flat number is required for residents.")
            
            # Get resident_id from form data
            resident_id = self.cleaned_data.get("resident_id")
            if not resident_id and hasattr(self, 'data'):
                resident_id = self.data.get("resident_id")
                if resident_id:
                    try:
                        resident_id = int(resident_id)
                    except (ValueError, TypeError):
                        resident_id = None
            
            if not resident_id:  # New resident (tenant/family)
                # Check for existing residents of same type
                existing_residents = Resident.objects.filter(
                    flat_number=flat_number,
                    resident_type=resident_type
                )
                if existing_residents.exists():
                    raise forms.ValidationError(
                        f"This flat number already has a {resident_type}. "
                        "Please contact management if this is an error."
                    )
            else:  # Existing owner linking
                try:
                    existing_resident = Resident.objects.get(id=resident_id)
                    if existing_resident.flat_number != flat_number:
                        raise forms.ValidationError(
                            "Selected flat number doesn't match the resident record."
                        )
                    if existing_resident.user is not None:
                        raise forms.ValidationError(
                            "This resident record is already linked to a user account."
                        )
                except Resident.DoesNotExist:
                    raise forms.ValidationError("Invalid resident record selected.")
        
        return flat_number
    
    def save(self, request):
        """Create user and link to existing resident if applicable."""
        user = super().save(request)
        
        if user.user_type == "resident":
            resident_id = self.cleaned_data.get("resident_id")
            if resident_id:
                # Store resident_id for signal to pick up
                user._resident_id_to_associate = resident_id
                user.save()
            else:
                # Create new resident profile for tenants/family
                Resident.objects.create(
                    user=user,
                    flat_number=self.cleaned_data["flat_number"],
                    block=self.cleaned_data.get("block", ""),
                    phone_number=self.cleaned_data["phone_number"],
                    alternate_phone=self.cleaned_data.get("alternate_phone", ""),
                    resident_type=self.cleaned_data["resident_type"],
                    move_in_date=self.cleaned_data.get("move_in_date"),
                    emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
                    emergency_contact_phone=self.cleaned_data.get("emergency_contact_phone", ""),
                )
        
        return user
```

### **API Endpoint for Flat Autocomplete**

```python
@require_http_methods(["GET"])
def get_available_flats(request):
    """
    API endpoint to get available flats for owner signup.
    
    Returns flats that don't have associated users yet, formatted for
    the signup form autocomplete functionality.
    """
    try:
        # Get all residents that don't have associated users
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
```

### **Signal-Based User-Resident Linking**

```python
@receiver(post_save, sender=User)
def handle_resident_association(sender, instance, created, **kwargs):
    """
    Signal to handle resident association for owner signups.
    
    This signal is triggered when a user is created and checks if there's
    a resident_id in the user's metadata that needs to be associated.
    This is used for the new owner signup workflow where existing residents
    from the CSV are linked to new user accounts.
    """
    # Only process for newly created resident users
    if not created or instance.user_type != "resident":
        return
    
    # Check if there's a resident_id in the user's metadata
    resident_id = getattr(instance, '_resident_id_to_associate', None)
    
    if resident_id:
        try:
            from the_khaki_estate.backend.models import Resident
            
            # Find the existing resident record
            existing_resident = Resident.objects.get(id=resident_id, user__isnull=True)
            
            # Associate the user with the existing resident
            existing_resident.user = instance
            existing_resident.save()
            
            # Update resident with additional signup data
            if hasattr(instance, '_signup_data'):
                signup_data = instance._signup_data
                existing_resident.move_in_date = signup_data.get('move_in_date')
                existing_resident.emergency_contact_name = signup_data.get('emergency_contact_name', '')
                existing_resident.emergency_contact_phone = signup_data.get('emergency_contact_phone', '')
                existing_resident.alternate_phone = signup_data.get('alternate_phone', '')
                existing_resident.save()
            
            logger.info(
                f"Successfully associated user {instance.username} with existing resident {existing_resident.flat_number}"
            )
            
        except Resident.DoesNotExist:
            logger.error(
                f"Failed to associate user {instance.username} with resident_id {resident_id}: Resident not found"
            )
        except Exception as e:
            logger.error(
                f"Failed to associate user {instance.username} with resident_id {resident_id}: {e}"
            )
```

### **Frontend JavaScript Implementation**

```javascript
// signup-form.js - Dynamic form behavior
$(document).ready(function() {
    let availableFlats = [];
    let filteredFlats = [];
    
    // Load available flats on page load
    loadAvailableFlats();
    
    function loadAvailableFlats() {
        fetch('/backend/api/flats/available/')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    availableFlats = data.flats;
                    console.log('Loaded available flats:', availableFlats.length);
                }
            })
            .catch(error => console.error('Error loading flats:', error));
    }
    
    // User type change handler
    $('#id_user_type').on('change', function() {
        const userType = $(this).val();
        toggleResidentFields(userType === 'resident');
    });
    
    // Resident type change handler
    $('#id_resident_type').on('change', function() {
        const residentType = $(this).val();
        toggleOwnerFields(residentType === 'owner');
    });
    
    // Flat number autocomplete
    $('#id_flat_number').on('input', function() {
        filterFlatNumbers();
    });
    
    // Flat selection handler
    $(document).on('click', '.flat-suggestion', function() {
        const flatData = $(this).data('flat');
        selectFlat(flatData);
    });
    
    function selectFlat(flatData) {
        // Populate form fields with owner data
        $('#id_flat_number').val(flatData.flat_number);
        $('#id_resident_id').val(flatData.id);
        $('#id_email').val(flatData.email);
        $('#id_first_name').val(flatData.owner_name.split(' ')[0]);
        $('#id_last_name').val(flatData.owner_name.split(' ').slice(1).join(' '));
        $('#id_block').val(flatData.block);
        $('#id_phone_number').val(flatData.phone);
        
        // Hide suggestions
        hideFlatSuggestions();
        
        // Show additional fields
        $('.dynamic-field').show();
    }
    
    function filterFlatNumbers() {
        const query = $('#id_flat_number').val().toLowerCase();
        
        if (query.length < 1) {
            hideFlatSuggestions();
            return;
        }
        
        // Filter available flats
        filteredFlats = availableFlats.filter(flat =>
            flat.flat_number.toLowerCase().includes(query) ||
            flat.owner_name.toLowerCase().includes(query)
        );
        
        showFlatSuggestions();
    }
    
    function showFlatSuggestions() {
        const $suggestionsContainer = $('#flat-suggestions');
        $suggestionsContainer.empty();
        
        filteredFlats.forEach(flat => {
            const $suggestion = $('<div>')
                .addClass('flat-suggestion')
                .data('flat', flat)
                .html(`
                    <strong>${flat.flat_number}</strong> - ${flat.owner_name}
                    <br><small>${flat.email} | ${flat.phone}</small>
                `);
            $suggestionsContainer.append($suggestion);
        });
        
        $suggestionsContainer.show();
    }
    
    function hideFlatSuggestions() {
        $('#flat-suggestions').hide().empty();
    }
});
```

### **Migration Strategy**

```python
# Migration 0009: populate_residents_from_csv
def populate_residents(apps, schema_editor):
    """Run the CSV population command during migration."""
    from django.core.management import call_command
    call_command("populate_residents_from_csv", "data /List of Total Flat Owners Khaki Estate.csv")

def reverse_populate_residents(apps, schema_editor):
    """Clean up CSV-created residents during rollback."""
    Resident = apps.get_model("backend", "Resident")
    Resident.objects.filter(user__isnull=True, resident_type='owner').delete()

class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0008_populate_announcement_categories"),
    ]
    
    operations = [
        migrations.RunPython(populate_residents, reverse_populate_residents),
    ]
```

### **Workflow Benefits**

**For Owners:**
- **Streamlined Registration**: Pre-populated data reduces form filling
- **Data Accuracy**: Owner information comes from verified CSV data
- **Quick Setup**: Only need to provide additional details (emergency contacts, move-in date)

**For Administrators:**
- **Bulk Import**: All owners imported from CSV in one operation
- **Data Consistency**: Standardized data format and validation
- **Audit Trail**: Complete tracking of user-resident associations

**For System:**
- **Scalable**: Handles large numbers of owners efficiently
- **Flexible**: Supports both CSV-imported owners and manual tenant registration
- **Maintainable**: Clear separation between data import and user account creation

### **Testing Strategy**

```python
# Test cases for owner signup workflow
class TestOwnerSignupWorkflow(TestCase):
    """Test the complete owner signup workflow."""
    
    def setUp(self):
        """Create test data."""
        # Create CSV-imported resident without user
        self.resident = Resident.objects.create(
            user=None,
            flat_number='A-101',
            block='A',
            phone_number='+919876543210',
            owner_name='John Doe',
            owner_email='john@example.com',
            resident_type='owner'
        )
    
    def test_owner_signup_with_existing_resident(self):
        """Test owner signup linking to existing resident."""
        form_data = {
            'user_type': 'resident',
            'resident_type': 'owner',
            'flat_number': 'A-101',
            'resident_id': str(self.resident.id),
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!'
        }
        
        form = NewUserSignupForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        user = form.save(None)
        self.assertEqual(user.user_type, 'resident')
        
        # Check resident linking
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.user, user)
    
    def test_flat_autocomplete_api(self):
        """Test the flat autocomplete API endpoint."""
        response = self.client.get('/backend/api/flats/available/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['flats']), 1)
        self.assertEqual(data['flats'][0]['flat_number'], 'A-101')
```

---

## 🔔 Enhanced Notification & Maintenance Workflow (v2.1)

### **Major UX Improvements**

**Auto-Mark Notifications as Read:**
- Notifications automatically marked as read when user visits notification center
- Eliminated manual "Mark Read" buttons for better UX
- Smart notification badge that clears automatically

**Streamlined Maintenance Workflow:**
- **Staff-Resident Communication**: Direct workflow between facility managers and residents
- **Committee Role Simplified**: Committee members have dashboard visibility without operational notifications
- **Enhanced Permission System**: Proper staff vs resident permission checking
- **Real-time Notifications**: Staff updates trigger immediate resident notifications

### **Notification Types Enhanced**

```python
# New notification types added for maintenance workflow
MAINTENANCE_NOTIFICATION_TYPES = [
    'maintenance_status_change',     # When staff changes request status
    'maintenance_resident_update',   # When resident adds update (notifies staff)
    'maintenance_update',           # When staff adds update (notifies resident)
]

# Notification Flow
Staff Update → Resident Notification (Email + In-App)
Resident Update → Staff Notification (Email + In-App)
Status Change → Resident Notification (Email + In-App)
Committee Members → Dashboard Visibility Only (No Notifications)
```

### **Permission Architecture Redesigned**

```python
# Simplified permission model focusing on operational roles
def can_manage_maintenance(user):
    """
    Enhanced permission checking for maintenance operations.
    Focuses on staff capabilities rather than committee membership.
    """
    if user.is_staff_member():
        staff = user.staff
        return staff.is_active and (
            staff.can_access_all_maintenance
            or staff.can_assign_requests
            or staff.staff_role in ["facility_manager", "maintenance_supervisor"]
        )
    return False

# Committee members retain view access but no operational responsibilities
```

---

## 🗄️ Database Schema & Models

### Enhanced User Model (`users/models.py`)

```python
class User(AbstractUser):
    """
    Enhanced User model with user type distinction.
    Supports both residents and maintenance staff.
    """

    USER_TYPE_CHOICES = [
        ("resident", "Resident"),
        ("staff", "Staff"),
    ]

    # Core fields
    name = CharField(max_length=255, blank=True)
    user_type = CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="resident"
    )

    def get_full_name(self):
        """
        Return the user's full name with fallback logic.

        Priority:
        1. first_name + last_name (Django standard)
        2. name field (fallback)
        3. username (final fallback)
        """
        # Try Django's standard first_name + last_name combination first
        full_name = f"{self.first_name} {self.last_name}".strip()
        if full_name:
            return full_name

        # Fall back to the name field if first_name/last_name are empty
        if self.name:
            return self.name

        # Final fallback to username
        return self.username

    # Helper methods for type checking
    def is_resident(self) -> bool
    def is_staff_member(self) -> bool
```

**Key Design Decisions:**
- Single User model for all user types (residents and staff)
- `user_type` field enables role-based functionality
- Maintains backward compatibility with existing resident users
- Helper methods provide clean API for type checking

### Staff Model (`backend/models.py`)

```python
class Staff(models.Model):
    """
    Professional staff profile with role-based permissions.
    Handles maintenance staff, facility managers, accountants, etc.
    """

    STAFF_ROLES = [
        ("facility_manager", "Facility Manager"),
        ("accountant", "Accountant"),
        ("security_head", "Security Head"),
        ("maintenance_supervisor", "Maintenance Supervisor"),
        ("electrician", "Electrician"),
        ("plumber", "Plumber"),
        ("cleaner", "Cleaner"),
        ("gardener", "Gardener"),
    ]

    # Core identification
    user = OneToOneField(User, related_name="staff")
    employee_id = CharField(max_length=20, unique=True)
    staff_role = CharField(max_length=25, choices=STAFF_ROLES)

    # Permissions (role-based access control)
    can_access_all_maintenance = BooleanField(default=False)
    can_assign_requests = BooleanField(default=False)
    can_close_requests = BooleanField(default=False)
    can_manage_finances = BooleanField(default=False)
    can_send_announcements = BooleanField(default=False)

    # Employment & hierarchy
    employment_status = CharField(max_length=15, choices=EMPLOYMENT_STATUS)
    hire_date = DateField()
    reporting_to = ForeignKey("self", null=True, blank=True)

    # Business logic methods
    def can_handle_maintenance(self) -> bool
    def is_facility_manager(self) -> bool
    def is_accountant(self) -> bool
    def get_subordinate_count(self) -> int
```

**Design Patterns:**
- **One-to-One Relationship**: Each User can have one Staff profile
- **Self-Referencing FK**: Enables hierarchical reporting structure
- **Permission Fields**: Granular control over staff capabilities
- **Role-Based Defaults**: Automatic permission assignment based on role

### Enhanced MaintenanceRequest Model (`backend/models.py`)

```python
class MaintenanceRequest(models.Model):
    """
    Enhanced maintenance request with staff assignment capabilities.
    Supports complete workflow from submission to closure.
    """

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("assigned", "Assigned"),        # NEW
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
        ("cancelled", "Cancelled"),      # NEW
    ]

    # Enhanced assignment tracking
    assigned_to = ForeignKey(User, related_name="assigned_maintenance_requests")
    assigned_by = ForeignKey(User, related_name="assigned_maintenance_by")
    assigned_at = DateTimeField(null=True, blank=True)

    # Enhanced timestamp tracking
    acknowledged_at = DateTimeField(null=True, blank=True)
    resolved_at = DateTimeField(null=True, blank=True)
    closed_at = DateTimeField(null=True, blank=True)

    # Cost management
    estimated_cost = DecimalField(max_digits=10, decimal_places=2)
    actual_cost = DecimalField(max_digits=10, decimal_places=2)

    # Resident feedback
    resident_rating = IntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)])
    resident_feedback = TextField(blank=True)

    # Business logic methods
    def assign_to_staff(self, staff_user, assigned_by_user=None)
    def can_be_assigned_to(self, staff_user) -> bool
    def get_suitable_staff(self) -> QuerySet
    def is_overdue(self) -> bool
    def get_resolution_time(self) -> timedelta
```

**Workflow State Machine:**
```
submitted → acknowledged → assigned → in_progress → resolved → closed
     ↓                                                    ↓
 cancelled ←──────────────────────────────────────────────┘
```

### Database Relationships

```mermaid
erDiagram
    User ||--o| Resident : "user_type='resident'"
    User ||--o| Staff : "user_type='staff'"
    User ||--o{ MaintenanceRequest : "resident"
    User ||--o{ MaintenanceRequest : "assigned_to"
    User ||--o{ MaintenanceRequest : "assigned_by"
    Staff ||--o{ Staff : "reporting_to"
    MaintenanceCategory ||--o{ MaintenanceRequest : "category"
    MaintenanceRequest ||--o{ MaintenanceUpdate : "request"
```

---

## 👥 User Management System

### User Type Architecture

The system implements a **Single Table Inheritance** pattern for user management:

```python
# Base User model with type discrimination
class User(AbstractUser):
    user_type = CharField(choices=[("resident", "Resident"), ("staff", "Staff")])

    def is_resident(self) -> bool:
        return self.user_type == "resident"

    def is_staff_member(self) -> bool:
        return self.user_type == "staff"

# Profile models extend the base User
class Resident(models.Model):
    user = OneToOneField(User, related_name="resident")
    # Resident-specific fields...

class Staff(models.Model):
    user = OneToOneField(User, related_name="staff")
    # Staff-specific fields...
```

### User Creation Workflow

```python
# Resident registration workflow
def create_resident(user_data, resident_data):
    """
    1. Create User with user_type='resident'
    2. Create Resident profile linked to User
    3. Set default notification preferences
    4. Send welcome email notification
    """
    user = User.objects.create_user(**user_data, user_type="resident")
    resident = Resident.objects.create(user=user, **resident_data)
    # Trigger signals for notification setup
    return user, resident

# Staff registration workflow
def create_staff(user_data, staff_data):
    """
    1. Create User with user_type='staff'
    2. Create Staff profile with role-based permissions
    3. Set work schedule and availability
    4. Configure notification preferences based on role
    """
    user = User.objects.create_user(**user_data, user_type="staff")

    # Set role-based permissions
    permissions = get_role_permissions(staff_data['staff_role'])
    staff = Staff.objects.create(user=user, **staff_data, **permissions)

    return user, staff
```

---

## 🔧 Maintenance Staff Architecture

### Role-Based Permission Matrix

| Role | Access All | Assign | Close | Finances | Announcements | Handle Maintenance |
|------|------------|--------|-------|----------|---------------|-------------------|
| **Facility Manager** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Accountant** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Maintenance Supervisor** | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Electrician** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Plumber** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| **Security Head** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Cleaner** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Gardener** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Staff Assignment Algorithm

```python
def get_suitable_staff(maintenance_request):
    """
    Smart staff assignment based on request category and staff expertise.

    Algorithm:
    1. Filter active staff members
    2. Check role-based permissions
    3. Match expertise to request category
    4. Consider current workload
    5. Return ranked list of suitable staff
    """
    suitable_staff = Staff.objects.filter(
        is_active=True,
        user__is_active=True
    ).filter(
        Q(can_access_all_maintenance=True) |  # Facility Managers, Supervisors
        Q(staff_role__in=get_role_matches(request.category))  # Specialists
    )

    # Future enhancement: Add workload balancing
    # suitable_staff = suitable_staff.annotate(
    #     current_workload=Count('user__assigned_maintenance_requests',
    #                           filter=Q(user__assigned_maintenance_requests__status__in=['assigned', 'in_progress']))
    # ).order_by('current_workload')

    return suitable_staff

def get_role_matches(category):
    """Map maintenance categories to suitable staff roles."""
    category_mapping = {
        'Electrical': ['facility_manager', 'maintenance_supervisor', 'electrician'],
        'Plumbing': ['facility_manager', 'maintenance_supervisor', 'plumber'],
        'HVAC': ['facility_manager', 'maintenance_supervisor'],
        'Security': ['facility_manager', 'security_head'],
        'Cleaning': ['facility_manager', 'cleaner'],
        'Landscaping': ['facility_manager', 'gardener'],
    }
    return category_mapping.get(category.name, ['facility_manager'])
```

---

## 🔄 Enhanced Maintenance Request Workflow (v2.1)

### **Redesigned Workflow Architecture**

**Key Design Changes:**
- **Staff-Focused Operations**: Facility managers handle all maintenance operations
- **Committee Oversight Only**: Committee members have dashboard visibility without operational burden
- **Direct Communication**: Staff ↔ Resident communication, no committee notification spam
- **Auto-Notification System**: Real-time notifications for all workflow changes

**Workflow Participants:**
```python
# Primary Actors
STAFF_ROLES = ['facility_manager', 'maintenance_supervisor', 'electrician', 'plumber']
RESIDENT_ROLE = 'resident'

# Oversight Only (No Operational Notifications)
COMMITTEE_ROLE = 'committee_member'  # Dashboard visibility only
```

### State Machine Implementation

```python
class MaintenanceRequestStateMachine:
    """
    Implements the maintenance request state machine with automatic
    timestamp tracking and validation.
    """

    VALID_TRANSITIONS = {
        'submitted': ['acknowledged', 'cancelled'],
        'acknowledged': ['assigned', 'in_progress', 'cancelled'],
        'assigned': ['in_progress', 'acknowledged', 'cancelled'],
        'in_progress': ['resolved', 'assigned', 'cancelled'],
        'resolved': ['closed', 'in_progress'],
        'closed': [],  # Terminal state
        'cancelled': [],  # Terminal state
    }

    def transition_to(self, new_status, user=None):
        """
        Safely transition request to new status with validation.

        Args:
            new_status: Target status
            user: User making the transition (for audit trail)

        Raises:
            InvalidTransition: If transition is not allowed
            PermissionDenied: If user lacks permission for transition
        """
        if new_status not in self.VALID_TRANSITIONS[self.status]:
            raise InvalidTransition(f"Cannot transition from {self.status} to {new_status}")

        if not self.can_user_transition(user, new_status):
            raise PermissionDenied(f"User {user} cannot transition to {new_status}")

        # Update status and set timestamp
        old_status = self.status
        self.status = new_status
        self._set_status_timestamp(new_status)

        # Trigger signals for notifications
        maintenance_status_changed.send(
            sender=self.__class__,
            instance=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user
        )

        self.save()

    def _set_status_timestamp(self, status):
        """Set appropriate timestamp based on status."""
        timestamp_mapping = {
            'acknowledged': 'acknowledged_at',
            'assigned': 'assigned_at',
            'resolved': 'resolved_at',
            'closed': 'closed_at',
        }

        if status in timestamp_mapping:
            setattr(self, timestamp_mapping[status], timezone.now())
```

### Assignment Workflow

```python
class MaintenanceAssignmentService:
    """
    Service class for handling maintenance request assignments.
    Implements business logic for staff assignment and workload balancing.
    """

    @staticmethod
    def assign_request(request, staff_user, assigned_by_user):
        """
        Assign maintenance request to staff member.

        Workflow:
        1. Validate staff can handle request
        2. Check staff availability/workload
        3. Update request assignment fields
        4. Transition status to 'assigned'
        5. Send notifications
        6. Log assignment for audit
        """
        # Validation
        if not request.can_be_assigned_to(staff_user):
            raise ValidationError("Staff member cannot handle this request type")

        # Check workload (future enhancement)
        current_workload = MaintenanceRequest.objects.filter(
            assigned_to=staff_user,
            status__in=['assigned', 'in_progress']
        ).count()

        if current_workload >= settings.MAX_CONCURRENT_ASSIGNMENTS:
            raise ValidationError("Staff member has reached maximum workload")

        # Perform assignment
        request.assigned_to = staff_user
        request.assigned_by = assigned_by_user
        request.assigned_at = timezone.now()

        # Transition status
        if request.status in ['submitted', 'acknowledged']:
            request.status = 'assigned'

        request.save()

        # Trigger notifications
        send_assignment_notification.delay(request.id, staff_user.id)

        return request

    @staticmethod
    def get_workload_stats(staff_user):
        """Get current workload statistics for staff member."""
        return {
            'active_requests': MaintenanceRequest.objects.filter(
                assigned_to=staff_user,
                status__in=['assigned', 'in_progress']
            ).count(),
            'completed_this_month': MaintenanceRequest.objects.filter(
                assigned_to=staff_user,
                status='closed',
                closed_at__month=timezone.now().month
            ).count(),
            'avg_resolution_time': calculate_avg_resolution_time(staff_user),
            'satisfaction_rating': calculate_avg_satisfaction(staff_user),
        }
```

---

## 🏢 Booking Approval Workflow (v2.1)

### **Designated Resident Approval System**

**Key Design Principles:**
- **Resident-Based Approvals**: Designated residents (not staff) approve bookings for their assigned areas
- **Admin-Managed Assignments**: Approver assignments managed through Django admin interface
- **Notification-Driven**: Real-time notifications for approval requests and status changes
- **Audit Trail**: Complete tracking of approval decisions and timestamps

### **Workflow Participants**

1. **Residents**: Create booking requests for common areas
2. **Designated Approvers**: Specific residents assigned to approve bookings for particular areas
3. **Committee Members**: Can view all bookings and perform status updates
4. **Administrators**: Manage approver assignments through Django admin

### **Booking Model Enhancements**

```python
class Booking(models.Model):
    """
    Enhanced booking model with designated resident approval workflow.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # Core booking fields
    booking_number = CharField(max_length=20, unique=True)
    common_area = ForeignKey(CommonArea, on_delete=models.CASCADE)
    resident = ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    purpose = CharField(max_length=200)
    booking_date = DateField()
    start_time = TimeField()
    end_time = TimeField()
    
    # Approval workflow fields
    designated_approver = ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approvals_to_review',
        help_text="The resident designated to approve this booking"
    )
    approved_by = ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bookings'
    )
    approved_at = DateTimeField(null=True, blank=True)
    rejection_reason = TextField(blank=True)
    
    # Status tracking
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    status_changed_at = DateTimeField(auto_now=True)
    status_changed_by = ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Business logic methods
    def get_designated_approver(self):
        """Get the designated approver from CommonArea's ApproverAssignment"""
        return self.common_area.get_designated_approver()
    
    def can_be_approved_by(self, user):
        """Check if user can approve this booking"""
        return (
            self.status == 'pending' and
            self.designated_approver == user and
            user.user_type == 'resident'
        )
    
    def approve_booking(self, approver, rejection_reason=None):
        """Approve or reject the booking"""
        if rejection_reason:
            self.status = 'rejected'
            self.rejection_reason = rejection_reason
        else:
            self.status = 'approved'
        
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.status_changed_by = approver
        self.save()
```

### **ApproverAssignment Model**

```python
class ApproverAssignment(models.Model):
    """
    Manages designated approvers for common areas.
    Allows administrators to assign specific residents as approvers
    for different common areas through Django admin interface.
    """
    
    common_area = ForeignKey(
        CommonArea,
        on_delete=models.CASCADE,
        related_name='approver_assignments'
    )
    
    approver = ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approver_assignments',
        limit_choices_to={'user_type': 'resident', 'is_active': True}
    )
    
    is_active = BooleanField(default=True)
    assigned_by = ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_at = DateTimeField(auto_now_add=True)
    notes = TextField(blank=True)
    
    class Meta:
        unique_together = ['common_area', 'approver']
    
    def save(self, *args, **kwargs):
        """Ensure only one active assignment per common area"""
        if self.is_active:
            ApproverAssignment.objects.filter(
                common_area=self.common_area,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
```

### **CommonArea Model Enhancement**

```python
class CommonArea(models.Model):
    # ... existing fields ...
    
    def get_designated_approver(self):
        """
        Get the designated approver for this common area.
        Returns the User object of the active approver, or None if not found.
        """
        try:
            assignment = ApproverAssignment.objects.get(
                common_area=self,
                is_active=True
            )
            return assignment.approver if assignment.approver.is_active else None
        except ApproverAssignment.DoesNotExist:
            return None
```

### **Notification Types for Booking Workflow**

```python
BOOKING_NOTIFICATION_TYPES = [
    {
        'name': 'booking_pending_approval',
        'title_template': 'New Booking Request: {booking_number}',
        'message_template': 'Booking request for {common_area} on {booking_date} requires your approval.',
        'channels': ['in_app', 'email'],
        'priority': 'high',
    },
    {
        'name': 'booking_approved',
        'title_template': 'Booking Approved: {booking_number}',
        'message_template': 'Your booking for {common_area} on {booking_date} has been approved.',
        'channels': ['in_app', 'email'],
        'priority': 'medium',
    },
    {
        'name': 'booking_rejected',
        'title_template': 'Booking Rejected: {booking_number}',
        'message_template': 'Your booking for {common_area} on {booking_date} was rejected. Reason: {rejection_reason}',
        'channels': ['in_app', 'email'],
        'priority': 'high',
    },
    {
        'name': 'booking_confirmed',
        'title_template': 'Booking Confirmed: {booking_number}',
        'message_template': 'Your booking for {common_area} on {booking_date} has been confirmed.',
        'channels': ['in_app', 'email'],
        'priority': 'medium',
    },
    {
        'name': 'booking_cancelled',
        'title_template': 'Booking Cancelled: {booking_number}',
        'message_template': 'Your booking for {common_area} on {booking_date} has been cancelled.',
        'channels': ['in_app', 'email'],
        'priority': 'medium',
    },
]
```

### **Signal Handlers for Booking Workflow**

```python
@receiver(post_save, sender=Booking)
def booking_workflow_handler(sender, instance, created, **kwargs):
    """
    Handle booking creation and status change notifications.
    """
    if created:
        _handle_new_booking(instance)
    else:
        _handle_booking_status_change(instance)

def _handle_new_booking(booking):
    """Handle new booking creation workflow"""
    # Set designated approver based on common area
    approver = booking.set_designated_approver()
    
    # Save the booking to persist the designated_approver field
    if approver:
        booking.save()
    
    if approver:
        # Notify designated approver about new booking request
        NotificationService.create_notification(
            recipient=approver,
            notification_type_name="booking_pending_approval",
            title=f"New Booking Request: {booking.booking_number}",
            message=f"Booking request for {booking.common_area.name} on {booking.booking_date} requires your approval.",
            context_data={
                'booking_id': booking.id,
                'booking_number': booking.booking_number,
                'common_area': booking.common_area.name,
                'booking_date': booking.booking_date.strftime('%Y-%m-%d'),
                'start_time': booking.start_time.strftime('%H:%M'),
                'end_time': booking.end_time.strftime('%H:%M'),
                'purpose': booking.purpose,
                'resident': booking.resident.get_full_name(),
            }
        )

def _handle_booking_status_change(booking):
    """Handle booking status change notifications"""
    if booking.status == 'approved':
        _notify_booking_approved(booking)
    elif booking.status == 'rejected':
        _notify_booking_rejected(booking)
    elif booking.status == 'confirmed':
        _notify_booking_confirmed(booking)
    elif booking.status == 'cancelled':
        _notify_booking_cancelled(booking)
```

### **Views for Booking Approval**

```python
def approve_booking(request, booking_id):
    """
    Approve or reject a booking - designated resident approvers only
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
            "message": "Invalid action. Must be 'approve' or 'reject'."
        })
    
    # Validate rejection reason for rejections
    if action == "reject" and not rejection_reason:
        return JsonResponse({
            "status": "error",
            "message": "Rejection reason is required."
        })
    
    # Approve or reject the booking
    booking.approve_booking(request.user, rejection_reason if action == "reject" else None)
    
    # Return success response
    status_text = "approved" if action == "approve" else "rejected"
    return JsonResponse({
        "status": "success",
        "message": f"Booking {booking.booking_number} has been {status_text} successfully"
    })
```

### **Django Admin Interface**

```python
class ApproverAssignmentInline(admin.TabularInline):
    """Inline admin for managing approver assignments within CommonArea admin"""
    model = ApproverAssignment
    extra = 1
    fields = ["approver", "is_active", "assigned_at", "notes"]
    readonly_fields = ["assigned_at"]
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "approver":
            # Only show active residents
            residents = User.objects.filter(
                user_type="resident",
                is_active=True,
                resident__isnull=False
            )
            kwargs["queryset"] = residents
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(CommonArea)
class CommonAreaAdmin(admin.ModelAdmin):
    """Enhanced admin for CommonArea with inline approver assignment management"""
    list_display = ["name", "capacity", "booking_fee", "is_active", "get_current_approver"]
    inlines = [ApproverAssignmentInline]
    
    def get_current_approver(self, obj):
        """Display the current active approver for this common area"""
        approver = obj.get_designated_approver()
        if approver:
            return f"{approver.get_full_name() or approver.username} ({approver.email})"
        return "No approver assigned"
    get_current_approver.short_description = "Current Approver"
```

### **Frontend Implementation**

**Booking Detail Template Features:**
- Approval interface for designated approvers
- Status badges with color coding
- Modal dialogs for approval/rejection actions
- Real-time status updates via AJAX
- Proper JavaScript error handling

**Key Template Features:**
```html
<!-- Approval Actions Section -->
{% if can_approve and booking.status == 'pending' %}
<div class="approval-actions">
    <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#approveModal">
        <i class="fas fa-check me-2"></i>Approve Booking
    </button>
    <button class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#rejectModal">
        <i class="fas fa-times me-2"></i>Reject Booking
    </button>
</div>
{% endif %}

<!-- JavaScript for AJAX Approval -->
<script>
const approveUrl = '{% url "backend:approve_booking" booking.id %}';
fetch(approveUrl, {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': csrfToken.value
    }
})
</script>
```

### **Testing Strategy**

**Test Coverage Includes:**
- Model business logic (`can_be_approved_by`, `approve_booking`)
- Signal handlers and notification creation
- View permissions and approval workflow
- Admin interface functionality
- Frontend JavaScript interactions

**Key Test Files:**
- `test_booking_approval_workflow.py`: Core workflow testing
- `test_admin_approver_management.py`: Admin interface testing

---

## 📅 Enhanced Booking Calendar System (v2.2)

### **Calendar View Architecture**

**Key Features:**
- **Interactive Calendar Interface**: Monthly view with booking visualization
- **AJAX-Powered Navigation**: Dynamic month switching without page refresh
- **Privacy-Aware Display**: Shows appropriate booking details based on user permissions
- **Timezone-Safe Operations**: Proper handling of Asia/Kolkata timezone
- **Mobile-Responsive Design**: Optimized for all device sizes

### **Calendar View Implementation**

```python
@login_required
def booking_calendar(request):
    """
    Enhanced calendar view for facility bookings with proper data serialization.
    Shows current bookings so residents can plan their requests accordingly.
    """
    # Get filter parameters from request
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    
    # Create date range for the requested month
    start_of_month = date(year, month, 1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Get bookings with privacy controls
    bookings = Booking.objects.filter(
        booking_date__range=[start_of_month, end_of_month],
        status__in=["pending", "approved", "confirmed", "completed"]
    ).select_related('common_area', 'resident', 'resident__resident')
    
    # Serialize with permission-based data filtering
    bookings_data = []
    for booking in bookings:
        if booking.resident == request.user or is_committee_member(request.user):
            # Full details for own bookings or committee members
            booking_data = {
                'id': booking.id,
                'booking_number': booking.booking_number,
                'purpose': booking.purpose,
                'resident_name': booking.resident.get_full_name(),
                'is_own_booking': True
                # ... full details
            }
        else:
            # Limited details for privacy
            booking_data = {
                'purpose': 'Private Event',
                'resident_name': 'Resident',
                'is_own_booking': False
                # ... limited details
            }
        bookings_data.append(booking_data)
```

### **AJAX API Endpoint**

```python
@login_required
def booking_calendar_api(request):
    """
    API endpoint for dynamic calendar data loading.
    Returns booking data for a specific month/year as JSON.
    """
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    area_filter = request.GET.get('area', '')
    
    # Dynamic data loading with filtering support
    bookings_query = Booking.objects.filter(
        booking_date__range=[start_of_month, end_of_month],
        status__in=["pending", "approved", "confirmed", "completed"]
    )
    
    if area_filter:
        bookings_query = bookings_query.filter(common_area_id=area_filter)
    
    return JsonResponse({
        'bookings': bookings_data,
        'month': month,
        'year': year,
        'success': True
    })
```

### **Frontend Calendar Features**

**JavaScript Implementation:**
```javascript
// Timezone-safe date handling for Asia/Kolkata
function handleDayClick(day) {
    const selectedDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    
    // Fix timezone issue: Use local date formatting instead of ISO
    const year = selectedDate.getFullYear();
    const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
    const dayStr = String(selectedDate.getDate()).padStart(2, '0');
    const dateString = `${year}-${month}-${dayStr}`;
    
    window.location.href = `/backend/bookings/create/?date=${dateString}`;
}

// AJAX calendar navigation
function loadCalendarData() {
    const apiUrl = new URL('/backend/bookings/calendar/api/', window.location.origin);
    apiUrl.searchParams.append('month', month);
    apiUrl.searchParams.append('year', year);
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            bookingsData = groupBookingsByArea(data.bookings);
            renderCalendar();
        });
}
```

**Key Frontend Features:**
- **Visual Status Indicators**: Color-coded booking statuses (green=confirmed, yellow=pending, etc.)
- **Interactive Booking Details**: Click on bookings to view details in modal
- **Quick Booking Creation**: Click on available dates to create bookings
- **Facility Filtering**: Filter calendar by specific common areas
- **Mobile Optimization**: Responsive design for all screen sizes

### **Privacy & Permission Controls**

**Data Visibility Rules:**
```python
# Permission-based booking information display
if booking.resident == request.user or is_committee_member(request.user):
    # Show full booking details including:
    # - Actual purpose
    # - Resident name and flat number
    # - Guest count and fees
    # - Full booking management options
else:
    # Show limited information for planning purposes:
    # - Generic "Private Event" purpose
    # - Anonymous "Resident" name
    # - Time slots only (for availability planning)
```

**Security Features:**
- **Role-Based Access**: Different information visibility based on user type
- **Privacy Protection**: Personal details hidden from other residents
- **Planning Transparency**: Enough information for residents to plan without privacy invasion

---

## 🔔 Enhanced Booking Notification Workflow (v2.2)

### **Complete Bidirectional Notification System**

**Fixed Issues:**
- **Signal Handler Bug**: Fixed `_handle_booking_status_change` that wasn't triggering notifications
- **Missing Notifications**: Residents now receive notifications when bookings are approved/rejected
- **Manual Triggers**: Added explicit notification calls in approval views

### **Notification Flow Implementation**

```python
# Enhanced approval view with manual notification triggers
@login_required
def approve_booking(request, booking_id):
    """
    Approve or reject a booking with proper notification workflow.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Perform approval/rejection
    approved = (action == "approve")
    booking.approve_booking(
        approver=request.user,
        approved=approved,
        rejection_reason=rejection_reason if not approved else None
    )
    
    # Manually trigger notifications (bypassing broken signal handler)
    from .signals import _notify_booking_approved, _notify_booking_rejected
    
    if approved:
        _notify_booking_approved(booking)
    else:
        _notify_booking_rejected(booking)
    
    return JsonResponse({"status": "success"})
```

### **Enhanced Notification Messages**

```python
def _notify_booking_approved(booking):
    """Enhanced approval notification with detailed information."""
    NotificationService.create_notification(
        recipient=booking.resident,
        notification_type_name="booking_approved",
        title=f"Booking Approved: {booking.booking_number}",
        message=f"Great news! Your booking for {booking.common_area.name} on {booking.booking_date} from {booking.start_time.strftime('%H:%M')} to {booking.end_time.strftime('%H:%M')} has been approved by {booking.approved_by.get_full_name()}",
        data={
            "booking_number": booking.booking_number,
            "area_name": booking.common_area.name,
            "start_time": booking.start_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M"),
            "approved_by": booking.approved_by.get_full_name(),
            "approved_at": booking.approved_at.strftime("%Y-%m-%d %H:%M"),
        }
    )

def _notify_booking_rejected(booking):
    """Enhanced rejection notification with reason and details."""
    NotificationService.create_notification(
        recipient=booking.resident,
        notification_type_name="booking_rejected",
        message=f"Unfortunately, your booking for {booking.common_area.name} on {booking.booking_date} from {booking.start_time.strftime('%H:%M')} to {booking.end_time.strftime('%H:%M')} has been rejected by {booking.approved_by.get_full_name()}. Reason: {booking.rejection_reason}",
        data={
            "rejection_reason": booking.rejection_reason,
            "rejected_by": booking.approved_by.get_full_name(),
            "rejected_at": booking.approved_at.strftime("%Y-%m-%d %H:%M"),
        }
    )
```

### **Complete Notification Workflow**

**Booking Creation → Approval Request:**
1. Resident creates booking → Designated approver receives notification ✅
2. Email + in-app notification sent to approver
3. Notification includes booking details and approval link

**Approval Decision → Resident Notification:**
1. Approver approves/rejects → Resident receives notification ✅ (Fixed)
2. Detailed notification with approver name and timestamp
3. Rejection notifications include reason and next steps

**Status Updates → Relevant Parties:**
1. Status changes (confirmed/cancelled) → Notifications sent ✅
2. Committee members can update status with notifications
3. Complete audit trail maintained

### **Timezone Handling Improvements**

**Problem Solved:**
- **JavaScript Date Issues**: `toISOString()` was causing timezone conversion problems
- **Asia/Kolkata Timezone**: UTC+5:30 offset was shifting dates by one day
- **Calendar Date Selection**: Clicking dates was pre-filling wrong dates in forms

**Solution Implemented:**
```javascript
// Before (problematic):
const dateString = selectedDate.toISOString().split('T')[0];

// After (timezone-safe):
const year = selectedDate.getFullYear();
const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
const dayStr = String(selectedDate.getDate()).padStart(2, '0');
const dateString = `${year}-${month}-${dayStr}`;
```

**Django Configuration:**
```python
# settings/base.py
TIME_ZONE = "Asia/Kolkata"
USE_TZ = True
```

---

## 🔐 Permission & Access Control

### Permission Checking Framework

```python
class MaintenancePermissionMixin:
    """
    Mixin for views that need maintenance-related permission checking.
    Provides methods for checking various maintenance permissions.
    """

    def can_view_request(self, user, request):
        """Check if user can view specific maintenance request."""
        # Residents can view their own requests
        if user.is_resident() and request.resident == user:
            return True

        # Staff permissions
        if user.is_staff_member():
            staff = user.staff

            # Facility managers can view all
            if staff.can_access_all_maintenance:
                return True

            # Assigned staff can view their requests
            if request.assigned_to == user:
                return True

            # Supervisors can view subordinate's requests
            if request.assigned_to and request.assigned_to.staff.reporting_to == staff:
                return True

        return False

    def can_assign_request(self, user, request):
        """Check if user can assign maintenance request."""
        if not user.is_staff_member():
            return False

        return user.staff.can_assign_requests

    def can_close_request(self, user, request):
        """Check if user can close maintenance request."""
        if not user.is_staff_member():
            return False

        staff = user.staff

        # Staff with close permission
        if staff.can_close_requests:
            return True

        # Assigned staff can close their own requests
        if request.assigned_to == user:
            return True

        return False

# Decorator for view-level permission checking
def require_maintenance_permission(permission_method):
    """
    Decorator to check maintenance permissions before view execution.

    Usage:
    @require_maintenance_permission('can_assign_request')
    def assign_request_view(request, request_id):
        # View logic here
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            maintenance_request = get_object_or_404(MaintenanceRequest, pk=kwargs['request_id'])

            if not getattr(MaintenancePermissionMixin(), permission_method)(request.user, maintenance_request):
                raise PermissionDenied("Insufficient permissions for this action")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### Role-Based View Access

```python
# views.py implementation example
class MaintenanceRequestListView(LoginRequiredMixin, ListView):
    """
    List view with role-based filtering.
    Shows different requests based on user type and permissions.
    """
    model = MaintenanceRequest
    template_name = 'backend/maintenance/list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        """Filter requests based on user permissions."""
        user = self.request.user

        if user.is_resident():
            # Residents see only their requests
            return MaintenanceRequest.objects.filter(resident=user)

        elif user.is_staff_member():
            staff = user.staff

            if staff.can_access_all_maintenance:
                # Facility managers see all requests
                return MaintenanceRequest.objects.all()

            elif staff.can_handle_maintenance():
                # Technical staff see assigned requests + unassigned in their domain
                return MaintenanceRequest.objects.filter(
                    Q(assigned_to=user) |
                    Q(assigned_to__isnull=True, category__in=staff.get_expertise_categories())
                )

            else:
                # Other staff see only assigned requests
                return MaintenanceRequest.objects.filter(assigned_to=user)

        return MaintenanceRequest.objects.none()

    def get_context_data(self, **kwargs):
        """Add role-specific context data."""
        context = super().get_context_data(**kwargs)

        if self.request.user.is_staff_member():
            context.update({
                'can_assign': self.request.user.staff.can_assign_requests,
                'can_close': self.request.user.staff.can_close_requests,
                'staff_list': Staff.objects.filter(is_active=True, can_handle_maintenance=True),
                'workload_stats': get_workload_stats(self.request.user),
            })

        return context
```

---

## 📝 Forms & Validation

### StaffSignupForm Architecture (`users/forms.py`)

```python
class StaffSignupForm(SignupForm):
    """
    Multi-step staff registration form with role-based permission assignment.

    Workflow:
    1. Collect basic user information
    2. Collect staff-specific details
    3. Validate employee ID uniqueness
    4. Set role-based permissions automatically
    5. Create User and Staff profiles atomically
    """

    def __init__(self, *args, **kwargs):
        """
        Dynamic form initialization.
        Loads staff role choices from model to ensure consistency.
        """
        super().__init__(*args, **kwargs)

        # Import here to avoid circular imports
        from the_khaki_estate.backend.models import Staff

        # Dynamically set choices from model
        self.fields["staff_role"] = forms.ChoiceField(
            choices=Staff.STAFF_ROLES,
            widget=forms.Select(attrs={"class": "form-control"})
        )

    def clean_employee_id(self):
        """Validate employee ID uniqueness across all staff."""
        employee_id = self.cleaned_data.get("employee_id")
        if employee_id and Staff.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError(
                "This employee ID is already registered. Please use a different ID."
            )
        return employee_id

    def save(self, request):
        """
        Atomic user and staff creation with role-based permissions.

        Transaction ensures both User and Staff are created successfully
        or both operations are rolled back.
        """
        with transaction.atomic():
            # Create user
            user = super().save(request)
            user.user_type = "staff"
            user.name = f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}".strip()
            user.save()

            # Get role-based permissions
            permissions = self._get_default_permissions(self.cleaned_data["staff_role"])

            # Create staff profile
            Staff.objects.create(
                user=user,
                employee_id=self.cleaned_data["employee_id"],
                staff_role=self.cleaned_data["staff_role"],
                # ... other fields
                **permissions
            )

            # Trigger post-creation signals
            staff_created.send(sender=Staff, user=user, staff_role=self.cleaned_data["staff_role"])

            return user

    def _get_default_permissions(self, staff_role):
        """
        Get default permissions based on staff role.
        Centralized permission logic ensures consistency.
        """
        permission_matrix = {
            "facility_manager": {
                "can_access_all_maintenance": True,
                "can_assign_requests": True,
                "can_close_requests": True,
                "can_send_announcements": True,
            },
            "accountant": {
                "can_manage_finances": True,
                "can_send_announcements": True,
            },
            # ... other roles
        }

        return permission_matrix.get(staff_role, {})
```

### Form Validation Pipeline

```python
class MaintenanceRequestForm(forms.ModelForm):
    """
    Enhanced maintenance request form with staff assignment capabilities.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Customize assigned_to field based on user permissions
        if self.user and self.user.is_staff_member() and self.user.staff.can_assign_requests:
            self.fields['assigned_to'].queryset = Staff.objects.filter(
                is_active=True,
                can_handle_maintenance=True
            ).select_related('user')
        else:
            # Hide assignment field for users without permission
            del self.fields['assigned_to']

    def clean(self):
        """Cross-field validation for maintenance requests."""
        cleaned_data = super().clean()

        # Validate assignment permissions
        assigned_to = cleaned_data.get('assigned_to')
        if assigned_to and not self.instance.can_be_assigned_to(assigned_to):
            raise forms.ValidationError("Selected staff member cannot handle this request type")

        # Validate priority vs category
        priority = cleaned_data.get('priority')
        category = cleaned_data.get('category')
        if priority and category and priority > category.priority_level:
            self.add_error('priority', 'Priority cannot exceed category maximum')

        return cleaned_data
```

---

## 🌐 Views & URL Patterns

### View Architecture

```python
# backend/views.py - Enhanced maintenance views

class MaintenanceRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Create maintenance request with automatic resident assignment.
    Supports both resident self-service and staff-assisted creation.
    """
    model = MaintenanceRequest
    form_class = MaintenanceRequestForm
    template_name = 'backend/maintenance/create.html'

    def get_form_kwargs(self):
        """Pass current user to form for permission-based customization."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Set resident and trigger workflow."""
        form.instance.resident = self.request.user

        # Auto-assign if staff member is creating for resident
        if self.request.user.is_staff_member() and not form.instance.resident:
            form.instance.resident = form.cleaned_data.get('resident')

        response = super().form_valid(form)

        # Trigger post-creation workflow
        maintenance_request_created.send(
            sender=MaintenanceRequest,
            instance=self.object,
            created_by=self.request.user
        )

        return response

class MaintenanceRequestAssignView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Staff assignment view with permission checking and workflow automation.
    """
    model = MaintenanceRequest
    fields = ['assigned_to', 'estimated_completion', 'estimated_cost']
    template_name = 'backend/maintenance/assign.html'

    def test_func(self):
        """Check if user can assign requests."""
        return (self.request.user.is_staff_member() and
                self.request.user.staff.can_assign_requests)

    def form_valid(self, form):
        """Handle assignment with proper workflow."""
        request_obj = form.instance
        assigned_to = form.cleaned_data['assigned_to']

        # Use assignment service for proper workflow
        MaintenanceAssignmentService.assign_request(
            request_obj,
            assigned_to,
            self.request.user
        )

        messages.success(
            self.request,
            f"Request {request_obj.ticket_number} assigned to {assigned_to.name}"
        )

        return redirect('backend:maintenance_detail', pk=request_obj.pk)

class StaffDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Role-based staff dashboard with personalized content.
    """
    template_name = 'backend/staff_dashboard.html'

    def test_func(self):
        """Only staff members can access staff dashboard."""
        return self.request.user.is_staff_member()

    def get_context_data(self, **kwargs):
        """Provide role-specific dashboard data."""
        context = super().get_context_data(**kwargs)
        staff = self.request.user.staff

        # Base stats for all staff
        context.update({
            'staff_profile': staff,
            'my_requests': MaintenanceRequest.objects.filter(assigned_to=self.request.user),
            'workload_stats': MaintenanceAssignmentService.get_workload_stats(self.request.user),
        })

        # Role-specific data
        if staff.is_facility_manager():
            context.update({
                'all_requests': MaintenanceRequest.objects.all()[:10],
                'pending_assignments': MaintenanceRequest.objects.filter(
                    status__in=['submitted', 'acknowledged']
                ),
                'overdue_requests': MaintenanceRequest.objects.filter(
                    estimated_completion__lt=timezone.now(),
                    status__in=['assigned', 'in_progress']
                ),
                'team_performance': get_team_performance_stats(),
            })

        elif staff.is_accountant():
            context.update({
                'cost_summary': get_monthly_cost_summary(),
                'budget_alerts': get_budget_alerts(),
                'vendor_performance': get_vendor_stats(),
            })

        return context
```

### URL Pattern Architecture

```python
# backend/urls.py - Maintenance staff URLs

urlpatterns = [
    # Maintenance request management
    path('maintenance/', include([
        path('', MaintenanceRequestListView.as_view(), name='maintenance_list'),
        path('create/', MaintenanceRequestCreateView.as_view(), name='maintenance_create'),
        path('<int:pk>/', MaintenanceRequestDetailView.as_view(), name='maintenance_detail'),
        path('<int:pk>/assign/', MaintenanceRequestAssignView.as_view(), name='maintenance_assign'),
        path('<int:pk>/update-status/', MaintenanceStatusUpdateView.as_view(), name='maintenance_update_status'),
        path('<int:pk>/close/', MaintenanceCloseView.as_view(), name='maintenance_close'),
    ])),

    # Staff management
    path('staff/', include([
        path('dashboard/', StaffDashboardView.as_view(), name='staff_dashboard'),
        path('profile/', StaffProfileView.as_view(), name='staff_profile'),
        path('workload/', StaffWorkloadView.as_view(), name='staff_workload'),
        path('performance/', StaffPerformanceView.as_view(), name='staff_performance'),
    ])),

    # Admin/management views
    path('admin-panel/', include([
        path('staff-management/', StaffManagementView.as_view(), name='admin_staff_management'),
        path('reports/', MaintenanceReportsView.as_view(), name='admin_reports'),
        path('analytics/', MaintenanceAnalyticsView.as_view(), name='admin_analytics'),
    ])),
]
```

---

## ⚙️ Tasks & Background Processing

### Celery Task Architecture (`backend/tasks.py`)

```python
# Enhanced notification and workflow tasks

@shared_task(bind=True, max_retries=3)
def send_assignment_notification(self, request_id, staff_user_id):
    """
    Send notification when maintenance request is assigned to staff.

    Features:
    - Retry mechanism for failed deliveries
    - Multiple notification channels (email, SMS, in-app)
    - Template-based messaging
    """
    try:
        request = MaintenanceRequest.objects.get(id=request_id)
        staff_user = User.objects.get(id=staff_user_id)

        # Create in-app notification
        Notification.objects.create(
            recipient=staff_user,
            notification_type=NotificationType.objects.get(name='maintenance_assigned'),
            title=f'New Assignment: {request.title}',
            message=f'You have been assigned maintenance request {request.ticket_number}',
            data={
                'request_id': request.id,
                'priority': request.priority,
                'location': request.location,
                'url': f'/backend/maintenance/{request.id}/'
            }
        )

        # Send email if staff prefers email notifications
        if staff_user.staff.email_notifications:
            send_email_notification.delay(
                staff_user.email,
                'maintenance_assigned',
                {
                    'request': request,
                    'staff_member': staff_user.staff,
                }
            )

        # Send SMS for urgent requests if staff has SMS enabled
        if request.priority >= 3 and staff_user.staff.sms_notifications:
            send_sms_notification.delay(
                staff_user.staff.phone_number,
                f'URGENT: New maintenance assignment {request.ticket_number}. Check system for details.'
            )

    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@shared_task
def process_overdue_requests():
    """
    Periodic task to identify and escalate overdue maintenance requests.

    Runs every hour to:
    1. Identify overdue requests
    2. Send escalation notifications
    3. Auto-reassign if necessary
    4. Update priority levels
    """
    overdue_requests = MaintenanceRequest.objects.filter(
        estimated_completion__lt=timezone.now(),
        status__in=['assigned', 'in_progress']
    )

    for request in overdue_requests:
        # Send escalation notification to facility manager
        facility_managers = Staff.objects.filter(
            staff_role='facility_manager',
            is_active=True
        )

        for fm in facility_managers:
            send_escalation_notification.delay(request.id, fm.user.id)

        # Log overdue status
        MaintenanceUpdate.objects.create(
            request=request,
            author=None,  # System-generated
            content=f"Request is overdue. Original completion: {request.estimated_completion}",
            status_changed_to=request.status
        )

@shared_task
def generate_staff_performance_report(staff_id, period='monthly'):
    """
    Generate comprehensive staff performance report.

    Metrics calculated:
    - Request completion rate
    - Average resolution time
    - Resident satisfaction scores
    - Cost efficiency (actual vs estimated)
    - Workload distribution
    """
    staff = Staff.objects.get(id=staff_id)

    # Calculate date range
    if period == 'monthly':
        start_date = timezone.now().replace(day=1)
    elif period == 'weekly':
        start_date = timezone.now() - timedelta(days=7)

    # Query performance data
    requests = MaintenanceRequest.objects.filter(
        assigned_to=staff.user,
        created_at__gte=start_date
    )

    performance_data = {
        'total_requests': requests.count(),
        'completed_requests': requests.filter(status='closed').count(),
        'avg_resolution_time': calculate_avg_resolution_time(requests),
        'avg_satisfaction': calculate_avg_satisfaction(requests),
        'cost_efficiency': calculate_cost_efficiency(requests),
        'on_time_completion': calculate_on_time_rate(requests),
    }

    # Generate and store report
    report = StaffPerformanceReport.objects.create(
        staff=staff,
        period=period,
        data=performance_data,
        generated_at=timezone.now()
    )

    return report.id
```

### Celery Configuration (`config/celery_app.py`)

```python
# Enhanced celery configuration for maintenance workflows

from celery import Celery
from celery.schedules import crontab

app = Celery("the_khaki_estate")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Periodic tasks for maintenance management
app.conf.beat_schedule = {
    'process-overdue-requests': {
        'task': 'the_khaki_estate.backend.tasks.process_overdue_requests',
        'schedule': crontab(minute=0),  # Every hour
    },
    'daily-staff-reports': {
        'task': 'the_khaki_estate.backend.tasks.generate_daily_reports',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
    'weekly-performance-analysis': {
        'task': 'the_khaki_estate.backend.tasks.weekly_performance_analysis',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
    },
}

app.autodiscover_tasks()
```

---

## 📡 Signals & Event Handling

### Signal Architecture (`backend/signals.py`)

```python
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model

# Custom signals for maintenance workflow
maintenance_request_created = Signal()
maintenance_status_changed = Signal()
staff_created = Signal()
request_assigned = Signal()
request_completed = Signal()

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create appropriate profile when User is created.

    Workflow:
    - If user_type='resident' → Create Resident profile
    - If user_type='staff' → Staff profile creation handled by StaffSignupForm
    """
    if created and instance.user_type == 'resident':
        # Create minimal resident profile if not exists
        if not hasattr(instance, 'resident'):
            from the_khaki_estate.backend.models import Resident
            Resident.objects.create(
                user=instance,
                flat_number='TEMP',  # Will be updated during registration
                phone_number='',
                resident_type='owner'
            )

@receiver(maintenance_request_created)
def handle_new_maintenance_request(sender, instance, created_by, **kwargs):
    """
    Handle new maintenance request creation workflow.

    Actions:
    1. Send notification to facility managers
    2. Auto-assign if emergency priority
    3. Create initial audit log
    4. Schedule follow-up reminders
    """
    # Notify facility managers of new request
    facility_managers = Staff.objects.filter(
        staff_role='facility_manager',
        is_active=True,
        email_notifications=True
    )

    for fm in facility_managers:
        send_new_request_notification.delay(instance.id, fm.user.id)

    # Auto-assign emergency requests
    if instance.priority == 4:  # Emergency
        suitable_staff = instance.get_suitable_staff().filter(
            is_available_24x7=True
        ).first()

        if suitable_staff:
            instance.assign_to_staff(suitable_staff.user)
            send_emergency_assignment.delay(instance.id, suitable_staff.user.id)

@receiver(maintenance_status_changed)
def handle_status_change(sender, instance, old_status, new_status, changed_by, **kwargs):
    """
    Handle maintenance request status changes.

    Triggers different workflows based on status transition.
    """
    # Send notifications based on status
    notification_mapping = {
        'acknowledged': send_acknowledgment_notification,
        'assigned': send_assignment_notification,
        'in_progress': send_progress_notification,
        'resolved': send_completion_notification,
        'closed': send_closure_notification,
    }

    if new_status in notification_mapping:
        # Notify resident
        notification_mapping[new_status].delay(instance.id, instance.resident.id)

        # Notify relevant staff
        if instance.assigned_to:
            notification_mapping[new_status].delay(instance.id, instance.assigned_to.id)

@receiver(post_save, sender=MaintenanceRequest)
def maintenance_request_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log for all maintenance request changes.
    Maintains complete history for compliance and analysis.
    """
    if not created:  # Only log updates, not creation
        # Track what changed
        changed_fields = []
        if hasattr(instance, '_state') and instance._state.db:
            old_instance = MaintenanceRequest.objects.get(pk=instance.pk)

            for field in instance._meta.fields:
                old_value = getattr(old_instance, field.name)
                new_value = getattr(instance, field.name)

                if old_value != new_value:
                    changed_fields.append({
                        'field': field.name,
                        'old_value': str(old_value),
                        'new_value': str(new_value)
                    })

        # Create audit log entry
        MaintenanceAuditLog.objects.create(
            request=instance,
            changed_fields=changed_fields,
            timestamp=timezone.now(),
            user=getattr(instance, '_changed_by', None)
        )

@receiver(staff_created)
def setup_staff_permissions(sender, user, staff_role, **kwargs):
    """
    Set up staff member permissions and initial configuration.

    Actions:
    1. Configure notification preferences based on role
    2. Set up default work schedule
    3. Create initial performance tracking record
    4. Send welcome notification
    """
    staff = user.staff

    # Role-based notification setup
    if staff_role in ['facility_manager', 'security_head']:
        staff.sms_notifications = True
        staff.urgent_only = False
    elif staff_role in ['electrician', 'plumber']:
        staff.sms_notifications = True
        staff.urgent_only = True

    staff.save()

    # Send welcome notification
    send_staff_welcome_notification.delay(user.id)
```

---

## 🎛️ Admin Interface

### Enhanced Admin Architecture (`backend/admin.py`)

```python
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """
    Comprehensive staff administration interface.

    Features:
    - Role-based filtering and search
    - Permission management
    - Performance tracking integration
    - Bulk operations for staff management
    """

    list_display = [
        'user', 'employee_id', 'staff_role', 'department',
        'employment_status', 'is_active', 'current_workload'
    ]

    list_filter = [
        'staff_role', 'employment_status', 'is_active', 'department',
        'can_access_all_maintenance', 'can_assign_requests'
    ]

    search_fields = [
        'user__username', 'user__email', 'user__name',
        'employee_id', 'phone_number', 'department'
    ]

    actions = ['activate_staff', 'deactivate_staff', 'reset_permissions']

    def current_workload(self, obj):
        """Display current workload for staff member."""
        return MaintenanceRequest.objects.filter(
            assigned_to=obj.user,
            status__in=['assigned', 'in_progress']
        ).count()
    current_workload.short_description = 'Active Requests'

    def activate_staff(self, request, queryset):
        """Bulk activate staff members."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} staff members activated.')

    def deactivate_staff(self, request, queryset):
        """Bulk deactivate staff members."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} staff members deactivated.')

    def reset_permissions(self, request, queryset):
        """Reset permissions to role defaults."""
        for staff in queryset:
            permissions = get_role_permissions(staff.staff_role)
            for perm, value in permissions.items():
                setattr(staff, perm, value)
            staff.save()
        self.message_user(request, f'Permissions reset for {queryset.count()} staff members.')

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    """
    Enhanced maintenance request administration.

    Features:
    - Staff assignment with filtering
    - Status workflow management
    - Cost tracking and analysis
    - Performance metrics integration
    """

    list_display = [
        'ticket_number', 'title', 'resident', 'category',
        'priority', 'status', 'assigned_to', 'is_overdue',
        'cost_variance', 'resident_rating'
    ]

    list_filter = [
        'status', 'priority', 'category', 'assigned_to',
        'created_at', 'resolved_at'
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize assignment field to show only suitable staff."""
        if db_field.name == "assigned_to":
            kwargs["queryset"] = User.objects.filter(
                user_type="staff",
                is_active=True,
                staff__is_active=True
            ).filter(
                Q(staff__can_access_all_maintenance=True) |
                Q(staff__staff_role__in=['electrician', 'plumber', 'maintenance_supervisor'])
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def is_overdue(self, obj):
        """Display overdue status with color coding."""
        return obj.is_overdue()
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    def cost_variance(self, obj):
        """Display cost variance (actual vs estimated)."""
        if obj.estimated_cost and obj.actual_cost:
            variance = obj.actual_cost - obj.estimated_cost
            return f"₹{variance:+.2f}"
        return "-"
    cost_variance.short_description = 'Cost Variance'

    actions = ['bulk_assign', 'mark_acknowledged', 'generate_report']

    def bulk_assign(self, request, queryset):
        """Bulk assign requests to staff members."""
        # Custom admin action for bulk operations
        pass
```

---

## 🧪 Testing Strategy

### Test Architecture Overview

```python
# Test structure and patterns

class TestMaintenanceWorkflow:
    """
    Integration tests for complete maintenance workflow.
    Tests the entire flow from submission to closure.
    """

    @pytest.fixture
    def setup_users(self):
        """Create test users with proper relationships."""
        # Create resident
        resident_user = User.objects.create_user(
            username='test_resident',
            email='resident@test.com',
            user_type='resident'
        )

        # Create staff members
        fm_user = User.objects.create_user(
            username='facility_manager',
            email='fm@test.com',
            user_type='staff'
        )

        facility_manager = Staff.objects.create(
            user=fm_user,
            employee_id='FM001',
            staff_role='facility_manager',
            can_access_all_maintenance=True,
            can_assign_requests=True,
            can_close_requests=True
        )

        return {
            'resident': resident_user,
            'facility_manager': facility_manager,
        }

    def test_complete_workflow(self, setup_users):
        """Test end-to-end maintenance workflow."""
        # 1. Create request
        request = MaintenanceRequest.objects.create(
            resident=setup_users['resident'],
            title='Test maintenance request',
            category=MaintenanceCategory.objects.create(name='Electrical'),
            priority=3,
            status='submitted'
        )

        # 2. Acknowledge
        request.status = 'acknowledged'
        request.save()
        assert request.acknowledged_at is not None

        # 3. Assign
        fm = setup_users['facility_manager']
        request.assign_to_staff(fm.user, fm.user)
        assert request.status == 'assigned'
        assert request.assigned_to == fm.user

        # 4. Complete workflow
        request.status = 'resolved'
        request.save()
        assert request.resolved_at is not None

        # 5. Verify resolution time calculation
        resolution_time = request.get_resolution_time()
        assert resolution_time is not None
```

### Factory Pattern Implementation

```python
# Enhanced factories for testing

class StaffFactory(DjangoModelFactory):
    """
    Factory for creating Staff instances with realistic data.
    Supports all staff roles with appropriate default permissions.
    """

    user = SubFactory(StaffUserFactory)
    employee_id = Faker("bothify", text="EMP###")
    staff_role = Faker("random_element", elements=[
        "facility_manager", "accountant", "electrician", "plumber"
    ])

    # Role-based permission assignment
    can_access_all_maintenance = LazyAttribute(
        lambda obj: obj.staff_role in ["facility_manager", "maintenance_supervisor"]
    )
    can_assign_requests = LazyAttribute(
        lambda obj: obj.staff_role in ["facility_manager", "maintenance_supervisor"]
    )

    class Meta:
        model = Staff
        django_get_or_create = ["employee_id"]

# Usage in tests
def test_staff_permissions():
    facility_manager = StaffFactory(staff_role="facility_manager")
    electrician = StaffFactory(staff_role="electrician")

    assert facility_manager.can_access_all_maintenance is True
    assert electrician.can_access_all_maintenance is False
```

---

## 📊 API Design Patterns

### RESTful API Structure (Future Enhancement)

```python
# api/serializers.py - DRF serializers for maintenance staff

class StaffSerializer(serializers.ModelSerializer):
    """
    Staff serializer with nested user information and computed fields.
    """
    user_details = UserSerializer(source='user', read_only=True)
    current_workload = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            'id', 'employee_id', 'staff_role', 'department',
            'user_details', 'current_workload', 'performance_metrics',
            'can_access_all_maintenance', 'can_assign_requests'
        ]

    def get_current_workload(self, obj):
        """Get current active requests assigned to staff."""
        return MaintenanceRequest.objects.filter(
            assigned_to=obj.user,
            status__in=['assigned', 'in_progress']
        ).count()

    def get_performance_metrics(self, obj):
        """Get performance metrics for staff member."""
        return MaintenanceAssignmentService.get_workload_stats(obj.user)

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    """
    Enhanced maintenance request serializer with staff assignment.
    """
    assigned_to_details = StaffSerializer(source='assigned_to.staff', read_only=True)
    resident_details = ResidentSerializer(source='resident.resident', read_only=True)
    suitable_staff = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = '__all__'

    def get_suitable_staff(self, obj):
        """Get list of staff members who can handle this request."""
        suitable = obj.get_suitable_staff()
        return StaffSerializer(suitable, many=True).data

# api/views.py - ViewSets for maintenance management

class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for maintenance request CRUD operations with role-based access.
    """
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsAuthenticated, MaintenancePermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'category', 'assigned_to']
    search_fields = ['title', 'description', 'ticket_number']
    ordering_fields = ['created_at', 'priority', 'estimated_completion']

    def get_queryset(self):
        """Return requests based on user permissions."""
        user = self.request.user

        if user.is_resident():
            return MaintenanceRequest.objects.filter(resident=user)
        elif user.is_staff_member() and user.staff.can_access_all_maintenance:
            return MaintenanceRequest.objects.all()
        elif user.is_staff_member():
            return MaintenanceRequest.objects.filter(assigned_to=user)

        return MaintenanceRequest.objects.none()

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign request to staff member."""
        maintenance_request = self.get_object()
        staff_user_id = request.data.get('staff_user_id')

        try:
            staff_user = User.objects.get(id=staff_user_id, user_type='staff')
            MaintenanceAssignmentService.assign_request(
                maintenance_request,
                staff_user,
                request.user
            )
            return Response({'status': 'assigned'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update request status with workflow validation."""
        maintenance_request = self.get_object()
        new_status = request.data.get('status')

        try:
            maintenance_request.transition_to(new_status, request.user)
            return Response({'status': 'updated'})
        except (InvalidTransition, PermissionDenied) as e:
            return Response({'error': str(e)}, status=400)

class StaffViewSet(viewsets.ModelViewSet):
    """
    Staff management ViewSet with performance tracking.
    """
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get performance metrics for staff member."""
        staff = self.get_object()
        metrics = generate_staff_performance_report.delay(staff.id, 'monthly')
        return Response({'report_id': metrics.id})

    @action(detail=True, methods=['get'])
    def workload(self, request, pk=None):
        """Get current workload for staff member."""
        staff = self.get_object()
        workload = MaintenanceAssignmentService.get_workload_stats(staff.user)
        return Response(workload)
```

---

## ⚡ Performance Considerations

### Database Optimization

```python
# Optimized queries for maintenance views

class OptimizedMaintenanceQuerySet(models.QuerySet):
    """
    Custom QuerySet with optimized queries for maintenance requests.
    """

    def with_staff_details(self):
        """Prefetch staff and user details to avoid N+1 queries."""
        return self.select_related(
            'resident',
            'assigned_to',
            'assigned_by',
            'category'
        ).prefetch_related(
            'assigned_to__staff',
            'updates__author'
        )

    def for_staff_dashboard(self, staff_user):
        """Optimized query for staff dashboard."""
        return self.with_staff_details().filter(
            assigned_to=staff_user
        ).order_by('-priority', '-created_at')

    def overdue_requests(self):
        """Get overdue requests with minimal queries."""
        return self.filter(
            estimated_completion__lt=timezone.now(),
            status__in=['assigned', 'in_progress']
        ).select_related('assigned_to', 'category')

class MaintenanceRequest(models.Model):
    objects = OptimizedMaintenanceQuerySet.as_manager()

    # ... model fields ...

# Usage in views
def staff_dashboard_view(request):
    # Optimized query - single DB hit
    my_requests = MaintenanceRequest.objects.for_staff_dashboard(request.user)

    # Aggregate data efficiently
    stats = MaintenanceRequest.objects.filter(
        assigned_to=request.user
    ).aggregate(
        total_assigned=Count('id'),
        completed_this_month=Count('id', filter=Q(
            status='closed',
            closed_at__month=timezone.now().month
        )),
        avg_rating=Avg('resident_rating', filter=Q(resident_rating__isnull=False))
    )
```

### Caching Strategy

```python
# Caching for frequently accessed data

from django.core.cache import cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def staff_performance_api(request, staff_id):
    """Cached staff performance data."""
    cache_key = f'staff_performance_{staff_id}_{timezone.now().date()}'

    performance_data = cache.get(cache_key)
    if not performance_data:
        performance_data = calculate_staff_performance(staff_id)
        cache.set(cache_key, performance_data, 60 * 60)  # Cache for 1 hour

    return JsonResponse(performance_data)

# Cache invalidation on status changes
@receiver(maintenance_status_changed)
def invalidate_performance_cache(sender, instance, **kwargs):
    """Invalidate cache when request status changes."""
    if instance.assigned_to:
        cache_key = f'staff_performance_{instance.assigned_to.staff.id}_*'
        cache.delete_pattern(cache_key)
```

---

## 🚀 Deployment & Migration Guide

### Migration Strategy

```bash
# Step-by-step migration for production deployment

# 1. Backup existing database
pg_dump the_khaki_estate > backup_pre_staff_system.sql

# 2. Apply migrations
uv run python manage.py migrate users 0002_user_user_type
uv run python manage.py migrate backend 0002_alter_maintenancerequest_options_and_more

# 3. Update existing users (if needed)
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
# Set user_type for existing users (defaults to 'resident')
User.objects.filter(user_type__isnull=True).update(user_type='resident')
"

# 4. Create initial staff members
uv run python manage.py create_initial_staff

# 5. Verify deployment
uv run python manage.py demo_staff_functionality --cleanup
```

### Environment Configuration

```python
# settings/production.py - Production settings for staff system

# Celery configuration for maintenance tasks
CELERY_BEAT_SCHEDULE = {
    'process-overdue-requests': {
        'task': 'the_khaki_estate.backend.tasks.process_overdue_requests',
        'schedule': crontab(minute=0),  # Every hour
    },
    'daily-maintenance-reports': {
        'task': 'the_khaki_estate.backend.tasks.generate_daily_reports',
        'schedule': crontab(hour=6, minute=0),  # 6 AM daily
    },
}

# Staff system configuration
STAFF_SYSTEM_CONFIG = {
    'MAX_CONCURRENT_ASSIGNMENTS': 10,  # Max requests per staff member
    'AUTO_ASSIGN_EMERGENCY': True,     # Auto-assign emergency requests
    'ESCALATION_HOURS': 24,            # Hours before escalation
    'PERFORMANCE_TRACKING': True,       # Enable performance tracking
}

# Notification settings
NOTIFICATION_SETTINGS = {
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'SMS_BACKEND': 'twilio',  # or your SMS provider
    'URGENT_NOTIFICATION_CHANNELS': ['email', 'sms', 'in_app'],
    'NORMAL_NOTIFICATION_CHANNELS': ['email', 'in_app'],
}
```

### Monitoring & Logging

```python
# Enhanced logging for maintenance system

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'maintenance_formatter': {
            'format': '{levelname} {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'maintenance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/maintenance.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'maintenance_formatter',
        },
    },
    'loggers': {
        'the_khaki_estate.backend.maintenance': {
            'handlers': ['maintenance_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'the_khaki_estate.backend.tasks': {
            'handlers': ['maintenance_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Usage in views and tasks
import logging

logger = logging.getLogger('the_khaki_estate.backend.maintenance')

def assign_maintenance_request(request, staff_user, assigned_by):
    """Log all assignment operations for audit trail."""
    logger.info(
        f"Maintenance assignment: {request.ticket_number} "
        f"assigned to {staff_user.username} by {assigned_by.username}"
    )

    try:
        result = MaintenanceAssignmentService.assign_request(request, staff_user, assigned_by)
        logger.info(f"Assignment successful: {request.ticket_number}")
        return result
    except Exception as e:
        logger.error(f"Assignment failed: {request.ticket_number} - {str(e)}")
        raise
```

---

## 🔍 Debugging & Development Tools

### Management Commands

```python
# backend/management/commands/maintenance_diagnostics.py

class Command(BaseCommand):
    """
    Diagnostic command for maintenance system debugging.
    """
    help = 'Run diagnostics on maintenance staff system'

    def add_arguments(self, parser):
        parser.add_argument('--check-permissions', action='store_true')
        parser.add_argument('--verify-assignments', action='store_true')
        parser.add_argument('--performance-report', action='store_true')

    def handle(self, *args, **options):
        if options['check_permissions']:
            self.check_staff_permissions()

        if options['verify_assignments']:
            self.verify_request_assignments()

        if options['performance_report']:
            self.generate_system_performance_report()

    def check_staff_permissions(self):
        """Verify all staff have correct permissions for their roles."""
        for staff in Staff.objects.all():
            expected_perms = get_role_permissions(staff.staff_role)
            actual_perms = {
                'can_access_all_maintenance': staff.can_access_all_maintenance,
                'can_assign_requests': staff.can_assign_requests,
                'can_close_requests': staff.can_close_requests,
                'can_manage_finances': staff.can_manage_finances,
                'can_send_announcements': staff.can_send_announcements,
            }

            mismatches = []
            for perm, expected in expected_perms.items():
                if actual_perms.get(perm) != expected:
                    mismatches.append(f"{perm}: expected {expected}, got {actual_perms.get(perm)}")

            if mismatches:
                self.stdout.write(
                    self.style.WARNING(f"Permission mismatches for {staff}: {mismatches}")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Permissions correct for {staff}")
                )
```

### Development Utilities

```python
# utils/development.py - Development utilities

def create_sample_maintenance_scenario():
    """
    Create a complete sample maintenance scenario for testing.
    Useful for development and demonstration.
    """
    # Create users
    resident = create_test_resident('alice', 'alice@test.com', '101')
    fm = create_test_staff('john', 'facility_manager', 'FM001')
    electrician = create_test_staff('mike', 'electrician', 'EL001')

    # Create maintenance request
    request = MaintenanceRequest.objects.create(
        resident=resident,
        title='Electrical outlet not working',
        description='Kitchen outlet stopped working after power outage',
        category=MaintenanceCategory.objects.get(name='Electrical'),
        location='Flat 101',
        priority=3,
        status='submitted'
    )

    # Simulate workflow
    request.status = 'acknowledged'
    request.save()

    request.assign_to_staff(electrician, fm)

    return {
        'request': request,
        'resident': resident,
        'facility_manager': fm,
        'electrician': electrician
    }

def reset_maintenance_system():
    """Reset maintenance system to clean state (development only)."""
    MaintenanceRequest.objects.all().delete()
    Staff.objects.all().delete()
    User.objects.filter(user_type='staff').delete()
    print("Maintenance system reset to clean state")
```

---

## 📈 Analytics & Reporting

### Performance Metrics Calculation

```python
# analytics/maintenance_metrics.py

class MaintenanceAnalytics:
    """
    Analytics engine for maintenance system performance tracking.
    """

    @staticmethod
    def calculate_staff_efficiency(staff_user, period_days=30):
        """
        Calculate comprehensive staff efficiency metrics.

        Returns:
            dict: Performance metrics including resolution time,
                  satisfaction scores, cost efficiency
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)

        requests = MaintenanceRequest.objects.filter(
            assigned_to=staff_user,
            created_at__range=[start_date, end_date]
        )

        completed_requests = requests.filter(status='closed')

        metrics = {
            'total_requests': requests.count(),
            'completed_requests': completed_requests.count(),
            'completion_rate': completed_requests.count() / max(requests.count(), 1),
            'avg_resolution_time': calculate_avg_resolution_time(completed_requests),
            'avg_satisfaction': completed_requests.aggregate(
                avg_rating=Avg('resident_rating')
            )['avg_rating'] or 0,
            'cost_efficiency': calculate_cost_efficiency(completed_requests),
            'on_time_completion_rate': calculate_on_time_rate(completed_requests),
        }

        return metrics

    @staticmethod
    def system_performance_dashboard():
        """Generate system-wide performance dashboard data."""
        return {
            'total_active_requests': MaintenanceRequest.objects.filter(
                status__in=['submitted', 'acknowledged', 'assigned', 'in_progress']
            ).count(),
            'overdue_requests': MaintenanceRequest.objects.filter(
                estimated_completion__lt=timezone.now(),
                status__in=['assigned', 'in_progress']
            ).count(),
            'avg_resolution_time': calculate_system_avg_resolution(),
            'staff_utilization': calculate_staff_utilization(),
            'cost_trends': calculate_monthly_cost_trends(),
            'satisfaction_trends': calculate_satisfaction_trends(),
        }

def calculate_avg_resolution_time(queryset):
    """Calculate average resolution time for request queryset."""
    completed = queryset.filter(
        resolved_at__isnull=False,
        created_at__isnull=False
    )

    if not completed.exists():
        return timedelta(0)

    total_time = sum(
        (req.resolved_at - req.created_at).total_seconds()
        for req in completed
    )

    return timedelta(seconds=total_time / completed.count())
```

---

## 📚 Documentation Management

### Documentation Architecture

The project uses a dual documentation system:

#### **MkDocs System** (Primary Documentation)
- **Port**: 8000
- **Purpose**: General project documentation
- **Management**: Elaborate service system for automated startup [[memory:8555301]]
- **Status**: Always running via service

#### **Sphinx System** (Django-Specific Documentation)
- **Port**: 8080 (static) / 9000 (live reload)
- **Purpose**: Django project documentation with auto-generated API docs
- **Content**: Technical documentation, user guides, API references
- **Features**: Markdown support via MyST parser, auto-generated API docs

### Documentation Server Management

#### **After System Restart Workflow**

```bash
# 1. MkDocs (handled by your service system)
# Automatically starts on port 8000

# 2. Django Development Server
cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate
uv run python manage.py runserver 8001

# 3. Sphinx Documentation (when needed)
cd docs
uv run make html && cd _build/html && python -m http.server 8080

# Alternative: Sphinx with live reload
cd docs && uv run make livehtml  # Serves on port 9000
```

#### **Port Allocation Strategy**

| Service | Port | Purpose | Command |
|---------|------|---------|---------|
| **MkDocs** | 8000 | Primary documentation | Service system |
| **Django Dev** | 8001 | Application development | `runserver 8001` |
| **Sphinx Static** | 8080 | Project documentation | `http.server 8080` |
| **Sphinx Live** | 9000 | Documentation development | `make livehtml` |

#### **Documentation Update Workflow**

```bash
# 1. Update Markdown files in project root
vim TECHNICAL_DOCUMENTATION.md
vim USER_GUIDE.md
vim RESIDENT_REGISTRATION_GUIDE.md

# 2. Copy to Sphinx docs directory
cp TECHNICAL_DOCUMENTATION.md USER_GUIDE.md RESIDENT_REGISTRATION_GUIDE.md docs/

# 3. Rebuild Sphinx documentation
cd docs && uv run make html

# 4. Commit documentation changes
git add TECHNICAL_DOCUMENTATION.md USER_GUIDE.md RESIDENT_REGISTRATION_GUIDE.md docs/
git commit -m "docs: Update project documentation"
git push
```

#### **Sphinx Configuration**

```python
# docs/conf.py - MyST Parser Configuration
extensions = [
    "sphinx.ext.autodoc",      # Auto-generate API docs
    "sphinx.ext.napoleon",     # Google/NumPy docstring support
    "myst_parser",             # Markdown support
]

# MyST parser configuration for enhanced Markdown features
myst_enable_extensions = [
    "deflist",           # Definition lists
    "tasklist",          # Task lists with checkboxes
    "html_admonition",   # HTML-style admonitions
    "html_image",        # HTML image support
]

# Support both RST and Markdown files
source_suffix = ['.rst', '.md']
```

#### **Available Documentation Commands**

```bash
# Build static documentation
cd docs && uv run make html

# Serve with live reload (auto-rebuild on changes)
cd docs && uv run make livehtml

# Generate API documentation from Django code
cd docs && uv run make apidocs

# Clean build directory
cd docs && uv run make clean

# Build and serve on custom port
cd docs && uv run make html && cd _build/html && python -m http.server 8080
```

#### **Documentation Development Aliases**

Add to `~/.zshrc` for convenience:

```bash
# Documentation management aliases
alias khaki-docs-build="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate/docs && uv run make html"
alias khaki-docs-serve="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate/docs/_build/html && python -m http.server 8080"
alias khaki-docs-live="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate/docs && uv run make livehtml"
alias khaki-docs-update="cp TECHNICAL_DOCUMENTATION.md USER_GUIDE.md RESIDENT_REGISTRATION_GUIDE.md docs/ && cd docs && uv run make html"

# Django development aliases
alias khaki-django="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate && uv run python manage.py runserver 8001"
alias khaki-celery="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate && uv run celery -A config.celery_app worker -l info"
alias khaki-test="cd /Users/sanjaysingh/non_icloud/software_development_MBP_2025/the_khaki_estate && uv run pytest -v"
```

#### **Documentation Access URLs**

- **MkDocs Documentation**: http://localhost:8000
- **Django Application**: http://localhost:8001
- **Sphinx Documentation**: http://localhost:8080
- **Sphinx Live Reload**: http://localhost:9000

## 🔧 Development Commands

### Useful Management Commands

```bash
# Create sample data for development
uv run python manage.py demo_staff_functionality

# Check system health
uv run python manage.py maintenance_diagnostics --check-permissions --verify-assignments

# Generate performance reports
uv run python manage.py generate_staff_reports --period monthly

# Reset development data
uv run python manage.py flush_maintenance_data --confirm

# Test notification system
uv run python manage.py test_notifications --staff-id 1 --type assignment

# Validate database integrity
uv run python manage.py validate_maintenance_integrity
```

### Testing Commands

```bash
# Run comprehensive test suite
uv run pytest the_khaki_estate/backend/tests/ -v --cov=the_khaki_estate

# Run specific test categories
uv run pytest the_khaki_estate/backend/tests/test_staff_functionality_simple.py -v
uv run pytest the_khaki_estate/backend/tests/test_maintenance_workflow.py -v
uv run pytest the_khaki_estate/users/tests/test_staff_forms.py -v

# Run performance tests
uv run pytest the_khaki_estate/backend/tests/test_performance.py -v --benchmark

# Test with different database backends
uv run pytest --ds=config.settings.test_postgresql
uv run pytest --ds=config.settings.test_sqlite
```

---

## 📚 Code Examples & Patterns

### Common Usage Patterns

```python
# 1. Creating a facility manager
def create_facility_manager(username, email, name, employee_id):
    """Standard pattern for creating facility manager."""
    user = User.objects.create_user(
        username=username,
        email=email,
        name=name,
        user_type='staff'
    )

    staff = Staff.objects.create(
        user=user,
        employee_id=employee_id,
        staff_role='facility_manager',
        department='Management',
        hire_date=timezone.now().date(),
        can_access_all_maintenance=True,
        can_assign_requests=True,
        can_close_requests=True,
        can_send_announcements=True,
    )

    return user, staff

# 2. Assignment workflow
def assign_electrical_request(request_id, electrician_id, facility_manager_id):
    """Standard pattern for assigning electrical requests."""
    request = MaintenanceRequest.objects.get(id=request_id)
    electrician = User.objects.get(id=electrician_id)
    fm = User.objects.get(id=facility_manager_id)

    # Validate assignment
    if not request.can_be_assigned_to(electrician):
        raise ValidationError("Electrician cannot handle this request")

    # Perform assignment
    request.assign_to_staff(electrician, fm)

    # Set estimated completion based on category
    hours = request.category.estimated_resolution_hours
    request.estimated_completion = timezone.now() + timedelta(hours=hours)
    request.save()

    return request

# 3. Status update with validation
def update_request_status(request_id, new_status, user, notes=None):
    """Standard pattern for status updates with validation."""
    request = MaintenanceRequest.objects.get(id=request_id)

    # Permission check
    if not can_update_status(user, request, new_status):
        raise PermissionDenied("User cannot update to this status")

    # Status transition
    old_status = request.status
    request.status = new_status
    request.save()

    # Add update note
    if notes:
        MaintenanceUpdate.objects.create(
            request=request,
            author=user,
            content=notes,
            status_changed_to=new_status
        )

    # Trigger notifications
    notify_status_change.delay(request.id, old_status, new_status)

    return request
```

---

## 🎯 Best Practices & Guidelines

### Code Organization

```
the_khaki_estate/
├── backend/
│   ├── models.py           # Core business models
│   ├── views.py            # View logic with permission mixins
│   ├── admin.py            # Enhanced admin interfaces
│   ├── tasks.py            # Background tasks and workflows
│   ├── signals.py          # Event handling and notifications
│   ├── services/           # Business logic services
│   │   ├── assignment.py   # Assignment logic
│   │   ├── analytics.py    # Performance analytics
│   │   └── notifications.py # Notification management
│   ├── utils/              # Utility functions
│   └── tests/              # Comprehensive test suite
├── users/
│   ├── models.py           # Enhanced User model
│   ├── forms.py            # Registration and profile forms
│   ├── admin.py            # User administration
│   └── tests/              # User-related tests
└── config/
    ├── settings/           # Environment-specific settings
    └── celery_app.py       # Celery configuration
```

### Development Workflow

1. **Model Changes**: Always create migrations and test thoroughly
2. **Permission Updates**: Update both model permissions and view checks
3. **Signal Integration**: Use signals for loose coupling between components
4. **Task Processing**: Use Celery for long-running operations
5. **Testing**: Write tests for all new functionality
6. **Documentation**: Update both user and technical documentation

### Security Considerations

- **Permission Validation**: Always check permissions at both view and model level
- **SQL Injection**: Use Django ORM exclusively, avoid raw SQL
- **CSRF Protection**: Ensure all forms have CSRF tokens
- **Input Validation**: Validate all user inputs at form and model level
- **Audit Trail**: Log all significant actions for compliance
- **Data Privacy**: Ensure staff can only access data they're authorized for

---

## 🚀 Future Enhancements

### Planned Features

1. **Mobile API**: RESTful API for mobile staff applications
2. **Real-time Updates**: WebSocket integration for live status updates
3. **Advanced Analytics**: Machine learning for predictive maintenance
4. **Integration APIs**: Third-party service provider integration
5. **Workflow Automation**: Rules engine for automatic assignment
6. **Performance Dashboards**: Real-time performance monitoring

### Scalability Considerations

- **Database Sharding**: Partition data by building/complex
- **Caching Layer**: Redis for frequently accessed data
- **Load Balancing**: Multiple app servers with shared database
- **File Storage**: Cloud storage for attachments and documents
- **Monitoring**: Application performance monitoring (APM)

---

**This technical documentation is maintained alongside the codebase. For questions or contributions, please refer to the development team or create an issue in the project repository.**

**Last Updated**: September 21, 2025
### **Template Architecture Best Practices**

```python
# CRITICAL: Avoid template variable naming conflicts
# BAD - overwrites Django's request context
context = {
    "request": maintenance_request,  # ❌ Conflicts with HTTP request
}

# GOOD - uses descriptive names
context = {
    "maintenance_request": maintenance_request,  # ✅ Clear and specific
    "can_manage": can_manage_maintenance(request.user),
}

# Template usage
# BAD: {{ request.title }} - breaks authentication context
# GOOD: {{ maintenance_request.title }} - preserves request.user
```

**Documentation Version**: 2.3
**System Version**: The Khaki Estate Management System v2.3
