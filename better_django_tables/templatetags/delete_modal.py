from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag(takes_context=True)
def render_delete_modal(context, table):
    if hasattr(table, "is_deletable_table") or context.get(
        "include_delete_modal", False
    ):
        # Get the confirmation message from the table, or use a default
        delete_confirm_message = getattr(
            table,
            "delete_confirm_message",
            "Are you sure you want to delete this record?",
        )
        # Copy the context to ensure CSRF token is available
        ctx = context.flatten() if hasattr(context, "flatten") else dict(context)
        ctx["delete_confirm_message"] = delete_confirm_message
        return render_to_string("better_django_tables/partials/delete_modal.html", ctx)
    return ""
