"""Distinct school and address values already used on child records."""

from django.db.models import QuerySet

from apps.children.models import Child

SUGGEST_FIELDS = {
    "school_name": "school_name",
    "address": "address",
}


def suggest_child_field_values(field: str, term: str, *, limit: int = 8) -> list[str]:
    """Return distinct non-blank values for school_name or address matching term."""
    db_field = SUGGEST_FIELDS.get(field)
    term = (term or "").strip()
    if not db_field or not term:
        return []

    values: QuerySet[str] = (
        Child.objects.exclude(**{db_field: ""})
        .filter(**{f"{db_field}__icontains": term})
        .order_by(db_field)
        .values_list(db_field, flat=True)
        .distinct()[:limit]
    )
    return list(values)
