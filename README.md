============
better_django_tables
============

better_django_tables is a Django app to extend django tables2 with useful mixins and functionality.

Features
--------

- **ActionColumnMixin**: Add customizable action buttons (view, edit, delete) to your tables
- **DeletableTableMixin**: Add delete buttons with Bootstrap modal confirmation
- **EditableTableMixin**: Add edit buttons to your tables
- **BulkActionTableMixin**: Add bulk selection with checkboxes
- **TableIdMixin**: Add unique IDs to table instances
- **BootstrapTableMixin**: Apply Bootstrap 5 styling to tables

Quick start
-----------

1. Add "better_django_tables" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "better_django_tables",
    ]

2. Use the mixins in your table classes::

    from better_django_tables import ActionColumnMixin
    import django_tables2 as tables

    class MyTable(ActionColumnMixin, tables.Table):
        actions_url_names = {
            'view': 'myapp:detail',
            'edit': 'myapp:update',
            'delete': 'myapp:delete'
        }

        class Meta:
            model = MyModel
            fields = ('actions', 'name', 'email')

ActionColumnMixin Usage
----------------------

The ActionColumnMixin provides a flexible way to add action buttons to your tables:

**Basic Usage:**
```python
class MyTable(ActionColumnMixin, tables.Table):
    actions_url_names = {
        'view': 'myapp:detail',
        'edit': 'myapp:update',
        'delete': 'myapp:delete'
    }
```

**Customize Actions:**
```python
class MyTable(ActionColumnMixin, tables.Table):
    # Disable specific actions
    enable_delete_action = False

    # Custom styling
    action_icons = {
        'view': 'bi bi-eye-fill',
        'edit': 'bi bi-gear-fill'
    }

    action_classes = {
        'view': 'text-success',
        'edit': 'text-warning'
    }
```

**Add Custom Actions:**
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.add_custom_action(
        name='export',
        url_name='myapp:export',
        icon='bi bi-download',
        css_class='text-info',
        title='Export Data'
    )
```

See the `docs/` directory for detailed documentation and examples.

