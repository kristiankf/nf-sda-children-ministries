from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from apps.core.forms import apply_widget_styles


class MinistryAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)
        self.fields["username"].widget.attrs["autocomplete"] = "username"
        self.fields["username"].widget.attrs["autocapitalize"] = "none"
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"


class MinistryPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)
