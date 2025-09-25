from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from .models import User


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        error_messages = {
            "username": {"unique": _("This username has already been taken.")},
        }


class NewUserSignupForm(SignupForm):
    """
    New signup form with improved workflow for Owner Resident signup.
    
    Workflow:
    1. User Type (topmost field)
    2. Resident Type (if Resident selected)
    3. Flat Number (if Resident + Owner selected) - with autocomplete
    4. Auto-populated fields from database (Email, First name, Last name, Block, Phone)
    5. Emergency contact fields, Move in date, Password, Username
    
    For Tenants and Staff: Dynamic form fields (existing workflow)
    """

    # 1. USER TYPE - Topmost field
    USER_TYPE_CHOICES = [
        ("", "Select User Type"),  # Default empty option
        ("resident", "Resident"),
        ("staff", "Staff"),
    ]
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "id_user_type",
            },
        ),
        help_text="Are you a resident or staff member?",
    )

    # 2. RESIDENT TYPE - Second field (shown for residents)
    RESIDENT_TYPES = [
        ("", "Select Resident Type"),  # Default empty option
        ("owner", "Owner"),
        ("tenant", "Tenant"),
    ]
    resident_type = forms.ChoiceField(
        choices=RESIDENT_TYPES,
        required=False,  # Will be required conditionally via JavaScript validation
        widget=forms.Select(
            attrs={
                "class": "form-control resident-field",
                "id": "id_resident_type",
                "style": "display: none;",  # Hidden initially
            },
        ),
        help_text="Your relationship to the property",
    )

    # 3. FLAT NUMBER - Third field (shown for Resident + Owner)
    flat_number = forms.CharField(
        max_length=10,  # Keep original format (e.g., A-101, C1-201)
        required=False,  # Will be required conditionally
        widget=forms.TextInput(
            attrs={
                "placeholder": "Start typing flat number (e.g., A-101)",
                "class": "form-control owner-field",
                "id": "id_flat_number",
                "onblur": "fetchResidentData()",
                "oninput": "filterFlatNumbers()",
                "autocomplete": "off",
                "style": "display: none;",  # Hidden initially
            },
        ),
        help_text="Your flat/apartment number (will auto-populate other fields)",
    )

    # Hidden field to store resident_id for existing owners
    resident_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(
            attrs={
                "id": "id_resident_id",
            },
        ),
    )

    # 4. AUTO-POPULATED FIELDS (read-only for owners, editable for others)
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name",
                "class": "form-control",
                "id": "id_first_name",
                "readonly": False,  # Will be set readonly for owners
            },
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "class": "form-control",
                "id": "id_last_name",
                "readonly": False,  # Will be set readonly for owners
            },
        ),
    )

    # Email field (inherited from SignupForm, but we'll customize it)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required and add styling
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update({
            "class": "form-control",
            "id": "id_email",
            "readonly": False,  # Will be set readonly for owners
        })
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "id": "id_username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "id": "id_password1",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "id": "id_password2",
        })

    # Block field (auto-populated for owners)
    block = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Block (e.g., A)",
                "class": "form-control owner-field",
                "id": "id_block",
                "readonly": True,  # Read-only for owners
                "style": "display: none;",  # Hidden initially
            },
        ),
        help_text="Building block (auto-populated for owners)",
    )

    # Phone number (auto-populated for owners)
    phone_number = forms.CharField(
        max_length=13,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Phone number must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757",
                "class": "form-control",
                "id": "id_phone_number",
                "pattern": r"^\+\d{12}$",
                "readonly": False,  # Will be set readonly for owners
            },
        ),
        help_text="Your primary contact number (format: +919830425757)",
    )

    # 5. DYNAMIC FIELDS (shown for tenants/staff, hidden for owners)
    alternate_phone = forms.CharField(
        max_length=13,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Alternate phone must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_alternate_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757 (optional)",
                "class": "form-control dynamic-field",
                "id": "id_alternate_phone",
                "pattern": r"^\+\d{12}$",
                "style": "display: none;",  # Hidden initially
            },
        ),
        help_text="Alternate contact number (optional, format: +919830425757)",
    )

    # Emergency Contact
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Emergency Contact Name",
                "class": "form-control",
                "id": "id_emergency_contact_name",
            },
        ),
    )
    emergency_contact_phone = forms.CharField(
        max_length=13,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Emergency contact phone must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_emergency_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757 (optional)",
                "class": "form-control",
                "id": "id_emergency_contact_phone",
                "pattern": r"^\+\d{12}$",
            },
        ),
        help_text="Emergency contact phone number (optional, format: +919830425757)",
    )

    # Move-in Date
    move_in_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
                "id": "id_move_in_date",
            },
        ),
        help_text="When did you move in? (optional)",
    )

    def clean_user_type(self):
        """Validate that user_type is selected"""
        user_type = self.cleaned_data.get("user_type")
        if not user_type:
            raise forms.ValidationError(
                "Please select whether you are a resident or staff member.",
            )
        return user_type

    def clean_resident_type(self):
        """Validate resident_type is provided when user_type is resident"""
        user_type = self.cleaned_data.get("user_type")
        resident_type = self.cleaned_data.get("resident_type")

        if user_type == "resident" and not resident_type:
            raise forms.ValidationError("Please select your resident type.")

        return resident_type

    def clean_flat_number(self):
        """Validate flat number format and uniqueness for residents only"""
        user_type = self.cleaned_data.get("user_type")
        resident_type = self.cleaned_data.get("resident_type")
        flat_number = self.cleaned_data.get("flat_number")

        # Only validate flat number for residents
        if user_type == "resident":
            if not flat_number:
                raise forms.ValidationError("Flat number is required for residents.")

            # Import here to avoid circular imports
            from the_khaki_estate.backend.models import Resident

            # Check if flat number already exists (for new signups, not existing owners)
            resident_id = self.cleaned_data.get("resident_id")
            # If resident_id is not in cleaned_data yet, try to get it from raw data
            if not resident_id and hasattr(self, 'data'):
                resident_id = self.data.get("resident_id")
                if resident_id:
                    try:
                        resident_id = int(resident_id)
                    except (ValueError, TypeError):
                        resident_id = None
            
            if not resident_id:  # Only check if this is a new resident
                # Allow multiple residents per flat (owner + tenant)
                # Only prevent if there's already a resident of the same type
                existing_residents = Resident.objects.filter(
                    flat_number=flat_number,
                    resident_type=resident_type
                )
                if existing_residents.exists():
                    raise forms.ValidationError(
                        f"This flat number already has a {resident_type}. Please contact management if this is an error.",
                    )
            else:
                # If resident_id is provided, verify it matches the flat number
                try:
                    existing_resident = Resident.objects.get(id=resident_id)
                    if existing_resident.flat_number != flat_number:
                        raise forms.ValidationError(
                            "Selected flat number doesn't match the resident record.",
                        )
                    
                    # For tenants: Allow selection of flats that already have owners
                    # For owners: Prevent selection of flats that already have users
                    if existing_resident.user is not None and resident_type == "owner":
                        raise forms.ValidationError(
                            "This resident record is already linked to a user account.",
                        )
                    # For tenants, we allow selection of occupied flats (existing_resident.user is not None)
                    # This is the expected behavior - tenants can rent flats that have owners
                    
                except Resident.DoesNotExist:
                    raise forms.ValidationError(
                        "Invalid resident record selected.",
                    )

        elif user_type == "staff" and flat_number:
            # Clear flat number for staff users
            flat_number = ""

        return flat_number

    def clean_phone_number(self):
        """Validate phone number format - already handled by RegexValidator"""
        phone_number = self.cleaned_data.get("phone_number")
        # RegexValidator already ensures the format is correct
        return phone_number

    def clean_alternate_phone(self):
        """Validate alternate phone number format"""
        alternate_phone = self.cleaned_data.get("alternate_phone")
        # Only validate if provided (field is optional)
        if alternate_phone and alternate_phone.strip():
            # RegexValidator already handles the format validation
            pass
        return alternate_phone

    def clean_emergency_contact_phone(self):
        """Validate emergency contact phone number format"""
        emergency_phone = self.cleaned_data.get("emergency_contact_phone")
        # Only validate if provided (field is optional)
        if emergency_phone and emergency_phone.strip():
            # RegexValidator already handles the format validation
            pass
        return emergency_phone

    def save(self, request):
        """Create User and appropriate profile (Resident or Staff)"""
        from django.db import transaction
        from django.utils import timezone

        from the_khaki_estate.backend.models import Resident
        from the_khaki_estate.backend.models import Staff

        # Use atomic transaction to ensure both User and profile are created together
        with transaction.atomic():
            # Temporarily disable the signal to prevent interference
            from django.db.models.signals import post_save
            from the_khaki_estate.users.signals import create_resident_profile

            # Disconnect the signal temporarily
            post_save.disconnect(create_resident_profile, sender=User)

            try:
                # Save the user first
                user = super().save(request)

                # Set the user's name and type from form data
                user.name = f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}".strip()
                user.first_name = self.cleaned_data.get("first_name", "")
                user.last_name = self.cleaned_data.get("last_name", "")
                user.user_type = self.cleaned_data["user_type"]
                user.save()

            finally:
                # Reconnect the signal
                post_save.connect(create_resident_profile, sender=User)

            # Create appropriate profile based on user type
            if user.user_type == "resident":
                resident_type = self.cleaned_data["resident_type"]
                resident_id = self.cleaned_data.get("resident_id")
                
                if resident_type == "owner" and resident_id:
                    # This is an existing owner - update the existing resident record
                    try:
                        existing_resident = Resident.objects.get(id=resident_id)
                        existing_resident.user = user
                        existing_resident.move_in_date = self.cleaned_data.get("move_in_date")
                        existing_resident.emergency_contact_name = self.cleaned_data.get(
                            "emergency_contact_name", ""
                        )
                        existing_resident.emergency_contact_phone = self.cleaned_data.get(
                            "emergency_contact_phone", ""
                        )
                        existing_resident.alternate_phone = self.cleaned_data.get(
                            "alternate_phone", ""
                        )
                        existing_resident.save()
                    except Resident.DoesNotExist:
                        # Fallback to creating new resident
                        self._create_new_resident(user)
                        
                elif resident_type == "tenant" and resident_id:
                    # This is a tenant selecting an existing flat - create new resident record
                    # Get flat information from the owner's resident record
                    try:
                        owner_resident = Resident.objects.get(id=resident_id)
                        self._create_tenant_resident(user, owner_resident)
                    except Resident.DoesNotExist:
                        # Fallback to creating new resident with provided flat number
                        self._create_new_resident(user)
                        
                else:
                    # This is a new resident (family member, or new owner without resident_id)
                    self._create_new_resident(user)

            elif user.user_type == "staff":
                # For staff users, create a basic staff profile
                self._create_staff_profile(user)

        return user

    def _create_new_resident(self, user):
        """Create a new resident profile"""
        from the_khaki_estate.backend.models import Resident
        
        Resident.objects.create(
            user=user,
            flat_number=self.cleaned_data["flat_number"],
            block=self.cleaned_data.get("block", ""),
            phone_number=self.cleaned_data["phone_number"],
            alternate_phone=self.cleaned_data.get("alternate_phone", ""),
            resident_type=self.cleaned_data["resident_type"],
            emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
            emergency_contact_phone=self.cleaned_data.get("emergency_contact_phone", ""),
            move_in_date=self.cleaned_data.get("move_in_date"),
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
            is_committee_member=False,
        )

    def _create_tenant_resident(self, user, owner_resident):
        """
        Create a new tenant resident profile based on an existing owner resident.
        This is used when a tenant selects a flat that already has an owner.
        """
        from the_khaki_estate.backend.models import Resident
        
        Resident.objects.create(
            user=user,
            flat_number=owner_resident.flat_number,  # Use the same flat number
            block=owner_resident.block,  # Use the same block
            phone_number=self.cleaned_data["phone_number"],  # Tenant's own phone
            alternate_phone=self.cleaned_data.get("alternate_phone", ""),
            resident_type="tenant",  # Set as tenant
            emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
            emergency_contact_phone=self.cleaned_data.get("emergency_contact_phone", ""),
            move_in_date=self.cleaned_data.get("move_in_date"),
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
            is_committee_member=False,
            # No owner_name or owner_email - these are for the tenant's own data
        )

    def _create_staff_profile(self, user):
        """Create a basic staff profile"""
        from the_khaki_estate.backend.models import Staff
        from django.utils import timezone
        
        Staff.objects.create(
            user=user,
            employee_id=f"TEMP_{user.id}",  # Temporary ID - needs to be updated
            staff_role="cleaner",  # Default role - needs to be updated
            phone_number=self.cleaned_data["phone_number"],
            alternate_phone=self.cleaned_data.get("alternate_phone", ""),
            emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
            emergency_contact_phone=self.cleaned_data.get("emergency_contact_phone", ""),
            employment_status="full_time",
            hire_date=timezone.now().date(),
            # Default permissions (minimal)
            can_access_all_maintenance=False,
            can_assign_requests=False,
            can_close_requests=False,
            can_manage_finances=False,
            can_send_announcements=False,
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
        )


# Keep the old form for backward compatibility
class UserSignupForm(NewUserSignupForm):
    """
    Backward compatibility alias for the new signup form.
    """
    pass


class StaffSignupForm(SignupForm):
    """
    Extended signup form for creating maintenance staff user accounts.
    Creates both User and Staff profiles with appropriate permissions.
    """

    # Personal Information
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "First Name",
                "class": "form-control",
            },
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "class": "form-control",
            },
        ),
    )

    # Staff Identification
    employee_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Employee ID (e.g., EMP001)",
                "class": "form-control",
            },
        ),
        help_text="Unique employee identifier",
    )

    # Staff Role Selection - Import choices from backend models
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import here to avoid circular imports
        from the_khaki_estate.backend.models import Staff

        # Set staff role choices from the Staff model
        self.fields["staff_role"] = forms.ChoiceField(
            choices=Staff.STAFF_ROLES,
            required=True,
            widget=forms.Select(attrs={"class": "form-control"}),
            help_text="Role/designation of the staff member",
        )

        self.fields["employment_status"] = forms.ChoiceField(
            choices=Staff.EMPLOYMENT_STATUS,
            required=True,
            widget=forms.Select(attrs={"class": "form-control"}),
            initial="full_time",
        )

        # Make email required and add styling
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

    # Department Information
    department = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Department (e.g., Maintenance, Security)",
                "class": "form-control",
            },
        ),
        help_text="Department or team",
    )

    # Contact Information
    phone_number = forms.CharField(
        max_length=13,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Phone number must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757",
                "class": "form-control",
                "pattern": r"^\+\d{12}$",
            },
        ),
        help_text="Primary contact number (format: +919830425757)",
    )
    alternate_phone = forms.CharField(
        max_length=13,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Alternate phone must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_alternate_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757 (optional)",
                "class": "form-control",
                "pattern": r"^\+\d{12}$",
            },
        ),
        help_text="Alternate contact number (optional, format: +919830425757)",
    )

    # Emergency Contact
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Emergency Contact Name",
                "class": "form-control",
            },
        ),
    )
    emergency_contact_phone = forms.CharField(
        max_length=13,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+\d{12}$",
                message="Emergency contact phone must be in format: +919830425757 (+ followed by exactly 12 digits)",
                code="invalid_emergency_phone_format",
            ),
        ],
        widget=forms.TextInput(
            attrs={
                "placeholder": "+919830425757 (optional)",
                "class": "form-control",
                "pattern": r"^\+\d{12}$",
            },
        ),
        help_text="Emergency contact phone number (optional, format: +919830425757)",
    )

    # Employment Details
    hire_date = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            },
        ),
        help_text="Date of joining",
    )

    # Work Schedule
    work_schedule = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "e.g., Mon-Fri 9AM-6PM, Saturday on-call",
                "class": "form-control",
                "rows": 3,
            },
        ),
        help_text="Work schedule description",
    )

    # Availability
    is_available_24x7 = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Available for emergency calls 24/7",
    )

    def clean_employee_id(self):
        """Validate employee ID uniqueness"""
        employee_id = self.cleaned_data.get("employee_id")
        if employee_id:
            # Import here to avoid circular imports
            from the_khaki_estate.backend.models import Staff

            # Check if employee ID already exists
            if Staff.objects.filter(employee_id=employee_id).exists():
                raise forms.ValidationError(
                    "This employee ID is already registered. Please use a different ID.",
                )

        return employee_id

    def clean_phone_number(self):
        """Validate phone number format - already handled by RegexValidator"""
        phone_number = self.cleaned_data.get("phone_number")
        # RegexValidator already ensures the format is correct
        return phone_number

    def clean_alternate_phone(self):
        """Validate alternate phone number format"""
        alternate_phone = self.cleaned_data.get("alternate_phone")
        # Only validate if provided (field is optional)
        if alternate_phone and alternate_phone.strip():
            # RegexValidator already handles the format validation
            pass
        return alternate_phone

    def clean_emergency_contact_phone(self):
        """Validate emergency contact phone number format"""
        emergency_phone = self.cleaned_data.get("emergency_contact_phone")
        # Only validate if provided (field is optional)
        if emergency_phone and emergency_phone.strip():
            # RegexValidator already handles the format validation
            pass
        return emergency_phone

    def save(self, request):
        """Create both User and Staff profiles with appropriate permissions"""
        # Save the user first with staff user type
        user = super().save(request)

        # Set the user's name and type
        user.name = f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}".strip()
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.user_type = "staff"  # Set user type to staff
        user.save()

        # Create the staff profile
        from the_khaki_estate.backend.models import Staff

        staff_role = self.cleaned_data["staff_role"]

        # Set default permissions based on staff role
        permissions = self._get_default_permissions(staff_role)

        Staff.objects.create(
            user=user,
            employee_id=self.cleaned_data["employee_id"],
            staff_role=staff_role,
            department=self.cleaned_data.get("department", ""),
            phone_number=self.cleaned_data["phone_number"],
            alternate_phone=self.cleaned_data.get("alternate_phone", ""),
            emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
            emergency_contact_phone=self.cleaned_data.get(
                "emergency_contact_phone",
                "",
            ),
            employment_status=self.cleaned_data["employment_status"],
            hire_date=self.cleaned_data["hire_date"],
            work_schedule=self.cleaned_data.get("work_schedule", ""),
            is_available_24x7=self.cleaned_data.get("is_available_24x7", False),
            # Set permissions based on role
            **permissions,
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
        )

        return user

    def _get_default_permissions(self, staff_role):
        """
        Get default permissions based on staff role.
        This defines what each type of staff member can do by default.
        """
        # Default permissions for different staff roles
        role_permissions = {
            "facility_manager": {
                "can_access_all_maintenance": True,
                "can_assign_requests": True,
                "can_close_requests": True,
                "can_manage_finances": False,
                "can_send_announcements": True,
            },
            "accountant": {
                "can_access_all_maintenance": False,
                "can_assign_requests": False,
                "can_close_requests": False,
                "can_manage_finances": True,
                "can_send_announcements": True,
            },
            "security_head": {
                "can_access_all_maintenance": False,
                "can_assign_requests": False,
                "can_close_requests": False,
                "can_manage_finances": False,
                "can_send_announcements": True,
            },
            "maintenance_supervisor": {
                "can_access_all_maintenance": True,
                "can_assign_requests": True,
                "can_close_requests": True,
                "can_manage_finances": False,
                "can_send_announcements": False,
            },
            # Technical staff have limited permissions
            "electrician": {
                "can_access_all_maintenance": False,
                "can_assign_requests": False,
                "can_close_requests": True,
                "can_manage_finances": False,
                "can_send_announcements": False,
            },
            "plumber": {
                "can_access_all_maintenance": False,
                "can_assign_requests": False,
                "can_close_requests": True,
                "can_manage_finances": False,
                "can_send_announcements": False,
            },
        }

        # Return permissions for the role, or default minimal permissions
        return role_permissions.get(
            staff_role,
            {
                "can_access_all_maintenance": False,
                "can_assign_requests": False,
                "can_close_requests": False,
                "can_manage_finances": False,
                "can_send_announcements": False,
            },
        )


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """