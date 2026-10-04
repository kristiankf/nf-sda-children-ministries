from django.urls import path

from apps.children import guardian_views, views

app_name = "children"

urlpatterns = [
    path("", views.ChildListView.as_view(), name="list"),
    path("new/", views.ChildCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ChildDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ChildUpdateView.as_view(), name="edit"),
    path("<int:pk>/graduate/", views.GraduateChildView.as_view(), name="graduate"),
    path("<int:pk>/photo/", views.ChildPhotoView.as_view(), name="photo"),
    path("<int:pk>/guardians/add/", guardian_views.AddGuardianView.as_view(), name="add_guardian"),
    path(
        "<int:pk>/guardians/<int:link_pk>/remove/",
        guardian_views.RemoveGuardianView.as_view(),
        name="remove_guardian",
    ),
]
