# Release Notes

## Version 0.11.3 (2025-11-11)

### Improvements
- Optimized navigation PK storage to respect `navigation_max_pk_count` limit during queryset evaluation
- Improved database query efficiency for navigation storage by limiting PKs fetched from database
- Added debug logging for navigation PK count tracking

---

## Version 0.11.2 (2025-11-11)

### Improvements
- Enhanced HTMX support for template views
- Added `HtmxTemplateView` for better HTMX integration patterns
- Improved template response handling for partial page loads

---

## Version 0.11.1 (2025-11-10)

### Bug Fixes
- Fixed filter button positioning in sidebar filter template
- Improved template formatting and code organization

### Improvements
- Added filter submit button at the top of the sidebar for better UX
- Cleaned up whitespace formatting in view_mixins.py

---

## Version 0.11.0 (2025-11-05)

### Changes
- Removed deprecated reports functionality (models, views, filters, forms)
- Cleaned up commented-out report-related code across templates
- Removed NAVIGATION_TOKENS.md documentation file
- Improved code organization and formatting

### Breaking Changes
- Report-related functionality has been removed. If you were using the reports feature, please stay on version 0.10.0 or earlier.

---

## Version 0.10.0 (2025-11-04)

### New Features
- Enhanced `NavigationStorageMixin` with improved token-based navigation
- Added support for database-backed sessions with explicit `session.save()` calls
- Improved context data handling in `get_context_data()` method

### Improvements
- Better session management for multi-table navigation scenarios
- Enhanced navigation token caching mechanism
- Improved compatibility with complex view hierarchies

### Bug Fixes
- Fixed session persistence issues in certain edge cases
- Improved reliability of navigation state management

---

## Version 0.9.0

Previous release.
