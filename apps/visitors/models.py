from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from apps.core.dates import age_in_years, local_today
from apps.core.models import AuditModel
from apps.core.phones import format_phone, normalize_ghana_phone


class Visitor(AuditModel):
    class Gender(models.TextChoices):
        FEMALE = "FEMALE", "Girl"
        MALE = "MALE", "Boy"
        UNSPECIFIED = "UNSPECIFIED", "Unspecified"

    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank if unknown.",
    )
    gender = models.CharField(max_length=20, choices=Gender.choices)
    address = models.TextField(blank=True, help_text="Optional. Where they stay.")
    child = models.OneToOneField(
        "children.Child",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visitor_profile",
        help_text="Set when this visitor is converted to a child record.",
    )
    follow_up_baseline = models.PositiveIntegerField(
        default=0,
        help_text="Visit count when follow-up was last marked done.",
    )
    last_followed_up_at = models.DateTimeField(null=True, blank=True)
    last_followed_up_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visitor_follow_ups",
    )

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(gender__in=["FEMALE", "MALE", "UNSPECIFIED"]),
                name="visitor_gender_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["date_of_birth"]),
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("visitors:detail", args=[self.pk])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def short_name(self) -> str:
        return self.full_name

    @property
    def age(self) -> int | None:
        if self.date_of_birth is None:
            return None
        return age_in_years(self.date_of_birth, local_today())

    @property
    def is_converted(self) -> bool:
        return self.child_id is not None

    @property
    def visit_count(self) -> int:
        annotated = getattr(self, "total_visits", None)
        if annotated is not None:
            return annotated
        return self.visits.count()

    @property
    def visits_since_follow_up(self) -> int:
        annotated = getattr(self, "since", None)
        if annotated is not None:
            return annotated
        return max(self.visit_count - self.follow_up_baseline, 0)

    @property
    def needs_follow_up(self) -> bool:
        from apps.visitors.follow_up import FOLLOW_UP_THRESHOLD

        if self.is_converted:
            return False
        return self.visits_since_follow_up >= FOLLOW_UP_THRESHOLD

    def clean(self) -> None:
        super().clean()
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.address = (self.address or "").strip()
        if not self.first_name:
            raise ValidationError({"first_name": "First name is required."})
        if not self.last_name:
            raise ValidationError({"last_name": "Last name is required."})
        if self.date_of_birth and self.date_of_birth > local_today():
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})


class Visit(AuditModel):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name="visits")
    date = models.DateField()
    reason = models.TextField(help_text="Why they came to visit.")
    brought_by_parent = models.ForeignKey(
        "parents.Parent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visitor_brought",
    )
    brought_by_child = models.ForeignKey(
        "children.Child",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visitor_brought",
    )
    companion_name = models.CharField(
        max_length=160,
        blank=True,
        help_text="Optional. Full name of who they came with, when not already in the records.",
    )
    companion_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional. Ghana phone for the person they came with.",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visits_recorded",
    )

    class Meta:
        ordering = ["-date", "visitor__last_name", "visitor__first_name"]
        constraints = [
            models.UniqueConstraint(fields=["visitor", "date"], name="unique_visitor_visit_date"),
        ]
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self) -> str:
        return f"{self.visitor} — {self.date:%-d %B %Y}"

    @property
    def companion_phone_display(self) -> str:
        return format_phone(self.companion_phone)

    @property
    def came_with_label(self) -> str:
        if self.brought_by_parent_id:
            return self.brought_by_parent.full_name
        if self.brought_by_child_id:
            return self.brought_by_child.short_name
        name = (self.companion_name or "").strip()
        phone = self.companion_phone_display
        if name and phone:
            return f"{name} · {phone}"
        return name or phone or ""

    def clean(self) -> None:
        super().clean()
        self.reason = (self.reason or "").strip()
        self.companion_name = (self.companion_name or "").strip()
        if not self.reason:
            raise ValidationError({"reason": "Say why they came to visit."})
        if self.date and self.date > local_today():
            raise ValidationError({"date": "Visit date cannot be in the future."})
        linked = sum(
            1
            for value in (self.brought_by_parent_id, self.brought_by_child_id)
            if value is not None
        )
        has_companion = bool(self.companion_name or self.companion_phone)
        if linked > 1:
            raise ValidationError("Choose either a parent or a child who brought them, not both.")
        if linked and has_companion:
            raise ValidationError(
                "Clear the typed name and phone when linking someone already in the records."
            )
        if self.companion_phone:
            try:
                self.companion_phone = normalize_ghana_phone(self.companion_phone)
            except ValidationError as error:
                raise ValidationError({"companion_phone": error.messages}) from error
