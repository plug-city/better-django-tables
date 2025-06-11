from django import template

register = template.Library()

@register.inclusion_tag('better_django_tables/tables/better_table.html', takes_context=True)
def render_better_table(context, table):
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    return ctx


@register.inclusion_tag('better_django_tables/tables/better_table.html', takes_context=True)
def render_better_inline_table(context, table):
    ctx = context.flatten() if hasattr(context, 'flatten') else dict(context)
    ctx['table'] = table
    return ctx
