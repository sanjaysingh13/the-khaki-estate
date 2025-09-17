from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for The Khaki Estate.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # User type choices to distinguish between residents and staff
    USER_TYPE_CHOICES = [
        ("resident", "Resident"),
        ("staff", "Staff"),
    ]

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # User type field to distinguish between residents and maintenance staff
    user_type = CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="resident",
        help_text="Type of user - resident or maintenance staff",
    )

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def is_resident(self) -> bool:
        """Check if user is a resident."""
        return self.user_type == "resident"

    def is_staff_member(self) -> bool:
        """Check if user is a maintenance staff member."""
        return self.user_type == "staff"
