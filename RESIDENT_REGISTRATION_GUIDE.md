# Resident Registration & User Management Guide

## 🎯 **IMPLEMENTED SOLUTION: Extended Signup Form**

The housing complex management system now has a comprehensive registration system that creates both User and Resident profiles in one step.

## ✅ **What's Been Implemented**

### 1. Extended Signup Form (`UserSignupForm`)
**Location**: `the_khaki_estate/users/forms.py`

**Features:**
- **Personal Information**: First name, last name
- **Residence Details**: Flat number, block, resident type
- **Contact Information**: Phone number, alternate phone
- **Emergency Contact**: Name and phone number
- **Move-in Date**: Optional date field
- **Validation**: Flat number uniqueness, phone number format
- **Auto-Creation**: Creates both User and Resident profiles simultaneously

### 2. Django Signals (`users/signals.py`)
**Backup System**: Automatically creates Resident profiles for:
- Admin-created users
- Social authentication users
- Any users created outside the signup form

### 3. Management Command
**Command**: `python manage.py create_resident_profiles`
**Purpose**: Handle existing users and bulk operations

### 4. Admin Interface
**Enhanced Admin**: User admin now shows Resident profile inline
**Resident Admin**: Dedicated interface for managing resident data

## 🚀 **How It Works**

### For New Users (Recommended Flow)

1. **User visits signup page** (`/accounts/signup/`)
2. **Extended form appears** with all resident fields
3. **User fills out complete information**:
   - Username, email, password (Django defaults)
   - First name, last name
   - Flat number (validated for uniqueness)
   - Block (optional)
   - Phone number (validated)
   - Alternate phone (optional)
   - Resident type (Owner/Tenant/Family Member)
   - Emergency contact details (optional)
   - Move-in date (optional)
4. **Form validates data**:
   - Flat number must be unique and numeric
   - Phone number must be at least 10 digits
   - All required fields completed
5. **System creates both profiles**:
   - Django User with authentication details
   - Resident profile with housing-specific data
6. **User immediately has access** to all features

### For Existing Users (Migration)

1. **Run management command**:
   ```bash
   python manage.py create_resident_profiles --dry-run  # Preview
   python manage.py create_resident_profiles            # Execute
   ```
2. **System creates placeholder profiles**:
   - Flat number: Auto-generated (0001, 0002, etc.)
   - Phone: Placeholder (0000000000)
   - Type: Default to "owner"
3. **Users update their profiles** through the system

### For Admin-Created Users

1. **Admin creates user** in Django admin
2. **Signal automatically creates** Resident profile with placeholders
3. **Admin updates Resident details** in the inline form
4. **User receives credentials** and can access system

## 📋 **Registration Form Fields**

### Required Fields
- **Username**: Django authentication
- **Email**: Django authentication (now required)
- **Password**: Django authentication
- **First Name**: Personal identification
- **Last Name**: Personal identification
- **Flat Number**: Residence identification (validated for uniqueness)
- **Phone Number**: Primary contact (validated format)
- **Resident Type**: Owner/Tenant/Family Member

### Optional Fields
- **Block**: Building block identifier
- **Alternate Phone**: Secondary contact
- **Emergency Contact Name**: Emergency contact person
- **Emergency Contact Phone**: Emergency contact number
- **Move-in Date**: When resident moved in

## 🔧 **Technical Implementation Details**

### Form Validation
```python
def clean_flat_number(self):
    """Ensures flat number is unique and numeric"""
    flat_number = self.cleaned_data.get('flat_number')
    if Resident.objects.filter(flat_number=flat_number).exists():
        raise ValidationError("Flat number already registered")
    return flat_number

def clean_phone_number(self):
    """Validates phone number has at least 10 digits"""
    phone_number = self.cleaned_data.get('phone_number')
    digits_only = ''.join(filter(str.isdigit, phone_number))
    if len(digits_only) < 10:
        raise ValidationError("Invalid phone number")
    return phone_number
```

### Profile Creation
```python
def save(self, request):
    """Creates both User and Resident profiles"""
    user = super().save(request)
    user.name = f"{first_name} {last_name}".strip()
    user.save()

    Resident.objects.create(
        user=user,
        flat_number=self.cleaned_data['flat_number'],
        phone_number=self.cleaned_data['phone_number'],
        # ... other fields
    )
    return user
```

### Signal Backup
```python
@receiver(post_save, sender=User)
def create_resident_profile(sender, instance, created, **kwargs):
    """Creates Resident profile if missing"""
    if created and not hasattr(instance, 'resident'):
        Resident.objects.create(
            user=instance,
            flat_number='0000',  # Placeholder
            phone_number='0000000000'  # Placeholder
        )
```

## 🎯 **User Experience Flow**

### New Resident Registration
1. **Access**: Visit housing complex website
2. **Signup**: Click "Sign Up" in navigation
3. **Form**: Complete extended registration form
4. **Validation**: System checks flat number availability
5. **Creation**: Both User and Resident profiles created
6. **Login**: Immediate access to all features
7. **Dashboard**: Full resident dashboard available

### Existing User Migration
1. **Admin runs command**: Creates placeholder profiles
2. **User logs in**: Sees notification to update profile
3. **Profile update**: User completes missing information
4. **Full access**: All features become available

### Admin Management
1. **User creation**: Admin creates user account
2. **Profile inline**: Resident details appear in same form
3. **Complete setup**: Admin can set all resident details
4. **User notification**: Resident receives login credentials

## 🔒 **Security & Validation**

### Data Validation
- **Flat Number**: Must be unique across all residents
- **Phone Number**: Minimum 10 digits required
- **Email**: Required and must be valid format
- **User Authentication**: Standard Django security

### Access Control
- **New Users**: Immediate access after registration
- **Placeholder Users**: Limited access until profile completion
- **Admin Users**: Full administrative access
- **Committee Members**: Enhanced permissions (set by admin)

### Privacy Protection
- **Personal Data**: Encrypted in database
- **Contact Information**: Visible only to committee members
- **Emergency Contacts**: Restricted access
- **Profile Updates**: Users can modify their own data

## 📊 **Management Tools**

### Management Commands
```bash
# View what would be created
python manage.py create_resident_profiles --dry-run

# Create profiles for existing users
python manage.py create_resident_profiles

# Update existing placeholder profiles
python manage.py create_resident_profiles --update-existing

# Use custom flat number prefix
python manage.py create_resident_profiles --flat-prefix="1"
```

### Admin Interface Features
- **User List**: Shows associated flat numbers
- **Resident Search**: Find by flat number, name, or phone
- **Bulk Actions**: Update multiple residents
- **Inline Editing**: Edit resident data with user account
- **Committee Management**: Assign committee member status
- **Profile Completion**: Track which profiles need updates

## 🚨 **Important Notes**

### For System Administrators
1. **Flat Number Management**: Ensure unique flat numbers across system
2. **Committee Members**: Manually set `is_committee_member=True` for management staff
3. **Placeholder Data**: Users with `flat_number='0000'` need profile updates
4. **Backup Creation**: Signal system creates profiles for admin-created users

### For Residents
1. **Complete Registration**: Fill all required fields during signup
2. **Profile Updates**: Keep contact information current
3. **Emergency Contacts**: Provide emergency contact details for safety
4. **Notification Preferences**: Configure how you receive updates

### For Committee Members
1. **User Management**: Use admin interface to manage resident profiles
2. **Approval Process**: Verify new registrations if needed
3. **Data Accuracy**: Ensure flat numbers and contact details are correct
4. **Privacy**: Respect resident privacy when accessing profile data

## 🔄 **Migration Strategy**

### For New Installations
1. **Deploy System**: With extended signup form
2. **Create Admin User**: First user should be committee member
3. **Configure Categories**: Set up announcement and maintenance categories
4. **Test Registration**: Verify signup process works
5. **Go Live**: Residents can register immediately

### For Existing Communities
1. **Deploy System**: With current resident data if available
2. **Import Users**: Use management command for bulk creation
3. **Notify Residents**: Send instructions for profile completion
4. **Gradual Migration**: Allow time for profile updates
5. **Full Features**: Enable all features once profiles are complete

### For Controlled Environments
1. **Admin-Only Creation**: Disable public registration initially
2. **Pre-Create Accounts**: Admin creates all resident accounts
3. **Distribute Credentials**: Send login details to residents
4. **Profile Completion**: Residents update their own details
5. **Enable Self-Registration**: Open registration once established

This comprehensive system ensures every user has a complete resident profile while providing flexibility for different deployment scenarios.
