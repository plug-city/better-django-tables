from django import forms
from django.contrib.auth.models import Group

from better_django_tables import models


# class ReportSaveForm(forms.ModelForm):
#     allowed_groups = forms.ModelMultipleChoiceField(
#         queryset=Group.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False,
#         help_text="Select groups that can access this report (only for group-based reports)"
#     )

#     class Meta:
#         model = models.Report
#         fields = ['name', 'description', 'visibility', 'view_name', 'filter_params', 'allowed_groups']
#         widgets = {
#             'filter_params': forms.HiddenInput(),
#             'view_name': forms.HiddenInput(),
#             'description': forms.Textarea(attrs={'rows': 2}),
#             'visibility': forms.RadioSelect(),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Add some styling
#         self.fields['name'].widget.attrs.update({'class': 'form-control'})
#         self.fields['description'].widget.attrs.update({'class': 'form-control'})

#         # Add JavaScript to show/hide group selection based on visibility
#         self.fields['visibility'].widget.attrs.update({
#             'class': 'form-check-input',
#             'onchange': 'toggleGroupSelection()'
#         })


# class ReportBulkActionForm(forms.Form):
#     ACTION_CHOICES = [
#         ('delete', 'Delete Selected'),
#         ('make_global', 'Make Global'),
#         ('make_personal', 'Make Personal'),
#         ('export', 'Export'),
#     ]

#     action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
#     report_ids = forms.CharField(widget=forms.HiddenInput())
