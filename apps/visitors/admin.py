from django.contrib import admin

from apps.visitors.models import Visit, Visitor


class VisitInline(admin.TabularInline):
    model = Visit
    extra = 0
    fields = (
        "date",
        "reason",
        "brought_by_parent",
        "brought_by_child",
        "companion_name",
        "companion_phone",
    )


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "gender", "date_of_birth", "child")
    search_fields = ("first_name", "last_name")
    inlines = [VisitInline]


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("visitor", "date", "brought_by_parent", "brought_by_child", "companion_name")
    list_filter = ("date",)
    search_fields = ("visitor__first_name", "visitor__last_name", "reason", "companion_name")
