import mimetypes

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.children.forms import ChildForm, OptionalChildParentForm
from apps.children.groups import attach_ministry_groups, load_bands, oldest_sabbath_band
from apps.children.models import Child
from apps.children.queries import filtered_children
from apps.children.suggestions import SUGGEST_FIELDS, suggest_child_field_values
from apps.core import dates
from apps.core.htmx import is_htmx
from apps.parents.models import ChildGuardian, Parent
from apps.schools.levels import ClassLevel
from apps.schools.models import AcademicYear


class AuditSaveMixin:
    def form_valid(self, form):
        if form.instance.pk is None:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ChildListView(PermissionRequiredMixin, ListView):
    permission_required = "children.view_child"
    context_object_name = "children"
    paginate_by = 25

    def get_template_names(self):
        if is_htmx(self.request):
            return ["children/partials/results.html"]
        return ["children/list.html"]

    def get_queryset(self):
        return filtered_children(self.request.GET, dates.local_today())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = dates.local_today()
        attach_ministry_groups(context["children"], today)
        sabbath_classes, youth_groups = load_bands()
        context.update(
            {
                "class_levels": ClassLevel.choices,
                "statuses": Child.Status.choices,
                "genders": Child.Gender.choices,
                "sabbath_classes": sabbath_classes,
                "youth_groups": youth_groups,
                "filters_open": any(
                    self.request.GET.get(key)
                    for key in (
                        "class_level",
                        "gender",
                        "age_min",
                        "age_max",
                        "status",
                        "division",
                        "youth",
                    )
                    if not (
                        key == "status" and self.request.GET.get(key) in {"", Child.Status.ACTIVE}
                    )
                ),
            }
        )
        return context


class ChildCreateView(AuditSaveMixin, PermissionRequiredMixin, CreateView):
    permission_required = "children.add_child"
    model = Child
    form_class = ChildForm
    template_name = "children/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_parent_picker"] = self.request.user.has_perm("parents.add_childguardian")
        context["parent_form"] = kwargs.get("parent_form") or OptionalChildParentForm(
            prefix="parent"
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        parent_form = OptionalChildParentForm(request.POST, prefix="parent")
        if form.is_valid() and parent_form.is_valid():
            return self.forms_valid(form, parent_form)
        return self.render_to_response(self.get_context_data(form=form, parent_form=parent_form))

    @transaction.atomic
    def forms_valid(self, form, parent_form):
        response = super().form_valid(form)
        if parent_form.has_parent and self.request.user.has_perm("parents.add_childguardian"):
            self._link_optional_parent(parent_form)
        return response

    def _link_optional_parent(self, parent_form: OptionalChildParentForm) -> None:
        linked = parent_form.cleaned_data.get("linked_parent")
        relationship = parent_form.cleaned_data["relationship"]
        if linked is None:
            if not self.request.user.has_perm("parents.add_parent"):
                return
            linked = Parent(
                first_name=parent_form.cleaned_data["first_name"],
                last_name=parent_form.cleaned_data["last_name"],
                phone_primary=parent_form.cleaned_data["phone"],
                created_by=self.request.user,
                updated_by=self.request.user,
            )
            linked.full_clean()
            linked.save()
        ChildGuardian.objects.create(
            child=self.object,
            parent=linked,
            relationship=relationship,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def get_success_url(self):
        messages.success(self.request, f"{self.object.short_name} has been added.")
        return self.object.get_absolute_url()


class ChildUpdateView(AuditSaveMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "children.change_child"
    model = Child
    form_class = ChildForm
    template_name = "children/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_parent_picker"] = False
        return context

    def get_success_url(self):
        messages.success(self.request, f"{self.object.short_name} has been updated.")
        return self.object.get_absolute_url()


class ChildDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "children.view_child"
    model = Child
    context_object_name = "child"
    template_name = "children/detail.html"

    def get_queryset(self):
        return Child.objects.select_related("sabbath_class_override").prefetch_related(
            "guardians__parent", "class_placements__academic_year"
        )

    def get_context_data(self, **kwargs):
        from django.db.models import Count, Q

        from apps.attendance.models import Attendance
        from apps.attendance.streaks import streak_for_child
        from apps.core.dates import days_until_birthday, local_today, next_birthday

        context = super().get_context_data(**kwargs)
        child = self.object
        today = local_today()
        counts = child.attendance_records.filter(date__week_day=7).aggregate(
            present=Count("id", filter=Q(status=Attendance.Status.PRESENT)),
            absent=Count("id", filter=Q(status=Attendance.Status.ABSENT)),
        )
        attach_ministry_groups([child], today)
        oldest = oldest_sabbath_band()
        current_year = AcademicYear.objects.filter(is_current=True).first()
        earlier = child.class_placements.all()
        if current_year is not None:
            earlier = earlier.exclude(academic_year=current_year)
        context.update(
            {
                "today": today,
                "next_birthday": (
                    next_birthday(child.date_of_birth, today) if child.date_of_birth else None
                ),
                "days_until_birthday": (
                    days_until_birthday(child.date_of_birth, today) if child.date_of_birth else None
                ),
                "present_count": counts["present"] or 0,
                "absent_count": counts["absent"] or 0,
                "absence_weeks": streak_for_child(child, today),
                "recent_attendance": child.attendance_records.filter(date__week_day=7).order_by(
                    "-date"
                )[:8],
                "earlier_placements": earlier,
                "can_graduate": (
                    child.status == Child.Status.ACTIVE
                    and oldest is not None
                    and child.sabbath_class is not None
                    and child.sabbath_class.pk == oldest.pk
                ),
            }
        )
        return context


class ChildPhotoView(PermissionRequiredMixin, View):
    permission_required = "children.view_child"

    def get(self, request, pk):
        child = get_object_or_404(Child, pk=pk)
        if not child.photo:
            raise Http404("This child has no photo.")
        content_type = mimetypes.guess_type(child.photo.name)[0] or "application/octet-stream"
        response = FileResponse(child.photo.open("rb"), content_type=content_type)
        response["Content-Disposition"] = "inline"
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, max-age=3600"
        return response


class GraduateChildView(PermissionRequiredMixin, View):
    permission_required = "children.change_child"

    def _child(self, pk):
        child = get_object_or_404(
            Child.objects.select_related("sabbath_class_override"),
            pk=pk,
        )
        attach_ministry_groups([child], dates.local_today())
        return child

    def get(self, request, pk):
        child = self._child(pk)
        return render_graduate(request, child)

    def post(self, request, pk):
        child = self._child(pk)
        oldest = oldest_sabbath_band()
        if child.status != Child.Status.ACTIVE or (
            oldest is None or child.sabbath_class is None or child.sabbath_class.pk != oldest.pk
        ):
            messages.error(request, f"{child.short_name} is not ready to graduate.")
            return redirect(child.get_absolute_url())
        child.status = Child.Status.INACTIVE
        child.updated_by = request.user
        child.save(update_fields=["status", "updated_by", "updated_at"])
        messages.success(
            request,
            f"{child.short_name} has graduated. Attendance records were kept.",
        )
        return redirect(child.get_absolute_url())


def render_graduate(request, child):
    return render(request, "children/graduate.html", {"child": child})


class ChildFieldSuggestView(PermissionRequiredMixin, View):
    """HTMX suggestions for school and address on the child form."""

    permission_required = "children.view_child"
    template_name = "children/partials/field_suggestions.html"

    def get(self, request):
        field = (request.GET.get("field") or "").strip()
        term = (request.GET.get("q") or "").strip()
        if field not in SUGGEST_FIELDS:
            return render(
                request,
                self.template_name,
                {"suggestions": [], "search_term": term, "field": field},
            )
        return render(
            request,
            self.template_name,
            {
                "suggestions": suggest_child_field_values(field, term),
                "search_term": term,
                "field": field,
            },
        )


ChildCreateView.extra_context = {"form_title": "Add a child", "submit_label": "Save child"}
ChildUpdateView.extra_context = {"form_title": "Edit child", "submit_label": "Save changes"}
