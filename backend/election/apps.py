from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_admin(sender, **kwargs):
    from django.conf import settings
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if not User.objects.filter(is_staff=True).exists():
        User.objects.create_superuser(
            settings.ADMIN_USERNAME, "", settings.ADMIN_PASSWORD
        )


class ElectionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "election"

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
