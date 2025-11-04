# pylint: disable=missing-class-docstring,missing-function-docstring
"""
Configuration for better-django-tables.

Settings can be overridden in Django settings.py using the prefix BETTER_DJANGO_TABLES_
"""

from django.conf import settings


# Navigation Settings
NAVIGATION_MAX_PK_COUNT = getattr(
    settings, "BETTER_DJANGO_TABLES_NAVIGATION_MAX_PK_COUNT", 500
)
"""
Maximum number of PKs to store in session for navigation.
Default: 500
Set to 0 for unlimited (not recommended for large datasets)
"""

NAVIGATION_SESSION_TIMEOUT = getattr(
    settings,
    "BETTER_DJANGO_TABLES_NAVIGATION_SESSION_TIMEOUT",
    3600,  # 1 hour
)
"""
Time in seconds before navigation data expires from session.
Default: 3600 (1 hour)
"""

NAVIGATION_SESSION_KEY_PREFIX = getattr(
    settings, "BETTER_DJANGO_TABLES_NAVIGATION_SESSION_KEY_PREFIX", "bdt_nav_"
)
"""
Prefix for session keys used to store navigation data.
Default: 'bdt_nav_'
"""

NAVIGATION_CONTEXT_WINDOW = getattr(
    settings, "BETTER_DJANGO_TABLES_NAVIGATION_CONTEXT_WINDOW", 50
)
"""
Number of PKs to include before and after current PK when limiting.
Default: 50 (total 100 PKs stored: 50 before + current + 50 after)
This ensures smooth navigation even with limited PK storage.
"""

NAVIGATION_MAX_CONTEXTS = getattr(
    settings, "BETTER_DJANGO_TABLES_NAVIGATION_MAX_CONTEXTS", 50
)
"""
Maximum number of navigation contexts to keep in session.
Default: 20
When exceeded, oldest contexts are removed (LRU eviction).
Set to 0 for unlimited (may cause session bloat if user visits many scoped contexts).
Recommended: 10-30 for typical usage
"""
