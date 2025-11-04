# Save and Next Navigation

The Save and Next feature enables users to efficiently work through a list of records by saving the current record and automatically navigating to the next one from the filtered/sorted table they came from.

## Features

- 🔄 **Navigate through filtered lists**: Preserves the exact filter/sort order from the table view
- 💾 **Smart session storage**: Limits PKs stored to avoid memory issues with large datasets
- ⚙️ **Configurable limits**: Global and per-view settings for maximum PK storage
- 🎯 **Context-aware**: Centers PK window around current record for smooth navigation
- ⏱️ **Auto-expiry**: Navigation data expires after configurable timeout (default: 1 hour)
- 🔗 **URL parameter support**: Can pass navigation context via URL parameters

## Quick Start

### 1. Configure Settings (Optional)

Add to your Django settings.py to override defaults:

```python
# Maximum number of PKs to store in session (default: 500)
BETTER_DJANGO_TABLES_NAVIGATION_MAX_PK_COUNT = 500

# Session timeout in seconds (default: 3600 = 1 hour)
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_TIMEOUT = 3600

# Number of PKs before/after current when limiting (default: 50)
BETTER_DJANGO_TABLES_NAVIGATION_CONTEXT_WINDOW = 50

# Session key prefix (default: 'bdt_nav_')
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_KEY_PREFIX = 'bdt_nav_'
```

### 2. Enable in List View (TableView)

Your list view automatically stores navigation data if it inherits from `TableView`:

```python
from better_django_tables.views import TableView

class OrderListView(TableView):
    model = Order
    table_class = OrderTable
    filterset_class = OrderFilter

    # Optional: Override default max PK count for this view
    navigation_max_pk_count = 200  # Good for large tables
```

The `TableView` already includes `NavigationStorageMixin`, so it will automatically:
- Store filtered/sorted PKs in the session
- Limit storage to configured maximum
- Handle expiration automatically

### 3. Enable in Update View

Add `SaveAndNextMixin` to your update view:

```python
from better_django_tables.view_mixins import SaveAndNextMixin
from django.views.generic import UpdateView

class OrderUpdateView(SaveAndNextMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'

    # Optional: Customize navigation behavior
    navigation_max_pk_count = 100  # Override default
    navigation_enabled = True  # Enable/disable (default: True)
```

### 4. Add Navigation Buttons to Template

Include the navigation buttons partial in your form template:

```django
{% extends 'base.html' %}

{% block content %}
<h1>Edit Order</h1>

<form method="post">
    {% csrf_token %}

    {# Include save and next buttons #}
    {% include 'better_django_tables/partials/save_and_next_buttons.html' %}

    {{ form.as_p }}

    {# Include again at bottom for convenience #}
    {% include 'better_django_tables/partials/save_and_next_buttons.html' %}
</form>
{% endblock %}
```

Or create custom buttons:

```django
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}

    <div class="button-group">
        {% if has_previous %}
            <button type="submit" name="save_and_previous" class="btn btn-secondary">
                ← Save & Previous
            </button>
        {% endif %}

        <button type="submit" name="save" class="btn btn-primary">
            Save
        </button>

        {% if has_next %}
            <button type="submit" name="save_and_next" class="btn btn-secondary">
                Save & Next →
            </button>
        {% endif %}
    </div>

    {% if current_position %}
        <small>Record {{ current_position }} of {{ total_records }}</small>
    {% endif %}
</form>
```

## Configuration Options

### View-Level Configuration

#### NavigationStorageMixin (for list views)

```python
class MyListView(TableView):
    # Enable/disable storing navigation PKs
    enable_navigation_storage = True  # Default: True

    # Maximum PKs to store for this view
    navigation_max_pk_count = 300  # Default: from settings (500)

    # Context window size (PKs before/after current)
    navigation_context_window = 75  # Default: from settings (50)
```

#### SaveAndNextMixin (for update views)

```python
class MyUpdateView(SaveAndNextMixin, UpdateView):
    # Enable/disable navigation
    navigation_enabled = True  # Default: True

    # Override max PK count
    navigation_max_pk_count = 300

    # Custom session key (auto-generated if not set)
    navigation_session_key = 'custom_nav_key'
```

## Template Context Variables

When using `SaveAndNextMixin`, these variables are available in your template:

- `navigation_enabled` - Boolean, is navigation enabled
- `next_pk` - PK of next record (or None)
- `previous_pk` - PK of previous record (or None)
- `next_url` - Full URL to next record
- `previous_url` - Full URL to previous record
- `current_position` - Current position in list (1-indexed)
- `total_records` - Total number of records in navigation list
- `has_next` - Boolean, is there a next record
- `has_previous` - Boolean, is there a previous record

## How It Works

### PK Storage Strategy

1. **Full List Storage**: When you view a table with filters/sorting, all matching PKs are collected
2. **Smart Limiting**: If the PK count exceeds the limit, two strategies are used:
   - **Initial View**: Store first N PKs (where N = max_pk_count)
   - **With Current PK**: Store window around current PK (context_window before + after)
3. **Session Storage**: Limited PKs stored in session with timestamp
4. **Auto Expiry**: Data expires after timeout (default: 1 hour)

### Example with Large Dataset

```python
# Settings
BETTER_DJANGO_TABLES_NAVIGATION_MAX_PK_COUNT = 100
BETTER_DJANGO_TABLES_NAVIGATION_CONTEXT_WINDOW = 25

# Scenario: Table has 10,000 orders
# User applies filter, gets 1,000 matching orders
# User clicks on order #500

# What gets stored:
# - PKs from position 475 to 525 (50 total: 25 before + current + 25 after)
# - User can navigate smoothly through this window
# - If they reach the edge, window shifts to keep them centered
```

### PK Limiting Benefits

- **Memory Efficiency**: Don't store thousands of PKs in session
- **Performance**: Faster session reads/writes
- **Scalability**: Works with tables of any size
- **User Experience**: Users rarely navigate through hundreds of records

## Advanced Usage

### Disable Navigation for Specific View

```python
class QuickEditView(SaveAndNextMixin, UpdateView):
    navigation_enabled = False  # No navigation for this view
```

### Custom Navigation Logic

```python
class CustomUpdateView(SaveAndNextMixin, UpdateView):
    def get_next_pk(self):
        # Custom logic to determine next PK
        # For example, only navigate to unprocessed records
        pks = self.get_navigation_pks()
        current_index = pks.index(self.object.pk)

        for pk in pks[current_index + 1:]:
            obj = self.model.objects.get(pk=pk)
            if obj.status == 'pending':
                return pk
        return None
```

### URL-Based Navigation

Navigation context can also be passed via URL parameters (takes precedence over session):

```python
# In your list view template
<a href="{% url 'order_update' pk=order.pk %}?nav_pks={{ nav_pks_str }}">
    Edit Order
</a>
```

This is useful for:
- Sharing links with navigation context
- Bookmarking specific navigation states
- HTMX-based navigation

## Troubleshooting

### Navigation not working

1. **Check session is enabled** in Django settings
2. **Verify TableView** is used for list view (includes NavigationStorageMixin)
3. **Confirm SaveAndNextMixin** is added to update view
4. **Check button names** in template match: `save_and_next`, `save_and_previous`

### Too few PKs stored

Increase limits in settings or view:

```python
class MyListView(TableView):
    navigation_max_pk_count = 1000  # Increase limit
    navigation_context_window = 100  # Wider window
```

### Session data expires too quickly

Increase timeout in settings:

```python
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_TIMEOUT = 7200  # 2 hours
```

### Memory concerns with large datasets

The feature is specifically designed to handle this:
- Only limited PKs are stored (default: 500 max)
- Context window keeps most relevant PKs (default: 50 before/after)
- Old data auto-expires
- You can reduce limits further per-view

## Best Practices

1. **Set appropriate limits**: For tables with millions of rows, keep max_pk_count low (100-300)
2. **Use context windows**: Better UX than just storing first N PKs
3. **Add keyboard shortcuts**: Enhance navigation with Ctrl+→ / Ctrl+← (custom JS)
4. **Show progress**: Display "Record X of Y" to give users context
5. **Test with filters**: Ensure navigation respects active filters
6. **Consider pagination**: For very large result sets, paginate the table

## Example: Complete Implementation

```python
# views.py
from better_django_tables.views import TableView
from better_django_tables.view_mixins import SaveAndNextMixin
from django.views.generic import UpdateView

class OrderListView(TableView):
    model = Order
    table_class = OrderTable
    filterset_class = OrderFilter
    navigation_max_pk_count = 200  # Reasonable for order tables

class OrderUpdateView(SaveAndNextMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_update.html'

    def get_success_url(self):
        # Default behavior works, but you can customize
        return super().get_success_url()
```

```django
{# templates/orders/order_update.html #}
{% extends 'base.html' %}

{% block content %}
<div class="container">
    <h1>Edit Order #{{ object.pk }}</h1>

    <form method="post">
        {% csrf_token %}

        {# Navigation buttons at top #}
        {% include 'better_django_tables/partials/save_and_next_buttons.html' %}

        <div class="form-content my-4">
            {{ form.as_p }}
        </div>

        {# Navigation buttons at bottom #}
        {% include 'better_django_tables/partials/save_and_next_buttons.html' %}
    </form>

    <a href="{% url 'order_list' %}" class="btn btn-link">
        Back to List
    </a>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Optional: Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'ArrowRight' && document.querySelector('button[name="save_and_next"]')) {
                e.preventDefault();
                document.querySelector('button[name="save_and_next"]').click();
            } else if (e.key === 'ArrowLeft' && document.querySelector('button[name="save_and_previous"]')) {
                e.preventDefault();
                document.querySelector('button[name="save_and_previous"]').click();
            }
        }
    });
</script>
{% endblock %}
```

## See Also

- [Django Sessions Documentation](https://docs.djangoproject.com/en/stable/topics/http/sessions/)
- [Better Django Tables Documentation](../README.md)
