from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.htmx import is_htmx
from apps.parents.views import search_parents
from apps.visitors.follow_up import (
    convert_visitor_to_child,
    mark_followed_up,
    visitors_needing_follow_up,
)
from apps.visitors.forms import VisitForm, VisitorIdentityForm
from apps.visitors.models import Visitor
from apps.visitors.queries import search_children_for_companion, search_visitors


class VisitorListView(PermissionRequiredMixin, ListView):
    permission_required = "visitors.view_visitor"
    context_object_name = "visitors"
    paginate_by = 25

    def get_template_names(self):
        if is_htmx(self.request):
            return ["visitors/partials/results.html"]
        return ["visitors/list.html"]

    def get_queryset(self):
        return search_visitors(self.request.GET.get("q", ""))


class VisitorDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "visitors.view_visitor"
    model = Visitor
    context_object_name = "visitor"
    template_name = "visitors/detail.html"

    def get_queryset(self):
        return Visitor.objects.prefetch_related(
            "visits__brought_by_parent",
            "visits__brought_by_child",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visitor = self.object
        context.update(
            {
                "visits": visitor.visits.all(),
                "can_follow_up": self.request.user.has_perm("visitors.change_visitor")
                and visitor.needs_follow_up,
                "can_convert": self.request.user.has_perm("children.add_child")
                and not visitor.is_converted,
            }
        )
        return context


class VisitorCreateView(PermissionRequiredMixin, View):
    permission_required = ("visitors.add_visitor", "visitors.add_visit")
    template_name = "visitors/form.html"

    def get(self, request):
        existing = self._existing_from_get(request)
        initial = {"existing_visitor": existing.pk} if existing else {}
        identity = VisitorIdentityForm(prefix="visitor")
        visit = VisitForm(prefix="visit", initial=initial)
        return render(
            request,
            self.template_name,
            self._context(identity, visit, existing=existing),
        )

    def post(self, request):
        identity = VisitorIdentityForm(request.POST, prefix="visitor")
        visit = VisitForm(request.POST, prefix="visit")
        skip_identity = bool((request.POST.get("visit-existing_visitor") or "").strip())
        identity_ok = True if skip_identity else identity.is_valid()
        visit_ok = visit.is_valid()
        if identity_ok and visit_ok:
            return self._save(request, identity, visit)
        existing = None
        if visit_ok:
            existing = visit.cleaned_data.get("existing_visitor")
        elif skip_identity:
            existing = Visitor.objects.filter(
                pk=request.POST.get("visit-existing_visitor"),
                child__isnull=True,
            ).first()
        return render(
            request,
            self.template_name,
            self._context(identity, visit, existing=existing),
        )

    @transaction.atomic
    def _save(self, request, identity: VisitorIdentityForm, visit: VisitForm):
        existing = visit.cleaned_data.get("existing_visitor")
        if existing:
            visitor = existing
        else:
            visitor = identity.save(commit=False)
            visitor.created_by = request.user
            visitor.updated_by = request.user
            visitor.full_clean()
            visitor.save()
        record = visit.build_visit(visitor, request.user)
        record.full_clean()
        record.save()
        messages.success(
            request,
            f"Recorded {visitor.full_name}'s visit for {record.date:%-d %B %Y}.",
        )
        return redirect(visitor.get_absolute_url())

    def _existing_from_get(self, request):
        visitor_id = request.GET.get("visitor")
        if visitor_id and str(visitor_id).isdigit():
            return Visitor.objects.filter(pk=visitor_id, child__isnull=True).first()
        return None

    def _context(self, identity, visit, existing=None):
        return {
            "identity_form": identity,
            "visit_form": visit,
            "existing_visitor": existing,
            "form_title": (f"Add visit for {existing.full_name}" if existing else "Add a visitor"),
        }


class VisitorSearchView(PermissionRequiredMixin, View):
    permission_required = "visitors.view_visitor"
    template_name = "visitors/partials/visitor_matches.html"

    def get(self, request):
        term = request.GET.get("q", "")
        visitors = search_visitors(term).filter(child__isnull=True)[:12] if term else []
        return render(
            request,
            self.template_name,
            {"visitors": visitors, "search_term": term},
        )


class CompanionParentSearchView(PermissionRequiredMixin, View):
    permission_required = "visitors.add_visit"
    template_name = "visitors/partials/parent_matches.html"

    def get(self, request):
        term = request.GET.get("q", "")
        parents = search_parents(term)[:12] if term else []
        return render(
            request,
            self.template_name,
            {"parents": parents, "search_term": term},
        )


class CompanionChildSearchView(PermissionRequiredMixin, View):
    permission_required = "visitors.add_visit"
    template_name = "visitors/partials/child_matches.html"

    def get(self, request):
        term = request.GET.get("q", "")
        children = search_children_for_companion(term) if term else []
        return render(
            request,
            self.template_name,
            {"children": children, "search_term": term},
        )


class VisitorFollowUpView(PermissionRequiredMixin, View):
    permission_required = "visitors.change_visitor"

    def post(self, request, pk):
        visitor = get_object_or_404(Visitor, pk=pk)
        if visitor.is_converted:
            messages.error(request, "This visitor is already a child in the records.")
            return redirect(visitor.get_absolute_url())
        if not visitor.needs_follow_up:
            messages.info(request, f"{visitor.full_name} does not need follow-up yet.")
            return redirect(visitor.get_absolute_url())
        mark_followed_up(visitor, request.user)
        messages.success(request, f"Marked {visitor.full_name} as checked up on.")
        next_url = request.POST.get("next") or visitor.get_absolute_url()
        return redirect(next_url)


class VisitorConvertView(PermissionRequiredMixin, View):
    permission_required = "children.add_child"
    template_name = "visitors/convert.html"

    def get(self, request, pk):
        visitor = get_object_or_404(Visitor, pk=pk)
        if visitor.is_converted:
            messages.info(request, "This visitor is already linked to a child.")
            return redirect(visitor.child.get_absolute_url())
        return render(request, self.template_name, {"visitor": visitor})

    @transaction.atomic
    def post(self, request, pk):
        visitor = get_object_or_404(Visitor, pk=pk)
        if visitor.is_converted:
            return redirect(visitor.child.get_absolute_url())
        child = convert_visitor_to_child(visitor, request.user)
        messages.success(
            request,
            f"{visitor.full_name} is now a child record. Finish any missing details when you can.",
        )
        return redirect(child.get_absolute_url())


class VisitorFollowUpListView(PermissionRequiredMixin, ListView):
    permission_required = "visitors.view_visitor"
    template_name = "visitors/follow_up.html"
    context_object_name = "visitors"

    def get_queryset(self):
        return visitors_needing_follow_up()
