# ActionColumnMixin Usage Examples

## Basic Usage

```python
from better_django_tables import ActionColumnMixin
import django_tables2 as tables
from .models import MyModel

class MyTable(ActionColumnMixin, tables.Table):
    # Define URL names for the default actions
    actions_url_names = {
        'view': 'myapp:model_detail',
        'edit': 'myapp:model_update',
        'delete': 'myapp:model_delete'
    }

    class Meta:
        model = MyModel
        fields = ("actions", "name", "email", "created_at")
```

## Customizing Actions

```python
class CustomTable(ActionColumnMixin, tables.Table):
    # Only enable view and edit actions, disable delete
    enable_view_action = True
    enable_edit_action = True
    enable_delete_action = False

    actions_url_names = {
        'view': 'myapp:model_detail',
        'edit': 'myapp:model_update'
    }

    # Customize icons and styling
    action_icons = {
        'view': 'bi bi-eye-fill',
        'edit': 'bi bi-pencil-fill'
    }

    action_classes = {
        'view': 'text-success',
        'edit': 'text-warning'
    }

    action_titles = {
        'view': 'View Details',
        'edit': 'Edit Record'
    }

    class Meta:
        model = MyModel
        fields = ("actions", "name", "status")
```

## Adding Custom Actions

```python
class ExtendedTable(ActionColumnMixin, tables.Table):
    actions_url_names = {
        'view': 'myapp:model_detail',
        'edit': 'myapp:model_update',
        'delete': 'myapp:model_delete'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add a custom export action
        self.add_custom_action(
            name='export',
            url_name='myapp:model_export',
            icon='bi bi-download',
            css_class='text-success',
            title='Export Data'
        )

        # Add a custom archive action with modal
        self.add_custom_action(
            name='archive',
            url_name='myapp:model_archive',
            icon='bi bi-archive',
            css_class='text-warning',
            title='Archive Record',
            requires_modal=True,
            modal_target='#archiveModal',
            modal_toggle='modal'
        )

    class Meta:
        model = MyModel
        fields = ("actions", "name", "status", "created_at")
```

## Disabling Actions Completely

```python
class ReadOnlyTable(ActionColumnMixin, tables.Table):
    # Disable the actions column entirely
    has_actions_column = False

    # Or disable at instantiation
    def __init__(self, *args, **kwargs):
        super().__init__(*args, has_actions_column=False, **kwargs)

    class Meta:
        model = MyModel
        fields = ("name", "email", "created_at")
```

## Template Requirements

The ActionColumnMixin uses the DeletableTableMixin's delete modal for delete actions. Make sure your template includes:

```html
<!-- Include the delete modal if using delete actions -->
{% include 'better_django_tables/partials/delete_modal.html' %}

<!-- Your table -->
{% render_table table %}
```

## Styling Notes

The actions column uses Bootstrap 5 classes by default:
- `d-flex gap-2 justify-content-center` for layout
- Icon classes like `bi bi-eye`, `bi bi-pencil-square`, `bi bi-trash`
- Color classes like `text-info`, `text-primary`, `text-danger`

You can customize these by overriding the `action_classes` dictionary or by providing custom CSS.
