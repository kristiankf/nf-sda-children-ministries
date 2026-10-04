from django.contrib import admin

from apps.parents.models import ChildGuardian, Parent


class ChildGuardianInline(admin.TabularInline):
    model = ChildGuardian
    extra = 0
    autocomplete_fields = ("child", "parent")


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "phone_primary", "email")
    search_fields = ("first_name", "last_name", "phone_primary", "phone_secondary", "email")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    inlines = [ChildGuardianInline]


@admin.register(ChildGuardian)
class ChildGuardianAdmin(admin.ModelAdmin):
    list_display = ("parent", "relationship", "child")
    list_filter = ("relationship",)
    search_fields = (
        "parent__first_name",
        "parent__last_name",
        "child__first_name",
        "child__last_name",
    )
    autocomplete_fields = ("parent", "child")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
