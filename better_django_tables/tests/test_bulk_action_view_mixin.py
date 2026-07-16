from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import RequestFactory
from django.test import SimpleTestCase
from django.views.generic import TemplateView

from better_django_tables.view_mixins import BulkActionViewMixin


class BulkActionTestView(BulkActionViewMixin, TemplateView):
    extra_bulk_actions = [
        {
            "name": "lead_reviewed",
            "method_name": "bulk_lead_reviewed",
            "icon_class": "bi bi-check2-circle",
        }
    ]

    def bulk_lead_reviewed(self, selected_items, action):
        return None


class TestBulkActionViewMixin(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_context_includes_extra_bulk_actions_with_default_label(self):
        request = self.factory.get("/leads/?next=/leads/")
        view = BulkActionTestView()
        view.request = request

        context = view.get_context_data()

        self.assertEqual(context["bulk_action_redirect_url"], "/leads/")
        self.assertEqual(len(context["extra_bulk_actions"]), 1)
        self.assertEqual(context["extra_bulk_actions"][0]["name"], "lead_reviewed")
        self.assertEqual(context["extra_bulk_actions"][0]["label"], "Lead Reviewed")

    def test_bulk_actions_partial_renders_actions_dropdown_for_extra_actions(self):
        request = self.factory.get("/leads/")
        context = {
            "request": request,
            "table": SimpleNamespace(
                table_id="lead-table",
                bulk_delete_url_name=None,
            ),
            "bulk_action_redirect_url": "/leads/",
            "extra_bulk_actions": [
                {
                    "name": "lead_reviewed",
                    "label": "Lead Reviewed",
                    "icon_class": "bi bi-check2-circle",
                }
            ],
        }

        rendered = render_to_string(
            "better_django_tables/partials/bulk_actions.html",
            context,
        )

        self.assertIn("Actions", rendered)
        self.assertIn("Lead Reviewed", rendered)
        self.assertIn('value="lead_reviewed"', rendered)
        self.assertIn("dropdown-menu", rendered)
