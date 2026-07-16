function setupBulkActions() {
    const tables = document.querySelectorAll('.bulk-actions-table');

    tables.forEach((table) => {
        if (table.dataset.bulkActionsInitialized === 'true') {
            return;
        }
        table.dataset.bulkActionsInitialized = 'true';

        const tableId = table.id;
        const selectAllCheckbox = table.querySelector('.select-all-checkbox');
        const bulkActions = document.getElementById(`bulk-actions-${tableId}`);
        const selectedCountSpan = bulkActions
            ? bulkActions.querySelector(`#selected-count-${tableId}`)
            : null;
        const clearSelectionBtn = bulkActions
            ? bulkActions.querySelector(`#clear-selection-${tableId}`)
            : null;
        const bulkDeleteBtn = bulkActions
            ? bulkActions.querySelector(`#bulk-delete-btn-${tableId}`)
            : null;
        const bulkDeleteModal = document.getElementById(`bulkDeleteModal-${tableId}`);
        const bulkActionForms = bulkActions
            ? bulkActions.querySelectorAll('[data-bulk-action-form]')
            : [];

        if (!selectAllCheckbox) {
            return;
        }

        function getIndividualCheckboxes() {
            return Array.from(table.querySelectorAll(`.select-item-${tableId}`));
        }

        function getSelectedCheckboxes() {
            return Array.from(table.querySelectorAll(`.select-item-${tableId}:checked`));
        }

        function syncSelectedItems(form, selectedIds) {
            if (!form) {
                return;
            }

            form.querySelectorAll('input[name="selected_items"]').forEach((input) => {
                input.remove();
            });

            selectedIds.forEach((id) => {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'selected_items';
                hiddenInput.value = id;
                form.appendChild(hiddenInput);
            });
        }

        function updateBulkActionsVisibility() {
            const individualCheckboxes = getIndividualCheckboxes();
            const checkedCount = getSelectedCheckboxes().length;

            if (bulkActions && selectedCountSpan) {
                if (checkedCount > 0) {
                    bulkActions.classList.remove('d-none');
                    selectedCountSpan.textContent = checkedCount;
                } else {
                    bulkActions.classList.add('d-none');
                }
            }

            if (checkedCount === 0) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = false;
            } else if (checkedCount === individualCheckboxes.length) {
                selectAllCheckbox.indeterminate = false;
                selectAllCheckbox.checked = true;
            } else {
                selectAllCheckbox.indeterminate = true;
                selectAllCheckbox.checked = false;
            }
        }

        selectAllCheckbox.addEventListener('change', function() {
            getIndividualCheckboxes().forEach((checkbox) => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });

        getIndividualCheckboxes().forEach((checkbox) => {
            checkbox.addEventListener('change', updateBulkActionsVisibility);
        });

        if (clearSelectionBtn) {
            clearSelectionBtn.addEventListener('click', () => {
                getIndividualCheckboxes().forEach((checkbox) => {
                    checkbox.checked = false;
                });
                updateBulkActionsVisibility();
            });
        }

        bulkActionForms.forEach((form) => {
            form.addEventListener('submit', () => {
                const selectedIds = getSelectedCheckboxes().map((checkbox) => checkbox.value);
                syncSelectedItems(form, selectedIds);
            });
        });

        if (bulkDeleteBtn && bulkDeleteModal) {
            bulkDeleteBtn.addEventListener('click', () => {
                const selectedItems = getSelectedCheckboxes();
                const selectedIds = selectedItems.map((checkbox) => checkbox.value);
                const selectedNames = selectedItems.map((checkbox) => checkbox.dataset.itemName);

                const bulkDeleteForm = bulkDeleteModal.querySelector('#bulk-delete-form');
                syncSelectedItems(bulkDeleteForm, selectedIds);

                const countSpan = bulkDeleteModal.querySelector('#bulk-delete-count');
                const itemsList = bulkDeleteModal.querySelector('#bulk-delete-items');
                if (countSpan) {
                    countSpan.textContent = selectedIds.length;
                }
                if (itemsList) {
                    itemsList.innerHTML = selectedNames.map((name) => `<li>${name}</li>`).join('');
                }
            });
        }

        updateBulkActionsVisibility();
    });
}

document.addEventListener('DOMContentLoaded', setupBulkActions);
document.addEventListener('htmx:afterSwap', setupBulkActions);
