from django.db.models import Count, Q

from apps.core.phones import phone_search_digits
from apps.visitors.models import Visit, Visitor


def search_visitors(term: str = ""):
    queryset = Visitor.objects.annotate(total_visits=Count("visits")).order_by(
        "last_name", "first_name"
    )
    term = (term or "").strip()
    if not term:
        return queryset
    query = (
        Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(address__icontains=term)
    )
    return queryset.filter(query)


def search_children_for_companion(term: str):
    from apps.children.models import Child

    queryset = Child.objects.filter(status=Child.Status.ACTIVE)
    term = (term or "").strip()
    if not term:
        return queryset.order_by("last_name", "first_name")[:12]
    phone = phone_search_digits(term)
    query = (
        Q(first_name__icontains=term)
        | Q(middle_name__icontains=term)
        | Q(last_name__icontains=term)
        | Q(preferred_name__icontains=term)
    )
    if phone:
        query |= Q(phone__icontains=phone)
    return queryset.filter(query).order_by("last_name", "first_name")[:12]


def visits_on(day):
    return Visit.objects.filter(date=day).select_related(
        "visitor", "brought_by_parent", "brought_by_child"
    )
