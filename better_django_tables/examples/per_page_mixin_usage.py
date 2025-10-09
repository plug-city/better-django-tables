"""
Example demonstrating the PerPageViewMixin with better-django-tables.

This example shows:
1. Basic usage with a simple table view
2. HTMX-enabled table with per-page selection
3. Customized per-page options
4. Multiple tables with separate session keys
"""

from django.db import models
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
import django_tables2 as tables
import django_filters

from better_django_tables.views import TableView, HtmxTableView
from better_django_tables.view_mixins import PerPageViewMixin


# Example Model
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


# Example Table
class ProductTable(tables.Table):
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock', 'category', 'created_at']
        attrs = {'class': 'table table-striped'}


# Example Filter
class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['name', 'category']


# Example 1: Basic Per-Page View
class BasicProductListView(PerPageViewMixin, SingleTableMixin, FilterView):
    """
    Simple product list with per-page selection.
    Uses default options: [10, 25, 50, 100, 500, 1000]
    Default per-page: 25
    """
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter
    template_name = 'products/product_list.html'


# Example 2: Customized Per-Page Options
class CustomProductListView(PerPageViewMixin, TableView):
    """
    Product list with custom per-page options.
    Only allows 10, 25, 50, or 100 items per page.
    Default: 50 items per page
    """
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter

    # Customize the options
    per_page_options = [10, 25, 50, 100]
    default_per_page = 50


# Example 3: HTMX-Enabled Table View
class HtmxProductListView(PerPageViewMixin, HtmxTableView):
    """
    HTMX-enabled product list with dynamic per-page updates.
    Changes to per-page selection update the table without full page reload.
    """
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter

    # Enable per-page selector in HTMX template
    htmx_show_per_page = True
    htmx_show_filter_badges = True

    # Custom options for HTMX view
    per_page_options = [10, 20, 50, 100]
    default_per_page = 20


# Example 4: Multiple Tables with Separate Session Keys
class ProductListView(PerPageViewMixin, TableView):
    """Product list with its own per-page session."""
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter

    # Use a unique session key for this table
    per_page_session_key = 'products_per_page'
    default_per_page = 50


# Example 5: View with Dynamic Options Based on User
class AdminProductListView(PerPageViewMixin, TableView):
    """
    Product list where per-page options vary by user role.
    Staff users get more options including bulk options (500, 1000).
    """
    model = Product
    table_class = ProductTable
    filterset_class = ProductFilter

    def get_per_page_options(self):
        """Override to customize options based on request."""
        if self.request.user.is_staff:
            return [10, 25, 50, 100, 500, 1000]
        return [10, 25, 50]

    def dispatch(self, request, *args, **kwargs):
        """Set per_page_options before view processing."""
        self.per_page_options = self.get_per_page_options()
        return super().dispatch(request, *args, **kwargs)


# URLs configuration example
"""
from django.urls import path
from .views import (
    BasicProductListView,
    CustomProductListView,
    HtmxProductListView,
    ProductListView,
    AdminProductListView
)

urlpatterns = [
    path('products/', BasicProductListView.as_view(), name='product_list'),
    path('products/custom/', CustomProductListView.as_view(), name='product_list_custom'),
    path('products/htmx/', HtmxProductListView.as_view(), name='product_list_htmx'),
    path('products/separate/', ProductListView.as_view(), name='product_list_separate'),
    path('products/admin/', AdminProductListView.as_view(), name='product_list_admin'),
]
"""


# Template example (products/product_list.html)
"""
{% extends 'base.html' %}
{% load render_table from django_tables2 %}

{% block content %}
<div class="container-fluid">
  <div class="row">
    <div class="col-12">
      <h1>Products</h1>

      <!-- Per-page selector is automatically included in the table -->
      <div class="d-flex justify-content-end mb-3">
        {% include "better_django_tables/partials/per_page_selector.html" %}
      </div>

      <!-- Render the table -->
      {% render_table table %}
    </div>
  </div>
</div>
{% endblock %}
"""


# HTMX Template example (products/product_list_htmx.html)
"""
{% extends 'base.html' %}
{% load render_better_inline_table from better_django_tables %}

{% block content %}
<div class="container-fluid">
  <div class="row">
    <div class="col-12">
      <h1>Products (HTMX)</h1>

      <!-- The table will update dynamically when per-page changes -->
      <div id="product-table">
        {% render_better_inline_table table %}
      </div>
    </div>
  </div>
</div>

<!-- Load HTMX -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
{% endblock %}
"""
