"""Sabbath classes and youth groups derived from a child's age.

The birthday decides the group. A coordinator may set
`Child.sabbath_class_override` when a child should sit in a different
Sabbath class. Youth group always follows the birthday.
"""

from apps.children.models import AgeGroup
from apps.core.dates import age_in_years, latest_birth_date_for_age

AGE_GROUP_ROWS = (
    {
        "slug": "baby-steps",
        "name": "Baby Steps",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 1,
        "min_years": 0,
        "max_years": 0,
        "color": "rose",
    },
    {
        "slug": "beginner",
        "name": "Beginner",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 2,
        "min_years": 1,
        "max_years": 3,
        "color": "amber",
    },
    {
        "slug": "kindergarten",
        "name": "Kindergarten",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 3,
        "min_years": 4,
        "max_years": 6,
        "color": "lime",
    },
    {
        "slug": "primary",
        "name": "Primary",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 4,
        "min_years": 7,
        "max_years": 9,
        "color": "teal",
    },
    {
        "slug": "power-point",
        "name": "Power Point",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 5,
        "min_years": 10,
        "max_years": 12,
        "color": "blue",
    },
    {
        "slug": "realtime",
        "name": "RealTime",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 6,
        "min_years": 13,
        "max_years": 14,
        "color": "indigo",
    },
    {
        "slug": "corner-stone",
        "name": "Corner Stone",
        "kind": AgeGroup.Kind.SABBATH,
        "sort_order": 7,
        "min_years": 15,
        "max_years": None,
        "color": "purple",
    },
    {
        "slug": "adventurer",
        "name": "Adventurer",
        "kind": AgeGroup.Kind.YOUTH,
        "sort_order": 1,
        "min_years": 4,
        "max_years": 9,
        "color": "sky",
    },
    {
        "slug": "pathfinder",
        "name": "Pathfinder",
        "kind": AgeGroup.Kind.YOUTH,
        "sort_order": 2,
        "min_years": 10,
        "max_years": 15,
        "color": "orange",
    },
)


def oldest_sabbath_band(bands=None):
    """The Sabbath class that starts at the highest age. Graduation uses this class."""
    if bands is None:
        bands = load_bands()[0]
    if not bands:
        return None
    return max(bands, key=lambda band: (band.min_years, band.sort_order))


def renumber_bands(kind: str) -> None:
    bands = AgeGroup.objects.filter(kind=kind).order_by("min_years", "name", "pk")
    for index, band in enumerate(bands, start=1):
        if band.sort_order != index:
            AgeGroup.objects.filter(pk=band.pk).update(sort_order=index)


def ranges_overlap(left_min, left_max, right_min, right_max) -> bool:
    left_end = 200 if left_max is None else left_max
    right_end = 200 if right_max is None else right_max
    return left_min <= right_end and right_min <= left_end


def match_band(age: int, bands):
    for band in bands:
        if age >= band.min_years and (band.max_years is None or age <= band.max_years):
            return band
    return None


def birth_date_bounds(today, band):
    """Dates of birth whose completed age falls inside this band."""
    oldest = None
    if band.max_years is not None:
        oldest = latest_birth_date_for_age(today, band.max_years + 1)
    youngest = latest_birth_date_for_age(today, band.min_years)
    return oldest, youngest


def load_bands():
    sabbath = list(AgeGroup.objects.filter(kind=AgeGroup.Kind.SABBATH).order_by("sort_order", "pk"))
    youth = list(AgeGroup.objects.filter(kind=AgeGroup.Kind.YOUTH).order_by("sort_order", "pk"))
    return sabbath, youth


def attach_ministry_groups(children, today):
    """Set sabbath_class, youth_group, and calculated_sabbath_class on each child."""
    children = list(children)
    sabbath_bands, youth_bands = load_bands()
    for child in children:
        age = age_in_years(child.date_of_birth, today)
        calculated = match_band(age, sabbath_bands)
        child.calculated_sabbath_class = calculated
        child.sabbath_class = child.sabbath_class_override or calculated
        child.youth_group = match_band(age, youth_bands)
    return children


def class_summary(today):
    """Counts of active children in each Sabbath class, plus Corner Stone children."""
    from apps.children.models import Child

    sabbath_bands, _youth = load_bands()
    children = attach_ministry_groups(
        Child.objects.filter(status=Child.Status.ACTIVE).select_related("sabbath_class_override"),
        today,
    )
    counts = []
    for band in sabbath_bands:
        count = sum(
            1 for child in children if child.sabbath_class and child.sabbath_class.pk == band.pk
        )
        counts.append({"band": band, "count": count})
    oldest = oldest_sabbath_band(sabbath_bands)
    ready = [
        child
        for child in children
        if oldest and child.sabbath_class and child.sabbath_class.pk == oldest.pk
    ]
    return counts, ready, oldest
