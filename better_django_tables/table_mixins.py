import collections

from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html
import django_tables2 as tables


class DeletableTableMixin:
    """
    Mixin for django-tables2 Table classes to add a delete button/column with Bootstrap 5 modal.
    Usage:
        class MyTable(DeletableTableMixin, tables.Table):
            delete_url_name = 'myapp:model_delete'
            delete_confirm_message = "Are you sure you want to delete this item?"  # Optional

            class Meta:
                model = MyModel
                fields = ("field1", "field2", "delete")
    """
    delete_url_name = None  # Override in your table or set as class attribute
    delete_confirm_message = "Are you sure you want to delete this record?"
    is_deletable_table = True

    def __new__(cls, *args, **kwargs):
        # Only add the column once per class, not per instance
        if not getattr(cls, 'is_deletable_table', True):
            return super().__new__(cls)
        if 'delete' not in cls.base_columns:
            cls.base_columns['delete'] = tables.TemplateColumn(
                template_code=cls.get_delete_template(),
                orderable=False,
                verbose_name='',
                attrs={'td': {'class': 'text-center'}},
                empty_values=(),
            )
        return super().__new__(cls)

    def __init__(self, *args, is_deletable_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        if is_deletable_table is not None:
            self.is_deletable_table = is_deletable_table

    @classmethod
    def get_delete_template(cls):
        """Return the template code for the delete button."""
        if cls.delete_url_name is None:
            raise ImproperlyConfigured(f"{cls.__class__.__name__} must define 'delete_url_name' attribute")

        return '''
        <button type="button"
                class="btn btn-danger btn-sm"
                data-bs-toggle="modal"
                data-bs-target="#deleteModal"
                data-delete-url="{% url "''' + cls.delete_url_name + '''" record.pk %}"
                data-item-name="{{ record }}"
                title="Delete">
            <i class="bi bi-trash"></i>
        </button>
        '''



class BulkActionTableMixin:
    """
    Mixin for django-tables2 Table classes to add bulk selection with checkboxes and actions.
    Usage:
        class MyTable(BulkActionTableMixin, tables.Table):
            bulk_delete_url_name = 'myapp:bulk_delete'  # Optional, for bulk delete

            class Meta:
                model = MyModel
                fields = ("select", "field1", "field2")
    """
    bulk_delete_url_name = None
    select_all_checkbox_id = "select-all"
    individual_checkbox_class = "select-item"
    is_bulk_action_table = True  # Toggle this to enable/disable the bulk action column

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, 'is_bulk_action_table', True):
            return super().__new__(cls) # Skip adding the bulk action column if toggled off
        # Only add the column once per class, not per instance
        if 'select' not in cls.base_columns:
            cls.base_columns['select'] = tables.TemplateColumn(
                template_code=cls.get_checkbox_template(),
                orderable=False,
                verbose_name=cls.get_select_all_checkbox(),
                attrs={'td': {'class': 'text-center'}, 'th': {'class': 'text-center'}},
                empty_values=(),
            )
            # Move 'select' to the first position
            cls.base_columns = collections.OrderedDict(
                [('select', cls.base_columns['select'])] +
                [(k, v) for k, v in cls.base_columns.items() if k != 'select']
            )
        return super().__new__(cls)

    def __init__(self, *args, is_bulk_action_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        if is_bulk_action_table is not None:
            self.is_bulk_action_table = is_bulk_action_table
        if not getattr(self, 'is_bulk_action_table', True):
            return
        # If sequence is set, ensure "select" is first
        if hasattr(self, 'sequence'):
            seq = list(self.sequence)
            if 'select' in self.base_columns and (not seq or seq[0] != 'select'):
                if 'select' in seq:
                    seq.remove('select')
                self.sequence = ['select'] + seq

    @classmethod
    def get_checkbox_template(cls):
        """Return the template code for individual row checkboxes."""
        return f'''
        <input type="checkbox"
               class="{cls.individual_checkbox_class}"
               name="selected_items"
               value="{{{{ record.pk }}}}"
               data-item-name="{{{{ record }}}}">
        '''

    @classmethod
    def get_select_all_checkbox(cls):
        """Return the HTML for the select all checkbox in the header."""
        return format_html(
            '<input type="checkbox" id="{}" class="select-all-checkbox" title="Select All">',
            cls.select_all_checkbox_id
        )


class EditableTableMixin:
    """
    Mixin for django-tables2 Table classes to add an edit button/column.
    Usage:
        class MyTable(EditableTableMixin, tables.Table):
            edit_url_name = 'myapp:model_update'
            edit_icon_class = 'bi bi-pencil-square'  # Optional, defaults to pencil-square
            edit_button_class = 'text-primary'  # Optional, defaults to text-primary

            class Meta:
                model = MyModel
                fields = ("edit", "field1", "field2")
    """
    is_editable_table = True  # Toggle this to enable/disable the edit column
    edit_url_name = None
    edit_icon_class = 'bi bi-pencil-square'
    edit_button_class = 'text-primary'
    edit_column_verbose_name = ''
    edit_column_title = 'Edit'
    edit_template_name = 'better_django_tables/partials/edit_button.html'  # Add this attribute

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, 'is_editable_table', True):
            return super().__new__(cls) # Skip adding the edit column if is has been toggled off
        if 'edit' not in cls.base_columns:
            cls.base_columns['edit'] = tables.TemplateColumn(
                template_name=cls.edit_template_name,  # Use template_name instead of template_code
                orderable=False,
                verbose_name=cls.edit_column_verbose_name,
                empty_values=(),
                attrs={'td': {'class': 'text-center'}},
            )
            cls.base_columns = collections.OrderedDict(
                [('edit', cls.base_columns['edit'])] +
                [(k, v) for k, v in cls.base_columns.items() if k != 'edit']
            )
        return super().__new__(cls)

    def __init__(self, *args, is_editable_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        if is_editable_table is not None:
            self.is_editable_table = is_editable_table
        if not getattr(self, 'is_editable_table', True):
            return  # Skip initialization if not editable
        # Check if the model has get_absolute_url
        model = getattr(self._meta, 'model', None)
        if model and not hasattr(model, 'get_absolute_url'):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires the model '{model.__name__}' to define a 'get_absolute_url' method."
            )
        # If sequence is set, ensure "edit" is first
        if hasattr(self, 'sequence'):
            seq = list(self.sequence)
            if 'edit' in self.base_columns and (not seq or seq[0] != 'edit'):
                if 'edit' in seq:
                    seq.remove('edit')
                self.sequence = ['edit'] + seq


    # @classmethod
    # def get_edit_template(cls):
    #     """Return the template code for the edit button."""
    #     return '''
    #     {% load django_tables2 %}
    #     <a href="{{ record.get_absolute_url }}?next={{ request.get_full_path|urlencode }}"
    #        class="''' + cls.edit_button_class + '''"
    #        title="''' + cls.edit_column_title + '''">
    #         <i class="''' + cls.edit_icon_class + '''"></i>
    #     </a>
    #     '''


class CreateTableMixin:
    """
    mixin for tables that adds a new record button.
    """
    add_create_button = True  # Toggle this to enable/disable the create button
    create_url: str = None
    create_url_label: str = 'New Record'

    def __init__(self, *args, add_create_button=None, **kwargs):
        super().__init__(*args, **kwargs)
        print(f'{add_create_button=}')
        if add_create_button is not None:
            self.add_create_button = add_create_button
        if not getattr(self, 'add_create_button', True):
            return
        if not self.create_url:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'create_url' to be set."
            )


class TableNameMixin:
    """
    Mixin for django-tables2 Table classes to add a `name` attribute to each table.
    Usage:
        class MyTable(TableNameMixin, tables.Table):
            table_name = "My Custom Table Name"
    """
    table_name: str = None  # Override in your table or set as class attribute

    def __init__(self, *args, table_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        if table_name is not None:
            self.table_name = table_name
        # If not set on the class, default to the class name
        if not hasattr(self, 'table_name') or self.table_name is None:
            self.table_name = self.__class__.__name__


