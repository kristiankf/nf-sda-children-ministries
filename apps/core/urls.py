from django.urls import path

from apps.attendance import report_views as attendance_reports
from apps.children import group_views
from apps.children import report_views as children_reports
from apps.children.models import AgeGroup
from apps.core import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("more/", views.MoreView.as_view(), name="more"),
    path(
        "more/sabbath-classes/",
        group_views.AgeGroupListView.as_view(),
        {"kind": AgeGroup.Kind.SABBATH},
        name="sabbath_classes",
    ),
    path(
        "more/sabbath-classes/new/",
        group_views.AgeGroupCreateView.as_view(),
        {"kind": AgeGroup.Kind.SABBATH},
        name="sabbath_class_create",
    ),
    path(
        "more/sabbath-classes/<slug:slug>/edit/",
        group_views.AgeGroupUpdateView.as_view(),
        {"kind": AgeGroup.Kind.SABBATH},
        name="sabbath_class_edit",
    ),
    path(
        "more/sabbath-classes/<slug:slug>/remove/",
        group_views.AgeGroupDeleteView.as_view(),
        {"kind": AgeGroup.Kind.SABBATH},
        name="sabbath_class_remove",
    ),
    path(
        "more/youth-groups/",
        group_views.AgeGroupListView.as_view(),
        {"kind": AgeGroup.Kind.YOUTH},
        name="youth_groups",
    ),
    path(
        "more/youth-groups/new/",
        group_views.AgeGroupCreateView.as_view(),
        {"kind": AgeGroup.Kind.YOUTH},
        name="youth_group_create",
    ),
    path(
        "more/youth-groups/<slug:slug>/edit/",
        group_views.AgeGroupUpdateView.as_view(),
        {"kind": AgeGroup.Kind.YOUTH},
        name="youth_group_edit",
    ),
    path(
        "more/youth-groups/<slug:slug>/remove/",
        group_views.AgeGroupDeleteView.as_view(),
        {"kind": AgeGroup.Kind.YOUTH},
        name="youth_group_remove",
    ),
    path("reports/", views.ReportIndexView.as_view(), name="reports"),
    path("reports/children/", children_reports.children_report, name="report_children"),
    path("reports/children.csv", children_reports.children_csv, name="report_children_csv"),
    path("reports/birthdays/", children_reports.birthday_report, name="report_birthdays"),
    path("reports/birthdays.csv", children_reports.birthday_csv, name="report_birthdays_csv"),
    path("reports/attendance/", attendance_reports.attendance_report, name="report_attendance"),
    path("reports/attendance.csv", attendance_reports.attendance_csv, name="report_attendance_csv"),
]
