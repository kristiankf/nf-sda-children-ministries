import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from PIL import Image, UnidentifiedImageError

from apps.core.dates import age_in_years, local_today
from apps.core.models import AuditModel
from apps.core.phones import normalize_ghana_phone
from apps.schools.levels import ClassLevel

MAX_PHOTO_BYTES = 5 * 1024 * 1024
ALLOWED_PHOTO_FORMATS = {"JPEG", "PNG", "WEBP"}


def child_photo_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        extension = ""
    return f"children/photos/{uuid.uuid4().hex}{extension}"


def validate_child_photo(uploaded) -> None:
    if uploaded.size > MAX_PHOTO_BYTES:
        raise ValidationError("Photo must be 5 MB or smaller.")
    try:
        image = Image.open(uploaded)
        image_format = image.format
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.") from exc
    finally:
        uploaded.seek(0)
    if image_format not in ALLOWED_PHOTO_FORMATS:
        raise ValidationError("Upload a JPEG, PNG, or WebP image.")


class AgeGroup(models.Model):
    """A Sabbath class or youth group, chosen from a child's age."""

    class Kind(models.TextChoices):
        SABBATH = "SABBATH", "Sabbath class"
        YOUTH = "YOUTH", "Youth group"

    class Color(models.TextChoices):
        ROSE = "rose", "Rose"
        AMBER = "amber", "Amber"
        LIME = "lime", "Green"
        TEAL = "teal", "Teal"
        BLUE = "blue", "Blue"
        INDIGO = "indigo", "Indigo"
        PURPLE = "purple", "Purple"
        SKY = "sky", "Sky"
        ORANGE = "orange", "Orange"

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=40)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    sort_order = models.PositiveSmallIntegerField()
    min_years = models.PositiveSmallIntegerField()
    max_years = models.PositiveSmallIntegerField(null=True, blank=True)
    color = models.CharField(max_length=20, choices=Color.choices, default=Color.BLUE)

    class Meta:
        ordering = ["kind", "sort_order"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["SABBATH", "YOUTH"]),
                name="age_group_kind_valid",
            ),
            models.CheckConstraint(
                condition=Q(max_years__isnull=True) | Q(max_years__gte=models.F("min_years")),
                name="age_group_years_ordered",
            ),
            models.CheckConstraint(
                condition=Q(
                    color__in=[
                        "rose",
                        "amber",
                        "lime",
                        "teal",
                        "blue",
                        "indigo",
                        "purple",
                        "sky",
                        "orange",
                    ]
                ),
                name="age_group_color_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def age_label(self) -> str:
        if self.min_years == 0 and self.max_years == 0:
            return "Under 1 year"
        if self.max_years is None:
            return f"{self.min_years} and older"
        return f"Ages {self.min_years}–{self.max_years}"


class Child(AuditModel):
    class Gender(models.TextChoices):
        FEMALE = "FEMALE", "Girl"
        MALE = "MALE", "Boy"
        UNSPECIFIED = "UNSPECIFIED", "Unspecified"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        TRANSFERRED = "TRANSFERRED", "Transferred"

    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    preferred_name = models.CharField(max_length=80, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional. The child's own Ghana number, for example 024 412 3456.",
    )
    photo = models.ImageField(
        upload_to=child_photo_path,
        blank=True,
        validators=[validate_child_photo],
        help_text="Optional. JPEG, PNG, or WebP, up to 5 MB.",
    )
    school_name = models.CharField(
        max_length=160,
        blank=True,
        help_text="The school this child attends.",
    )
    class_level = models.CharField(
        max_length=20,
        choices=ClassLevel.choices,
        blank=True,
    )
    sabbath_class_override = models.ForeignKey(
        "children.AgeGroup",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="overridden_children",
        limit_choices_to={"kind": AgeGroup.Kind.SABBATH},
        help_text="Leave empty and the birthday decides the Sabbath class.",
    )
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name_plural = "children"
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["ACTIVE", "INACTIVE", "TRANSFERRED"]),
                name="child_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(gender__in=["FEMALE", "MALE", "UNSPECIFIED"]),
                name="child_gender_valid",
            ),
            models.CheckConstraint(
                condition=Q(class_level="") | Q(class_level__in=ClassLevel.values),
                name="child_class_level_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["preferred_name"]),
            models.Index(fields=["date_of_birth"]),
            models.Index(fields=["status"]),
            models.Index(fields=["class_level"]),
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("children:detail", args=[self.pk])

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(part for part in parts if part)

    @property
    def short_name(self) -> str:
        given = self.preferred_name or self.first_name
        return f"{given} {self.last_name}".strip()

    @property
    def initials(self) -> str:
        return f"{(self.first_name or ' ')[:1]}{(self.last_name or ' ')[:1]}".upper()

    @property
    def age(self) -> int:
        return age_in_years(self.date_of_birth, local_today())

    def clean(self) -> None:
        super().clean()
        self.first_name = (self.first_name or "").strip()
        self.middle_name = (self.middle_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.preferred_name = (self.preferred_name or "").strip()
        self.school_name = (self.school_name or "").strip()
        if not self.first_name:
            raise ValidationError({"first_name": "First name is required."})
        if not self.last_name:
            raise ValidationError({"last_name": "Last name is required."})
        if self.date_of_birth and self.date_of_birth > local_today():
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})
        if self.phone:
            try:
                self.phone = normalize_ghana_phone(self.phone)
            except ValidationError as error:
                raise ValidationError({"phone": error.messages}) from error
        override = self.sabbath_class_override
        if override is not None and override.kind != AgeGroup.Kind.SABBATH:
            raise ValidationError(
                {"sabbath_class_override": "Choose a Sabbath class, or leave this empty."}
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from apps.schools.calendar import sync_current_placement

        sync_current_placement(self)
