from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, DeleteView
from django.http import HttpResponse
from django.template.loader import render_to_string

from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from better_django_tables.view_mixins import (
    NextViewMixin,
    ActiveFilterMixin,
    BulkActionViewMixin,
    ReportableViewMixin,
    BetterMultiTableMixin
)
from better_django_tables import models, filters, tables


class TableView(NextViewMixin, ActiveFilterMixin, BulkActionViewMixin,
                ReportableViewMixin, SingleTableMixin, FilterView):
    """
    TableView is a reusable base class for Django views that display tabular data using django-tables2 and django-filter.

    Usage:
        Subclass TableView and specify at least `table_class` and `model` or `queryset`.
        Optionally override methods or add mixins for custom behavior.

    Attributes to define in subclasses:
        table_class: The django-tables2 Table class to use for rendering.
        model: The Django model to use for the queryset (optional if queryset is provided).
        queryset: The queryset to display in the table (optional if model is provided).
        filterset_class: The django-filter FilterSet class for filtering (optional).
        template_name: The template to use for rendering the view (optional).
        bulk_delete_url_name: The URL name for bulk delete actions (optional).

    Methods to override in subclasses:
        get_queryset(self): Return the queryset for the table.
        get_table_class(self): Return the table class to use.
        get_context_data(self, **kwargs): Add extra context to the template.
        post(self, request, *args, **kwargs): Handle POST requests (bulk actions, etc).

    The `post` method is overridden to handle both report actions and bulk actions in a single endpoint.
    """

    def post(self, request, *args, **kwargs):
        # Handle report actions first
        if any(key in request.POST for key in ['save_report', 'toggle_favorite']):
            return super().post(request, *args, **kwargs)  # ReportableMixin handles this
        # Then handle bulk actions
        return self.handle_bulk_action(request)



class ReportListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = models.Report
    table_class = tables.ReportTable
    template_name = 'better_django_tables/tables/table_view.html'
    filterset_class = filters.ReportFilter

    def get_queryset(self):
        user = self.request.user

        # Get all reports the user can access
        personal_reports = models.Report.objects.filter(
            visibility='personal',
            created_by=user
        )
        global_reports = models.Report.objects.filter(visibility='global')

        user_groups = user.groups.all()
        group_reports = models.Report.objects.filter(
            visibility='group',
            allowed_groups__in=user_groups
        )

        return (personal_reports | global_reports | group_reports).distinct()


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = models.Report
    template_name = 'better_django_tables/reports/report_detail.html'

    def get_queryset(self):
        # Only show reports the user can access
        return models.Report.objects.filter(
            id__in=self.get_accessible_report_ids()
        )

    def get_accessible_report_ids(self):
        user = self.request.user
        personal_ids = models.Report.objects.filter(
            visibility='personal', created_by=user
        ).values_list('id', flat=True)

        global_ids = models.Report.objects.filter(
            visibility='global'
        ).values_list('id', flat=True)

        group_ids = models.Report.objects.filter(
            visibility='group',
            allowed_groups__in=user.groups.all()
        ).values_list('id', flat=True)

        return list(personal_ids) + list(global_ids) + list(group_ids)


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Report
    template_name = 'better_django_tables/reports/report_confirm_delete.html'
    success_url = reverse_lazy('better_django_tables:report_list')

    def get_queryset(self):
        user = self.request.user
        # Only allow deletion of own reports or global reports if user has permission
        if user.has_perm('better_django_tables.delete_report'):
            return models.Report.objects.all()
        return models.Report.objects.filter(created_by=user)


class HtmxTableView(NextViewMixin, BulkActionViewMixin, SingleTableMixin, FilterView):
    """
    HTMX-enabled table view for dynamic updates.
    Inherits from NextViewMixin, BulkActionViewMixin, SingleTableMixin, and FilterView.
    """
    template_name = 'better_django_tables/tables/htmx_table_view.html'
    show_new_record = False
    show_table_name = True
    table_pagination = False

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            error_html = render_to_string(
                'better_django_tables/partials/error_htmx_table.html',
                {'error': str(e)}
            )
            return HttpResponse(error_html, status=500)

    def post(self, request, *args, **kwargs):
        # Handle bulk actions
        return self.handle_bulk_action(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_new_record'] = self.show_new_record
        context['show_table_name'] = self.show_table_name
        return context


class RenderRowMixin:
    """
    Mixin to render a single row of a table using HTMX.
    This is useful for updating a specific row without reloading the entire table.
    """
    row_template_name = 'better_django_tables/partials/row.html'

    def render_row(self, record, table_class=None) -> HttpResponse:
        """ Render a single row of the table for HTMX updates.
        Args:
            record: The record to render.
            table_class: Optional table class to use for rendering.
        Returns:
            HttpResponse with the rendered row HTML.
        """
        if not table_class:
            table_class = self.get_table_class()
        table = table_class([record])
        context = self.get_context_data(record=record, table=table)
        html = render_to_string(self.row_template_name, context, request=self.request)
        return HttpResponse(html)

    def get_context_data(self, **kwargs) -> dict:
        # Safely call super() if it exists
        if hasattr(super(), 'get_context_data'):
            context = super().get_context_data(**kwargs)
        else:
            context = kwargs.copy()

        context["record"] = kwargs.get("record")
        context["table"] = kwargs.get("table")
        return context

    def get_table_class(self):
        """
        Return the table class to use for rendering the row.
        This can be overridden in subclasses to provide a specific table class.
        """
        if hasattr(self, 'table_class'):
            return self.table_class
        raise NotImplementedError("Subclasses must define a table_class attribute.")
