from django.urls import path

from apps.visitors import views

app_name = "visitors"

urlpatterns = [
    path("", views.VisitorListView.as_view(), name="list"),
    path("add/", views.VisitorCreateView.as_view(), name="create"),
    path("follow-up/", views.VisitorFollowUpListView.as_view(), name="follow_up"),
    path("search/", views.VisitorSearchView.as_view(), name="search"),
    path("companions/parents/", views.CompanionParentSearchView.as_view(), name="parent_search"),
    path("companions/children/", views.CompanionChildSearchView.as_view(), name="child_search"),
    path("<int:pk>/", views.VisitorDetailView.as_view(), name="detail"),
    path("<int:pk>/follow-up/", views.VisitorFollowUpView.as_view(), name="mark_follow_up"),
    path("<int:pk>/convert/", views.VisitorConvertView.as_view(), name="convert"),
]
