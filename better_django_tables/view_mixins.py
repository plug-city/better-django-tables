# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods
import logging
import csv
import json
import time
from urllib.parse import urlparse
import uuid

from itertools import count

from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateResponseMixin
from django.http import StreamingHttpResponse
from django.urls import resolve
from django.http import HttpResponse
from django.urls import reverse

from django_tables2.views import TableMixinBase
from django_tables2 import RequestConfig

from better_django_tables import conf


logger = logging.getLogger(__name__)


class NextViewMixin:
    """
    Base mixin for views that provides standard functions for all views.
    """

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return super().get_success_url()


class SaveAndNextMixin:
    """
    Mixin for update views that enables "Save and Next" navigation with multiple save options.

    This mixin allows users to save the current record and choose what happens next:
    - Save: Standard save, redirect to success URL
    - Save & Continue Editing: Save and stay on the same page
    - Save & Next: Save and navigate to next record in the filtered list
    - Save & Previous: Save and navigate to previous record
    - Save & Close: Save and return to list view

    The user's save preference is remembered across pages using sessionStorage.
    It retrieves navigation data from session using a navigation token (UUID) passed
    via query parameters from the table view.

    Configuration:
        - navigation_max_pk_count: Max PKs to store (default from settings)
        - navigation_enabled: Enable/disable navigation (default: True)
        - navigation_context_window: PKs to include before/after when limiting
        - navigation_form_id: Optional form ID for the save buttons

    Usage:
        class MyUpdateView(SaveAndNextMixin, UpdateView):
            model = MyModel
            navigation_max_pk_count = 100  # Override default

        In template:
            {% include 'better_django_tables/partials/save_and_next_buttons.html' %}

        The table view will automatically add ?nav_token=XXX to edit URLs.
        No need to manually pass filter parameters!
    """

    navigation_max_pk_count = None  # Will use setting default if None
    navigation_enabled = True
    navigation_context_window = None  # Will use setting default if None
    navigation_form_id = None  # Optional form ID for the save buttons

    def get_navigation_max_pk_count(self):
        """Get the maximum number of PKs to store in session."""
        if self.navigation_max_pk_count is not None:
            return self.navigation_max_pk_count
        return conf.NAVIGATION_MAX_PK_COUNT

    def get_navigation_context_window(self):
        """Get the number of PKs to include before/after current PK."""
        if self.navigation_context_window is not None:
            return self.navigation_context_window
        return conf.NAVIGATION_CONTEXT_WINDOW

    def get_navigation_token(self):
        """
        Get navigation token from request query parameters.

        The token is passed from the table view via URL parameter.
        Returns None if no token is present.
        """
        return self.request.GET.get("nav_token")

    def get_navigation_session_key(self, nav_token=None):
        """
        Get the session key for retrieving navigation data.

        Args:
            nav_token: Navigation token. If None, tries to get from request.
        """
        if nav_token is None:
            nav_token = self.get_navigation_token()

        if nav_token:
            return f"{conf.NAVIGATION_SESSION_KEY_PREFIX}token_{nav_token}"

        return None

    def get_navigation_data(self):
        """
        Get navigation data from session using the token from query params.

        Returns dict with:
            - pks: list of PKs for navigation
            - timestamp: when data was stored
            - referrer_url: URL that set the navigation PKs
        """
        session_key = self.get_navigation_session_key()

        if not session_key:
            # No token in URL, no navigation data
            return {}

        # Get navigation data from session
        nav_data = self.request.session.get(session_key, {})
        # Check if data has expired
        if nav_data:
            timestamp = nav_data.get("timestamp", 0)
            age = time.time() - timestamp
            if age > conf.NAVIGATION_SESSION_TIMEOUT:
                logger.debug("Navigation data expired (age: %s seconds)", age)
                return {}

        return nav_data

    def get_navigation_pks(self):
        """Get the list of PKs for navigation."""
        nav_data = self.get_navigation_data()
        return nav_data.get("pks", [])

    def get_current_position(self):
        """
        Get current position in the navigation list.

        Returns tuple: (current_index, total_count) or (None, None) if not in list
        """
        # Only works for detail views (UpdateView, DetailView) that have self.object
        if not hasattr(self, "object") or self.object is None:
            return (None, None)

        pks = self.get_navigation_pks()
        current_pk = self.object.pk

        try:
            current_index = pks.index(current_pk)
            return (current_index, len(pks))
        except (ValueError, AttributeError):
            return (None, None)

    def get_next_pk(self):
        """Get the next PK in the navigation list."""
        pks = self.get_navigation_pks()
        if not pks:
            return None

        current_pk = self.object.pk

        try:
            current_index = pks.index(current_pk)
            if current_index < len(pks) - 1:
                return pks[current_index + 1]
        except (ValueError, IndexError):
            pass

        return None

    def get_previous_pk(self):
        """Get the previous PK in the navigation list."""
        pks = self.get_navigation_pks()
        if not pks:
            return None

        current_pk = self.object.pk

        try:
            current_index = pks.index(current_pk)
            if current_index > 0:
                return pks[current_index - 1]
        except (ValueError, IndexError):
            pass

        return None

    def get_navigation_url(self, pk):
        """
        Build URL for navigating to a specific PK.

        Preserves the navigation token from the current request so navigation
        continues to work across saves.
        """
        if not pk:
            return None

        try:
            obj = self.model.objects.get(pk=pk)
            base_url = obj.get_absolute_url()

            # Preserve navigation token and any other query parameters
            query_params = self.request.GET.copy()

            # Remove pagination/navigation params that shouldn't be carried over
            for param in ["page", "per_page"]:
                query_params.pop(param, None)

            # Ensure nav_token is present (it should be from original request)
            # If it's not, navigation will just be disabled (graceful degradation)

            # Add query string if there are parameters
            if query_params:
                query_string = query_params.urlencode()
                separator = "&" if "?" in base_url else "?"
                return f"{base_url}{separator}{query_string}"

            return base_url
        except self.model.DoesNotExist:
            logger.warning("Object with pk=%s does not exist", pk)
            return None

    def get_context_data(self, **kwargs):
        """Add navigation context to the template."""
        context = super().get_context_data(**kwargs)

        if not self.navigation_enabled:
            return context

        next_pk = self.get_next_pk()
        previous_pk = self.get_previous_pk()
        current_index, total_count = self.get_current_position()

        # Consolidate all navigation data into a single context variable
        context["save_and_next"] = {
            "enabled": True,
            "form_id": self.navigation_form_id,
            "close_url": self.get_close_url(),
            "next": {
                "pk": next_pk,
                "url": self.get_navigation_url(next_pk),
                "available": next_pk is not None,
            },
            "previous": {
                "pk": previous_pk,
                "url": self.get_navigation_url(previous_pk),
                "available": previous_pk is not None,
            },
            "position": {
                "current": current_index + 1
                if current_index is not None
                else None,  # 1-indexed
                "total": total_count,
            }
            if current_index is not None
            else None,
        }

        return context

    def form_valid(self, form):
        """Handle save and next functionality."""
        response = super().form_valid(form)

        if not self.navigation_enabled:
            return response

        # Check which save action was selected
        # The button sets its name attribute based on the selected action
        if "save_and_next" in self.request.POST:
            next_url = self.get_navigation_url(self.get_next_pk())
            if next_url:
                return redirect(next_url)
        elif "save_and_previous" in self.request.POST:
            previous_url = self.get_navigation_url(self.get_previous_pk())
            if previous_url:
                return redirect(previous_url)
        elif "save_and_continue" in self.request.POST:
            # Stay on the same page (just refresh)
            return redirect(self.request.path)
        elif "save_and_close" in self.request.POST:
            # Redirect to the list view or a custom close URL
            close_url = self.get_close_url()
            if close_url:
                return redirect(close_url)

        return response

    def get_close_url(self):
        """
        Get the URL to redirect to when "Save & Close" is clicked.

        Returns the URL that originally set the navigation PKs (the list view),
        or falls back to 'next' parameter or model's list view.
        """
        # First try to get the referrer URL from navigation data
        nav_data = self.get_navigation_data()
        referrer_url = nav_data.get("referrer_url")
        if referrer_url:
            return referrer_url

        # Check for 'next' parameter in GET or POST
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url

        # Try to construct a list URL based on model name
        # This is a convention - adjust as needed for your project
        try:
            model_name = self.model._meta.model_name
            app_label = self.model._meta.app_label
            list_url_name = f"{app_label}:{model_name}_list"
            return reverse(list_url_name)
        except Exception:
            pass

        # Fallback to root
        return "/"


class NavigationStorageMixin:
    """
    Mixin for table views that stores navigation data for SaveAndNext.

    This mixin automatically stores PKs from the filtered queryset in the session
    using a unique navigation token (UUID). The token is passed to edit views via
    query parameters, eliminating the need for complex scope key logic.

    Configuration:
        - enable_navigation_storage: Enable/disable storing PKs (default: True)
        - navigation_max_pk_count: Max PKs to store (default from settings)
        - navigation_context_window: PKs to include before/after when limiting
        - navigation_token_length: Length of navigation token (default: 16 chars)

    Usage:
        # Basic usage - works automatically with any filtered queryset
        class MyTableView(NavigationStorageMixin, FilterView):
            model = MyModel
            navigation_max_pk_count = 100

        # The mixin generates a unique token and adds it to template context
        # Templates automatically include the token in edit URLs:
        # <a href="{{ record.get_absolute_url }}?nav_token={{ nav_token }}">Edit</a>
    """

    enable_navigation_storage = True
    navigation_max_pk_count = None
    navigation_context_window = None
    navigation_token_length = 16  # UUID substring length

    def get_navigation_max_pk_count(self):
        """Get the maximum number of PKs to store in session."""
        if self.navigation_max_pk_count is not None:
            return self.navigation_max_pk_count
        return conf.NAVIGATION_MAX_PK_COUNT

    def get_navigation_context_window(self):
        """Get the number of PKs to include before/after current PK."""
        if self.navigation_context_window is not None:
            return self.navigation_context_window
        return conf.NAVIGATION_CONTEXT_WINDOW

    def get_or_create_navigation_token(self):
        """
        Get existing navigation token from request or generate a new one.

        The token is a short UUID that uniquely identifies this navigation context.
        It's generated once per table view render and passed to edit views via URL.
        """
        if getattr(self, "_nav_token", None):
            return self._nav_token
        # Check if token already exists in query params (e.g., returning from edit view)
        nav_token = self.request.GET.get("nav_token")
        if nav_token:
            # Validate token exists in session
            session_key = self.get_navigation_session_key(nav_token)
            if session_key in self.request.session:
                return nav_token

        # Generate new token
        self._nav_token = uuid.uuid4().hex[: self.navigation_token_length]
        return self._nav_token

    def get_navigation_session_key(self, nav_token=None):
        """
        Get the session key for storing navigation data.

        Args:
            nav_token: Navigation token (UUID). If None, must be provided later.
        """
        if nav_token:
            return f"{conf.NAVIGATION_SESSION_KEY_PREFIX}token_{nav_token}"
        # This shouldn't be called without a token, but provide a fallback
        return f"{conf.NAVIGATION_SESSION_KEY_PREFIX}token_default"

    def limit_pks_around_current(self, all_pks, current_pk=None):
        """
        Limit PKs to a window around the current PK.

        If current_pk is in the list, keep context_window PKs before and after.
        Otherwise, keep the first navigation_max_pk_count PKs.
        """
        max_count = self.get_navigation_max_pk_count()

        # If max is 0 or None, don't limit
        if not max_count:
            return all_pks

        # If we're already under the limit, return all
        if len(all_pks) <= max_count:
            return all_pks

        # If no current PK, just take the first max_count
        if current_pk is None:
            return all_pks[:max_count]

        # Try to center around current_pk
        try:
            current_index = all_pks.index(current_pk)
            context_window = self.get_navigation_context_window()

            # Calculate slice boundaries
            start = max(0, current_index - context_window)
            end = min(len(all_pks), current_index + context_window + 1)

            # Ensure we don't exceed max_count
            window_size = end - start
            if window_size > max_count:
                # Prefer keeping more items after current
                end = start + max_count

            return all_pks[start:end]
        except ValueError:
            # current_pk not in list, take first max_count
            return all_pks[:max_count]

    def cleanup_expired_navigation_data(self, force=False):
        """
        Remove expired navigation data from session to prevent accumulation.

        This is important for views with scoped navigation where users might
        visit many different contexts (e.g., 100 different orders) in a session.
        Without cleanup, old navigation data accumulates and wastes session storage.

        Cleanup only runs when:
        - force=True, OR
        - Number of contexts >= NAVIGATION_MAX_CONTEXTS (lazy cleanup)

        Two cleanup strategies:
        1. Remove expired contexts (older than NAVIGATION_SESSION_TIMEOUT)
        2. Enforce max context limit (NAVIGATION_MAX_CONTEXTS) using LRU eviction

        Args:
            force: If True, always run cleanup. If False, only run when at limit.
        """
        prefix = conf.NAVIGATION_SESSION_KEY_PREFIX
        current_time = time.time()

        # Collect all navigation contexts with their timestamps
        nav_contexts = []
        for key in list(self.request.session.keys()):
            if key.startswith(prefix):
                nav_data = self.request.session.get(key, {})
                if nav_data:
                    timestamp = nav_data.get("timestamp", 0)
                    nav_contexts.append((key, timestamp))

        # Only run cleanup if we're at/near the limit (unless forced)
        max_contexts = conf.NAVIGATION_MAX_CONTEXTS
        if not force and (max_contexts == 0 or len(nav_contexts) < max_contexts):
            return  # Skip cleanup - we're under the limit

        # Strategy 1: Remove expired contexts
        expired_count = 0
        for key, timestamp in nav_contexts[:]:
            age = current_time - timestamp
            if age > conf.NAVIGATION_SESSION_TIMEOUT:
                del self.request.session[key]
                nav_contexts.remove((key, timestamp))
                expired_count += 1

        if expired_count > 0:
            logger.debug("Cleaned up %d expired navigation contexts", expired_count)

        # Strategy 2: Enforce max contexts limit (LRU eviction)
        if max_contexts > 0 and len(nav_contexts) >= max_contexts:
            # Sort by timestamp (oldest first)
            nav_contexts.sort(key=lambda x: x[1])

            # Remove oldest contexts to make room
            num_to_remove = (
                len(nav_contexts) - max_contexts + 1
            )  # +1 for the new one we're about to add
            removed_count = 0
            for key, _ in nav_contexts[:num_to_remove]:
                del self.request.session[key]
                removed_count += 1

            if removed_count > 0:
                logger.debug(
                    "Removed %d oldest navigation contexts (limit: %d)",
                    removed_count,
                    max_contexts,
                )

    def store_navigation_pks(self, pks, nav_token, current_pk=None):
        """
        Store PKs in session for navigation.

        Args:
            pks: List of PKs from the queryset
            nav_token: Navigation token (UUID) to use as session key
            current_pk: Optional current PK to center the window around
        """
        if not self.enable_navigation_storage:
            return

        # Lazy cleanup: only runs when we're at/near the limit
        self.cleanup_expired_navigation_data()

        # Limit PKs if needed
        limited_pks = self.limit_pks_around_current(list(pks), current_pk)

        session_key = self.get_navigation_session_key(nav_token)
        nav_data = {
            "pks": limited_pks,
            "timestamp": time.time(),
            "total_count": len(pks),  # Store original count for reference
            "limited": len(limited_pks) < len(pks),
            "referrer_url": self.request.build_absolute_uri(),  # Store the URL that set the PKs
        }

        self.request.session[session_key] = nav_data
        self.request.session.save()
        logger.debug(
            "Stored %d PKs (of %d total) in session key '%s'",
            len(limited_pks),
            len(pks),
            session_key,
        )

    def get_table_kwargs(self):
        """Add navigation token to table kwargs so it's accessible in table templates."""
        kwargs = super().get_table_kwargs()

        if self.enable_navigation_storage:
            # Generate or retrieve navigation token
            nav_token = self.get_or_create_navigation_token()
            kwargs["nav_token"] = nav_token
        return kwargs

    def get_context_data(self, **kwargs):
        """Add navigation token and PKs to context and store in session."""
        context = super().get_context_data(**kwargs)

        if not self.enable_navigation_storage:
            return context

        # Get PKs from the current page/queryset
        if hasattr(self, "object_list") and self.object_list is not None:
            # Generate or retrieve navigation token
            nav_token = self.get_or_create_navigation_token()

            pks = list(self.object_list.values_list("pk", flat=True))

            # Store in session with token
            self.store_navigation_pks(pks, nav_token)

        return context


class ActiveFilterMixin:
    """Mixin to add active filter context to views using django-filter"""

    show_filter_badges: bool | None = None
    default_show_filter_badges = True

    def get_active_filters(self, filter_instance):
        """Extract active filters from a django-filter instance, including date ranges"""
        active_filters = []

        if not filter_instance.form.is_bound:
            return active_filters

        for field_name, field in filter_instance.form.fields.items():
            if field_name == "search":
                continue

            value = filter_instance.form.cleaned_data.get(field_name)
            if not value:
                continue

            # Handle date range (list, tuple, or slice)
            if (isinstance(value, (list, tuple)) and len(value) == 2) or isinstance(
                value, slice
            ):
                if isinstance(value, slice):
                    start, end = value.start, value.stop
                else:
                    start, end = value

                # Remove time portion if value is datetime
                def format_date(val):
                    if hasattr(val, "date"):
                        return val.date().isoformat()
                    return str(val)

                # Try to guess parameter names for clearing
                clear_params = []
                # Django-filter usually uses field_name + '_after' and '_before' for DateFromToRangeFilter
                for suffix, v in zip(["_min", "_max"], [start, end]):
                    if v:
                        clear_params.append(f"{field_name}{suffix}")

                if start or end:
                    display_value = ""
                    if start and end:
                        display_value = f"{format_date(start)} – {format_date(end)}"
                    elif start:
                        display_value = f"From {format_date(start)}"
                    elif end:
                        display_value = f"Until {format_date(end)}"
                    clear_url = self.build_clear_url(clear_params)
                    active_filters.append(
                        {
                            "name": field_name,
                            "label": field.label
                            or field_name.replace("_", " ").title(),
                            "value": value,
                            "display_value": display_value,
                            "clear_params": clear_params,
                            "clear_url": clear_url,
                        }
                    )
                continue

            # Handle normal fields
            active_filters.append(
                {
                    "name": field_name,
                    "label": field.label or field_name.replace("_", " ").title(),
                    "value": value,
                    "display_value": str(value),
                }
            )

        # Handle search field separately
        search_value = filter_instance.form.cleaned_data.get("search")
        if search_value:
            active_filters.append(
                {
                    "name": "search",
                    "label": "Search",
                    "value": search_value,
                    "display_value": f'"{search_value}"',
                }
            )

        return active_filters

    def build_clear_url(self, clear_params):
        """Return a URL with the given params removed from the current querystring."""
        request = self.request  # assumes self.request is available
        params = request.GET.copy()
        for key in clear_params:
            params.pop(key, None)
        base_path = request.path
        query = params.urlencode()
        return f"{base_path}?{query}" if query else base_path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_filter_badges"] = self.get_show_filter_badges()
        # Look for filter in context
        filter_instance = context.get("filter")
        if filter_instance:
            context["active_filters"] = self.get_active_filters(filter_instance)
        return context

    def get_show_filter_badges(self, value: bool | None = None) -> bool:
        """
        Determines if the filter badges should be shown.

        Priority order:
        1. 'show_filter_badges' query parameter (e.g., ?show_filter_badges=true)
        2. value method argument if provided
        2. View's show_filter_badges attribute
        3. default_show_filter_badges attribute

        Returns: bool: True if the links should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_filter_badges")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]

        if value is not None:
            return value

        if self.show_filter_badges is not None:
            return self.show_filter_badges

        return self.default_show_filter_badges


class BulkActionViewMixin:
    """
    Mixin for views that handle bulk actions. Provides methods for bulk delete.

    Attributes:
        delete_method: Optional method that handles deletion of individual objects
        bulk_delete_hx_trigger (str|dict): HX-Trigger value for bulk delete responses.
            Can be a string for simple events or dict for events with details.
            Default: 'bulkDeleteComplete'

    Usage:
        # Basic usage with default trigger
        class MyListView(BulkActionViewMixin, ListView):
            model = MyModel
            delete_method = services.object_delete

            def post(self, request, *args, **kwargs):
                return self.handle_bulk_action(request)

        # Custom single event trigger
        class MyListView(BulkActionViewMixin, ListView):
            model = MyModel
            bulk_delete_hx_trigger = 'myCustomEvent'

        # Multiple events with details
        class MyListView(BulkActionViewMixin, ListView):
            model = MyModel
            bulk_delete_hx_trigger = {
                'itemsDeleted': {'count': 5},
                'updateSidebar': {},
                'showNotification': {'message': 'Items deleted successfully'}
            }

        # Dynamic trigger based on runtime conditions
        class MyListView(BulkActionViewMixin, ListView):
            model = MyModel

            def get_bulk_delete_hx_trigger(self):
                # Return different triggers based on conditions
                if some_condition:
                    return 'specialEvent'
                return {'standardEvent': {}, 'refreshTable': {}}
    """

    delete_method = None  # Set this to the method that handles deletion
    bulk_delete_hx_trigger = "bulkDeleteComplete"  # Default HX-Trigger event

    def get_bulk_delete_hx_trigger(self):
        """
        Get the HX-Trigger value for bulk delete responses.

        Can be overridden in subclasses to provide dynamic trigger values.

        Returns:
            str or dict: HX-Trigger value. Can be:
                - Simple string: 'eventName'
                - JSON dict: {'event1': {}, 'event2': {'detail': 'value'}}
        """
        if isinstance(self.bulk_delete_hx_trigger, dict):
            return json.dumps(self.bulk_delete_hx_trigger)
        return self.bulk_delete_hx_trigger

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = self.request.GET.get("next", self.request.path)
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for bulk actions.
        This method checks for selected items and performs the appropriate bulk action.
        """
        if "bulk_action" in request.POST:
            logger.info("Handling bulk action POST request")
            return self.handle_bulk_action(request)
        logger.debug("No bulk action found in POST, passing to super()")
        return super().post(request, *args, **kwargs)

    def handle_bulk_action(self, request):
        """Handle bulk action POST requests."""
        selected_items = request.POST.getlist("selected_items")
        if not selected_items:
            messages.error(request, "No items were selected.")
            return self.get(request)
        # Handle bulk delete
        if "selected_items" in request.POST:
            return self.handle_bulk_delete(request, selected_items)

        return self.get(request)

    def handle_bulk_delete(self, request, selected_items):
        """Handle bulk delete action."""
        if self.delete_method:
            return self._delete_with_custom_method(request, selected_items)
        try:
            # Get the model from the view
            model = getattr(self, "model", None)
            if not model:
                raise ValueError("Model not specified")
            # Delete selected items
            deleted_count, _ = model.objects.filter(pk__in=selected_items).delete()
            if deleted_count > 0:
                messages.warning(
                    request,
                    f"Successfully deleted {deleted_count} {model._meta.verbose_name}(s).",
                )
            else:
                messages.warning(request, "No items were deleted.")
        except Exception as e:
            messages.error(request, f"Error deleting items: {str(e)}")

        # For HTMX requests, return the updated table view
        if request.htmx:
            response = self.get(request)
            # hx_trigger = self.get_bulk_delete_hx_trigger()
            response["HX-Trigger"] = self.get_bulk_delete_hx_trigger()
            # Handle both string and dict trigger values
            # if isinstance(hx_trigger, dict):
            #     response['HX-Trigger'] = json.dumps(hx_trigger)
            # else:
            #     response['HX-Trigger'] = hx_trigger
            return response

        # Redirect to the same page to prevent re-submission
        return redirect(self.get_success_url())

    def _delete_with_custom_method(self, request, selected_items):
        """Handle bulk delete action."""

        try:
            # Get the model from the view
            model = getattr(self, "model", None)
            if not model:
                raise ValueError("Model not specified")
            # Delete selected items
            deleted_count = 0
            for object in model.objects.filter(pk__in=selected_items):
                self.delete_method(object)
                deleted_count += 1
            # deleted_count, _ = model.objects.filter(pk__in=selected_items).delete()
            if deleted_count > 0:
                messages.warning(
                    request,
                    f"Successfully deleted {deleted_count} {model._meta.verbose_name}(s).",
                )
            else:
                messages.warning(request, "No items were deleted.")
        except Exception as e:
            logger.exception("Error during bulk delete: %s", e)
            messages.error(request, f"Error deleting items: {str(e)}")

        # For HTMX requests, return the updated table view
        if request.htmx:
            response = self.get(request)
            hx_trigger = self.get_bulk_delete_hx_trigger()
            # Handle both string and dict trigger values
            if isinstance(hx_trigger, dict):
                response["HX-Trigger"] = json.dumps(hx_trigger)
            else:
                response["HX-Trigger"] = hx_trigger
            return response

        # Redirect to the same page to prevent re-submission
        return redirect(self.get_success_url())


class ReportableViewMixin:
    """
    Mixin to add report saving/loading functionality to FilterViews
    """

    show_reports: bool | None = None
    default_show_reports: bool = True

    def get_context_data(self, **kwargs):
        # Lazy import to avoid circular imports
        from better_django_tables import forms

        context = super().get_context_data(**kwargs)
        context["available_reports"] = self.get_available_reports()
        context["current_filters"] = self.get_current_filter_params()
        context["save_report_form"] = forms.ReportSaveForm(
            initial={
                "view_name": self.request.resolver_match.view_name,
                "filter_params": self.get_current_filter_params(),
            }
        )
        context["show_reports"] = self.get_show_reports()
        return context

    def get_available_reports(self):
        """Get reports available to current user for this view"""
        # Lazy import to avoid circular imports
        from better_django_tables import models

        view_name = self.request.resolver_match.view_name
        user = self.request.user

        # Build a single query with Q objects instead of combining QuerySets
        query = Q()

        # Personal reports
        query |= Q(
            view_name=view_name, visibility="personal", created_by=user, is_active=True
        )

        # Global reports
        query |= Q(view_name=view_name, visibility="global", is_active=True)

        # Group-based reports
        user_groups = user.groups.all()
        if user_groups.exists():
            query |= Q(
                view_name=view_name,
                visibility="group",  # Change to 'group' if you updated the model
                allowed_groups__in=user_groups,
                is_active=True,
            )

        # Get all reports in one query
        all_reports = models.Report.objects.filter(query).distinct().order_by("name")

        # Add favorite status
        favorite_report_ids = models.ReportFavorite.objects.filter(
            user=user, report__in=all_reports
        ).values_list("report_id", flat=True)

        # Convert to list and add is_favorite attribute
        reports_list = list(all_reports)
        for report in reports_list:
            report.is_favorite = report.id in favorite_report_ids

        return reports_list

    def get_current_filter_params(self):
        """Extract current filter parameters from request"""
        # Remove pagination and other non-filter params
        excluded_params = ["page", "per_page", "export", "csrfmiddlewaretoken"]
        return {
            key: value
            for key, value in self.request.GET.items()
            if key not in excluded_params and value
        }

    def post(self, request, *args, **kwargs):
        """Handle report saving and other POST actions"""
        if "save_report" in request.POST:
            return self.handle_save_report(request)
        elif "toggle_favorite" in request.POST:
            return self.handle_toggle_favorite(request)
        return super().post(request, *args, **kwargs)

    def handle_save_report(self, request):
        """Save a new report"""
        # Lazy import to avoid circular imports
        from better_django_tables import forms

        form = forms.ReportSaveForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()

            # Handle group assignments for group-based reports
            if report.visibility == "group":
                groups = form.cleaned_data.get("allowed_groups", [])
                report.allowed_groups.set(groups)

            messages.success(request, f'Report "{report.name}" saved successfully.')
        else:
            messages.error(request, "Error saving report. Please check the form.")

        return redirect(request.path)

    def handle_toggle_favorite(self, request):
        """Toggle favorite status for a report"""
        # Lazy import to avoid circular imports
        from better_django_tables import models

        report_id = request.POST.get("report_id")
        try:
            report = models.Report.objects.get(id=report_id)
            favorite, created = models.ReportFavorite.objects.get_or_create(
                user=request.user, report=report
            )
            if not created:
                favorite.delete()
                messages.success(request, f'Removed "{report.name}" from favorites.')
            else:
                messages.success(request, f'Added "{report.name}" to favorites.')
        except models.Report.DoesNotExist:
            messages.error(request, "Report not found.")

        return redirect(request.path)

    def get_show_reports(self, value: bool | None = None) -> bool:
        """
        Determines if the reports section should be shown.

        Priority order:
        1. 'show_reports' query parameter (e.g., ?show_reports=true)
        2. value method argument if provided
        2. View's show_reports attribute if it exists
        3. Default to True

        Returns: bool: True if the reports section should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_reports")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]

        if value is not None:
            return value

        if hasattr(self, "show_reports") and self.show_reports is not None:
            return self.show_reports

        return self.default_show_reports


class BetterMultiTableMixin(TableMixinBase):
    """
    Mixin for views that need to display multiple tables on the same page.
    This mixin allows you to define multiple tables with their own data and
    configurations, and it will handle rendering them in the context of the view.
    Usage:
        class MyMultiTableView(BetterMultiTableMixin, TemplateView):
            template_name = 'my_template.html'
            tables = [
                {
                    'context_name': 'table1',
                    'table_class': MyTableClass1,
                    'table_kwargs': {'some_kwarg': 'value'},  # Optional kwargs for the table
                },
                {
                    'context_name': 'table2',
                    'table_class': MyTableClass2,
                    'table_kwargs': {'another_kwarg': 'value'},
                },
            ]
            tables_data = [data_for_table1, data_for_table2]

    """

    tables: list[dict] = None
    tables_data = None
    include_delete_modal = None  # Set to True if any table is deletable
    table_prefix = "table_{}-"

    # override context table name to make sense in a multiple table context
    context_table_name = "tables"

    def get_tables(self):
        """
        Return an array of table instances containing data.
        """
        if self.tables is None:
            view_name = type(self).__name__
            raise ImproperlyConfigured(
                f"No tables were specified. Define {view_name}.tables"
            )
        data = self.get_tables_data()

        if data is None:
            return self.tables

        if len(data) != len(self.tables):
            view_name = type(self).__name__
            raise ImproperlyConfigured(
                f"len({view_name}.tables_data) != len({view_name}.tables)"
            )

        for i, table in enumerate(self.tables):
            table_kwargs = table.get("table_kwargs", {})  # <-- support per-table kwargs
            table["table"] = table["table_class"](data[i], **table_kwargs)
        return self.tables

    def get_tables_data(self):
        """
        Return an array of table_data that should be used to populate each table
        """
        return self.tables_data

    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        tables = self.get_tables()

        # apply prefixes and execute requestConfig for each table
        table_counter = count()
        context["tables"] = []
        for table in tables:
            table["table"].prefix = table["table"].prefix or self.table_prefix.format(
                next(table_counter)
            )

            RequestConfig(
                self.request, paginate=self.get_table_pagination(table["table"])
            ).configure(table["table"])

            context[table["context_name"]] = table["table"]
            context["tables"].append(
                {
                    "title": table["context_name"],
                    "table": table["table"],
                }
            )
            table_class = table.get("table_class", None)
            if (
                getattr(table_class, "is_deletable_table", None)
                and self.include_delete_modal is None
            ):
                self.include_delete_modal = True
        context["include_delete_modal"] = self.include_delete_modal
        return context


# class ExcludeColumnsMixin:
#     """
#     Mixin to exclude columns from a table based on 'excludeColumns' query parameter.
#     Usage:
#         class MyTableView(ExcludeColumnsMixin, SingleTableMixin, FilterView):
#             model = MyModel
#             table_class = MyTable
#     """
#     param_key: str = 'excludeColumns'

#     def get_table_kwargs(self):
#         kwargs = super().get_table_kwargs()
#         exclude_columns_params = self.request.GET.get(self.param_key, '').split(',')
#         exclude_columns_params = [param.strip() for param in exclude_columns_params if param]  # Remove empty strings
#         if exclude_columns_params:
#             exclude = kwargs.get('exclude', [])
#             exclude.extend(exclude_columns_params)
#             kwargs['exclude'] = exclude
#         return kwargs


class SelectColumnsViewMixin:
    """
    Mixin to select or exclude columns from a table based on 'excludeColumns' or
    'cols' query parameter.

    The mixin supports two modes:
    1. Exclude mode (?excludeColumns=col1,col2) - Hide specific columns
    2. Select mode (?cols=col1,col2) - Show only specific columns

    Usage:
        class MyTableView(SelectColumnsViewMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable

        # URLs:
        # /my-view/?excludeColumns=id,created_at  -> Hide id and created_at columns
        # /my-view/?cols=name,status              -> Show only name and status columns
    """

    exclude_param_key: str = "excludeColumns"
    select_param_key: str = "cols"

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        exclude_columns_params = self.get_exclude_columns()
        select_columns_params = self.get_select_columns()

        # Ensure both parameters aren't used simultaneously
        if select_columns_params and exclude_columns_params:
            raise ImproperlyConfigured(
                f"Cannot use both '{self.exclude_param_key}' and '{self.select_param_key}' "
                "parameters simultaneously."
            )

        # Handle exclude mode
        if exclude_columns_params:
            exclude = kwargs.get("exclude", [])
            exclude.extend(exclude_columns_params)
            kwargs["exclude"] = exclude

        # Handle select mode - delegate to separate method
        elif select_columns_params:
            exclude_columns = self.create_exclude_columns_from_select()
            exclude = kwargs.get("exclude", [])
            exclude.extend(exclude_columns)
            kwargs["exclude"] = exclude

        return kwargs

    def get_exclude_columns(self):
        """Parse and return list of columns to exclude from query params"""
        exclude_columns_params = self.request.GET.get(self.exclude_param_key, "").split(
            ","
        )
        return [param.strip() for param in exclude_columns_params if param.strip()]

    def get_select_columns(self):
        """Parse and return list of columns to show from query params"""
        select_columns_params = self.request.GET.get(self.select_param_key, "").split(
            ","
        )
        return [param.strip() for param in select_columns_params if param.strip()]

    def create_exclude_columns_from_select(self):
        """
        Create an exclude list based on the select columns parameter.

        This method converts a positive selection (show these columns) into
        an exclusion list (hide everything except these columns).

        Returns:
            list: Column names to exclude

        Example:
            If table has columns: ['id', 'name', 'price', 'stock', 'created_at']
            And ?cols=name,price is specified
            Returns: ['id', 'stock', 'created_at']
        """
        select_columns_params = self.get_select_columns()
        if not select_columns_params:
            return []

        # Get all available columns from the table class
        table_class = self.get_table_class()
        all_columns = set(table_class.base_columns.keys())
        selected_columns = set(select_columns_params)

        # Calculate columns to exclude (everything not selected)
        exclude_columns = list(all_columns - selected_columns)
        return exclude_columns


# class CreateViewMixin:
#     """
#     Base mixin for views that provides standard functions for all views.
#     """
#     create_url: str = None
#     create_url_label: str = 'New Record'

#     def get_context_data(self, **kwargs: any) -> dict[str, any]:
#         context = super().get_context_data(**kwargs)
#         if self.create_url is None:
#             warnings.warn(
#                 f"{self.__class__.__name__}: 'create_url' is None. "
#                 "Set 'create_url' or set create_url=False to suppress this warning.",
#                 stacklevel=2
#             )
#         context['create_url'] = self.create_url
#         context['create_url_label'] = self.create_url_label
#         return context


# class BootstrapTableMixin:
#     """
#     Mixin to apply Bootstrap classes to django-tables2 tables.
#     This mixin should be used with django-tables2 Table classes.
#     """
#     table_classes = "table table-sm"

#     def get_table_kwargs(self):
#         kwargs = super().get_table_kwargs()
#         attrs = kwargs.get('attrs', {}).copy()
#         print(f'Pre attributes: {attrs}')  # Debug
#         existing_classes = attrs.get('class', '')
#         print(f'Existing classes: {existing_classes}')
#         # Add 'bulk-actions-table' without removing existing classes
#         attrs['class'] = f"{existing_classes} bulk-actions-table".strip()
#         print(f'Updated attributes: {attrs}')  # Debug
#         kwargs['attrs'] = attrs
#         return kwargs


class PerPageViewMixin:
    """
    Mixin to add per-page selection functionality to table views.

    This mixin allows users to select how many records to display per page.
    The selection is saved in the session and persists across requests.
    Works with HTMX requests for dynamic updates.

    Attributes:
        per_page_options (list): List of available per-page options. Default: [10, 25, 50, 100, 500, 1000]
        default_per_page (int): Default number of records per page if no preference is set. Default: 25
        per_page_session_key (str): Session key to store the per-page preference. Default: 'table_per_page'

    Usage:
        class MyTableView(PerPageViewMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25
    """

    per_page_options = [10, 25, 50, 100, 500, 1000]
    default_per_page = 25
    per_page_session_key: str | None = None
    default_per_page_session_key = "table_per_page"
    paginate_by: int | None
    show_per_page_selector: bool | None = None
    default_show_per_page_selector: bool = True

    def get_paginate_by(self, table_data):
        """
        Get the number of items to display per page.

        Priority order:
        1. 'per_page' query parameter (e.g., ?per_page=50)
        2. Session-stored preference
        3. View's paginate_by attribute
        4. default_per_page attribute

        Also saves the selection to the session for future requests.

        Args:
            table_data: The queryset or table data (required by django-tables2)
        """
        # Check for per_page in query parameters (GET or POST for HTMX)
        per_page = self.request.GET.get("per_page") or self.request.POST.get("per_page")

        if per_page:
            try:
                per_page = int(per_page)
                # Validate it's in the allowed options
                if per_page in self.per_page_options:
                    # Save to session
                    self.request.session[self.get_per_page_session_key()] = per_page
                    return per_page
            except (ValueError, TypeError):
                pass
        # Check session for saved preference
        session_per_page = self.request.session.get(self.get_per_page_session_key())
        if session_per_page and session_per_page in self.per_page_options:
            return session_per_page

        # Fall back to view's paginate_by attribute if set
        if hasattr(self, "paginate_by") and self.paginate_by:
            return self.paginate_by

        # Finally, use default_per_page
        return self.default_per_page

    def get_per_page_session_key(self, view_name: str | None = None) -> str:
        """Return the session key used to store per-page preference."""
        try:
            # Try to build a unique key based on view name and table name
            if not view_name:
                view_name = self.request.resolver_match.view_name
            table_name = self.get_table_class().__name__
            return f"per_page_{table_name}_{view_name}"
        except Exception:
            logger.warning(
                "Could not determine unique per_page_session_key, using default."
            )
            # Fallback to the default key if any error occurs
            pass
        if self.per_page_session_key:
            return self.per_page_session_key

        return self.default_per_page_session_key

    def get_show_per_page_selector(self, value: bool | None = None) -> bool:
        """
        Determines if the per-page selector should be shown

        Priority order:
        1. 'show_per_page_selector' query parameter (e.g., ?show_per_page_selector=true)
        2. value method argument if provided
        3. View's show_per_page_selector attribute
        4. default_show_per_page_selector attribute

        Returns: bool: True if the selector should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_per_page_selector")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]

        if value is not None:
            return value

        if self.show_per_page_selector is not None:
            return self.show_per_page_selector

        return self.default_show_per_page_selector

    def get_context_data(self, **kwargs):
        """Add per_page options to context for template use."""
        context = super().get_context_data(**kwargs)
        context["per_page_options"] = self.per_page_options
        context["current_per_page"] = self.get_paginate_by(self.get_queryset())
        context["show_per_page_selector"] = self.get_show_per_page_selector()
        return context


class ShowFilterMixin:
    """
    Mixin to control the display of the filter sidebar in table views.

    Attributes:
        show_filter (bool): Whether to show the filter sidebar. Default: True

    Usage:
        class MyTableView(ShowFilterMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            show_filter = True  # or False to hide
    """

    show_filter: bool = True
    toggle_filter: bool = True

    def get_show_filter(self, value: bool | None = None) -> bool:
        """
        Determines if the filter sidebar should be shown.

        Priority order:
        1. 'show_filter' query parameter (e.g., ?show_filter=true)
        2. method argument 'value' if provided
        3. View's show_filter attribute

        Returns: bool: True if the filter should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_filter")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]
        if value is not None:
            return value
        return self.show_filter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_filter"] = self.get_show_filter()
        context["toggle_filter"] = self.get_toggle_filter()
        return context

    def get_toggle_filter(self):
        """
        Get the context boolean for toggling the filter sidebar.
        Save the preference in session.
        """
        session_key = self.get_toggle_filter_session_key()
        toggle = self.request.GET.get("toggle_filter")
        if toggle is not None:
            toggle_value = toggle.lower() in ["1", "true", "yes"]
            self.request.session[session_key] = toggle_value
            return toggle_value

        session_value = self.request.session.get(session_key)
        if session_value is not None:
            logger.debug(
                f"Using session value ({session_value}) from key: {session_key}"
            )
            return session_value

        return self.toggle_filter

    def get_toggle_filter_session_key(self, view_name: str | None = None) -> str:
        """Return the session key used to store toggle_filter preference."""
        try:
            # Try to build a unique key based on view name and table name
            if not view_name:
                view_name = self.request.resolver_match.view_name
            return f"toggle_filter__{view_name}"
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "Could not determine unique toggle_filter_session_key, using default."
            )
            # Fallback to the default key if any error occurs

        return f"toggle_filter__{self.__class__.__name__}"

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to toggle the filter sidebar.
        """
        if "toggle_filter" in request.POST:
            logger.info("Handling toggle_filter POST request")
            current_state = self.get_toggle_filter()
            # Toggle the state
            new_state = not current_state
            session_key = self.get_toggle_filter_session_key()
            request.session[session_key] = new_state
            # Redirect to the same page to prevent re-submission
            logger.info(
                f"Toggling filter sidebar to {new_state}, session_key={session_key}"
            )
            return HttpResponse(status=204, headers={"Toggle-Filter": "true"})
        return super().post(request, *args, **kwargs)


class LinksMixin:
    """
    Mixin to add navigation links to the context of table views.

    Attributes:
        links (list): List of navigation links to display. Each link is a dict with 'url' and 'label'.
                      Default: None (no links)

    Usage:
        class MyTableView(LinksMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            links = [
                {
                    'url': '/some/url/',
                    'label': 'Some Link',
                    'method': 'get',  # Optional, defaults to 'get'
                    'confirm_message': 'Are you sure?',
                    'button_type': 'primary',  # defaults to btn-primary
                },
                {'url': '/another/url/', 'label': 'Another Link'},
            ]
    """

    links: list[dict] | None = None
    show_links: bool | None = None
    default_show_links: bool = True

    def get_links(self):
        """Return the list of navigation links."""
        return self.links or []

    def get_show_links(self, value: bool | None = None) -> bool:
        """
        Determines if the navigation links should be shown.

        Priority order:
        1. 'show_links' query parameter (e.g., ?show_links=true)
        2. value method argument if provided
        2. View's show_links attribute
        3. default_show_links attribute

        Returns: bool: True if the links should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_links")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]

        if value is not None:
            return value

        if self.show_links is not None:
            return self.show_links

        return self.default_show_links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["links"] = self.get_links()
        context["show_links"] = self.get_show_links()
        return context


class SearchbarMixin:
    """
    Mixin to add a search bar to the context of table views.

    Attributes:
        show_search_bar (bool): Whether to show the search bar. Default: True

    Usage:
        class MyTableView(SearchbarMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            show_search_bar = True  # or False to hide
    """

    show_search_bar: bool = True

    def get_show_search_bar(self, value: bool | None = None) -> bool:
        """
        Determines if the search bar should be shown.

        Priority order:
        1. 'show_search_bar' query parameter (e.g., ?show_search_bar=true)
        2. method argument 'value' if provided
        3. View's show_search_bar attribute

        Returns: bool: True if the search bar should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_search_bar")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]
        if value is not None:
            return value
        return self.show_search_bar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_search_bar"] = self.get_show_search_bar()
        return context


class ShowCreateButtonMixin:
    """
    Mixin to add a create button to the context of table views.

    Attributes:
        show_create_button (bool): Whether to show the create button. Default: True

    Usage:
        class MyTableView(ShowCreateButtonMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            create_url = '/path/to/create/'
            create_url_label = 'Add New'
            show_create_button = True  # or False to hide
    """

    show_create_button: bool | None = None
    default_show_create_button: bool = True

    def get_show_create_button(self, value: bool | None = None) -> bool:
        """
        Determines if the create button should be shown.

        Priority order:
        1. 'show_create_button' query parameter (e.g., ?show_create_button=true)
        2. method argument 'value' if provided
        3. View's show_create_button attribute
        4. default_show_create_button attribute

        Returns: bool: True if the create button should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_create_button")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]
        if value is not None:
            return value
        if self.show_create_button is not None:
            return self.show_create_button
        return self.default_show_create_button

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_create_button"] = self.get_show_create_button()
        return context


class ShowTableNameViewMixin:
    """
    Mixin to add the table name to the context of table views.

    Attributes:
        show_table_name (bool): Whether to show the table name. Default: True

    Usage:
        class MyTableView(ShowTableNameViewMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            show_table_name = True  # or False to hide
    """

    show_table_name: bool | None = None
    default_show_table_name: bool = True

    def get_show_table_name(self, value: bool | None = None) -> bool:
        """
        Determines if the table name should be shown.

        Priority order:
        1. 'show_table_name' query parameter (e.g., ?show_table_name=true)
        2. method argument 'value' if provided
        3. View's show_table_name attribute

        Returns: bool: True if the table name should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_table_name")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]
        if value is not None:
            return value
        if self.show_table_name is not None:
            return self.show_table_name
        return self.default_show_table_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_table_name"] = self.get_show_table_name()
        return context


class Echo:
    """
    A minimal file-like object that implements only the write method.

    Used for streaming CSV exports without buffering the entire file in memory.
    Instead of storing data in a buffer, it immediately returns the value written.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class StreamExportMixin:
    """
    Mixin to add CSV export functionality to table views with streaming support.

    This mixin allows exporting table data as CSV files using Django's StreamingHttpResponse,
    which is memory-efficient for large datasets. The export is triggered via a query parameter
    and uses the table's as_values() method to generate rows.

    Attributes:
        export_name (str): Base name for the exported file. Default: "table"
        export_trigger_param (str): Query parameter name to trigger export. Default: "_export"
        exclude_columns (tuple): Columns to exclude from export. Default: ()
        dataset_kwargs (dict|None): Additional kwargs for dataset creation. Default: None
        show_export_button (bool|None): Whether to show the export button. Default: None
        default_show_export_button (bool): Default value for showing export button. Default: True

    Usage:
        class MyTableView(StreamExportMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            export_name = "my_data"
            exclude_columns = ('actions', 'checkbox')
            show_export_button = True  # or False to hide

        # Access: /my-view/?_export=csv
    """

    export_name = "table"
    export_trigger_param = "_export"
    exclude_columns = ()
    dataset_kwargs = None
    show_export_button: bool | None = None
    default_show_export_button: bool = True

    def get_export_filename(self, export_format):
        """
        Generate the filename for the exported file.

        Args:
            export_format (str): The export format (e.g., 'csv')

        Returns:
            str: Filename in format "{export_name}.{export_format}"
        """
        return f"{self.export_name}.{export_format}"

    def get_dataset_kwargs(self):
        """
        Get additional keyword arguments for dataset creation.

        Returns:
            dict|None: Additional kwargs or None
        """
        return self.dataset_kwargs

    def get_show_export_button(self, value: bool | None = None) -> bool:
        """
        Determines if the export button should be shown.

        Priority order:
        1. 'show_export_button' query parameter (e.g., ?show_export_button=true)
        2. value method argument if provided
        3. View's show_export_button attribute
        4. default_show_export_button attribute

        Returns:
            bool: True if the export button should be shown, False otherwise.
        """
        show_param = self.request.GET.get("show_export_button")
        if show_param is not None:
            return show_param.lower() in ["1", "true", "yes"]

        if value is not None:
            return value

        if self.show_export_button is not None:
            return self.show_export_button

        return self.default_show_export_button

    def create_export(self, export_format):
        """
        Create a streaming CSV export response.

        Args:
            export_format (str): The export format (currently only 'csv' supported)

        Returns:
            StreamingHttpResponse: A streaming response with CSV data
        """
        # Get the table with all current filters/config applied
        table = self.get_table(**self.get_table_kwargs())

        # Get table data as rows (list of lists)
        rows = table.as_values(exclude_columns=self.exclude_columns)

        # Create CSV writer with streaming buffer
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        # Create streaming response
        return StreamingHttpResponse(
            (writer.writerow(row) for row in rows),
            content_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{self.get_export_filename(export_format)}"'
            },
        )

    def render_to_response(self, context, **kwargs):
        """
        Override render_to_response to handle export requests.

        If the export trigger parameter is present in the request,
        returns a CSV export instead of the normal HTML response.

        Args:
            context (dict): Template context
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: Either a CSV export or normal template response
        """
        export_format = self.request.GET.get(self.export_trigger_param, None)

        if export_format:
            return self.create_export(export_format)

        return super().render_to_response(context, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add export-related context variables for template use.

        Adds:
            exportable (bool): Always True, indicates export functionality is available
            show_export_button (bool): Whether to show the export button in the UI
        """
        context = super().get_context_data(**kwargs)
        context["exportable"] = True
        context["show_export_button"] = self.get_show_export_button()
        return context


class HtmxTableViewMixin(
    ActiveFilterMixin,
    ShowFilterMixin,
    LinksMixin,
    SearchbarMixin,
    ShowCreateButtonMixin,
    PerPageViewMixin,
    ShowTableNameViewMixin,
    ReportableViewMixin,
    StreamExportMixin,
    TemplateResponseMixin,
):
    """
    Comprehensive mixin for table views with HTMX support.

    This mixin combines multiple functionality mixins and provides HTMX-aware
    rendering with different settings for full-page vs partial table updates.

    Includes support for:
    - Active filter badges
    - Filter sidebar
    - Navigation links
    - Search bar
    - Create button
    - Per-page selector
    - Table name display
    - Report saving/loading
    - CSV export
    - HTMX partial rendering

    HTMX Behavior:
        When a request comes via HTMX (request.htmx is True), the view uses
        htmx_template_name and applies htmx-specific display settings
        (typically hiding navigation elements for cleaner partial updates).

    Attributes:
        htmx_template_name (str): Template for HTMX requests. Default: 'better_django_tables/table.html'
        htmx_show_reports (bool): Show reports in HTMX mode. Default: False
        htmx_show_per_page (bool): Show per-page selector in HTMX mode. Default: False
        htmx_show_filter_badges (bool): Show filter badges in HTMX mode. Default: False
        htmx_show_filter (bool): Show filter sidebar in HTMX mode. Default: False
        htmx_show_links (bool): Show navigation links in HTMX mode. Default: False
        htmx_show_search_bar (bool): Show search bar in HTMX mode. Default: False
        htmx_show_create_button (bool): Show create button in HTMX mode. Default: False
        htmx_show_per_page_selector (bool): Show per-page selector in HTMX mode. Default: True
        htmx_show_table_name (bool): Show table name in HTMX mode. Default: False
        htmx_show_export_button (bool): Show export button in HTMX mode. Default: False

    Usage:
        class MyTableView(HtmxTableViewMixin, SingleTableMixin, FilterView):
            model = MyModel
            table_class = MyTable
            filterset_class = MyFilter

            # Override HTMX settings if needed
            htmx_show_filter = True
            htmx_show_search_bar = True
    """

    # htmx_template_name = 'better_django_tables/tables/better_table_inline.html'
    htmx_template_name = "better_django_tables/table.html"
    htmx_show_reports = False
    htmx_show_per_page = False
    htmx_show_filter_badges = False
    htmx_show_filter = False
    htmx_show_links = False
    htmx_show_search_bar = False
    htmx_show_create_button = False
    htmx_show_per_page_selector = True
    htmx_show_table_name = False
    htmx_show_export_button = False

    def get_template_names(self):
        """
        Return a list of template names to be used for the request.

        Uses htmx_template_name for HTMX requests (partial updates),
        otherwise falls back to the default template (full page render).

        Returns:
            list: List of template name strings
        """
        if hasattr(self.request, "htmx") and self.request.htmx:
            return [self.htmx_template_name]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        """
        Add HTMX-specific context variables.

        These are used by templates to conditionally show/hide elements
        based on whether the request is an HTMX partial update.
        """
        context = super().get_context_data(**kwargs)
        context["is_htmx"] = hasattr(self.request, "htmx") and self.request.htmx
        context["htmx_show_reports"] = self.htmx_show_reports
        context["htmx_show_per_page"] = self.htmx_show_per_page
        context["htmx_show_filter_badges"] = self.htmx_show_filter_badges
        return context

    def get_show_filter(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for filter sidebar."""
        if self.request.htmx:
            return super().get_show_filter(self.htmx_show_filter)
        return super().get_show_filter(value)

    def get_show_links(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for navigation links."""
        if self.request.htmx:
            return super().get_show_links(self.htmx_show_links)
        return super().get_show_links(value)

    def get_show_filter_badges(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for filter badges."""
        if self.request.htmx:
            return super().get_show_filter_badges(self.htmx_show_filter_badges)
        return super().get_show_filter_badges(value)

    def get_show_search_bar(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for search bar."""
        if self.request.htmx:
            return super().get_show_search_bar(self.htmx_show_search_bar)
        return super().get_show_search_bar(value)

    def get_show_reports(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for reports section."""
        if self.request.htmx:
            return super().get_show_reports(self.htmx_show_reports)
        return super().get_show_reports(value)

    def get_show_create_button(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for create button."""
        if self.request.htmx:
            return super().get_show_create_button(self.htmx_show_create_button)
        return super().get_show_create_button(value)

    def get_show_per_page_selector(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for per-page selector."""
        if self.request.htmx:
            return super().get_show_per_page_selector(self.htmx_show_per_page_selector)
        return super().get_show_per_page_selector(value)

    def get_show_table_name(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for table name display."""
        if self.request.htmx:
            return super().get_show_table_name(self.htmx_show_table_name)
        return super().get_show_table_name(value)

    def get_show_export_button(self, value: bool | None = None) -> bool:
        """Apply HTMX-specific setting for export button."""
        if self.request.htmx:
            return super().get_show_export_button(self.htmx_show_export_button)
        return super().get_show_export_button(value)

    def get_per_page_session_key(self):
        """
        Override to handle HTMX requests by using the originating view's name.

        For HTMX requests, attempts to use the originating view's name from HX-Current-URL
        to ensure per-page settings persist across the parent view, not just the HTMX endpoint.
        """
        # For HTMX requests, try to get the originating view name
        if hasattr(self.request, "htmx") and self.request.htmx:
            current_url = self.request.headers.get("HX-Current-URL")
            if current_url:
                # Parse the current URL to get the path
                try:
                    parsed_url = urlparse(current_url)
                    resolved = resolve(parsed_url.path)
                    return super().get_per_page_session_key(resolved.view_name)
                    # # Temporarily override the view_name in resolver_match
                    # # This allows the parent's get_per_page_session_key to use the correct view_name
                    # original_view_name = self.request.resolver_match.view_name
                    # self.request.resolver_match.view_name = resolved.view_name
                    # try:
                    #     session_key = super().get_per_page_session_key()
                    #     return session_key
                    # finally:
                    #     # Restore original view_name
                    #     self.request.resolver_match.view_name = original_view_name
                except Exception as e:
                    logger.debug("Could not resolve HTMX current URL: %s", e)

        # Fall back to parent implementation for non-HTMX requests
        return super().get_per_page_session_key()
