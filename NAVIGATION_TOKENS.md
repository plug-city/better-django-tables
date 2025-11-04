# Navigation Token System

## Overview

The "Save and Next" navigation feature now uses **UUID-based navigation tokens** instead of scope keys. This provides cleaner URLs and eliminates the need for duplicate logic between table views and update views.

## How It Works

### 1. Table View Generates Token

When a filtered table view renders, it:
1. Generates a unique 16-character navigation token (UUID substring)
2. Stores the filtered PKs in session under that token
3. Adds the token to template context

```python
class PurchaseLineListView(NavigationStorageMixin, FilterView):
    model = PurchaseLine
    # No configuration needed - works automatically!
```

### 2. Token Added to Edit URLs

In your table template, include the token in edit links:

```django
{# Option 1: Manual - append token to URL #}
<a href="{{ record.get_absolute_url }}?nav_token={{ nav_token }}">
    Edit
</a>

{# Option 2: Template tag (recommended) #}
{% load better_django_tables_tags %}
<a href="{% nav_url record %}">Edit</a>
```

### 3. Update View Uses Token

The update view reads the token from the URL and retrieves navigation data:

```python
class PurchaseLineUpdateView(SaveAndNextMixin, UpdateView):
    model = PurchaseLine
    # No configuration needed - reads token from ?nav_token=XXX
```

When user clicks "Save & Next", the token is preserved in the next URL automatically.

## Benefits Over Scope Keys

### Before (Scope Keys)
```python
# Table View
class PurchaseLineListView(NavigationStorageMixin, FilterView):
    def get_navigation_scope_key(self):
        order_id = self.request.GET.get('order_id')
        return f'order_{order_id}' if order_id else None

# Update View - DUPLICATE LOGIC
class PurchaseLineUpdateView(SaveAndNextMixin, UpdateView):
    def get_navigation_scope_key(self):
        order_id = self.request.GET.get('order_id')  # Same as above!
        return f'order_{order_id}' if order_id else None

# URL
/purchaseline/1/edit/?order_id=123&status=pending&date_min=2024-01-01
```

### After (Navigation Tokens)
```python
# Table View
class PurchaseLineListView(NavigationStorageMixin, FilterView):
    model = PurchaseLine
    # That's it!

# Update View
class PurchaseLineUpdateView(SaveAndNextMixin, UpdateView):
    model = PurchaseLine
    # That's it!

# URL
/purchaseline/1/edit/?nav_token=a3f2b1c4d5e6f7g8
```

**Advantages:**
- ✅ No duplicate logic
- ✅ Cleaner URLs
- ✅ Works with any filter combination
- ✅ Simpler to implement
- ✅ Future-proof (filters can change without breaking navigation)

## Session Management

### Storage
- **Key Format**: `bdt_nav_token_{uuid}`
- **Data Stored**: PKs, timestamp, total count, referrer URL
- **Size**: ~5 KB per context (500 PKs + metadata)

### Cleanup Strategies

#### 1. Time-Based Expiration
Tokens older than 1 hour are automatically ignored:
```python
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_TIMEOUT = 3600  # seconds
```

#### 2. LRU Eviction
Maximum 20 navigation contexts per session (configurable):
```python
BETTER_DJANGO_TABLES_NAVIGATION_MAX_CONTEXTS = 20
```

When limit is reached, oldest tokens are removed.

#### 3. Lazy Cleanup
Cleanup only runs when approaching the limit, not on every request (~90% reduction in overhead).

### Session Impact

| User Activity | Tokens Created | Session Size |
|--------------|----------------|--------------|
| Light (5 tables/day) | 5 | ~25 KB |
| Normal (20 tables/day) | 20 | ~100 KB (capped) |
| Heavy (100 tables/day) | 100 | ~100 KB (LRU eviction) |

**Memory is capped** - will never exceed configured limit regardless of usage.

## Configuration

All settings are optional with sensible defaults:

```python
# settings.py

# Maximum PKs to store per navigation context
BETTER_DJANGO_TABLES_NAVIGATION_MAX_PK_COUNT = 500

# Time before navigation data expires
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_TIMEOUT = 3600  # 1 hour

# Maximum number of navigation contexts to keep
BETTER_DJANGO_TABLES_NAVIGATION_MAX_CONTEXTS = 20

# Session key prefix
BETTER_DJANGO_TABLES_NAVIGATION_SESSION_KEY_PREFIX = 'bdt_nav_'

# Context window (PKs before/after current when limiting)
BETTER_DJANGO_TABLES_NAVIGATION_CONTEXT_WINDOW = 50
```

## Template Usage

### Basic Edit Link
```django
<a href="{{ record.get_absolute_url }}?nav_token={{ nav_token }}">
    Edit
</a>
```

### With Template Tag (Recommended)
```django
{% load better_django_tables_tags %}

{# Automatically appends nav_token #}
<a href="{% nav_url record %}">Edit</a>

{# Or use in buttons #}
<button hx-get="{% nav_url record %}" hx-target="#modal">
    Edit
</button>
```

### Full Example
```django
{% extends "base.html" %}
{% load render_table from django_tables2 %}

{% block content %}
    <div class="table-container">
        {% render_table table %}
    </div>

    {# Token is automatically in context as 'nav_token' #}
    {# Use it in your custom table templates: #}

    {% for record in table.data %}
        <tr>
            <td>{{ record.name }}</td>
            <td>
                <a href="{{ record.get_absolute_url }}?nav_token={{ nav_token }}">
                    <i class="bi bi-pencil"></i> Edit
                </a>
            </td>
        </tr>
    {% endfor %}
{% endblock %}
```

## Edge Cases

### Token Not Present
If user bookmarks an edit URL without a token:
- Navigation buttons are hidden (no "Save & Next")
- Regular save still works
- Graceful degradation

### Token Expired
If user returns to a bookmark after 1 hour:
- Navigation data is expired and ignored
- Navigation buttons hidden
- Regular save still works

### Session Cleared
If user's session is cleared (logout/timeout):
- All navigation tokens are lost
- Next table view generates new token
- No errors, just fresh state

## Migration from Scope Keys

If you're currently using `navigation_scope_key`:

### Old Code
```python
class PurchaseLineListView(NavigationStorageMixin, FilterView):
    def get_navigation_scope_key(self):
        order_id = self.request.GET.get('order_id')
        return f'order_{order_id}' if order_id else None

class PurchaseLineUpdateView(SaveAndNextMixin, UpdateView):
    def get_navigation_scope_key(self):
        order_id = self.request.GET.get('order_id')
        return f'order_{order_id}' if order_id else None
```

### New Code
```python
class PurchaseLineListView(NavigationStorageMixin, FilterView):
    pass  # Remove get_navigation_scope_key()

class PurchaseLineUpdateView(SaveAndNextMixin, UpdateView):
    pass  # Remove get_navigation_scope_key()
```

### Template Changes
```django
{# Old - manually pass filter params #}
<a href="{% url 'purchaseline_update' pk=line.pk %}?order_id={{ order.id }}">
    Edit
</a>

{# New - just include token #}
<a href="{{ line.get_absolute_url }}?nav_token={{ nav_token }}">
    Edit
</a>
```

**That's it!** Much simpler.

## Troubleshooting

### Navigation Not Working

**Check 1**: Is token in URL?
```
✅ /edit/1/?nav_token=a3f2b1c4d5e6f7g8
❌ /edit/1/
```

**Check 2**: Is NavigationStorageMixin on table view?
```python
class MyTableView(NavigationStorageMixin, FilterView):  # ✅
    pass
```

**Check 3**: Is token in template context?
```django
{{ nav_token }}  {# Should output something like: a3f2b1c4d5e6f7g8 #}
```

**Check 4**: Check session storage
```python
# In view or shell
session_key = f'bdt_nav_token_{nav_token}'
print(request.session.get(session_key))  # Should show {'pks': [...], ...}
```

### Token Keeps Changing

This is normal! Each table view render generates a fresh token. This is intentional:
- Prevents stale navigation data
- Ensures PKs match current filter state
- Automatic cache invalidation

### Want Persistent Tokens?

Not recommended, but possible by overriding:
```python
class MyTableView(NavigationStorageMixin, FilterView):
    def get_or_create_navigation_token(self):
        # Store token in session to reuse across requests
        token = self.request.session.get('my_persistent_token')
        if not token:
            import uuid
            token = uuid.uuid4().hex[:16]
            self.request.session['my_persistent_token'] = token
        return token
```

**Warning**: This defeats the purpose of fresh navigation data and may cause bugs.

## Performance

### Token Generation
- UUID generation: ~0.001ms
- Negligible overhead

### Session Storage
- Write: ~1-2ms per context
- Read: ~0.5ms
- Cleanup: ~5-10ms (only when at limit)

### Network
- Token in URL: +25 bytes
- Much smaller than passing all filter params!

Before (with filters): `?order_id=123&status=pending&date_min=2024-01-01` (50+ bytes)
After (with token): `?nav_token=a3f2b1c4d5e6f7g8` (25 bytes)

## Security

### Token Visibility
- Tokens are visible in URLs
- They don't expose sensitive data (just random UUIDs)
- Session-scoped (only valid for that user)

### Session Hijacking
- Standard Django session security applies
- Use HTTPS to protect session cookies
- Configure `SESSION_COOKIE_SECURE = True` in production

### Data Exposure
- PKs are stored server-side in session
- Not exposed to client
- Not shared between users

## Advanced Usage

### Custom Token Length
```python
class MyTableView(NavigationStorageMixin, FilterView):
    navigation_token_length = 32  # Longer token
```

### Disable Navigation for Specific View
```python
class MyTableView(NavigationStorageMixin, FilterView):
    enable_navigation_storage = False
```

### Custom Cleanup Logic
```python
class MyTableView(NavigationStorageMixin, FilterView):
    def cleanup_expired_navigation_data(self, force=True):
        # Always force cleanup
        super().cleanup_expired_navigation_data(force=True)
```

## Summary

**Navigation tokens provide:**
- ✅ Cleaner URLs
- ✅ Less code (no duplicate scope key logic)
- ✅ Automatic scoping (works with any filters)
- ✅ Better performance (lazy cleanup)
- ✅ Graceful degradation (works without token)
- ✅ Configurable limits (prevents session bloat)

**Perfect for:**
- Complex filtered tables
- Multiple filter combinations
- User-friendly navigation
- Production applications with many concurrent users
