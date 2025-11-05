from django.utils.html import format_html
from django.urls import reverse

import django_tables2 as tables

from better_django_tables import models
from better_django_tables.table_mixins import (
    DeletableTableMixin,
    BulkActionTableMixin,
    EditableTableMixin,
    CreateTableMixin,
    TableNameMixin,
    BootstrapTableMixin,
    ActionsColumnMixin,
    HtmxTableMixin,
)


class TableMixin(
    DeletableTableMixin,
    BulkActionTableMixin,
    EditableTableMixin,
    CreateTableMixin,
    TableNameMixin,
    BootstrapTableMixin,
    ActionsColumnMixin,
    HtmxTableMixin,
):
    """
    Base table class with common
    functionality for deletion, bulk actions, and editing.
    To turn off any of these features, set the corresponding class attribute to False.
    - is_deletable_table: If True, adds a delete button column.
    - is_bulk_action_table: If True, adds a bulk action checkbox column.
    - is_editable_table: If True, adds an edit button column.
    - add_create_button: If True, adds a "Create" button above the table.

    - enable_view_action = True
    - view_action_url_name = 'myapp:model_detail'
    - enable_edit_action = True
    - edit_action_url_name = 'myapp:model_update'
    - enable_delete_action = True
    - delete_action_url_name = 'myapp:model_delete'

    Usage:
        class MyTable(Table):
            delete_url_name = 'myapp:model_delete'  # URL name for delete action
            bulk_action_url_name = 'myapp:bulk_action'  # URL name for bulk actions
            edit_url_name = 'myapp:model_edit'  # URL name for edit action
            table_name = "My Model"  # Name of the table for display
    class Meta:
        model = models.ModelName
    """

    is_editable_table = True
    is_bulk_action_table = True
    is_deletable_table = True
    add_create_button = True
    table_name = "Table"


class Table(TableMixin, tables.Table):
    """
    Enhanced django-tables2 base class with built-in functionality for common table operations.

    FEATURE TOGGLES:
        is_deletable_table = True
            Adds delete button column

        is_bulk_action_table = True
            Adds bulk action checkbox column

        is_editable_table = True
            Adds edit button column (legacy, use has_actions_column instead)

    CREATE BUTTON
        add_create_button = True
            Adds "Create New" button above table
        create_url = 'myapp:model_create'
            URL name for create new record

    BULK ACTIONS
        is_bulk_action_table = True
            Enables bulk action functionality

        bulk_delete_url_name = 'myapp:list_view'
            URL name for bulk operations

    ACTIONS COLUMN:
        has_actions_column = True
            Adds Actions column with view/edit/delete buttons

        enable_view_action = True
            Show view/detail button in actions column

        view_action_url_name = None
            URL name for detail view (e.g., 'myapp:model_detail')

        enable_edit_action = True
            Show edit button in actions column

        edit_action_url_name = None
            URL name for edit view (e.g., 'myapp:model_update')

        enable_delete_action = True
            Show delete button in actions column

        delete_action_url_name = None
            URL name for delete view (e.g., 'myapp:model_delete')

    URL CONFIGURATION:
        delete_url_name = None
            URL for delete action (legacy)

        bulk_action_url_name = None
            URL for bulk operations

        edit_url_name = None
            URL for edit action (legacy)

        create_url_name = None
            URL for create new record button

    DISPLAY:
        table_name = "Table"
            Display name for the table

    HTMX:
        htmx_table = False
            Enable HTMX auto-refresh functionality

    EXAMPLE:
        class ProductTable(Table):
            # Display
            table_name = "Products"

            # Features
            is_bulk_action_table = True
            add_create_button = True
            has_actions_column = True

            # Actions
            enable_view_action = True
            view_action_url_name = 'products:product_detail'
            enable_edit_action = True
            edit_action_url_name = 'products:product_update'
            enable_delete_action = True
            delete_action_url_name = 'products:product_delete'

            # URLs
            create_url_name = 'products:product_create'
            bulk_action_url_name = 'products:bulk_action'

            # HTMX
            htmx_table = True

            class Meta:
                model = Product
                fields = ['name', 'sku', 'price', 'stock']
                attrs = {"class": "table table-sm table-hover"}
    """

    is_editable_table = False
    is_bulk_action_table = False
    is_deletable_table = False
    add_create_button = False
    table_name = "Table"


# class ReportTable(DeletableTableMixin, BulkActionTableMixin, EditableTableMixin, tables.Table):
#     delete_url_name = 'better_django_tables:report_delete'

#     name = tables.Column(linkify=True, verbose_name="Report Name")
#     visibility = tables.Column(verbose_name="Visibility")
#     created_by = tables.Column(verbose_name="Created By")
#     view_name = tables.Column(verbose_name="View")
#     allowed_groups = tables.TemplateColumn(
#         template_code="{% for group in record.allowed_groups.all %}<span class='badge bg-secondary me-1'>{{ group.name }}</span>{% endfor %}",
#         orderable=False,
#         verbose_name="Groups",
#         empty_values=(),
#     )
#     filter_count = tables.Column(
#         verbose_name="Filters",
#         empty_values=(),
#         orderable=False
#     )
#     created_at = tables.DateTimeColumn(
#         verbose_name="Created",
#         format='M j, Y g:i A'
#     )
#     is_active = tables.Column(verbose_name="Active")
#     actions = tables.Column(
#         verbose_name='Actions',
#         empty_values=(),
#         orderable=False
#     )

#     class Meta:
#         model = models.Report
#         fields = ("id", "name", "description", "visibility", "created_by", "view_name",
#                  "allowed_groups", "filter_count", "created_at", "is_active", "actions")
#         attrs = {"class": "table table-sm table-hover"}

#     def render_visibility(self, value):
#         # Map visibility to Bootstrap badge classes
#         badge_map = {
#             "personal": "bg-info text-dark",
#             "role": "bg-warning text-dark",
#             "global": "bg-success",
#         }
#         badge_class = badge_map.get(value, "bg-light text-dark")
#         return format_html('<span class="badge {}">{}</span>', badge_class, value.title())

#     def render_view_name(self, value):
#         """Make view name more readable"""
#         if ':' in value:
#             app, view = value.split(':', 1)
#             return view.replace('_', ' ').title()
#         return value.replace('_', ' ').title()

#     def render_filter_count(self, record):
#         """Show number of active filters"""
#         if record.filter_params:
#             count = len([v for v in record.filter_params.values() if v])
#             if count > 0:
#                 return format_html('<span class="badge bg-primary">{}</span>', count)
#             else:
#                 return format_html('<span class="text-muted">0</span>')
#         return format_html('<span class="text-muted">0</span>')

#     def render_is_active(self, value):
#         if value:
#             return format_html('<span class="badge bg-success">Active</span>')
#         else:
#             return format_html('<span class="badge bg-secondary">Inactive</span>')

#     def render_actions(self, record: models.Report):
#         actions = []

#         # Apply/View Report
#         apply_url = record.get_absolute_url()
#         actions.append(f'<a href="{apply_url}" class="btn btn-primary btn-sm me-1" title="Apply Report">Apply</a>')

#         # Toggle Favorite (if user system exists)
#         if hasattr(record, 'is_favorite') and record.is_favorite:
#             actions.append(
#                 f'<form method="post" class="d-inline">'
#                 f'<input type="hidden" name="csrfmiddlewaretoken" value="">'  # Will be populated by template
#                 f'<input type="hidden" name="report_id" value="{record.id}">'
#                 f'<button type="submit" name="toggle_favorite" class="btn btn-warning btn-sm me-1" title="Remove from Favorites">'
#                 f'<i class="bi bi-star-fill"></i>'
#                 f'</button>'
#                 f'</form>'
#             )
#         else:
#             actions.append(
#                 f'<form method="post" class="d-inline">'
#                 f'<input type="hidden" name="csrfmiddlewaretoken" value="">'  # Will be populated by template
#                 f'<input type="hidden" name="report_id" value="{record.id}">'
#                 f'<button type="submit" name="toggle_favorite" class="btn btn-outline-warning btn-sm me-1" title="Add to Favorites">'
#                 f'<i class="bi bi-star"></i>'
#                 f'</button>'
#                 f'</form>'
#             )

#         # Edit/Detail link (only for own reports or admin)
#         detail_url = reverse('better_django_tables:report_detail', args=[record.pk])
#         actions.append(f'<a href="{detail_url}" class="btn btn-outline-secondary btn-sm me-1" title="View Details">Details</a>')

#         # Return formatted actions
#         if actions:
#             return format_html('<div class="btn-group btn-group-sm">{}</div>', ''.join(actions))
#         else:
#             return format_html('<span class="text-muted small">No actions</span>')
