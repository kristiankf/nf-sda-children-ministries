from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.children.forms import LinkGuardianForm, NewGuardianForm
from apps.children.models import Child
from apps.core.htmx import is_htmx
from apps.core.phones import phone_search_digits
from apps.parents.models import ChildGuardian, Parent


class AddGuardianView(PermissionRequiredMixin, View):
    permission_required = "parents.add_childguardian"
    template_name = "children/add_guardian.html"

    def _child(self, pk):
        return get_object_or_404(Child, pk=pk)

    def get(self, request, pk):
        child = self._child(pk)
        template = (
            "children/partials/parent_matches.html" if is_htmx(request) else self.template_name
        )
        return render(request, template, self._context(request, child))

    def post(self, request, pk):
        child = self._child(pk)
        action = request.POST.get("action")
        if action == "link":
            form = LinkGuardianForm(request.POST, child=child, prefix="link")
            new_form = NewGuardianForm(prefix="new")
            if form.is_valid():
                link = form.save(commit=False)
                link.created_by = request.user
                link.updated_by = request.user
                link.save()
                messages.success(
                    request, f"{link.parent.full_name} is now linked to {child.short_name}."
                )
                return redirect(child.get_absolute_url())
        elif action == "create":
            form = LinkGuardianForm(child=child, prefix="link")
            new_form = NewGuardianForm(request.POST, prefix="new")
            if new_form.is_valid():
                parent = new_form.save(commit=False)
                parent.created_by = request.user
                parent.updated_by = request.user
                parent.save()
                ChildGuardian.objects.create(
                    child=child,
                    parent=parent,
                    relationship=new_form.cleaned_data["relationship"],
                    created_by=request.user,
                    updated_by=request.user,
                )
                messages.success(
                    request, f"{parent.full_name} has been added for {child.short_name}."
                )
                return redirect(child.get_absolute_url())
        else:
            form = LinkGuardianForm(child=child, prefix="link")
            new_form = NewGuardianForm(prefix="new")
        return render(
            request,
            self.template_name,
            self._context(request, child, link_form=form, new_form=new_form),
        )

    def _context(self, request, child, link_form=None, new_form=None):
        term = (request.GET.get("q") or "").strip()
        parents = Parent.objects.none()
        if term:
            phone = phone_search_digits(term)
            query = Q(first_name__icontains=term) | Q(last_name__icontains=term)
            if phone:
                query |= Q(phone_primary__icontains=phone) | Q(phone_secondary__icontains=phone)
            parents = Parent.objects.filter(query).order_by("last_name", "first_name")[:12]
        return {
            "child": child,
            "link_form": link_form or LinkGuardianForm(child=child, prefix="link"),
            "new_form": new_form or NewGuardianForm(prefix="new"),
            "parent_matches": parents,
            "search_term": term,
        }


class RemoveGuardianView(PermissionRequiredMixin, View):
    permission_required = "parents.delete_childguardian"
    template_name = "children/remove_guardian.html"

    def _link(self, child_pk, link_pk):
        return get_object_or_404(
            ChildGuardian.objects.select_related("child", "parent"),
            pk=link_pk,
            child_id=child_pk,
        )

    def get(self, request, pk, link_pk):
        link = self._link(pk, link_pk)
        return render(request, self.template_name, {"link": link, "child": link.child})

    def post(self, request, pk, link_pk):
        link = self._link(pk, link_pk)
        child = link.child
        name = link.parent.full_name
        link.delete()
        messages.success(
            request,
            f"{name} is no longer linked to {child.short_name}. The parent record was kept.",
        )
        return redirect(child.get_absolute_url())
