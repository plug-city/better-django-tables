# PerPageViewMixin Documentation

## Overview

The `PerPageViewMixin` adds per-page selection functionality to table views, allowing users to choose how many records to display per page. The selection is saved in the user's session and persists across requests. It works seamlessly with both standard page loads and HTMX requests.

## Features

- **User-configurable page size**: Users can select from predefined options
- **Session persistence**: User's choice is saved and remembered
- **HTMX support**: Works with dynamic table updates via HTMX
- **Flexible configuration**: Customizable options and defaults
- **Works with django-tables2**: Integrates seamlessly with `paginate_by`

## Installation

The mixin is already included in `better_django_tables.view_mixins`:

```python
from better_django_tables.view_mixins import PerPageViewMixin
```

## Basic Usage

### Simple Example

```python
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from better_django_tables.view_mixins import PerPageViewMixin
from .models import MyModel
from .tables import MyTable

class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    model = MyModel
    table_class = MyTable
    template_name = 'my_app/table.html'
```

### With BetterDjangoTables TableView

```python
from better_django_tables.views import TableView
from better_django_tables.view_mixins import PerPageViewMixin
from .models import Product
from .tables import ProductTable

class ProductListView(PerPageViewMixin, TableView):
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter
```

## Configuration

### Attributes

#### `per_page_options`
List of available per-page options that users can select from.

**Default**: `[10, 25, 50, 100, 500, 1000]`

**Example**:
```python
class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    per_page_options = [10, 25, 50, 100]  # Custom options
```

#### `default_per_page`
Default number of records per page if no preference is set.

**Default**: `25`

**Example**:
```python
class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    default_per_page = 50  # Show 50 records by default
```

#### `per_page_session_key`
Session key used to store the user's per-page preference.

**Default**: `'table_per_page'`

**Example**:
```python
class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    per_page_session_key = 'products_per_page'  # Custom session key
```

### Priority Order

The mixin determines the number of items per page using this priority:

1. **URL parameter**: `?per_page=50` (highest priority)
2. **Session value**: Saved user preference
3. **View's `paginate_by`**: If defined on the view
4. **`default_per_page`**: Fallback default (lowest priority)

## Template Integration

### Including the Per-Page Selector

The per-page selector is automatically included in the default better-django-tables templates:
- `better_django_tables/tables/better_table.html`
- `better_django_tables/tables/better_table_inline.html`

You can also manually include it in your custom templates:

```django
{% include "better_django_tables/partials/per_page_selector.html" %}
```

### Template Context Variables

The mixin adds these variables to the template context:

- `per_page_options`: List of available options
- `current_per_page`: Currently selected per-page value

## HTMX Integration

The per-page selector automatically detects HTMX requests and updates the table dynamically.

### HTMX Table View Example

```python
from better_django_tables.views import HtmxTableView
from better_django_tables.view_mixins import PerPageViewMixin

class MyHtmxTableView(PerPageViewMixin, HtmxTableView):
    model = MyModel
    table_class = MyTable
    htmx_show_per_page = True  # Enable per-page selector for HTMX
```

### How It Works

When a user selects a per-page option:
1. If it's an HTMX request, the table updates dynamically
2. The selection is saved to the session
3. The URL is updated with the new parameter
4. All subsequent requests use the saved preference

The template automatically adds HTMX attributes:
```html
<a class="dropdown-item" 
   href="?per_page=50"
   hx-get="?per_page=50"
   hx-target="closest .inline-table, closest main"
   hx-swap="outerHTML"
   hx-push-url="true">
  50
</a>
```

## Advanced Usage

### Per-Table Session Keys

If you have multiple tables and want separate per-page preferences for each:

```python
class ProductTableView(PerPageViewMixin, TableView):
    model = Product
    table_class = ProductTable
    per_page_session_key = 'products_per_page'

class OrderTableView(PerPageViewMixin, TableView):
    model = Order
    table_class = OrderTable
    per_page_session_key = 'orders_per_page'
```

### Custom Options Based on User Role

```python
class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize options based on conditions
        if self.request.user.is_staff:
            self.per_page_options = [10, 25, 50, 100, 500, 1000]
        else:
            self.per_page_options = [10, 25, 50]
```

### Combining with Other Mixins

```python
from better_django_tables.views import TableView
from better_django_tables.view_mixins import (
    PerPageViewMixin,
    ActiveFilterMixin,
    BulkActionViewMixin,
    ReportableViewMixin,
)

class AdvancedTableView(
    PerPageViewMixin,          # Per-page selection
    ActiveFilterMixin,         # Show active filters
    BulkActionViewMixin,       # Bulk actions
    ReportableViewMixin,       # Save reports
    TableView
):
    model = MyModel
    table_class = MyTable
    filterset_class = MyFilter
```

## Testing

### Test Session Persistence

```python
from django.test import TestCase, Client

class PerPageMixinTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_per_page_saved_to_session(self):
        # First request with per_page parameter
        response = self.client.get('/my-table/?per_page=50')
        self.assertEqual(self.client.session['table_per_page'], 50)
        
        # Second request without parameter should use session value
        response = self.client.get('/my-table/')
        # Verify 50 items are displayed
```

### Test HTMX Requests

```python
def test_htmx_per_page_update(self):
    response = self.client.get(
        '/my-table/?per_page=100',
        HTTP_HX_REQUEST='true'
    )
    self.assertTemplateUsed(
        response,
        'better_django_tables/tables/better_table_inline.html'
    )
```

## Troubleshooting

### Per-page selector not showing

Make sure:
1. The mixin is included in your view's inheritance chain
2. The table has pagination enabled
3. The template includes the per-page selector partial

### Selection not persisting

Check that:
1. Django sessions are properly configured
2. Session middleware is enabled
3. The session key is not conflicting with other session data

### HTMX not updating

Verify:
1. HTMX is properly loaded in your templates
2. The `htmx_show_per_page` attribute is set to `True` for HTMX views
3. The HTMX target selectors match your template structure

## Migration from Manual Pagination

If you're currently using manual `paginate_by` in your views:

**Before**:
```python
class MyTableView(SingleTableMixin, FilterView):
    model = MyModel
    table_class = MyTable
    paginate_by = 25  # Fixed value
```

**After**:
```python
class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
    model = MyModel
    table_class = MyTable
    default_per_page = 25  # Default, but user can change
    per_page_options = [10, 25, 50, 100]
```

The `paginate_by` attribute will still work as a fallback if defined, but the mixin's options will take precedence.

## Browser Compatibility

The per-page selector uses Bootstrap dropdown components, which are supported in:
- Chrome, Firefox, Safari, Edge (latest versions)
- IE 11 (with polyfills)

HTMX functionality requires:
- Modern browsers with ES6 support
- HTMX library loaded in templates
