from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, UpdateView

from apps.children.models import Child
from apps.schools.calendar import advance_academic_calendar
from apps.schools.forms import AcademicYearForm
from apps.schools.levels import ClassLevel
from apps.schools.models import AcademicYear


class ClassListView(PermissionRequiredMixin, ListView):
    permission_required = "children.view_child"
    template_name = "classes/list.html"
    context_object_name = "levels"

    def get_queryset(self):
        counts = {
            row["class_level"]: row["count"]
            for row in Child.objects.filter(status=Child.Status.ACTIVE)
            .values("class_level")
            .annotate(count=Count("id"))
        }
        return [
            {"value": value, "label": label, "count": counts.get(value, 0)}
            for value, label in ClassLevel.choices
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["academic_year"] = AcademicYear.objects.filter(is_current=True).first()
        context["without_class"] = Child.objects.filter(
            status=Child.Status.ACTIVE, class_level=""
        ).count()
        return context


class AcademicYearUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "schools.change_academicyear"
    model = AcademicYear
    form_class = AcademicYearForm
    template_name = "classes/year.html"

    def get_object(self, queryset=None):
        return advance_academic_calendar()

    def form_valid(self, form):
        saved = form.save()
        current = advance_academic_calendar()
        if current.pk != saved.pk:
            messages.success(
                self.request,
                "That year has ended, so each active child has moved up one class.",
            )
        else:
            messages.success(self.request, f"{current.name} has been saved.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("classes:list")
