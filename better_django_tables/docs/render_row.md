# render_row Template Tag

The `render_row` template tag allows you to render a single table row from a django-tables2 Table. This is particularly useful for HTMX applications where you want to update a specific row without re-rendering the entire table.

## Usage

```html
{% load better_django_tables %}
{% render_row table record %}
```

## Parameters

- `table`: A django-tables2 Table instance
- `record`: The model instance/record to render as a row

## Example with HTMX

### View
```python
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from .models import MyModel
from .tables import MyTable

def update_record_htmx(request, pk):
    record = get_object_or_404(MyModel, pk=pk)

    # Handle form submission and update record
    if request.method == 'POST':
        # Update logic here...
        record.save()

    # Create table instance
    table = MyTable([record])  # Single record

    # Render just the row
    html = render_to_string(
        'path/to/row_template.html',
        {'table': table, 'record': record},
        request=request
    )

    return HttpResponse(html)
```

### Template
```html
<!-- row_template.html -->
{% load better_django_tables %}
{% render_row table record %}
```

### Frontend HTMX
```html
<button hx-post="/update-record/{{ record.pk }}/"
        hx-target="#row-{{ record.pk }}"
        hx-swap="outerHTML">
    Update Record
</button>
```

## Notes

- The rendered row will include all the same styling, attributes, and custom rendering as if it were part of the full table
- Row attributes (CSS classes, data attributes, etc.) are preserved
- Column-specific rendering (custom render methods) is applied
- Localization settings are respected
