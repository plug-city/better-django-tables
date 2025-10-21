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
        <i class="bi bi-trash text-danger"
           style="cursor: pointer;"
           data-bs-toggle="modal"
           data-bs-target="#deleteModalBdt"
           data-delete-url="{% url "''' + cls.delete_url_name + '''" record.pk %}"
           data-item-name="{{ record }}"
           title="Delete"></i>
        '''


class TableIdMixin:
    """
    Mixin for django-tables2 Table classes to add a unique ID to each table instance.
    This is useful for targeting specific tables in JavaScript or CSS.
    Usage:
        class MyTable(TableIdMixin, tables.Table):
            table_id = "my_table_id"

            class Meta:
                model = MyModel
                fields = ("field1", "field2")
    """
    table_id: str = None  # Override in your table or set as class attribute

    def __init__(self, *args, table_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if table_id is not None:
            self.table_id = table_id
        if not self.table_id:
            self.table_id = f"{self.__class__.__name__.lower()}-table"


class BulkActionTableMixin(TableIdMixin):
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
    select_all_checkbox_id = None
    individual_checkbox_class = None
    checkbox_class_attrs = 'form-check-input'
    is_bulk_action_table = True  # Toggle this to enable/disable the bulk action column

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, 'is_bulk_action_table', True):
            return super().__new__(cls) # Skip adding the bulk action column if toggled off
        # Only add the column once per class, not per instance
        if 'select' not in cls.base_columns:
            cls.base_columns['select'] = tables.TemplateColumn(
                template_code='TEMP',  # Will be set in __init__
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
        if self.select_all_checkbox_id is None:
            self.select_all_checkbox_id = f"select-all-{self.table_id}"
        if self.individual_checkbox_class is None:
            self.individual_checkbox_class = f"select-item-{self.table_id} {self.checkbox_class_attrs}"
        # # Update the checkbox template for the actual column instance
        # if 'select' in self.columns:
        #     select_col = self.columns['select']
        #     select_col.template_code = self.get_checkbox_template().format(
        #         checkbox_class=self.individual_checkbox_class
        #     )
        if not hasattr(self, 'attrs'):
            self.attrs = {}
        existing_classes = self.attrs.get('class', '')
        self.attrs['class'] = f"{existing_classes} bulk-actions-table".strip()
        if not hasattr(self, 'attrs'):
            self.attrs = {}
        self.attrs['id'] = self.table_id
        self.attrs.setdefault('id', self.table_id)

    # def get_checkbox_template(self):
    #     """Return the template code for individual row checkboxes."""
    #     return f'''
    #     <input type="checkbox"
    #            class="{self.individual_checkbox_class}"
    #            name="selected_items"
    #            value="{{{{ record.pk }}}}"
    #            data-item-name="{{{{ record }}}}">
    #     '''

    def render_select(self, record):
        """Return the template code for individual row checkboxes."""
        return format_html('''<input type="checkbox"
               class="{}"
               name="selected_items"
               value="{}"
               data-item-name="{}">''',
               self.individual_checkbox_class,
               record.pk,
               record)

    @classmethod
    def get_select_all_checkbox(cls):
        """Return the HTML for the select all checkbox in the header."""
        return format_html(
            '<input type="checkbox" id="{}" class="select-all-checkbox {}" title="Select All">',
            cls.select_all_checkbox_id,
            cls.checkbox_class_attrs,
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


class ActionsColumnMixin:
    """
    Mixin for django-tables2 Table classes to add an actions column with multiple action buttons.

    Usage:
        class MyTable(ActionColumnMixin, tables.Table):
            has_actions_column = True

            enable_view_action = True
            view_action_url_name = 'myapp:model_detail'
            enable_edit_action = True
            edit_action_url_name = 'myapp:model_update'
            enable_delete_action = True
            delete_action_url_name = 'myapp:model_delete'
            actions = [
                {
                    'name': 'view',
                    'url_name': 'myapp:model_detail',
                    'icon': 'bi bi-eye',
                    'class': 'text-info',
                    'title': 'View',
                },
                {
                    'name': 'edit',
                    'url_name': 'myapp:model_update',
                    'url_kwargs': lambda record: {'slug': record.slug},
                    'icon': 'bi bi-pencil-square',
                    'class': 'text-primary',
                    'title': 'Edit',
                },
            ]

            class Meta:
                model = MyModel
                fields = ("actions", "field1", "field2")
    """
    has_actions_column = False  # Toggle this to enable/disable the actions column

    # New structured approach - define actions as a list of dicts
    actions = []

    # Standard Action Toggles
    enable_view_action = False
    enable_edit_action = False
    enable_delete_action = False

    view_action_url_name = None
    edit_action_url_name = None
    delete_action_url_name = None

    # Standard actions
    view_action = {
        'name': 'view',
        'url_name': None,  # Must be set in the table class
        'icon': 'bi bi-eye',
        'class': 'text-primary',
        'title': 'View',
        'requires_modal': False,
    }
    edit_action = {
        'name': 'edit',
        'url_name': None,  # Must be set in the table class
        'icon': 'bi bi-pencil-square',
        'class': 'text-primary',
        'title': 'Edit',
        'requires_modal': False,
    }
    delete_action = {
        'name': 'delete',
        'url_name': None,  # Must be set in the table class
        'icon': 'bi bi-trash',
        'class': 'text-danger',
        'title': 'Delete',
        'requires_modal': True,
        'modal_target': '#deleteModalBdt',
        'modal_toggle': 'modal',
    }

    actions_column_verbose_name = ''
    actions_template_name = 'better_django_tables/partials/actions_column.html'

    def __new__(cls, *args, **kwargs):
        if not getattr(cls, 'has_actions_column'):
            return super().__new__(cls)

        if 'bdtactions' not in cls.base_columns:
            cls.base_columns['bdtactions'] = tables.TemplateColumn(
                template_name=cls.actions_template_name,
                orderable=False,
                verbose_name=cls.actions_column_verbose_name,
                empty_values=(),
                attrs={'td': {'class': 'text-center actions-column'}},
            )
            cls.base_columns = collections.OrderedDict(
                [('bdtactions', cls.base_columns['bdtactions'])] +
                [(k, v) for k, v in cls.base_columns.items() if k != 'bdtactions']
            )
        return super().__new__(cls)

    def __init__(self, *args, has_actions_column=None, **kwargs):
        super().__init__(*args, **kwargs)
        if has_actions_column is not None:
            self.has_actions_column = has_actions_column

        if not getattr(self, 'has_actions_column', True):
            return

        # Build the list of enabled actions
        self.enabled_actions = self._get_enabled_actions()

        # If sequence is set, ensure "bdtactions" is first
        if hasattr(self, 'sequence'):
            seq = list(self.sequence)
            if 'bdtactions' in self.base_columns and (not seq or seq[0] != 'bdtactions'):
                if 'bdtactions' in seq:
                    seq.remove('bdtactions')
                self.sequence = ['bdtactions'] + seq

    def _get_enabled_actions(self):
        """Return a list of enabled actions with their configuration."""
        actions = []

        # Standard Actions Configuration
        actions = self._add_standard_actions(actions)


        if hasattr(self, 'actions') and self.actions:
            # Use the structured actions list
            for action_config in self.actions:
                action = self._normalize_action_config(action_config)
                if action:
                    actions.append(action)

        return actions

    def _add_standard_actions(self, actions: list[dict]) -> list[dict]:
        """Add standard actions to the actions list."""
        if self.enable_view_action:
            # Create a copy to avoid modifying the class-level dictionary
            view_action = self.view_action.copy()
            if view_action['url_name'] is None:
                try:
                    view_action['url_name'] = self.view_action_url_name
                except KeyError as exc:
                    raise ImproperlyConfigured(
                        f"{self.__class__.__name__} requires 'view_action' to have a \
                              'url_name' or 'view_action_url_name' to be defined."
                    ) from exc
            actions.append(self._normalize_action_config(view_action))
        if self.enable_edit_action:
            # Create a copy to avoid modifying the class-level dictionary
            edit_action = self.edit_action.copy()
            if edit_action['url_name'] is None:
                try:
                    edit_action['url_name'] = self.edit_action_url_name
                except KeyError as exc:
                    raise ImproperlyConfigured(
                        f"{self.__class__.__name__} requires 'edit_action' to have a \
                              'url_name' or 'edit_action_url_name' to be defined."
                    ) from exc
            actions.append(self._normalize_action_config(edit_action))
        if self.enable_delete_action:
            # Create a copy to avoid modifying the class-level dictionary
            delete_action = self.delete_action.copy()
            if delete_action['url_name'] is None:
                try:
                    delete_action['url_name'] = self.delete_action_url_name
                except KeyError as exc:
                    raise ImproperlyConfigured(
                        f"{self.__class__.__name__} requires 'delete_action' to have a \
                              'url_name' or 'delete_action_url_name' to be defined."
                    ) from exc
            actions.append(self._normalize_action_config(delete_action))
        return actions

    def _normalize_action_config(self, config):
        """Normalize an action configuration dictionary."""
        try:
            # Build normalized action config
            action = {
                'name': config['name'],
                'url_name': config.get('url_name'),
                'url_kwargs': config.get('url_kwargs'),
                'icon': config['icon'],
                'class': config['class'],
                'title': config['title'],
                'requires_modal': config.get('requires_modal', False),
            }

            # Handle modal configuration
            if action['requires_modal']:
                action['modal_target'] = config['modal_target']
                action['modal_toggle'] = config['modal_toggle']
        except Exception as exc:
            raise ImproperlyConfigured(f'{self.__class__.__name__} is improperly configured') from exc
        return action

    # def _get_legacy_actions(self):
    #     """Get actions using the legacy approach for backward compatibility."""
    #     actions = []

    #     if getattr(self, 'enable_view_action', True) and 'view' in self.actions_url_names:
    #         actions.append({
    #             'name': 'view',
    #             'url_name': self.actions_url_names['view'],
    #             'url_kwargs': None,
    #             'icon': self.action_icons.get('view', 'bi bi-eye'),
    #             'class': self.action_classes.get('view', 'text-info'),
    #             'title': self.action_titles.get('view', 'View'),
    #             'requires_modal': False,
    #         })

    #     if getattr(self, 'enable_edit_action', True) and 'edit' in self.actions_url_names:
    #         actions.append({
    #             'name': 'edit',
    #             'url_name': self.actions_url_names['edit'],
    #             'url_kwargs': None,
    #             'icon': self.action_icons.get('edit', 'bi bi-pencil-square'),
    #             'class': self.action_classes.get('edit', 'text-primary'),
    #             'title': self.action_titles.get('edit', 'Edit'),
    #             'requires_modal': False,
    #         })

    #     if getattr(self, 'enable_delete_action', True) and 'delete' in self.actions_url_names:
    #         actions.append({
    #             'name': 'delete',
    #             'url_name': self.actions_url_names['delete'],
    #             'url_kwargs': None,
    #             'icon': self.action_icons.get('delete', 'bi bi-trash'),
    #             'class': self.action_classes.get('delete', 'text-danger'),
    #             'title': self.action_titles.get('delete', 'Delete'),
    #             'requires_modal': True,
    #             'modal_target': '#deleteModalBdt',
    #             'modal_toggle': 'modal',
    #         })

    #     return actions

    # def add_custom_action(self, name, url_name, icon='bi bi-gear', css_class='text-secondary',
    #                      title=None, requires_modal=False, modal_target=None, modal_toggle=None):
    #     """
    #     Add a custom action to the actions column.

    #     Args:
    #         name: Unique name for the action
    #         url_name: Django URL name for the action
    #         icon: CSS class for the icon (default: 'bi bi-gear')
    #         css_class: CSS class for styling (default: 'text-secondary')
    #         title: Tooltip text (default: capitalized name)
    #         requires_modal: Whether this action requires a modal (default: False)
    #         modal_target: Modal target selector (e.g., '#myModal')
    #         modal_toggle: Modal toggle type (e.g., 'modal')
    #     """
    #     if not hasattr(self, 'enabled_actions'):
    #         self.enabled_actions = []

    #     action = {
    #         'name': name,
    #         'url_name': url_name,
    #         'icon': icon,
    #         'class': css_class,
    #         'title': title or name.replace('_', ' ').title(),
    #         'requires_modal': requires_modal,
    #     }

    #     if requires_modal:
    #         action['modal_target'] = modal_target
    #         action['modal_toggle'] = modal_toggle

    #     self.enabled_actions.append(action)


class BootstrapTableMixin:
    """
    Mixin for django-tables2 Table classes to add Bootstrap 5 classes to the table.
    Usage:
        class MyTable(Bootstrap5TableMixin, tables.Table):
            ...
    """
    bootstrap_table_class = "table table-sm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set Bootstrap classes on the table
        if not hasattr(self, 'attrs'):
            self.attrs = {}
        self.attrs.setdefault("class", self.bootstrap_table_class)


class HtmxTableMixin:
    """
    Mixin to add HTMX support to tables.
    Provides methods to handle HTMX requests and render HTMX-specific templates.

    Methods to override in subclasses:
        get_htmx_template_name(self): Return the HTMX template name to use.
    """

    htmx_template_name = "better_django_tables/tables/bootstrap5-htmx-table.html"

    def __init__(self, *args, htmx_template_name=None, htmx_show_per_page:bool=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        if htmx_template_name is not None:
            self.htmx_template_name = htmx_template_name
        if htmx_show_per_page is not None:
            self.htmx_show_per_page = htmx_show_per_page

    def get_htmx_template_name(self):
        return self.htmx_template_name

