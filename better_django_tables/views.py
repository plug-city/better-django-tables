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
    Base view for displaying tables with common functionality.
    Inherits from BaseViewMixin, ActiveFilterMixin, BulkActionViewMixin, and ReportableViewMixin.
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

