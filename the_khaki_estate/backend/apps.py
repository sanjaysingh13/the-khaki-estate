from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "the_khaki_estate.backend"

    def ready(self):
        """
        Import signals when the app is ready to ensure they are connected.
        This is critical for the notification system to work properly.
        """
        import the_khaki_estate.backend.signals  # noqa: F401
