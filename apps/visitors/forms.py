from django import forms

from apps.attendance.calendar import upcoming_sabbath
from apps.children.models import Child
from apps.core import dates
from apps.core.forms import StyledModelForm, apply_widget_styles
from apps.core.phones import normalize_ghana_phone
from apps.parents.models import Parent
from apps.visitors.models import Visit, Visitor


class VisitorIdentityForm(StyledModelForm):
    class Meta:
        model = Visitor
        fields = ["first_name", "last_name", "date_of_birth", "gender", "address"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["date_of_birth"].required = False
        self.fields["date_of_birth"].help_text = "Leave blank if unknown."
        self.fields["address"].required = False
        self.fields["address"].label = "Address (optional)"
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"


class VisitForm(forms.Form):
    """One Sabbath visit, optionally for an existing visitor."""

    existing_visitor = forms.ModelChoiceField(
        queryset=Visitor.objects.filter(child__isnull=True),
        required=False,
        widget=forms.HiddenInput,
    )
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Reason for visit",
    )
    came_with = forms.ChoiceField(
        choices=[
            ("none", "Not recorded"),
            ("parent", "An existing parent or guardian"),
            ("child", "An existing child"),
            ("other", "Someone else (optional name and phone)"),
        ],
        initial="none",
        label="Who brought them / who they came with",
    )
    brought_by_parent = forms.ModelChoiceField(
        queryset=Parent.objects.all(),
        required=False,
        widget=forms.HiddenInput,
    )
    brought_by_child = forms.ModelChoiceField(
        queryset=Child.objects.filter(status=Child.Status.ACTIVE),
        required=False,
        widget=forms.HiddenInput,
    )
    companion_name = forms.CharField(
        max_length=160,
        required=False,
        label="Full name (optional)",
    )
    companion_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Phone (optional)",
        widget=forms.TextInput(
            attrs={
                "type": "tel",
                "inputmode": "tel",
                "placeholder": "024 412 3456",
                "autocomplete": "tel",
            }
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)
        if not self.is_bound and not self.initial.get("date"):
            self.fields["date"].initial = upcoming_sabbath(dates.local_today())

    def clean_companion_phone(self):
        value = (self.cleaned_data.get("companion_phone") or "").strip()
        if not value:
            return ""
        return normalize_ghana_phone(value)

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("came_with") or "none"
        parent = cleaned.get("brought_by_parent")
        child = cleaned.get("brought_by_child")

        if mode == "parent":
            if parent is None:
                self.add_error("came_with", "Choose the parent or guardian who brought them.")
            cleaned["brought_by_child"] = None
            cleaned["companion_name"] = ""
            cleaned["companion_phone"] = ""
        elif mode == "child":
            if child is None:
                self.add_error("came_with", "Choose the child they came with.")
            cleaned["brought_by_parent"] = None
            cleaned["companion_name"] = ""
            cleaned["companion_phone"] = ""
        elif mode == "other":
            cleaned["brought_by_parent"] = None
            cleaned["brought_by_child"] = None
            cleaned["companion_name"] = (cleaned.get("companion_name") or "").strip()
        else:
            cleaned["brought_by_parent"] = None
            cleaned["brought_by_child"] = None
            cleaned["companion_name"] = ""
            cleaned["companion_phone"] = ""

        visit_date = cleaned.get("date")
        if visit_date and visit_date > dates.local_today():
            self.add_error("date", "Visit date cannot be in the future.")

        visitor = cleaned.get("existing_visitor")
        if visitor and visit_date:
            if Visit.objects.filter(visitor=visitor, date=visit_date).exists():
                self.add_error(
                    "date",
                    f"{visitor.full_name} already has a visit recorded for this date.",
                )
        return cleaned

    def build_visit(self, visitor: Visitor, user) -> Visit:
        return Visit(
            visitor=visitor,
            date=self.cleaned_data["date"],
            reason=self.cleaned_data["reason"].strip(),
            brought_by_parent=self.cleaned_data.get("brought_by_parent"),
            brought_by_child=self.cleaned_data.get("brought_by_child"),
            companion_name=self.cleaned_data.get("companion_name") or "",
            companion_phone=self.cleaned_data.get("companion_phone") or "",
            recorded_by=user,
            created_by=user,
            updated_by=user,
        )
