# Release Notes

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
