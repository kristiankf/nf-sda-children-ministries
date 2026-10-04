from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.children.forms import AgeGroupForm
from apps.children.models import AgeGroup


def _kind_meta(kind: str) -> dict:
    if kind == AgeGroup.Kind.YOUTH:
        return {
            "kind": AgeGroup.Kind.YOUTH,
            "title": "Youth groups",
            "singular": "youth group",
            "list_url": "youth_groups",
            "create_url": "youth_group_create",
            "edit_url": "youth_group_edit",
            "remove_url": "youth_group_remove",
        }
    return {
        "kind": AgeGroup.Kind.SABBATH,
        "title": "Sabbath classes",
        "singular": "Sabbath class",
        "list_url": "sabbath_classes",
        "create_url": "sabbath_class_create",
        "edit_url": "sabbath_class_edit",
        "remove_url": "sabbath_class_remove",
    }


class AgeGroupListView(PermissionRequiredMixin, View):
    permission_required = "children.view_agegroup"

    def get(self, request, kind):
        meta = _kind_meta(kind)
        groups = AgeGroup.objects.filter(kind=meta["kind"]).order_by("sort_order", "name")
        return render(
            request,
            "children/age_groups/list.html",
            {
                "groups": groups,
                **meta,
                "can_change": request.user.has_perm("children.change_agegroup"),
            },
        )


class AgeGroupCreateView(PermissionRequiredMixin, View):
    permission_required = "children.add_agegroup"

    def get(self, request, kind):
        meta = _kind_meta(kind)
        form = AgeGroupForm(kind=meta["kind"])
        return render(request, "children/age_groups/form.html", {"form": form, **meta})

    def post(self, request, kind):
        meta = _kind_meta(kind)
        form = AgeGroupForm(request.POST, kind=meta["kind"])
        if form.is_valid():
            group = form.save()
            messages.success(request, f"{group.name} has been added.")
            return redirect(meta["list_url"])
        return render(request, "children/age_groups/form.html", {"form": form, **meta})


class AgeGroupUpdateView(PermissionRequiredMixin, View):
    permission_required = "children.change_agegroup"

    def _group(self, kind, slug):
        meta = _kind_meta(kind)
        return meta, get_object_or_404(AgeGroup, kind=meta["kind"], slug=slug)

    def get(self, request, kind, slug):
        meta, group = self._group(kind, slug)
        form = AgeGroupForm(instance=group, kind=meta["kind"])
        return render(
            request,
            "children/age_groups/form.html",
            {"form": form, "group": group, **meta},
        )

    def post(self, request, kind, slug):
        meta, group = self._group(kind, slug)
        form = AgeGroupForm(request.POST, instance=group, kind=meta["kind"])
        if form.is_valid():
            saved = form.save()
            messages.success(request, f"{saved.name} has been updated.")
            return redirect(meta["list_url"])
        return render(
            request,
            "children/age_groups/form.html",
            {"form": form, "group": group, **meta},
        )


class AgeGroupDeleteView(PermissionRequiredMixin, View):
    permission_required = "children.delete_agegroup"

    def _group(self, kind, slug):
        meta = _kind_meta(kind)
        return meta, get_object_or_404(AgeGroup, kind=meta["kind"], slug=slug)

    def get(self, request, kind, slug):
        meta, group = self._group(kind, slug)
        return render(
            request,
            "children/age_groups/delete.html",
            {"group": group, **meta},
        )

    def post(self, request, kind, slug):
        meta, group = self._group(kind, slug)
        name = group.name
        try:
            group.delete()
        except ProtectedError:
            messages.error(
                request,
                f"{name} is still chosen for some children. Clear those placements first.",
            )
            return redirect(meta["list_url"])
        messages.success(request, f"{name} has been removed.")
        return redirect(meta["list_url"])
