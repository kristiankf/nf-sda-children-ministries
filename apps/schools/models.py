from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from apps.core.models import TimeStampedModel
from apps.schools.levels import ClassLevel


class AcademicYear(TimeStampedModel):
    """A school year. A new year defaults to 1 September through 31 August.

    The dates can be changed. The day after `end_date`, active children move
    up one class and a placement is kept for the year that closed.
    """

    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=F("start_date")),
                name="academic_year_dates_ordered",
            ),
            models.UniqueConstraint(
                fields=["is_current"],
                condition=Q(is_current=True),
                name="one_current_academic_year",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        self.name = (self.name or "").strip()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "The end date must be on or after the start date."})
        if not (self.start_date and self.end_date):
            return
        self.name = f"{self.start_date.year}/{self.end_date.year}"
        clash = AcademicYear.objects.filter(name=self.name)
        overlap = AcademicYear.objects.filter(
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        )
        if self.pk:
            clash = clash.exclude(pk=self.pk)
            overlap = overlap.exclude(pk=self.pk)
        if clash.exists():
            raise ValidationError({"end_date": "Another academic year already uses these years."})
        if overlap.exists():
            raise ValidationError({"start_date": "These dates overlap another academic year."})


class ClassPlacement(TimeStampedModel):
    """The class a child was in for one academic year."""

    child = models.ForeignKey(
        "children.Child",
        on_delete=models.CASCADE,
        related_name="class_placements",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="placements",
    )
    class_level = models.CharField(max_length=20, choices=ClassLevel.choices)

    class Meta:
        ordering = ["-academic_year__start_date"]
        verbose_name = "class placement"
        constraints = [
            models.UniqueConstraint(
                fields=["child", "academic_year"],
                name="one_class_placement_per_year",
            ),
            models.CheckConstraint(
                condition=Q(class_level__in=ClassLevel.values),
                name="class_placement_level_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["academic_year", "class_level"]),
        ]

    def __str__(self) -> str:
        return f"{self.child} · {self.get_class_level_display()} · {self.academic_year}"
