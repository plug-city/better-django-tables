# from django import template
# from django.template.loader import render_to_string
# from django.urls import reverse
# from django_tables2 import RequestConfig

# register = template.Library()

# @register.inclusion_tag('daapp/partials/table_with_modals.html', takes_context=True)
# def render_table_with_modals(context, table, delete_url_name=None, object_label=None):
#     """
#     Render a table with delete modals using an inclusion template.
#     """
#     # Auto-detect delete URL name and object label from table
#     if hasattr(table, 'delete_url_name'):
#         delete_url_name = delete_url_name or table.delete_url_name

#     if hasattr(table, '_meta') and hasattr(table._meta, 'model'):
#         object_label = object_label or table._meta.model._meta.verbose_name.title()
#         table_name = table._meta.model._meta.model_name
#     else:
#         table_name = table.__class__.__name__.lower().replace('table', '')

#     return {
#         'table': table,
#         'delete_url_name': delete_url_name,
#         'object_label': object_label,
#         'table_name': table_name,
#         'request': context['request']
#     }
