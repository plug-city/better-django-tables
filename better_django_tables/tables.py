from django.utils.html import format_html
from django.urls import reverse

import django_tables2 as tables

from better_django_tables.table_mixins import (
    DeletableTableMixin,
    BulkActionTableMixin,
    EditableTableMixin,
    CreateTableMixin,
    TableNameMixin,
    BootstrapTableMixin,
    ActionsColumnMixin,
    HtmxTableMixin,
    ShowPaginationTableMixin,
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
    ShowPaginationTableMixin,
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
