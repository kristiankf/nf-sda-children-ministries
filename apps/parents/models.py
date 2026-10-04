from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from apps.core.models import AuditModel
from apps.core.phones import format_phone, normalize_ghana_phone


class Parent(AuditModel):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["phone_primary"]),
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("parents:detail", args=[self.pk])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def phone_display(self) -> str:
        return format_phone(self.phone_primary)

    @property
    def phone_secondary_display(self) -> str:
        return format_phone(self.phone_secondary)

    def clean(self) -> None:
        super().clean()
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        if not self.first_name:
            raise ValidationError({"first_name": "First name is required."})
        if not self.last_name:
            raise ValidationError({"last_name": "Last name is required."})
        if self.phone_primary:
            self.phone_primary = normalize_ghana_phone(self.phone_primary)
        if self.phone_secondary:
            self.phone_secondary = normalize_ghana_phone(self.phone_secondary)


class ChildGuardian(AuditModel):
    class Relationship(models.TextChoices):
        FATHER = "FATHER", "Father"
        MOTHER = "MOTHER", "Mother"
        GUARDIAN = "GUARDIAN", "Guardian"
        OTHER = "OTHER", "Other"

    child = models.ForeignKey(
        "children.Child",
        on_delete=models.PROTECT,
        related_name="guardians",
    )
    parent = models.ForeignKey(Parent, on_delete=models.PROTECT, related_name="child_links")
    relationship = models.CharField(max_length=20, choices=Relationship.choices)

    class Meta:
        ordering = ["relationship", "parent__last_name"]
        constraints = [
            models.UniqueConstraint(fields=["child", "parent"], name="unique_child_parent"),
            models.CheckConstraint(
                condition=Q(relationship__in=["FATHER", "MOTHER", "GUARDIAN", "OTHER"]),
                name="guardian_relationship_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.parent.full_name} — {self.get_relationship_display()} of {self.child}"
