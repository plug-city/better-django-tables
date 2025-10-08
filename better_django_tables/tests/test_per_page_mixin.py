"""
Tests for PerPageViewMixin
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.views.generic import ListView
from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from better_django_tables.view_mixins import PerPageViewMixin


class MockModel:
    """Mock model for testing"""
    def __init__(self, pk=1, name="Test"):
        self.pk = pk
        self.name = name

    def __str__(self):
        return self.name


class TestPerPageViewMixin(TestCase):
    """Test cases for PerPageViewMixin"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

    def add_session_to_request(self, request):
        """Add session to a request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_default_per_page(self):
        """Test that default per_page is used when no preference is set"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            default_per_page = 25

        request = self.factory.get('/test/')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should return default_per_page
        self.assertEqual(view.get_paginate_by(None), 25)

    def test_per_page_from_query_param(self):
        """Test that per_page is read from query parameter"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        request = self.factory.get('/test/?per_page=50')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should return the per_page from query param
        result = view.get_paginate_by(None)
        self.assertEqual(result, 50)

    def test_per_page_saved_to_session(self):
        """Test that per_page selection is saved to session"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        request = self.factory.get('/test/?per_page=100')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Call get_paginate_by to trigger session save
        view.get_paginate_by(None)

        # Check that it was saved to session
        self.assertEqual(request.session['table_per_page'], 100)

    def test_per_page_from_session(self):
        """Test that per_page is read from session if no query param"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        # First request with per_page parameter
        request1 = self.factory.get('/test/?per_page=50')
        request1 = self.add_session_to_request(request1)
        request1.user = self.user

        view1 = TestView()
        view1.request = request1
        view1.get_paginate_by(None)

        # Second request without parameter, using same session
        request2 = self.factory.get('/test/')
        request2.session = request1.session
        request2.user = self.user

        view2 = TestView()
        view2.request = request2

        # Should return the session value
        self.assertEqual(view2.get_paginate_by(None), 50)

    def test_invalid_per_page_ignored(self):
        """Test that invalid per_page values are ignored"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        # Test with invalid number (not in options)
        request = self.factory.get('/test/?per_page=999')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should return default since 999 is not in options
        self.assertEqual(view.get_paginate_by(None), 25)

    def test_non_numeric_per_page_ignored(self):
        """Test that non-numeric per_page values are ignored"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        request = self.factory.get('/test/?per_page=invalid')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should return default since 'invalid' is not a number
        self.assertEqual(view.get_paginate_by(None), 25)

    def test_custom_session_key(self):
        """Test using a custom session key"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25
            per_page_session_key = 'custom_per_page'

        request = self.factory.get('/test/?per_page=50')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        view.get_paginate_by(None)

        # Check that custom session key was used
        self.assertEqual(request.session['custom_per_page'], 50)
        self.assertNotIn('table_per_page', request.session)

    def test_post_request_per_page(self):
        """Test that per_page works with POST requests (for HTMX)"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        request = self.factory.post('/test/', {'per_page': '100'})
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should work with POST data too
        self.assertEqual(view.get_paginate_by(None), 100)

    def test_context_data_includes_options(self):
        """Test that context data includes per_page_options"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50]
            default_per_page = 25
            queryset = []

            def get_queryset(self):
                return self.queryset

        request = self.factory.get('/test/')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        context = view.get_context_data()

        # Check that per_page_options is in context
        self.assertIn('per_page_options', context)
        self.assertEqual(context['per_page_options'], [10, 25, 50])

        # Check that current_per_page is in context
        self.assertIn('current_per_page', context)
        self.assertEqual(context['current_per_page'], 25)

    def test_fallback_to_paginate_by(self):
        """Test that it falls back to paginate_by attribute"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            paginate_by = 75  # Traditional django paginate_by

        request = self.factory.get('/test/')
        request = self.add_session_to_request(request)
        request.user = self.user

        view = TestView()
        view.request = request

        # Should fall back to paginate_by if no session/param
        self.assertEqual(view.get_paginate_by(None), 75)

    def test_query_param_overrides_session(self):
        """Test that query parameter takes priority over session"""

        class TestView(PerPageViewMixin, ListView):
            model = MockModel
            per_page_options = [10, 25, 50, 100]
            default_per_page = 25

        # First request sets session to 50
        request1 = self.factory.get('/test/?per_page=50')
        request1 = self.add_session_to_request(request1)
        request1.user = self.user

        view1 = TestView()
        view1.request = request1
        view1.get_paginate_by(None)

        # Second request with different per_page param
        request2 = self.factory.get('/test/?per_page=100')
        request2.session = request1.session
        request2.user = self.user

        view2 = TestView()
        view2.request = request2

        # Should use query param (100) not session (50)
        self.assertEqual(view2.get_paginate_by(None), 100)

        # Session should be updated to 100
        self.assertEqual(request2.session['table_per_page'], 100)
