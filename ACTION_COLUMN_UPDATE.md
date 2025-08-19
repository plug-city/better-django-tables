# ActionColumnMixin - Major Update: Structured Actions

The `ActionColumnMixin` has been significantly enhanced with a new **structured actions approach** that provides much more flexibility and cleaner configuration.

## ✨ New Features

### 1. Structured Actions Approach (Recommended)

Define actions as a list of dictionaries with full configuration:

```python
class MyTable(ActionColumnMixin, tables.Table):
    actions = [
        {
            'name': 'view',
            'url_name': 'app:detail',
            'url_kwargs': lambda record: {'slug': record.slug},
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View Details',
        },
        {
            'name': 'delete',
            'url_name': 'app:delete',
            'icon': 'bi bi-trash',
            'class': 'text-danger',
            'title': 'Delete',
            'requires_modal': True,
            'modal_target': '#deleteModal',
            'modal_toggle': 'modal',
        }
    ]
```

### 2. Custom URL Generation

Support for complex URL patterns with custom kwargs:

```python
# Simple slug-based URLs
'url_kwargs': lambda record: {'slug': record.slug}

# Complex multi-parameter URLs
'url_kwargs': lambda record: {
    'pk': record.pk,
    'category': record.category.slug,
    'format': 'pdf'
}
```

### 3. Dynamic Action Management

Add actions conditionally based on permissions or context:

```python
def __init__(self, *args, user=None, **kwargs):
    super().__init__(*args, **kwargs)

    if user and user.is_staff:
        self.enabled_actions.append({
            'name': 'admin_edit',
            'url_name': 'admin:update',
            'icon': 'bi bi-gear',
            'class': 'text-warning',
            'title': 'Admin Edit',
        })
```

### 4. Custom Template Tags

New `action_url` template tag handles complex URL generation:

```django
{% load action_tags %}
<a href="{% action_url action record %}">{{ action.title }}</a>
```

## 🔄 Backward Compatibility

The legacy approach is still fully supported:

```python
class LegacyTable(ActionColumnMixin, tables.Table):
    actions_url_names = {
        'view': 'app:detail',
        'edit': 'app:update'
    }

    action_icons = {
        'view': 'bi bi-eye',
        'edit': 'bi bi-pencil'
    }
```

## 📁 Files Updated

- `table_mixins.py` - Enhanced ActionColumnMixin with structured actions
- `templates/partials/actions_column.html` - Updated template using new template tags
- `templatetags/action_tags.py` - New custom template tag for URL generation
- `examples/action_column_examples.py` - Comprehensive examples of all approaches
- `docs/structured_actions_guide.md` - Detailed guide and migration information

## 🚀 Migration Guide

### Simple Migration (Recommended)
1. Replace your `actions_url_names` dict with a structured `actions` list
2. Move icon/class/title configurations into the action dictionaries
3. Test URL generation with your existing URL patterns

### Gradual Migration
The old approach still works, so you can:
1. Keep existing tables as-is
2. Use structured approach for new tables
3. Migrate tables one by one when convenient

## 💡 Key Benefits

- **More Flexible**: Custom URL kwargs, conditional actions, complex configurations
- **Cleaner Code**: Single `actions` list instead of multiple configuration dicts
- **Better Organization**: All action configuration in one place
- **Future-Proof**: Extensible structure for new features
- **Type Safety**: Better IDE support and error checking

## 📖 Examples

See `examples/action_column_examples.py` for comprehensive examples including:
- Basic structured actions
- Custom URL patterns with kwargs
- Modal integration
- Dynamic/conditional actions
- Mixed approaches
- Legacy compatibility

The structured approach provides much more power and flexibility while maintaining the simplicity that made ActionColumnMixin popular!
