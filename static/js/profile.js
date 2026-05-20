/**
 * Profile page JavaScript functionality
 * Handles expandable sections for account settings
 */

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    const arrow = header.querySelector('.toggle-arrow');
    
    // Close all other sections first
    const allSections = document.querySelectorAll('.setting-content');
    allSections.forEach(otherSection => {
        if (otherSection.id !== sectionId && otherSection.classList.contains('expanded')) {
            const otherHeader = otherSection.previousElementSibling;
            const otherArrow = otherHeader.querySelector('.toggle-arrow');
            otherSection.classList.remove('expanded');
            otherArrow.classList.remove('rotated');
        }
    });
    
    if (section.classList.contains('expanded')) {
        // Collapse section
        section.classList.remove('expanded');
        arrow.classList.remove('rotated');
    } else {
        // Expand section
        section.classList.add('expanded');
        arrow.classList.add('rotated');
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Add click event listeners to all setting headers
    const settingHeaders = document.querySelectorAll('.setting-header');
    
    settingHeaders.forEach(header => {
        header.addEventListener('click', function() {
            // Find the corresponding content section
            const content = this.nextElementSibling;
            if (content && content.classList.contains('setting-content')) {
                const sectionId = content.id;
                toggleSection(sectionId);
            }
        });
    });

    // Auto-expand section if there are form errors
    const errorMessages = document.querySelectorAll('.alert-danger');
    if (errorMessages.length > 0) {
        // Look for any visible error messages in forms
        const forms = document.querySelectorAll('.setting-form');
        forms.forEach(form => {
            const formErrors = form.querySelectorAll('.text-danger, .error');
            if (formErrors.length > 0) {
                const sectionContent = form.closest('.setting-content');
                if (sectionContent && !sectionContent.classList.contains('expanded')) {
                    const sectionId = sectionContent.id;
                    toggleSection(sectionId);
                }
            }
        });
    }

    // Form validation feedback
    const forms = document.querySelectorAll('.setting-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('.btn-save');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Salvando...';
                
                // Re-enable after 3 seconds as failsafe
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.getAttribute('data-original-text') || 'Salvar';
                }, 3000);
            }
        });
    });
});