function setupBulkActions() {
    // Find all tables and process each one separately
    const tables = document.querySelectorAll('.bulk-actions-table');
    console.log(`Found ${tables.length} tables for bulk actions setup.`);

    tables.forEach(table => {
        const tableId = table.id;
        // Find elements specific to this table
        // const selectAllCheckbox = document.getElementById(`select-all-${tableId}`);
        const selectAllCheckbox = table.querySelector('.select-all-checkbox');
        const individualCheckboxes = document.querySelectorAll(`.select-item-${tableId}`);
        const bulkActions = document.getElementById(`bulk-actions-${tableId}`);
        const selectedCountSpan = bulkActions ? bulkActions.querySelector(`#selected-count-${tableId}`) : null;
        const clearSelectionBtn = bulkActions ? bulkActions.querySelector(`#clear-selection-${tableId}`) : null;
        const bulkDeleteBtn = bulkActions ? bulkActions.querySelector(`#bulk-delete-btn-${tableId}`) : null;
        const bulkDeleteModal = document.getElementById(`bulkDeleteModal-${tableId}`);
        console.log(`Processing table with ID: ${tableId}`);
        console.log('table:', table);
        console.log('Setting up bulk actions for table:', tableId);
        console.log('individualCheckboxes:', individualCheckboxes);
        console.log('selectAllCheckbox:', selectAllCheckbox);
        console.log('bulkActions:', bulkActions);
        console.log('selectedCountSpan:', selectedCountSpan);
        console.log('clearSelectionBtn:', clearSelectionBtn);
        console.log('bulkDeleteBtn:', bulkDeleteBtn);
        console.log('bulkDeleteModal:', bulkDeleteModal);

        // Skip if essential elements aren't found
        if (!selectAllCheckbox || !individualCheckboxes.length) return;

        function updateBulkActionsVisibility() {
            const checkedCount = document.querySelectorAll(`.select-item-${tableId}:checked`).length;

            if (bulkActions && selectedCountSpan) {
                if (checkedCount > 0) {
                    bulkActions.classList.remove('d-none');
                    selectedCountSpan.textContent = checkedCount;
                } else {
                    bulkActions.classList.add('d-none');
                }
            }

            // Update select all checkbox state
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

        // Set up event handlers
        selectAllCheckbox.addEventListener('change', function() {
            individualCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });

        individualCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateBulkActionsVisibility);
        });

        if (clearSelectionBtn) {
            clearSelectionBtn.addEventListener('click', function() {
                individualCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                updateBulkActionsVisibility();
            });
        }

        if (bulkDeleteBtn && bulkDeleteModal) {
            bulkDeleteBtn.addEventListener('click', function() {
                const selectedItems = Array.from(document.querySelectorAll(`.select-item-${tableId}:checked`));
                const selectedIds = selectedItems.map(cb => cb.value);
                const selectedNames = selectedItems.map(cb => cb.dataset.itemName);

                const bulkDeleteForm = bulkDeleteModal.querySelector('#bulk-delete-form');
                if (bulkDeleteForm) {
                    bulkDeleteForm.querySelectorAll('input[name="selected_items"]').forEach(input => input.remove());
                    selectedIds.forEach(id => {
                        const hiddenInput = document.createElement('input');
                        hiddenInput.type = 'hidden';
                        hiddenInput.name = 'selected_items';
                        hiddenInput.value = id;
                        bulkDeleteForm.appendChild(hiddenInput);
                    });
                }

                const countSpan = bulkDeleteModal.querySelector('#bulk-delete-count');
                const itemsList = bulkDeleteModal.querySelector('#bulk-delete-items');
                if (countSpan) countSpan.textContent = selectedIds.length;
                if (itemsList) {
                    itemsList.innerHTML = selectedNames.map(name => `<li>${name}</li>`).join('');
                }
            });
        }

        // Initialize visibility
        updateBulkActionsVisibility();
    });
}

document.addEventListener('DOMContentLoaded', setupBulkActions);
document.addEventListener('htmx:afterSwap', setupBulkActions);
