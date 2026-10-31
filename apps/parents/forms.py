from django import forms

from apps.children.models import Child
from apps.core.forms import StyledModelForm, apply_widget_styles
from apps.parents.models import ChildGuardian, Parent


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


class LinkChildrenForm(forms.Form):
    children = forms.ModelMultipleChoiceField(
        queryset=Child.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Children",
    )
    relationship = forms.ChoiceField(
        choices=ChildGuardian.Relationship.choices,
        label="Relationship to these children",
    )

    def __init__(self, *args, parent: Parent, children_queryset, **kwargs) -> None:
        self.parent = parent
        super().__init__(*args, **kwargs)
        self.fields["children"].queryset = children_queryset
        self.fields["children"].help_text = "Select one or more children to link."
        apply_widget_styles(self)

    def clean_children(self):
        children = self.cleaned_data["children"]
        already = ChildGuardian.objects.filter(parent=self.parent, child__in=children).values_list(
            "child_id", flat=True
        )
        if already:
            names = ", ".join(child.full_name for child in children if child.pk in set(already))
            raise forms.ValidationError(
                f"Already linked: {names}. Uncheck them or pick someone else."
            )
        return children
