# Enhanced Links Functionality

## Overview

The better-django-tables template now supports different HTTP methods for links, allowing you to create both regular GET links and POST form submissions with CSRF protection.

## Features

- **Backward Compatibility**: Existing link configurations continue to work without changes
- **Multiple HTTP Methods**: Support for GET (default) and POST methods
- **CSRF Protection**: Automatic CSRF token inclusion for POST requests
- **Confirmation Dialogs**: Optional confirmation messages for destructive actions
- **Flexible Styling**: Customizable button types and styles

## Link Configuration Options

### Basic Structure

```python
link = {
    'url': '/path/to/endpoint/',           # Required: The URL to link to
    'method': 'GET|POST',                  # Optional: HTTP method (default: GET)
    'text': 'Link Text',                   # Optional: Plain text link (for GET only)
    'label': 'Button Label',               # Optional: Button label (renders as button)
    'button_type': 'btn-primary',          # Optional: Bootstrap button class
    'confirm_message': 'Are you sure?'     # Optional: Confirmation dialog text
}
```

### Configuration Examples

#### 1. GET Link (Legacy - Plain Text)
```python
{
    'url': '/view/details/',
    'text': 'View Details'
}
```

#### 2. GET Link (Button Style)
```python
{
    'url': '/export/data/',
    'label': 'Export Data',
    'button_type': 'btn-info'
}
```

#### 3. POST Form (Simple)
```python
{
    'url': '/refresh/data/',
    'label': 'Refresh Data',
    'method': 'POST',
    'button_type': 'btn-warning'
}
```

#### 4. POST Form (With Confirmation)
```python
{
    'url': '/sync/contacts/',
    'label': 'Sync Contacts',
    'method': 'POST',
    'button_type': 'btn-success',
    'confirm_message': 'This will sync all contacts from OpenPhone. Continue?'
}
```

## Usage in Django Views

### TableView Integration

```python
from django.urls import reverse_lazy
from better_django_tables.views import TableView

class MyTableView(TableView):
    model = MyModel

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['links'] = [
            # Multiple link types can be combined
            {
                'url': reverse_lazy('my_app:create'),
                'label': 'Create New',
                'button_type': 'btn-primary'
            },
            {
                'url': reverse_lazy('my_app:sync'),
                'label': 'Sync Data',
                'method': 'POST',
                'button_type': 'btn-success',
                'confirm_message': 'Sync all data from external source?'
            }
        ]

        return context
```

### View Handling POST Requests

```python
from django.contrib import messages
from django.shortcuts import redirect

class MySyncView(LoginRequiredMixin, ListView):
    model = MyModel

    def post(self, request, *args, **kwargs):
        """Handle POST request for sync operation"""
        try:
            # Perform sync operation
            my_sync_service = MySyncService()
            my_sync_service.sync_data()

            messages.success(request, 'Data synced successfully!')
        except Exception as e:
            messages.error(request, f'Sync failed: {e}')

        return redirect('my_app:list')
```

## Button Types (Bootstrap Classes)

Common button types you can use:

- `btn-primary` - Primary action (blue)
- `btn-secondary` - Secondary action (gray)
- `btn-success` - Success action (green)
- `btn-danger` - Destructive action (red)
- `btn-warning` - Warning action (yellow)
- `btn-info` - Information action (cyan)
- `btn-light` - Light action (light gray)
- `btn-dark` - Dark action (dark gray)

Add `btn-outline-*` for outlined versions (e.g., `btn-outline-primary`).

## Migration from Old Format

### Before (Old Format)
```python
context['links'] = [
    {
        'url': '/some/endpoint/',
        'text': 'Click Here',
        'button_type': 'btn-primary'
    }
]
```

### After (Enhanced Format)
```python
context['links'] = [
    {
        'url': '/some/endpoint/',
        'label': 'Click Here',  # Changed from 'text' to 'label' for button style
        'button_type': 'btn-primary'
        # method defaults to GET, so no change needed
    }
]
```

## Implementation Details

The template automatically:

1. **Detects Method**: Checks `link.method` (defaults to GET)
2. **Renders Appropriately**:
   - GET: Renders as `<a>` tag
   - POST: Renders as `<form>` with `<button>`
3. **Adds CSRF Protection**: Includes `{% csrf_token %}` for POST forms
4. **Handles Confirmations**: Adds `onclick` confirmation for POST with confirmation message
5. **Maintains Styling**: Applies Bootstrap classes consistently

## Security Considerations

- CSRF tokens are automatically included for all POST requests
- Confirmation dialogs help prevent accidental actions
- URL validation should still be performed in your Django views
- Consider adding additional permissions checks for sensitive operations

## Example: OpenPhone Contact Sync

This is how the OpenPhone contact sync functionality uses the enhanced links:

```python
class OpenPhoneContactListView(TableView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['links'] = [
            {
                'url': reverse_lazy("openphone:contact_sync"),
                'label': "Sync Contacts from OpenPhone",
                'button_type': 'btn-success',
                'method': 'POST',
                'confirm_message': 'This will sync all contacts from OpenPhone to the database. This may take a while. Continue?'
            }
        ]
        return context
```
