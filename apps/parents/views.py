from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.children.models import Child
from apps.core.htmx import is_htmx
from apps.core.phones import phone_search_digits
from apps.parents.forms import LinkChildrenForm, ParentForm
from apps.parents.models import ChildGuardian, Parent


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


def children_available_to_link(parent: Parent, term: str = "", selected_ids=None):
    """Active children not yet linked to this parent, plus any still-selected rows."""
    linked_ids = set(parent.child_links.values_list("child_id", flat=True))
    selected_ids = {int(pk) for pk in (selected_ids or []) if str(pk).isdigit()}
    queryset = Child.objects.filter(status=Child.Status.ACTIVE).exclude(pk__in=linked_ids)
    term = (term or "").strip()
    matches = queryset
    if term:
        phone = phone_search_digits(term)
        query = (
            Q(first_name__icontains=term)
            | Q(middle_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(preferred_name__icontains=term)
            | Q(school_name__icontains=term)
        )
        if phone:
            query |= Q(phone__icontains=phone)
        matches = queryset.filter(query)
    selected = Child.objects.filter(pk__in=selected_ids).exclude(pk__in=linked_ids)
    combined_ids = list(matches.values_list("pk", flat=True)[:40]) + list(
        selected.values_list("pk", flat=True)
    )
    return (
        Child.objects.filter(pk__in=combined_ids)
        .order_by("last_name", "first_name", "pk")
        .distinct()
    )


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


class LinkChildrenView(PermissionRequiredMixin, View):
    permission_required = "parents.add_childguardian"
    template_name = "parents/link_children.html"
    partial_template_name = "parents/partials/child_picker.html"

    def _parent(self, pk):
        return get_object_or_404(Parent, pk=pk)

    def _selected_ids(self, request):
        return request.POST.getlist("children") or request.GET.getlist("children")

    def _context(self, request, parent, form=None):
        term = (request.POST.get("q") if request.method == "POST" else request.GET.get("q")) or ""
        term = term.strip()
        selected_ids = self._selected_ids(request)
        children_queryset = children_available_to_link(parent, term, selected_ids)
        return {
            "parent": parent,
            "form": form
            or LinkChildrenForm(
                parent=parent,
                children_queryset=children_queryset,
                initial={"children": selected_ids} if selected_ids else None,
            ),
            "search_term": term,
            "child_matches": children_queryset,
            "selected_ids": {str(pk) for pk in selected_ids},
        }

    def get(self, request, pk):
        parent = self._parent(pk)
        context = self._context(request, parent)
        template = self.partial_template_name if is_htmx(request) else self.template_name
        return render(request, template, context)

    def post(self, request, pk):
        parent = self._parent(pk)
        term = (request.POST.get("q") or "").strip()
        selected_ids = self._selected_ids(request)
        children_queryset = children_available_to_link(parent, term, selected_ids)
        form = LinkChildrenForm(
            request.POST,
            parent=parent,
            children_queryset=children_queryset,
        )
        if form.is_valid():
            relationship = form.cleaned_data["relationship"]
            linked = []
            for child in form.cleaned_data["children"]:
                ChildGuardian.objects.create(
                    child=child,
                    parent=parent,
                    relationship=relationship,
                    created_by=request.user,
                    updated_by=request.user,
                )
                linked.append(child.short_name)
            if len(linked) == 1:
                messages.success(
                    request,
                    f"{parent.full_name} is now linked to {linked[0]}.",
                )
            else:
                messages.success(
                    request,
                    f"{parent.full_name} is now linked to {len(linked)} children.",
                )
            return redirect(parent.get_absolute_url())
        return render(
            request,
            self.template_name,
            self._context(request, parent, form=form),
        )
