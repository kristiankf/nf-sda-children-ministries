from django.contrib import admin

from apps.children.models import Child
from apps.parents.models import ChildGuardian


class ChildGuardianInline(admin.TabularInline):
    model = ChildGuardian
    extra = 0
    autocomplete_fields = ("parent",)


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "preferred_name",
        "date_of_birth",
        "status",
        "school_name",
        "class_level",
        "sabbath_class_override",
    )
    list_filter = ("status", "gender", "class_level", "sabbath_class_override")
    search_fields = (
        "first_name",
        "middle_name",
        "last_name",
        "preferred_name",
        "phone",
        "school_name",
    )
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [ChildGuardianInline]
    ordering = ("last_name", "first_name")
