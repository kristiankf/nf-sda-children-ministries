from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import path

from apps.accounts.forms import MinistryAuthenticationForm, MinistryPasswordChangeForm

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=MinistryAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "password/",
        PasswordChangeView.as_view(
            template_name="registration/password_change.html",
            form_class=MinistryPasswordChangeForm,
        ),
        name="password_change",
    ),
    path(
        "password/done/",
        PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"),
        name="password_change_done",
    ),
]
