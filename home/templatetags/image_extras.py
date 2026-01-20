import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter
def media_exists(path):
    """
    Check if a media file exists on disk.
    Usage: {{ path|media_exists }}
    """
    if not path:
        return False

    # Convert /media/... → absolute filesystem path
    relative_path = path.replace(settings.MEDIA_URL, "")
    full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    return os.path.exists(full_path)
