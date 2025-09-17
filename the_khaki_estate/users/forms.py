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
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Last Name",
                "class": "form-control",
            }
        ),
    )

    # Residence Information
    flat_number = forms.CharField(
        max_length=4,
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Flat Number (e.g., 101)",
                "class": "form-control",
            }
        ),
        help_text="Your flat/apartment number",
    )
    block = forms.CharField(
        max_length=2,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Block (e.g., A)",
                "class": "form-control",
            }
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
            }
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
            }
        ),
        help_text="Alternate contact number (optional, format: +919830425757)",
    )

    # Resident Type
    RESIDENT_TYPES = [
        ("owner", "Owner"),
        ("tenant", "Tenant"),
        ("family", "Family Member"),
    ]
    resident_type = forms.ChoiceField(
        choices=RESIDENT_TYPES,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
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
            }
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
            }
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
            }
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

    def clean_flat_number(self):
        """Validate flat number format and uniqueness"""
        flat_number = self.cleaned_data.get("flat_number")
        if flat_number:
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
        """Create both User and Resident profiles"""
        # Save the user first
        user = super().save(request)

        # Set the user's name from first_name and last_name
        user.name = f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}".strip()
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.save()

        # Create the resident profile
        from the_khaki_estate.backend.models import Resident

        Resident.objects.create(
            user=user,
            flat_number=self.cleaned_data["flat_number"],
            block=self.cleaned_data.get("block", ""),
            phone_number=self.cleaned_data["phone_number"],
            alternate_phone=self.cleaned_data.get("alternate_phone", ""),
            resident_type=self.cleaned_data["resident_type"],
            emergency_contact_name=self.cleaned_data.get("emergency_contact_name", ""),
            emergency_contact_phone=self.cleaned_data.get(
                "emergency_contact_phone", ""
            ),
            move_in_date=self.cleaned_data.get("move_in_date"),
            # Default notification preferences
            email_notifications=True,
            sms_notifications=False,
            urgent_only=False,
            is_committee_member=False,  # Default to False, admin can change later
        )

        return user


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """
