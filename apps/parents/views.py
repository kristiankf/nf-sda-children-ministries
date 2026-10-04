from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.htmx import is_htmx
from apps.core.phones import phone_search_digits
from apps.parents.forms import ParentForm
from apps.parents.models import Parent


class AuditSaveMixin:
    def form_valid(self, form):
        if form.instance.pk is None:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


def search_parents(term: str):
    queryset = Parent.objects.prefetch_related("child_links__child")
    term = (term or "").strip()
    if not term:
        return queryset.order_by("last_name", "first_name")
    phone = phone_search_digits(term)
    query = Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(email__icontains=term)
    if phone:
        query |= Q(phone_primary__icontains=phone) | Q(phone_secondary__icontains=phone)
    return queryset.filter(query).distinct().order_by("last_name", "first_name")


class ParentListView(PermissionRequiredMixin, ListView):
    permission_required = "parents.view_parent"
    context_object_name = "parents"
    paginate_by = 25

    def get_template_names(self):
        if is_htmx(self.request):
            return ["parents/partials/results.html"]
        return ["parents/list.html"]

    def get_queryset(self):
        return search_parents(self.request.GET.get("q", ""))


class ParentCreateView(AuditSaveMixin, PermissionRequiredMixin, CreateView):
    permission_required = "parents.add_parent"
    model = Parent
    form_class = ParentForm
    template_name = "parents/form.html"
    extra_context = {"form_title": "Add a parent or guardian", "submit_label": "Save"}

    def get_success_url(self):
        messages.success(self.request, f"{self.object.full_name} has been added.")
        return self.object.get_absolute_url()


class ParentUpdateView(AuditSaveMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "parents.change_parent"
    model = Parent
    form_class = ParentForm
    template_name = "parents/form.html"
    extra_context = {"form_title": "Edit parent or guardian", "submit_label": "Save changes"}

    def get_success_url(self):
        messages.success(self.request, f"{self.object.full_name} has been updated.")
        return self.object.get_absolute_url()


class ParentDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "parents.view_parent"
    model = Parent
    context_object_name = "parent"
    template_name = "parents/detail.html"

    def get_queryset(self):
        return Parent.objects.prefetch_related("child_links__child")
