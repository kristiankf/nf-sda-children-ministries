"""Ghana phone numbers stored in E.164 and shown in local form."""

import re

from django.core.exceptions import ValidationError

_SEPARATORS = re.compile(r"[\s\-().]")


def normalize_ghana_phone(value: str) -> str:
    """Return +233 followed by the 9-digit national number."""
    if value is None or not str(value).strip():
        raise ValidationError("Enter a phone number.")

    compact = _SEPARATORS.sub("", str(value).strip())
    digits = re.sub(r"\D", "", compact)
    if digits.startswith("233"):
        national = digits[3:]
    elif digits.startswith("0"):
        national = digits[1:]
    else:
        national = digits

    if not re.fullmatch(r"\d{9}", national):
        raise ValidationError("Enter a valid Ghana phone number, for example 024 412 3456.")
    return f"+233{national}"


def format_phone(value: str | None) -> str:
    """Show +233244123456 as 024 412 3456."""
    if not value:
        return ""
    if value.startswith("+233") and len(value) == 13 and value[1:].isdigit():
        national = "0" + value[4:]
        return f"{national[:3]} {national[3:6]} {national[6:]}"
    return value


def phone_search_digits(value: str) -> str:
    """Digits that can match a stored +233 number."""
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        return ""
    if digits.startswith("233"):
        return digits
    if digits.startswith("0"):
        return "233" + digits[1:]
    if len(digits) == 9:
        return "233" + digits
    return digits
