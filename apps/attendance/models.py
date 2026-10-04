from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import AuditModel


class Attendance(AuditModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    child = models.ForeignKey(
        "children.Child",
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attendance_recorded",
    )

    class Meta:
        ordering = ["-date", "child__last_name", "child__first_name"]
        verbose_name_plural = "attendance"
        constraints = [
            models.UniqueConstraint(fields=["child", "date"], name="unique_child_attendance_date"),
            models.CheckConstraint(
                condition=Q(status__in=["PRESENT", "ABSENT"]),
                name="attendance_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.child} — {self.date:%-d %B %Y} — {self.get_status_display()}"
