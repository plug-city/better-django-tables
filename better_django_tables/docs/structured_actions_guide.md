# ActionColumnMixin - Structured Actions Guide

The ActionColumnMixin now supports a new structured approach for defining actions that provides more flexibility and cleaner code.

## Structured Actions Approach (Recommended)

### Basic Usage

```python
from better_django_tables import ActionColumnMixin
import django_tables2 as tables
from .models import MyModel

class MyTable(ActionColumnMixin, tables.Table):
    # Define actions using the structured approach
    actions = [
        {
            'name': 'view',
            'url_name': 'myapp:model_detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View Details',
        },
        {
            'name': 'edit',
            'url_name': 'myapp:model_update',
            'icon': 'bi bi-pencil-square',
            'class': 'text-primary',
            'title': 'Edit Record',
        },
        {
            'name': 'delete',
            'url_name': 'myapp:model_delete',
            'icon': 'bi bi-trash',
            'class': 'text-danger',
            'title': 'Delete Record',
            'requires_modal': True,
            'modal_target': '#deleteModalBdt',
            'modal_toggle': 'modal',
        }
    ]

    class Meta:
        model = MyModel
        fields = ("actions", "name", "email", "created_at")
```

### Custom URL Arguments

The structured approach supports custom URL kwargs using lambda functions:

```python
class CustomTable(ActionColumnMixin, tables.Table):
    actions = [
        {
            'name': 'view',
            'url_name': 'myapp:detail_by_slug',
            'url_kwargs': lambda record: {'slug': record.slug},
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View',
        },
        {
            'name': 'edit',
            'url_name': 'myapp:update_by_category',
            'url_kwargs': lambda record: {
                'pk': record.pk,
                'category': record.category.slug
            },
            'icon': 'bi bi-pencil-square',
            'class': 'text-primary',
            'title': 'Edit',
        },
        {
            'name': 'export',
            'url_name': 'myapp:export_record',
            'url_kwargs': lambda record: {
                'format': 'pdf',
                'record_id': record.pk
            },
            'icon': 'bi bi-download',
            'class': 'text-success',
            'title': 'Export as PDF',
        }
    ]

    class Meta:
        model = MyModel
        fields = ("actions", "name", "category")
```

### Custom Actions with Modals

```python
class AdvancedTable(ActionColumnMixin, tables.Table):
    actions = [
        {
            'name': 'approve',
            'url_name': 'myapp:approve',
            'icon': 'bi bi-check-circle',
            'class': 'text-success',
            'title': 'Approve',
            'requires_modal': True,
            'modal_target': '#approveModal',
            'modal_toggle': 'modal',
        },
        {
            'name': 'archive',
            'url_name': 'myapp:archive',
            'url_kwargs': lambda record: {'pk': record.pk, 'redirect': 'list'},
            'icon': 'bi bi-archive',
            'class': 'text-warning',
            'title': 'Archive',
            'requires_modal': True,
            'modal_target': '#archiveModal',
            'modal_toggle': 'modal',
        }
    ]

    class Meta:
        model = MyModel
        fields = ("actions", "name", "status")
```

### Dynamic Actions

You can modify actions at runtime:

```python
class DynamicTable(ActionColumnMixin, tables.Table):
    actions = [
        {
            'name': 'view',
            'url_name': 'myapp:detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View',
        }
    ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Add edit action only for staff users
        if user and user.is_staff:
            self.enabled_actions.append({
                'name': 'edit',
                'url_name': 'myapp:update',
                'icon': 'bi bi-pencil-square',
                'class': 'text-primary',
                'title': 'Edit',
                'requires_modal': False,
            })

        # Add delete action only for superusers
        if user and user.is_superuser:
            self.enabled_actions.append({
                'name': 'delete',
                'url_name': 'myapp:delete',
                'icon': 'bi bi-trash',
                'class': 'text-danger',
                'title': 'Delete',
                'requires_modal': True,
                'modal_target': '#deleteModalBdt',
                'modal_toggle': 'modal',
            })

    class Meta:
        model = MyModel
        fields = ("actions", "name", "created_at")
```

## Action Configuration Reference

Each action in the `actions` list supports these properties:

- **`name`** (required): Unique identifier for the action
- **`url_name`** (required): Django URL name for the action
- **`url_kwargs`** (optional): Function that takes `record` and returns kwargs dict for URL
- **`icon`** (optional): CSS class for the icon (defaults to action_icons)
- **`class`** (optional): CSS class for styling (defaults to action_classes)
- **`title`** (optional): Tooltip text (defaults to action_titles)
- **`requires_modal`** (optional): Whether action needs modal confirmation (default: False)
- **`modal_target`** (optional): CSS selector for modal (default: '#deleteModalBdt')
- **`modal_toggle`** (optional): Modal toggle type (default: 'modal')

## Legacy Approach (Still Supported)

The original approach still works for backward compatibility:

```python
class LegacyTable(ActionColumnMixin, tables.Table):
    enable_view_action = True
    enable_edit_action = True
    enable_delete_action = False

    actions_url_names = {
        'view': 'myapp:model_detail',
        'edit': 'myapp:model_update'
    }

    action_icons = {
        'view': 'bi bi-eye-fill',
        'edit': 'bi bi-pencil-fill'
    }

    action_classes = {
        'view': 'text-success',
        'edit': 'text-warning'
    }

    class Meta:
        model = MyModel
        fields = ("actions", "name", "status")
```

## Comparison: Structured vs Legacy

### Structured Approach Benefits:
- ✅ More explicit and readable
- ✅ Supports custom URL kwargs easily
- ✅ Each action is self-contained
- ✅ Better for complex URL patterns
- ✅ Easier to maintain and modify

### Legacy Approach:
- ✅ Still supported for backward compatibility
- ❌ Limited to simple URL patterns with `record.pk`
- ❌ Configuration spread across multiple dictionaries
- ❌ Less flexible for custom URLs

## Template Requirements

Make sure your template includes any required modals:

```html
<!-- Include the delete modal if using delete actions -->
{% include 'better_django_tables/partials/delete_modal.html' %}

<!-- Custom modals for other actions -->
<div class="modal fade" id="approveModal">
    <!-- Modal content -->
</div>

<!-- Your table -->
{% render_table table %}
```

## URL Kwargs Examples

Here are some common patterns for the `url_kwargs` function:

```python
# Simple slug-based URL
'url_kwargs': lambda record: {'slug': record.slug}

# Multiple arguments
'url_kwargs': lambda record: {
    'pk': record.pk,
    'category': record.category.slug,
    'year': record.created_at.year
}

# With query parameters (use additional view logic)
'url_kwargs': lambda record: {
    'pk': record.pk,
    'next': '/return-url/'
}

# Complex logic
'url_kwargs': lambda record: {
    'identifier': record.custom_id if record.custom_id else record.pk,
    'format': 'json' if record.is_api_accessible else 'html'
}
```
