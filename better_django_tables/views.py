import logging

from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, DeleteView
from django.http import HttpResponse

from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from better_django_tables.view_mixins import (
    NextViewMixin,
    NavigationStorageMixin,
    # ActiveFilterMixin,
    BulkActionViewMixin,
    # BetterMultiTableMixin,
    HtmxTableViewMixin,
    # PerPageViewMixin,
    # ShowFilterMixin,
    SelectColumnsViewMixin,
    # LinksMixin,
)
from better_django_tables import models, filters, tables


logger = logging.getLogger(__name__)


class TableView(
    NavigationStorageMixin,
    NextViewMixin,
    BulkActionViewMixin,
    SelectColumnsViewMixin,
    HtmxTableViewMixin,
    SingleTableMixin,
    FilterView,
):
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
        bulk_delete_hx_trigger: The HTMX trigger event name for bulk delete actions (optional).

    Methods to override in subclasses:
        get_queryset(self): Return the queryset for the table.
        get_table_class(self): Return the table class to use.
        get_context_data(self, **kwargs): Add extra context to the template.
        post(self, request, *args, **kwargs): Handle POST requests (bulk actions, etc).

    """


class RenderRowMixin:
    """
    Mixin to render a single row of a table using HTMX.
    This is useful for updating a specific row without reloading the entire table.
    """

    row_template_name = "better_django_tables/partials/row.html"

    def render_row(
        self, record, table_class=None, table_kwargs: dict | None = None
    ) -> HttpResponse:
        """Render a single row of the table for HTMX updates.
        Args:
            record: The record to render.
            table_class: Optional table class to use for rendering.
        Returns:
            HttpResponse with the rendered row HTML.
        """
        if table_kwargs is None:
            table_kwargs = {}
        if not table_class:
            table_class = self.get_table_class()
        table = table_class([record], **self.get_table_kwargs(**table_kwargs))
        context = self.get_context_data(record=record, table=table)
        return render(self.request, self.row_template_name, context)

    def get_context_data(self, **kwargs) -> dict:
        # Safely call super() if it exists
        if hasattr(super(), "get_context_data"):
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
        if hasattr(self, "table_class"):
            return self.table_class
        raise NotImplementedError("Subclasses must define a table_class attribute.")

    def get_table_kwargs(self, **kwargs) -> dict:
        """
        Return the keyword arguments for instantiating the table.

        Allows passing customized arguments to the table constructor, for example,
        to remove the buttons column, you could define this method in your View::

            def get_table_kwargs(self):
                return {
                    'exclude': ('buttons', )
                }
        """
        if hasattr(self, "table_kwargs"):
            kwargs.update(self.table_kwargs)
        return kwargs or {}
