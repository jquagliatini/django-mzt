from datetime import datetime, timedelta

from django import template

register = template.Library()


@register.filter
def milliseconds(value: timedelta) -> int:
    return int(value / timedelta(milliseconds=1))


@register.filter
def duration(value: timedelta, format: str | None = None) -> str:
    d = datetime.min + value

    if format is None:
        if d.hour > 0:
            format = "%H:%M:%S"
        else:
            format = "%M:%S"

    return d.strftime(format)
