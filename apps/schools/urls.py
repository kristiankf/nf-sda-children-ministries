from django.urls import path

from apps.schools import views

app_name = "classes"

urlpatterns = [
    path("", views.ClassListView.as_view(), name="list"),
    path("year/", views.AcademicYearUpdateView.as_view(), name="year"),
]
