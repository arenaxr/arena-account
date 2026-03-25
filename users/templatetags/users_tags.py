from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def short_timesince(value):
    if not value:
        return ""
    try:
        now = timezone.now()
        diff = now - value
    except TypeError:
        return ""

    if diff.days >= 365:
        return f"{diff.days // 365}y"
    if diff.days >= 30:
        return f"{diff.days // 30}mo"
    if diff.days >= 7:
        return f"{diff.days // 7}w"
    if diff.days >= 1:
        return f"{diff.days}d"
    if diff.seconds >= 3600:
        return f"{diff.seconds // 3600}h"
    if diff.seconds >= 60:
        return f"{diff.seconds // 60}m"
    return f"{diff.seconds}s"
