from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.accounts.roles import ensure_ministry_roles

        post_migrate.connect(
            ensure_ministry_roles,
            dispatch_uid="apps.accounts.ensure_ministry_roles",
        )
