import urllib.parse

from django.db import models
# from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import get_user_model

# User = get_user_model()

class Report(models.Model):
    VISIBILITY_CHOICES = [
        ('personal', 'Personal'),
        ('group', 'Group-based'),
        ('global', 'Global'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    view_name = models.CharField(max_length=100)
    filter_params = models.JSONField()  # Store the filter parameters
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='bdt_reports_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # For group-based reports - use Django's built-in Group model
    allowed_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        help_text="Groups that can access this report (only for group-based reports)",
        related_name='bdt_reports'
    )

    # For summary reports (optional)
    is_summary_report = models.BooleanField(default=False)
    summary_config = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        db_table = 'django_bdt_report'

    def __str__(self):
        return f"{self.name} ({self.get_visibility_display()})"

    def get_absolute_url(self):
        params = urllib.parse.urlencode(self.filter_params)
        base_url = reverse(self.view_name)
        return f"{base_url}?{params}"

    def user_can_access(self, user):
        """Check if a user can access this report"""
        if self.visibility == 'personal':
            return self.created_by == user
        elif self.visibility == 'global':
            return True
        elif self.visibility == 'role':
            user_groups = user.groups.all()
            return self.allowed_groups.filter(id__in=user_groups).exists()
        return False


class ReportFavorite(models.Model):
    """Track user's favorite reports"""
    user = models.ForeignKey(
            'users.User',
            on_delete=models.CASCADE,
            related_name='bdt_report_favorites'
        )
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'report']
        db_table = 'django_bdt_report_favorite'
