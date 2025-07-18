# pylint: disable=missing-class-docstring,missing-function-docstring,too-few-public-methods
from itertools import count

from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured

from django_tables2.views import TableMixinBase
from django_tables2 import RequestConfig

from better_django_tables import models, forms


class NextViewMixin:
    """
    Base mixin for views that provides standard functions for all views.
    """

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        if next_url:
            return next_url
        return super().get_success_url()


class ActiveFilterMixin:
    """Mixin to add active filter context to views using django-filter"""

    def get_active_filters(self, filter_instance):
        """Extract active filters from a django-filter instance, including date ranges"""
        active_filters = []

        if not filter_instance.form.is_bound:
            return active_filters

        for field_name, field in filter_instance.form.fields.items():
            if field_name == 'search':
                continue

            value = filter_instance.form.cleaned_data.get(field_name)
            if not value:
                continue

            # Handle date range (list, tuple, or slice)
            if (
                (isinstance(value, (list, tuple)) and len(value) == 2)
                or isinstance(value, slice)
            ):
                if isinstance(value, slice):
                    start, end = value.start, value.stop
                else:
                    start, end = value

                # Remove time portion if value is datetime
                def format_date(val):
                    if hasattr(val, 'date'):
                        return val.date().isoformat()
                    return str(val)

                # Try to guess parameter names for clearing
                clear_params = []
                # Django-filter usually uses field_name + '_after' and '_before' for DateFromToRangeFilter
                for suffix, v in zip(['_min', '_max'], [start, end]):
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
                    active_filters.append({
                        'name': field_name,
                        'label': field.label or field_name.replace('_', ' ').title(),
                        'value': value,
                        'display_value': display_value,
                        'clear_params': clear_params,
                        'clear_url': clear_url,
                    })
                continue

            # Handle normal fields
            active_filters.append({
                'name': field_name,
                'label': field.label or field_name.replace('_', ' ').title(),
                'value': value,
                'display_value': str(value)
            })

        # Handle search field separately
        search_value = filter_instance.form.cleaned_data.get('search')
        if search_value:
            active_filters.append({
                'name': 'search',
                'label': 'Search',
                'value': search_value,
                'display_value': f'"{search_value}"'
            })

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

        # Look for filter in context
        filter_instance = context.get('filter')
        if filter_instance:
            context['active_filters'] = self.get_active_filters(filter_instance)

        return context


class BulkActionViewMixin:
    """
    Mixin for views that handle bulk actions. Provides methods for bulk delete.
    Usage:
        class MyListView(BulkActionViewMixin, ListView):
            model = MyModel

            def post(self, request, *args, **kwargs):
                return self.handle_bulk_action(request)
    """
    bulk_delete_url_name = None  # Override in your view or set as class attribute


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.bulk_delete_url_name is None:
            view_name = type(self).__name__
            raise ImproperlyConfigured(f"No bulk delete URL name specified. Define {view_name}.bulk_delete_url_name")
        context['bulk_delete_url_name'] = self.bulk_delete_url_name
        return context

    def handle_bulk_action(self, request):
        """Handle bulk action POST requests."""
        selected_items = request.POST.getlist('selected_items')
        print(f"Selected items: {selected_items}")
        if not selected_items:
            messages.error(request, "No items were selected.")
            return self.get(request)

        # Handle bulk delete
        if 'selected_items' in request.POST:
            return self.handle_bulk_delete(request, selected_items)

        return self.get(request)


    def handle_bulk_delete(self, request, selected_items):
        """Handle bulk delete action."""

        try:
            # Get the model from the view
            model = getattr(self, 'model', None)
            if not model:
                raise ValueError("Model not specified")

            # Delete selected items
            deleted_count, _ = model.objects.filter(pk__in=selected_items).delete()

            if deleted_count > 0:
                messages.success(
                    request,
                    f"Successfully deleted {deleted_count} item(s)."
                )
            else:
                messages.warning(request, "No items were deleted.")

        except Exception as e:
            messages.error(request, f"Error deleting items: {str(e)}")
            print(f"{e}")
        # Redirect to the same page to prevent re-submission
        return redirect(request.path)


class ReportableViewMixin:
    """
    Mixin to add report saving/loading functionality to FilterViews
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_reports'] = self.get_available_reports()
        context['current_filters'] = self.get_current_filter_params()
        context['save_report_form'] = forms.ReportSaveForm(
            initial={
                'view_name': self.request.resolver_match.view_name,
                'filter_params': self.get_current_filter_params()
            }
        )
        return context

    def get_available_reports(self):
        """Get reports available to current user for this view"""
        view_name = self.request.resolver_match.view_name
        user = self.request.user

        # Build a single query with Q objects instead of combining QuerySets
        query = Q()

        # Personal reports
        query |= Q(
            view_name=view_name,
            visibility='personal',
            created_by=user,
            is_active=True
        )

        # Global reports
        query |= Q(
            view_name=view_name,
            visibility='global',
            is_active=True
        )

        # Group-based reports
        user_groups = user.groups.all()
        if user_groups.exists():
            query |= Q(
                view_name=view_name,
                visibility='group',  # Change to 'group' if you updated the model
                allowed_groups__in=user_groups,
                is_active=True
            )

        # Get all reports in one query
        all_reports = models.Report.objects.filter(query).distinct().order_by('name')

        # Add favorite status
        favorite_report_ids = models.ReportFavorite.objects.filter(
            user=user,
            report__in=all_reports
        ).values_list('report_id', flat=True)

        # Convert to list and add is_favorite attribute
        reports_list = list(all_reports)
        for report in reports_list:
            report.is_favorite = report.id in favorite_report_ids

        return reports_list

    def get_current_filter_params(self):
        """Extract current filter parameters from request"""
        # Remove pagination and other non-filter params
        excluded_params = ['page', 'per_page', 'export', 'csrfmiddlewaretoken']
        return {
            key: value for key, value in self.request.GET.items()
            if key not in excluded_params and value
        }

    def post(self, request, *args, **kwargs):
        """Handle report saving and other POST actions"""
        if 'save_report' in request.POST:
            return self.handle_save_report(request)
        elif 'toggle_favorite' in request.POST:
            return self.handle_toggle_favorite(request)
        return super().post(request, *args, **kwargs)

    def handle_save_report(self, request):
        """Save a new report"""

        form = forms.ReportSaveForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()

            # Handle group assignments for group-based reports
            if report.visibility == 'group':
                groups = form.cleaned_data.get('allowed_groups', [])
                report.allowed_groups.set(groups)

            messages.success(request, f'Report "{report.name}" saved successfully.')
        else:
            messages.error(request, 'Error saving report. Please check the form.')

        return redirect(request.path)

    def handle_toggle_favorite(self, request):
        """Toggle favorite status for a report"""

        report_id = request.POST.get('report_id')
        try:
            report = models.Report.objects.get(id=report_id)
            favorite, created = models.ReportFavorite.objects.get_or_create(
                user=request.user,
                report=report
            )
            if not created:
                favorite.delete()
                messages.success(request, f'Removed "{report.name}" from favorites.')
            else:
                messages.success(request, f'Added "{report.name}" to favorites.')
        except models.Report.DoesNotExist:
            messages.error(request, 'Report not found.')

        return redirect(request.path)


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
            raise ImproperlyConfigured(f"No tables were specified. Define {view_name}.tables")
        data = self.get_tables_data()

        if data is None:
            return self.tables

        if len(data) != len(self.tables):
            view_name = type(self).__name__
            raise ImproperlyConfigured(f"len({view_name}.tables_data) != len({view_name}.tables)")

        for i, table in enumerate(self.tables):
            table_kwargs = table.get('table_kwargs', {})  # <-- support per-table kwargs
            table['table'] = table['table_class'](data[i], **table_kwargs)
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
        context['tables'] = []
        for table in tables:
            table['table'].prefix = table['table'].prefix or self.table_prefix.format(next(table_counter))

            RequestConfig(self.request, paginate=self.get_table_pagination(table['table'])).configure(table['table'])

            context[table['context_name']] = table['table']
            context['tables'].append({
                'title': table['context_name'],
                'table': table['table'],
            })
            table_class = table.get('table_class', None)
            if getattr(table_class, 'is_deletable_table', None) and self.include_delete_modal is None:
                self.include_delete_modal = True
        context['include_delete_modal'] = self.include_delete_modal
        return context


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

