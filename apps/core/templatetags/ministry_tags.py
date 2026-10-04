from django import template

from apps.core.dates import age_in_years, local_today
from apps.core.phones import format_phone

register = template.Library()


@register.filter
def phone(value) -> str:
    return format_phone(value)


@register.filter
def years_old(dob) -> str:
    if not dob:
        return ""
    return str(age_in_years(dob, local_today()))


@register.simple_tag(takes_context=True)
def query_with(context, **kwargs) -> str:
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
