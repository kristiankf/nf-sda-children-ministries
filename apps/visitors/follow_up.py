"""Visitor follow-up: check in after every three visits since the last checkup."""

from django.db.models import Count, F
from django.utils import timezone

from apps.visitors.models import Visitor

FOLLOW_UP_THRESHOLD = 3


def visitors_needing_follow_up(*, limit: int | None = None):
    """Visitors with enough new visits since the last checkup, not yet converted."""
    queryset = (
        Visitor.objects.filter(child__isnull=True)
        .annotate(total_visits=Count("visits"))
        .filter(total_visits__gte=F("follow_up_baseline") + FOLLOW_UP_THRESHOLD)
        .annotate(since=F("total_visits") - F("follow_up_baseline"))
        .order_by("-since", "last_name", "first_name")
    )
    if limit is not None:
        return list(queryset[:limit])
    return list(queryset)


def mark_followed_up(visitor, user) -> None:
    visitor.follow_up_baseline = visitor.visits.count()
    visitor.last_followed_up_at = timezone.now()
    visitor.last_followed_up_by = user
    visitor.updated_by = user
    visitor.save(
        update_fields=[
            "follow_up_baseline",
            "last_followed_up_at",
            "last_followed_up_by",
            "updated_by",
            "updated_at",
        ]
    )


def convert_visitor_to_child(visitor, user):
    """Create an incomplete Child from a visitor and link them. Visit history stays."""
    from apps.children.models import Child

    if visitor.child_id:
        raise ValueError("This visitor is already linked to a child.")

    child = Child(
        first_name=visitor.first_name,
        last_name=visitor.last_name,
        date_of_birth=visitor.date_of_birth,
        gender=visitor.gender,
        address=visitor.address,
        status=Child.Status.ACTIVE,
        created_by=user,
        updated_by=user,
    )
    child.full_clean()
    child.save()
    visitor.child = child
    visitor.updated_by = user
    visitor.save(update_fields=["child", "updated_by", "updated_at"])
    return child
