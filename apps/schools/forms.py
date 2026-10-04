from django import forms

from apps.core.forms import StyledModelForm
from apps.schools.models import AcademicYear


class AcademicYearForm(StyledModelForm):
    class Meta:
        model = AcademicYear
        fields = ["start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
        labels = {
            "start_date": "Starts",
            "end_date": "Ends",
        }
