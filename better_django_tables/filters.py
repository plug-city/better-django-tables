import django_filters
from django_filters.widgets import RangeWidget, BooleanWidget
from django.contrib.auth.models import User
from django import forms
from django.db.models import Q
from django.contrib.auth.models import Group

from better_django_tables import models


class ReportFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name...'
        }),
        label='Name'
    )

    description = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search description...'
        }),
        label='Description'
    )

    visibility = django_filters.ChoiceFilter(
        choices=models.Report.VISIBILITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Visibility'
    )

    created_by = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Created By'
    )

    view_name = django_filters.AllValuesFilter(
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='View'
    )

    allowed_groups = django_filters.ModelMultipleChoiceFilter(
        queryset=Group.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Groups'
    )

    is_active = django_filters.BooleanFilter(
        widget=BooleanWidget(),
        label='Active'
    )

    created_at = django_filters.DateFromToRangeFilter(
        widget=RangeWidget(attrs={'type': 'date', 'class': 'form-control'}),
        label='Created Date'
    )

    # Custom filters
    my_reports = django_filters.BooleanFilter(
        method='filter_my_reports',
        label='My Reports Only',
        widget=BooleanWidget()
    )

    has_filters = django_filters.BooleanFilter(
        method='filter_has_filters',
        label='Has Active Filters',
        widget=BooleanWidget()
    )

    search = django_filters.CharFilter(
        method='filter_search',
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search reports, descriptions, view names...'
        })
    )

    class Meta:
        model = models.Report
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Filter created_by to only show users who have created reports
        if User.objects.filter(report__isnull=False).exists():
            self.filters['created_by'].queryset = User.objects.filter(
                report__isnull=False
            ).distinct()

    def filter_my_reports(self, queryset, name, value):
        """Filter to show only reports accessible to the current user"""
        if not value or not self.request or not self.request.user.is_authenticated:
            return queryset

        user = self.request.user

        # Build query for accessible reports
        query = Q(visibility='personal', created_by=user) | Q(visibility='global')

        # Add group-based reports if user has groups
        user_groups = user.groups.all()
        if user_groups.exists():
            query |= Q(visibility='role', allowed_groups__in=user_groups)

        return queryset.filter(query).distinct()

    def filter_has_filters(self, queryset, name, value):
        """Filter reports that have active filter parameters"""
        if not value:
            return queryset

        # Filter reports that have non-empty filter_params
        return queryset.exclude(
            Q(filter_params__isnull=True) |
            Q(filter_params__exact={}) |
            Q(filter_params__exact='{}')
        )

    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(view_name__icontains=value) |
            Q(created_by__username__icontains=value) |
            Q(created_by__first_name__icontains=value) |
            Q(created_by__last_name__icontains=value) |
            Q(allowed_groups__name__icontains=value)
        ).distinct()

