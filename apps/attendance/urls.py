from django.urls import path

from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.roll, name="roll"),
    path("history/", views.history, name="history"),
    path("missing/", views.missing, name="missing"),
]
