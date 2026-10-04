from django.urls import path

from apps.parents import views

app_name = "parents"

urlpatterns = [
    path("", views.ParentListView.as_view(), name="list"),
    path("new/", views.ParentCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ParentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ParentUpdateView.as_view(), name="edit"),
]
