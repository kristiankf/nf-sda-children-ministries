from django.urls import path

from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.roll, name="roll"),
    path("export.csv", views.roll_csv, name="roll_csv"),
    path("history/", views.history, name="history"),
    path("missing/", views.missing, name="missing"),
]
