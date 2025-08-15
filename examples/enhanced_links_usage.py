"""
Example of how to use the enhanced links functionality with different HTTP methods.

Usage in your Django views:
"""

from django.views.generic import ListView
from better_django_tables.views import TableView


class ExampleTableView(TableView):
    """Example showing how to use enhanced links with different methods"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Define links with different methods
        context['links'] = [
            # GET method (default) - backward compatible
            {
                'url': '/some/get/endpoint/',
                'text': 'View Details',
                'button_type': 'btn-outline-primary'
            },

            # GET method with label (renders as button)
            {
                'url': '/some/get/endpoint/',
                'label': 'View Report',
                'button_type': 'btn-info'
            },

            # POST method - renders as form with CSRF token
            {
                'url': '/sync/contacts/',
                'label': 'Sync Contacts',
                'method': 'POST',
                'button_type': 'btn-success',
                'confirm_message': 'Are you sure you want to sync contacts? This may take a while.'
            },

            # POST method without confirmation
            {
                'url': '/refresh/data/',
                'label': 'Refresh Data',
                'method': 'POST',
                'button_type': 'btn-warning'
            },

            # Legacy format (still works)
            {
                'url': '/legacy/endpoint/',
                'text': 'Legacy Link'
            }
        ]

        return context


# Example for OpenPhone Contact Sync
class OpenPhoneContactListView(TableView):
    """OpenPhone contacts with sync button"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['links'] = [
            {
                'url': reverse('openphone:contact_sync'),
                'label': 'Sync from OpenPhone',
                'method': 'POST',
                'button_type': 'btn-success',
                'confirm_message': 'This will sync all contacts from OpenPhone. Continue?'
            }
        ]

        return context
