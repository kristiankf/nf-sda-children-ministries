from django.db.models import Q

from apps.children.groups import birth_date_bounds
from apps.children.models import AgeGroup, Child
from apps.core.dates import latest_birth_date_for_age
from apps.core.phones import phone_search_digits
from apps.schools.levels import ClassLevel


def _parse_age(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        age = int(value)
    except TypeError, ValueError:
        return None
    if age < 0 or age > 30:
        return None
    return age


def _age_query(today, band):
    oldest, youngest = birth_date_bounds(today, band)
    query = Q(date_of_birth__lte=youngest)
    if oldest is not None:
        query &= Q(date_of_birth__gt=oldest)
    return query


def filtered_children(params, today):
    queryset = Child.objects.select_related("sabbath_class_override").prefetch_related(
        "guardians__parent"
    )
    term = (params.get("q") or "").strip()
    if term:
        phone = phone_search_digits(term)
        matching_levels = [
            value for value, label in ClassLevel.choices if term.lower() in label.lower()
        ]
        query = (
            Q(first_name__icontains=term)
            | Q(middle_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(preferred_name__icontains=term)
            | Q(guardians__parent__first_name__icontains=term)
            | Q(guardians__parent__last_name__icontains=term)
            | Q(school_name__icontains=term)
        )
        if matching_levels:
            query |= Q(class_level__in=matching_levels)
        if phone:
            query |= Q(phone__icontains=phone)
            query |= Q(guardians__parent__phone_primary__icontains=phone)
            query |= Q(guardians__parent__phone_secondary__icontains=phone)
        queryset = queryset.filter(query)

    status = params.get("status") or Child.Status.ACTIVE
    if status != "all" and status in Child.Status.values:
        queryset = queryset.filter(status=status)

    gender = params.get("gender") or ""
    if gender in Child.Gender.values:
        queryset = queryset.filter(gender=gender)

    class_level = params.get("class_level") or ""
    if class_level == "none":
        queryset = queryset.filter(class_level="")
    elif class_level in ClassLevel.values:
        queryset = queryset.filter(class_level=class_level)

    age_min = _parse_age(params.get("age_min"))
    age_max = _parse_age(params.get("age_max"))
    if age_min is not None:
        queryset = queryset.filter(date_of_birth__lte=latest_birth_date_for_age(today, age_min))
    if age_max is not None:
        queryset = queryset.filter(date_of_birth__gt=latest_birth_date_for_age(today, age_max + 1))

    division = (params.get("division") or "").strip()
    if division == "none":
        queryset = queryset.filter(sabbath_class_override__isnull=True)
        bands = AgeGroup.objects.filter(kind=AgeGroup.Kind.SABBATH)
        if bands.exists():
            covered = Q()
            for band in bands:
                covered |= _age_query(today, band)
            queryset = queryset.exclude(covered)
    elif division:
        band = AgeGroup.objects.filter(kind=AgeGroup.Kind.SABBATH, slug=division).first()
        if band:
            calculated = Q(sabbath_class_override__isnull=True) & _age_query(today, band)
            queryset = queryset.filter(calculated | Q(sabbath_class_override=band))

    youth = (params.get("youth") or "").strip()
    if youth == "none":
        queryset = queryset.filter(
            Q(date_of_birth__gt=latest_birth_date_for_age(today, 4))
            | Q(date_of_birth__lte=latest_birth_date_for_age(today, 16))
        )
    elif youth:
        band = AgeGroup.objects.filter(kind=AgeGroup.Kind.YOUTH, slug=youth).first()
        if band:
            queryset = queryset.filter(_age_query(today, band))

    return queryset.distinct().order_by("last_name", "first_name", "pk")
