"""
Example usage of ActionColumnMixin for better-django-tables - Structured Actions Approach
"""
from better_django_tables import ActionColumnMixin
import django_tables2 as tables


class ExampleModel:
    """Mock model for demonstration"""
    def __init__(self, pk, name, email, slug=None, category=None):
        self.pk = pk
        self.name = name
        self.email = email
        self.slug = slug or f"item-{pk}"
        self.category = category or type('Category', (), {'slug': 'general'})()

    def __str__(self):
        return self.name


# ===== STRUCTURED ACTIONS APPROACH (RECOMMENDED) =====

class BasicStructuredActionsTable(ActionColumnMixin, tables.Table):
    """Basic table using structured actions approach"""

    actions = [
        {
            'name': 'view',
            'url_name': 'example:detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View Details',
        },
        {
            'name': 'edit',
            'url_name': 'example:update',
            'icon': 'bi bi-pencil-square',
            'class': 'text-primary',
            'title': 'Edit Record',
        },
        {
            'name': 'delete',
            'url_name': 'example:delete',
            'icon': 'bi bi-trash',
            'class': 'text-danger',
            'title': 'Delete Record',
            'requires_modal': True,
            'modal_target': '#deleteModalBdt',
            'modal_toggle': 'modal',
        }
    ]

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')


class CustomURLActionsTable(ActionColumnMixin, tables.Table):
    """Table with custom URL kwargs"""

    actions = [
        {
            'name': 'view',
            'url_name': 'example:detail_by_slug',
            'url_kwargs': lambda record: {'slug': record.slug},
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View by Slug',
        },
        {
            'name': 'edit',
            'url_name': 'example:update_by_category',
            'url_kwargs': lambda record: {
                'pk': record.pk,
                'category': record.category.slug
            },
            'icon': 'bi bi-pencil-square',
            'class': 'text-primary',
            'title': 'Edit by Category',
        },
        {
            'name': 'export',
            'url_name': 'example:export',
            'url_kwargs': lambda record: {
                'format': 'pdf',
                'record_id': record.pk
            },
            'icon': 'bi bi-download',
            'class': 'text-success',
            'title': 'Export as PDF',
        }
    ]

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')


class ModalActionsTable(ActionColumnMixin, tables.Table):
    """Table with custom modal actions"""

    actions = [
        {
            'name': 'view',
            'url_name': 'example:detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View',
        },
        {
            'name': 'approve',
            'url_name': 'example:approve',
            'icon': 'bi bi-check-circle',
            'class': 'text-success',
            'title': 'Approve',
            'requires_modal': True,
            'modal_target': '#approveModal',
            'modal_toggle': 'modal',
        },
        {
            'name': 'archive',
            'url_name': 'example:archive',
            'url_kwargs': lambda record: {'pk': record.pk, 'redirect': 'list'},
            'icon': 'bi bi-archive',
            'class': 'text-warning',
            'title': 'Archive',
            'requires_modal': True,
            'modal_target': '#archiveModal',
            'modal_toggle': 'modal',
        }
    ]

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')


class DynamicActionsTable(ActionColumnMixin, tables.Table):
    """Table with dynamic actions based on user permissions"""

    # Base actions available to all users
    actions = [
        {
            'name': 'view',
            'url_name': 'example:detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View',
        }
    ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Add edit action for staff users
        if user and user.is_staff:
            self.enabled_actions.append({
                'name': 'edit',
                'url_name': 'example:update',
                'icon': 'bi bi-pencil-square',
                'class': 'text-primary',
                'title': 'Edit',
                'requires_modal': False,
            })

        # Add delete action for superusers
        if user and user.is_superuser:
            self.enabled_actions.append({
                'name': 'delete',
                'url_name': 'example:delete',
                'icon': 'bi bi-trash',
                'class': 'text-danger',
                'title': 'Delete',
                'requires_modal': True,
                'modal_target': '#deleteModalBdt',
                'modal_toggle': 'modal',
            })

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')


# ===== LEGACY APPROACH (STILL SUPPORTED) =====

class LegacyActionsTable(ActionColumnMixin, tables.Table):
    """Table using legacy actions approach"""

    # Disable delete action
    enable_delete_action = False

    actions_url_names = {
        'view': 'example:detail',
        'edit': 'example:update'
    }

    # Custom styling
    action_icons = {
        'view': 'bi bi-eye-fill',
        'edit': 'bi bi-gear-fill'
    }

    action_classes = {
        'view': 'text-success',
        'edit': 'text-warning'
    }

    action_titles = {
        'view': 'View Details',
        'edit': 'Modify'
    }

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')


class ReadOnlyTable(ActionColumnMixin, tables.Table):
    """Table with actions disabled"""

    has_actions_column = False

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('name', 'email')  # No actions column


# ===== MIXED APPROACH EXAMPLE =====

class MixedApproachTable(ActionColumnMixin, tables.Table):
    """Example showing you can combine structured and dynamic approaches"""

    # Base structured actions
    actions = [
        {
            'name': 'view',
            'url_name': 'example:detail',
            'icon': 'bi bi-eye',
            'class': 'text-info',
            'title': 'View',
        }
    ]

    def __init__(self, *args, show_admin_actions=False, **kwargs):
        super().__init__(*args, **kwargs)

        # Conditionally add admin actions
        if show_admin_actions:
            # Add structured edit action
            self.enabled_actions.append({
                'name': 'edit',
                'url_name': 'example:update_admin',
                'url_kwargs': lambda record: {
                    'pk': record.pk,
                    'admin': 'true'
                },
                'icon': 'bi bi-gear',
                'class': 'text-warning',
                'title': 'Admin Edit',
            })

            # Add structured delete action
            self.enabled_actions.append({
                'name': 'force_delete',
                'url_name': 'example:force_delete',
                'icon': 'bi bi-x-circle',
                'class': 'text-danger',
                'title': 'Force Delete',
                'requires_modal': True,
                'modal_target': '#forceDeleteModal',
                'modal_toggle': 'modal',
            })

    name = tables.Column()
    email = tables.Column()

    class Meta:
        model = ExampleModel
        fields = ('actions', 'name', 'email')
