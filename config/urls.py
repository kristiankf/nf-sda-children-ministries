from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("children/", include("apps.children.urls")),
    path("parents/", include("apps.parents.urls")),
    path("classes/", include("apps.schools.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("", include("apps.core.urls")),
]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
