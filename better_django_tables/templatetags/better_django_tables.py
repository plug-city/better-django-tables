from django import template
from django_tables2.rows import BoundRow

register = template.Library()

@register.inclusion_tag('better_django_tables/tables/better_table.html', takes_context=True)
def render_better_table(context, table):
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    return ctx


@register.inclusion_tag('better_django_tables/tables/better_table_inline.html', takes_context=True)
def render_better_inline_table(context, table):
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    return ctx


@register.inclusion_tag('better_django_tables/tables/better_table_row.html', takes_context=True)
def render_row(context, table, record):
    """
    Render a single table row for the given record using the specified table.

    Args:
        context: The current template context
        table: The django-tables2 Table instance
        record: The record/object to render as a table row

    Usage:
        {% load better_django_tables %}
        {% render_row table record %}
    """
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    ctx['record'] = record

    # Create a BoundRow for the specific record
    bound_row = BoundRow(table=table, record=record)
    ctx['bound_row'] = bound_row

    return ctx
