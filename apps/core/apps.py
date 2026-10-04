from django.apps import AppConfig
from django.contrib import admin


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self) -> None:
        admin.site.site_header = "New Fadama SDA Children's Ministries"
        admin.site.site_title = "Children's Ministries"
        admin.site.index_title = "Ministry records"
