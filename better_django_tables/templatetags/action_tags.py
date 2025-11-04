from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def action_url(action, record):
    """Generate URL for an action based on its configuration."""
    url_name = action.get("url_name")
    if not url_name:
        return "#"

    url_kwargs_func = action.get("url_kwargs")

    if url_kwargs_func and callable(url_kwargs_func):
        # Use custom kwargs function
        try:
            kwargs = url_kwargs_func(record)
            if isinstance(kwargs, dict):
                return reverse(url_name, kwargs=kwargs)
            else:
                # If not a dict, fallback to pk
                return reverse(url_name, args=[record.pk])
        except (TypeError, ValueError, AttributeError):
            # Fallback to pk if custom function fails
            return reverse(url_name, args=[record.pk])
    else:
        # Default to using record.pk
        return reverse(url_name, args=[record.pk])
