"""
Tests for ActionColumnMixin
"""
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
import django_tables2 as tables

from better_django_tables.table_mixins import ActionColumnMixin


class MockModel:
    """Mock model for testing"""
    def __init__(self, pk=1, name="Test"):
        self.pk = pk
        self.name = name

    def __str__(self):
        return self.name


class TestActionColumnMixin(TestCase):
    """Test cases for ActionColumnMixin"""

    def test_basic_actions_table_creation(self):
        """Test that a basic actions table can be created"""

        class TestTable(ActionColumnMixin, tables.Table):
            actions_url_names = {
                'view': 'test:detail',
                'edit': 'test:update',
                'delete': 'test:delete'
            }

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([])

        # Check that actions column exists
        self.assertIn('actions', table.columns)

        # Check that enabled actions are properly configured
        self.assertEqual(len(table.enabled_actions), 3)

        action_names = [action['name'] for action in table.enabled_actions]
        self.assertIn('view', action_names)
        self.assertIn('edit', action_names)
        self.assertIn('delete', action_names)

    def test_disabled_actions(self):
        """Test that actions can be individually disabled"""

        class TestTable(ActionColumnMixin, tables.Table):
            enable_delete_action = False

            actions_url_names = {
                'view': 'test:detail',
                'edit': 'test:update'
            }

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([])

        # Should only have view and edit actions
        self.assertEqual(len(table.enabled_actions), 2)

        action_names = [action['name'] for action in table.enabled_actions]
        self.assertIn('view', action_names)
        self.assertIn('edit', action_names)
        self.assertNotIn('delete', action_names)

    def test_missing_url_names_raises_error(self):
        """Test that missing URL names raise ImproperlyConfigured"""

        with self.assertRaises(ImproperlyConfigured):
            class TestTable(ActionColumnMixin, tables.Table):
                # Missing delete URL name
                actions_url_names = {
                    'view': 'test:detail',
                    'edit': 'test:update'
                }

                name = tables.Column()

                class Meta:
                    model = MockModel
                    fields = ('actions', 'name')

            TestTable([])

    def test_custom_action_configuration(self):
        """Test custom action icons, classes, and titles"""

        class TestTable(ActionColumnMixin, tables.Table):
            actions_url_names = {
                'view': 'test:detail',
                'edit': 'test:update',
                'delete': 'test:delete'
            }

            action_icons = {
                'view': 'custom-eye',
                'edit': 'custom-edit',
                'delete': 'custom-trash'
            }

            action_classes = {
                'view': 'custom-view-class',
                'edit': 'custom-edit-class',
                'delete': 'custom-delete-class'
            }

            action_titles = {
                'view': 'Custom View',
                'edit': 'Custom Edit',
                'delete': 'Custom Delete'
            }

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([])

        # Check custom configurations
        view_action = next(a for a in table.enabled_actions if a['name'] == 'view')
        self.assertEqual(view_action['icon'], 'custom-eye')
        self.assertEqual(view_action['class'], 'custom-view-class')
        self.assertEqual(view_action['title'], 'Custom View')

    def test_add_custom_action(self):
        """Test adding custom actions dynamically"""

        class TestTable(ActionColumnMixin, tables.Table):
            actions_url_names = {
                'view': 'test:detail',
                'edit': 'test:update',
                'delete': 'test:delete'
            }

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([])

        # Add custom action
        table.add_custom_action(
            name='export',
            url_name='test:export',
            icon='bi bi-download',
            css_class='text-success',
            title='Export Data'
        )

        # Should now have 4 actions
        self.assertEqual(len(table.enabled_actions), 4)

        # Check custom action
        export_action = next(a for a in table.enabled_actions if a['name'] == 'export')
        self.assertEqual(export_action['url_name'], 'test:export')
        self.assertEqual(export_action['icon'], 'bi bi-download')
        self.assertEqual(export_action['class'], 'text-success')
        self.assertEqual(export_action['title'], 'Export Data')

    def test_actions_table_disabled(self):
        """Test that actions column can be disabled entirely"""

        class TestTable(ActionColumnMixin, tables.Table):
            has_actions_column = False

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('name',)

        table = TestTable([])

        # Actions column should not exist
        self.assertNotIn('actions', table.columns)

    def test_actions_table_disabled_at_runtime(self):
        """Test that actions column can be disabled at instantiation"""

        class TestTable(ActionColumnMixin, tables.Table):
            actions_url_names = {
                'view': 'test:detail',
                'edit': 'test:update',
                'delete': 'test:delete'
            }

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([], has_actions_column=False)

        # Actions should be disabled
        self.assertFalse(table.has_actions_column)

    def test_delete_action_requires_modal(self):
        """Test that delete action is configured for modal usage"""

        class TestTable(ActionColumnMixin, tables.Table):
            actions_url_names = {
                'delete': 'test:delete'
            }

            enable_view_action = False
            enable_edit_action = False

            name = tables.Column()

            class Meta:
                model = MockModel
                fields = ('actions', 'name')

        table = TestTable([])

        delete_action = table.enabled_actions[0]
        self.assertTrue(delete_action['requires_modal'])
        self.assertEqual(delete_action['modal_target'], '#deleteModalBdt')
        self.assertEqual(delete_action['modal_toggle'], 'modal')
