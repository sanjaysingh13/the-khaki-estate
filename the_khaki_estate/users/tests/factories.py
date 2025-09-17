from collections.abc import Sequence
from typing import Any

from factory import Faker
from factory import post_generation
from factory.django import DjangoModelFactory

from the_khaki_estate.users.models import User


class UserFactory(DjangoModelFactory[User]):
    """
    Factory for creating User instances with realistic test data.
    Can create both resident and staff users based on user_type.
    """

    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")
    user_type = "resident"  # Default to resident

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        """Save again the instance if creating and at least one hook ran."""
        if create and results and not cls._meta.skip_postgeneration_save:
            # Some post-generation hooks ran, and may have modified us.
            instance.save()

    class Meta:
        model = User
        django_get_or_create = ["username"]


class ResidentUserFactory(UserFactory):
    """Factory for creating resident users specifically."""

    user_type = "resident"


class StaffUserFactory(UserFactory):
    """Factory for creating staff users specifically."""

    user_type = "staff"
