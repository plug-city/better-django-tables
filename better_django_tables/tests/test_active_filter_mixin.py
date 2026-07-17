from types import SimpleNamespace

from django import forms
from django.test import RequestFactory
from django.test import SimpleTestCase

from better_django_tables.view_mixins import ActiveFilterMixin


class TestActiveFilterMixin(SimpleTestCase):
    def test_multi_choice_filters_have_per_value_clear_urls_and_human_labels(self):
        class FilterForm(forms.Form):
            status = forms.MultipleChoiceField(
                choices=[
                    ("contacted", "Contacted"),
                    ("dead", "Dead"),
                    ("closed", "Closed"),
                ],
                required=False,
            )
            status_exclude = forms.MultipleChoiceField(
                label="Exclude Statuses",
                choices=[
                    ("contacted", "Contacted"),
                    ("dead", "Dead"),
                    ("closed", "Closed"),
                ],
                required=False,
            )
            search = forms.CharField(required=False)

        class DummyView(ActiveFilterMixin):
            pass

        form = FilterForm(
            {
                "status": ["contacted"],
                "status_exclude": ["dead", "closed"],
            }
        )
        self.assertTrue(form.is_valid())

        filter_instance = SimpleNamespace(form=form)
        request = RequestFactory().get(
            "/leads/",
            {
                "status": ["contacted"],
                "status_exclude": ["dead", "closed"],
            },
        )

        view = DummyView()
        view.request = request

        active_filters = view.get_active_filters(filter_instance)

        self.assertEqual(active_filters[0]["display_value"], "Contacted")
        self.assertEqual(
            active_filters[0]["clear_url"],
            "/leads/?status_exclude=dead&status_exclude=closed",
        )

        self.assertEqual(active_filters[1]["display_value"], "Dead")
        self.assertEqual(
            active_filters[1]["clear_url"],
            "/leads/?status=contacted&status_exclude=closed",
        )

        self.assertEqual(active_filters[2]["display_value"], "Closed")
        self.assertEqual(
            active_filters[2]["clear_url"],
            "/leads/?status=contacted&status_exclude=dead",
        )
