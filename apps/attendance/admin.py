from django.contrib import admin

from apps.attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("date", "child", "status", "recorded_by", "updated_at")
    list_filter = ("status", "date")
    search_fields = ("child__first_name", "child__last_name", "child__preferred_name")
    autocomplete_fields = ("child",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "date"
    ordering = ("-date", "child__last_name")

    def save_model(self, request, obj, form, change):
        if not obj.recorded_by_id:
            obj.recorded_by = request.user
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
