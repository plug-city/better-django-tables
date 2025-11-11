from django import template
from django.http import QueryDict
from django_tables2.rows import BoundRow

register = template.Library()

# @register.inclusion_tag('better_django_tables/tables/better_table.html', takes_context=True)
@register.inclusion_tag('better_django_tables/table.html', takes_context=True)
def render_better_table(context, table):
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    return ctx


# @register.inclusion_tag('better_django_tables/tables/better_table_inline.html', takes_context=True)
# def render_better_inline_table(context, table):
#     ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
#     ctx['table'] = table
#     return ctx


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


@register.simple_tag
def build_querystring(**kwargs):
    """
    Build a querystring from scratch with the provided parameters.

    Unlike django-tables2's querystring tag, this does NOT inherit any existing
    URL parameters. It builds a completely fresh querystring from only the
    parameters you provide.

    This is useful when loading multiple tables via HTMX where you don't want
    parameters from one table to leak into another.

    Usage:
        {% load better_django_tables %}

        {# Build a fresh querystring with only these parameters #}
        {% build_querystring walmart_product=product.id page=1 %}

        {# Output: ?walmart_product=123&page=1 #}

        {# Remove a parameter by setting it to None or empty string #}
        {% build_querystring walmart_product=product.id page='' %}

        {# Output: ?walmart_product=123 #}

        {# Can be used with 'as' to store in a variable #}
        {% build_querystring walmart_product=product.id as product_params %}
        <div hx-get="/some/url/{{ product_params }}">...</div>

    Args:
        **kwargs: Key-value pairs to include in the querystring

    Returns:
        str: A querystring starting with '?' (or empty string if no params)
    """
    # Create a new QueryDict
    query = QueryDict(mutable=True)

    # Add all provided parameters
    for key, value in kwargs.items():
        # Skip None values or empty strings (allows parameter removal)
        if value is not None and value != '':
            query[key] = value

    # Return the querystring with leading '?' if there are params
    querystring = query.urlencode()
    return f'?{querystring}' if querystring else ''
