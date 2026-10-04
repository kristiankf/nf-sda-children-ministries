from django import forms
from django.utils.text import slugify

from apps.children.groups import ranges_overlap, renumber_bands
from apps.children.models import AgeGroup, Child
from apps.core.forms import StyledModelForm
from apps.parents.models import ChildGuardian, Parent


class ChildForm(StyledModelForm):
    class Meta:
        model = Child
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "preferred_name",
            "date_of_birth",
            "gender",
            "phone",
            "school_name",
            "class_level",
            "sabbath_class_override",
            "address",
            "status",
            "notes",
            "photo",
        ]
        labels = {
            "school_name": "School",
            "class_level": "Class",
        }
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "phone": forms.TextInput(
                attrs={
                    "type": "tel",
                    "inputmode": "tel",
                    "placeholder": "024 412 3456",
                    "autocomplete": "tel",
                }
            ),
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs["autocomplete"] = "given-name"
        self.fields["middle_name"].widget.attrs["autocomplete"] = "additional-name"
        self.fields["last_name"].widget.attrs["autocomplete"] = "family-name"
        self.fields["date_of_birth"].widget.attrs["autocomplete"] = "bday"
        self.fields["phone"].required = False
        self.fields["school_name"].required = False
        self.fields["class_level"].required = False
        self.fields["class_level"].empty_label = "No class yet"
        self.fields["sabbath_class_override"].queryset = AgeGroup.objects.filter(
            kind=AgeGroup.Kind.SABBATH
        ).order_by("sort_order")
        self.fields["sabbath_class_override"].required = False
        self.fields["sabbath_class_override"].empty_label = "Use the birthday"
        self.fields["sabbath_class_override"].label = "Sabbath class"


class AgeGroupForm(StyledModelForm):
    class Meta:
        model = AgeGroup
        fields = ["name", "min_years", "max_years", "color"]
        widgets = {"color": forms.RadioSelect()}
        labels = {
            "min_years": "Youngest age",
            "max_years": "Oldest age",
        }
        help_texts = {
            "max_years": (
                "Leave this empty when the class has no upper age, such as 15 and older. "
                "Use 0 and 0 for children under 1 year."
            ),
        }

    def __init__(self, *args, kind, **kwargs):
        self.kind = kind
        super().__init__(*args, **kwargs)
        self.fields["max_years"].required = False
        self.fields["color"].widget.attrs.pop("class", None)

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("min_years")
        maximum = cleaned.get("max_years")
        if minimum is None:
            return cleaned
        if maximum is not None and maximum < minimum:
            self.add_error("max_years", "Oldest age cannot be younger than the youngest age.")
            return cleaned
        others = AgeGroup.objects.filter(kind=self.kind)
        if self.instance.pk:
            others = others.exclude(pk=self.instance.pk)
        for other in others:
            if ranges_overlap(minimum, maximum, other.min_years, other.max_years):
                self.add_error(
                    "min_years",
                    f"These ages overlap {other.name} ({other.age_label}).",
                )
                break
        return cleaned

    def save(self, commit=True):
        self.instance.kind = self.kind
        if not self.instance.slug:
            base = slugify(self.cleaned_data["name"])[:40] or "class"
            slug = base
            number = 2
            while AgeGroup.objects.filter(slug=slug).exists():
                suffix = f"-{number}"
                slug = f"{base[: 40 - len(suffix)]}{suffix}"
                number += 1
            self.instance.slug = slug
        saved = super().save(commit=commit)
        if commit:
            renumber_bands(self.kind)
        return saved


class LinkGuardianForm(StyledModelForm):
    class Meta:
        model = ChildGuardian
        fields = ["parent", "relationship"]

    def __init__(self, *args, child, **kwargs) -> None:
        self.child = child
        super().__init__(*args, **kwargs)
        linked_ids = child.guardians.values_list("parent_id", flat=True)
        self.fields["parent"].queryset = Parent.objects.exclude(pk__in=linked_ids).order_by(
            "last_name", "first_name"
        )
        self.fields["parent"].empty_label = "Select a parent or guardian"

    def clean(self):
        cleaned = super().clean()
        parent = cleaned.get("parent")
        if parent and ChildGuardian.objects.filter(child=self.child, parent=parent).exists():
            self.add_error("parent", "This person is already linked to the child.")
        return cleaned

    def save(self, commit=True):
        self.instance.child = self.child
        return super().save(commit=commit)


class NewGuardianForm(StyledModelForm):
    relationship = forms.ChoiceField(choices=ChildGuardian.Relationship.choices)

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
                attrs={"type": "tel", "inputmode": "tel", "placeholder": "024 412 3456"}
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
        self.fields["phone_primary"].widget.attrs["autocomplete"] = "tel"
