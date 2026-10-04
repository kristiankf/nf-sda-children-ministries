from django import forms

from apps.core.forms import StyledModelForm
from apps.parents.models import Parent


class ParentForm(StyledModelForm):
    class Meta:
        model = Parent
        fields = [
            "first_name",
            "last_name",
            "phone_primary",
            "phone_secondary",
            "email",
            "address",
            "occupation",
            "notes",
        ]
        widgets = {
            "phone_primary": forms.TextInput(
                attrs={
                    "type": "tel",
                    "inputmode": "tel",
                    "placeholder": "024 412 3456",
                    "autocomplete": "tel",
                }
            ),
            "phone_secondary": forms.TextInput(attrs={"type": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"type": "email", "autocomplete": "email"}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
