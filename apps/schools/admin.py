from django.contrib import admin

from apps.schools.models import AcademicYear, ClassPlacement


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_current")
    list_filter = ("is_current",)
    search_fields = ("name",)
    ordering = ("-start_date",)


@admin.register(ClassPlacement)
class ClassPlacementAdmin(admin.ModelAdmin):
    list_display = ("child", "academic_year", "class_level")
    list_filter = ("academic_year", "class_level")
    search_fields = ("child__first_name", "child__last_name", "child__preferred_name")
    autocomplete_fields = ("child",)
    ordering = ("-academic_year__start_date", "child__last_name")
