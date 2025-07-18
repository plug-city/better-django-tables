function setupBulkActions() {
    const selectAllCheckbox = document.getElementById('select-all');
    const individualCheckboxes = document.querySelectorAll('.select-item');
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCountSpan = document.getElementById('selected-count');
    const clearSelectionBtn = document.getElementById('clear-selection');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');

    function updateBulkActionsVisibility() {
        const checkedCount = document.querySelectorAll('.select-item:checked').length;
        if (checkedCount > 0) {
            bulkActions.classList.remove('d-none');
            selectedCountSpan.textContent = checkedCount;
        } else {
            bulkActions.classList.add('d-none');
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

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            individualCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionsVisibility();
        });
    }

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

    if (bulkDeleteBtn) {
        bulkDeleteBtn.addEventListener('click', function() {
            const selectedItems = Array.from(document.querySelectorAll('.select-item:checked'));
            const selectedIds = selectedItems.map(cb => cb.value);
            const selectedNames = selectedItems.map(cb => cb.dataset.itemName);

            const bulkDeleteForm = document.getElementById('bulk-delete-form');
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

            const countSpan = document.getElementById('bulk-delete-count');
            const itemsList = document.getElementById('bulk-delete-items');
            if (countSpan) countSpan.textContent = selectedIds.length;
            if (itemsList) {
                itemsList.innerHTML = selectedNames.map(name => `<li>${name}</li>`).join('');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', setupBulkActions);
document.addEventListener('htmx:afterSwap', function(evt) {
    setupBulkActions();
});

