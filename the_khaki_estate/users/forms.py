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


class UserSignupForm(SignupForm):
    """
    Extended signup form that collects resident information during registration.
    Creates both User and Resident profiles in one step.
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

    # Residence Information - Only for residents
    flat_number = forms.CharField(
        max_length=4,
        required=False,  # Will be required conditionally for residents
        widget=forms.TextInput(
            attrs={
                "placeholder": "Flat Number (e.g., 101)",
                "class": "form-control resident-field",
                "id": "id_flat_number",
            },
        ),
        help_text="Your flat/apartment number",
    )
    block = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Block (e.g., A)",
                "class": "form-control resident-field",
                "id": "id_block",
            },
        ),
        help_text="Building block (if applicable)",
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
        help_text="Your primary contact number (format: +919830425757)",
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

    # User Type Selection - Resident or Staff
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

    # Resident Type - Only shown for residents
    RESIDENT_TYPES = [
        ("", "Select Resident Type"),  # Default empty option
        ("owner", "Owner"),
        ("tenant", "Tenant"),
        ("family", "Family Member"),
    ]
    resident_type = forms.ChoiceField(
        choices=RESIDENT_TYPES,
        required=False,  # Will be required conditionally via JavaScript validation
        widget=forms.Select(
            attrs={
                "class": "form-control resident-field",
                "id": "id_resident_type",
            },
        ),
        help_text="Your relationship to the property",
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

    # Move-in Date - Only for residents
    move_in_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control resident-field",
                "id": "id_move_in_date",
            },
        ),
        help_text="When did you move in? (optional)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email required and add styling
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})

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
        flat_number = self.cleaned_data.get("flat_number")

        # Only validate flat number for residents
        if user_type == "resident":
            if not flat_number:
                raise forms.ValidationError("Flat number is required for residents.")

            # Import here to avoid circular imports
            from the_khaki_estate.backend.models import Resident

            # Check if flat number already exists
            if Resident.objects.filter(flat_number=flat_number).exists():
                raise forms.ValidationError(
                    "This flat number is already registered. Please contact management if this is an error.",
                )

            # Validate format (should be numeric)
            if not flat_number.isdigit():
                raise forms.ValidationError("Flat number should contain only numbers.")
        elif user_type == "staff" and flat_number:
            # Clear flat number for staff users
            flat_number = ""

        return flat_number

    def clean_phone_number(self):
        """Validate phone number format - already handled by RegexValidator"""
        phone_number = self.cleaned_data.get("phone_number")
        # RegexValidator already ensures the format is correct
        # Additional validation can be added here if needed
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
        # This prevents the signal from interfering with our profile creation
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
                user.user_type = self.cleaned_data[
                    "user_type"
                ]  # Set user type from form
                user.save()

            finally:
                # Reconnect the signal
                post_save.connect(create_resident_profile, sender=User)

            # Create appropriate profile based on user type
            if user.user_type == "resident":
                # Handle Resident profile creation
                try:
                    resident = user.resident
                    # Update existing resident with form data
                    resident.flat_number = self.cleaned_data["flat_number"]
                    resident.block = self.cleaned_data.get("block", "")
                    resident.phone_number = self.cleaned_data["phone_number"]
                    resident.alternate_phone = self.cleaned_data.get(
                        "alternate_phone",
                        "",
                    )
                    resident.resident_type = self.cleaned_data["resident_type"]
                    resident.emergency_contact_name = self.cleaned_data.get(
                        "emergency_contact_name",
                        "",
                    )
                    resident.emergency_contact_phone = self.cleaned_data.get(
                        "emergency_contact_phone",
                        "",
                    )
                    resident.move_in_date = self.cleaned_data.get("move_in_date")
                    resident.email_notifications = True
                    resident.sms_notifications = False
                    resident.urgent_only = False
                    resident.is_committee_member = False
                    resident.save()
                except Resident.DoesNotExist:
                    # Create new resident profile if none exists
                    Resident.objects.create(
                        user=user,
                        flat_number=self.cleaned_data["flat_number"],
                        block=self.cleaned_data.get("block", ""),
                        phone_number=self.cleaned_data["phone_number"],
                        alternate_phone=self.cleaned_data.get("alternate_phone", ""),
                        resident_type=self.cleaned_data["resident_type"],
                        emergency_contact_name=self.cleaned_data.get(
                            "emergency_contact_name",
                            "",
                        ),
                        emergency_contact_phone=self.cleaned_data.get(
                            "emergency_contact_phone",
                            "",
                        ),
                        move_in_date=self.cleaned_data.get("move_in_date"),
                        # Default notification preferences
                        email_notifications=True,
                        sms_notifications=False,
                        urgent_only=False,
                        is_committee_member=False,  # Default to False, admin can change later
                    )

            elif user.user_type == "staff":
                # For staff users, we'll create a basic staff profile
                # Note: This form is primarily for residents. Staff should use StaffSignupForm
                # But we'll handle it gracefully by creating a basic profile
                try:
                    staff = user.staff
                    # Update basic information if staff profile already exists
                    staff.phone_number = self.cleaned_data["phone_number"]
                    staff.alternate_phone = self.cleaned_data.get("alternate_phone", "")
                    staff.emergency_contact_name = self.cleaned_data.get(
                        "emergency_contact_name",
                        "",
                    )
                    staff.emergency_contact_phone = self.cleaned_data.get(
                        "emergency_contact_phone",
                        "",
                    )
                    staff.save()
                except Staff.DoesNotExist:
                    # Create basic staff profile - they'll need to complete it later
                    Staff.objects.create(
                        user=user,
                        employee_id=f"TEMP_{user.id}",  # Temporary ID - needs to be updated
                        staff_role="cleaner",  # Default role - needs to be updated
                        phone_number=self.cleaned_data["phone_number"],
                        alternate_phone=self.cleaned_data.get("alternate_phone", ""),
                        emergency_contact_name=self.cleaned_data.get(
                            "emergency_contact_name",
                            "",
                        ),
                        emergency_contact_phone=self.cleaned_data.get(
                            "emergency_contact_phone",
                            "",
                        ),
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

        return user


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
