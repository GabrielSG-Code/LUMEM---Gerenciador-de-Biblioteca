/**
 * Character Limit Manager - LUMEN Library Management System
 * Provides real-time character counting and validation for input fields
 */

class CharacterLimitManager {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupCharacterCounters());
        } else {
            this.setupCharacterCounters();
        }
    }

    setupCharacterCounters() {
        // Define field configurations based on our character limits
        const fieldConfigs = {
            // Book fields
            'bookTitle': { limit: 200, type: 'title' },
            'editBookTitle': { limit: 200, type: 'title' },
            'bookAuthor': { limit: 150, type: 'author' },
            'editBookAuthor': { limit: 150, type: 'author' },
            'bookPublisher': { limit: 100, type: 'publisher' },
            'editBookPublisher': { limit: 100, type: 'publisher' },
            'bookDescription': { limit: 2000, type: 'description' },
            'editBookCategory': { limit: 50, type: 'category' },
            'bookYear': { limit: 4, type: 'year' },
            'editBookYear': { limit: 4, type: 'year' },
            'bookExemplary': { limit: 3, type: 'copies' },
            'editBookCopies': { limit: 3, type: 'copies' },
            
            // Search fields
            'searchInput': { limit: 150, type: 'search' },
            'loansSearchInput': { limit: 100, type: 'search' },
            
            // User fields (these will be handled by Django forms mostly)
            'id_username': { limit: 30, type: 'username' },
            'id_email': { limit: 320, type: 'email' },
            'id_new_email': { limit: 320, type: 'email' },
            'id_new_username': { limit: 30, type: 'username' }
        };

        // Setup counters for each configured field
        Object.entries(fieldConfigs).forEach(([fieldId, config]) => {
            this.setupFieldCounter(fieldId, config);
        });

        // Setup counters for any field with maxlength attribute
        this.setupGenericCounters();
    }

    setupFieldCounter(fieldId, config) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Skip character counters completely - no more "x caracteres restantes"
        return;
    }

    setupGenericCounters() {
        // Skip all generic counters - no more "x caracteres restantes"
        return;
    }

    getOrCreateCounter(field, config) {
        const counterId = field.id + 'Counter';
        let counter = document.getElementById(counterId);
        
        if (!counter) {
            counter = document.createElement('div');
            counter.id = counterId;
            counter.className = 'character-counter';
            counter.style.cssText = `
                font-size: 0.8rem;
                color: #6c757d;
                text-align: right;
                margin-top: 4px;
                transition: color 0.3s ease;
            `;

            // Insert counter after the field or its parent container
            const insertTarget = this.getInsertTarget(field);
            insertTarget.insertAdjacentElement('afterend', counter);
        }

        return counter;
    }

    getInsertTarget(field) {
        // Look for form-group, autocomplete-wrapper, or similar containers
        const containers = [
            '.form-group',
            '.autocomplete-wrapper',
            '.search-input-container',
            '.mb-3',
            '.col-md-6'
        ];

        for (let selector of containers) {
            const container = field.closest(selector);
            if (container) return container;
        }

        return field;
    }

    updateCounter(field, counter, config) {
        const currentLength = field.value.length;
        const remaining = config.limit - currentLength;
        
        // Update counter text
        if (remaining >= 0) {
            counter.textContent = `${remaining} caracteres restantes`;
        } else {
            counter.textContent = `${Math.abs(remaining)} caracteres excedentes`;
        }

        // Update counter color based on remaining characters
        this.updateCounterColor(counter, remaining, config.limit);

        // Update field styling
        this.updateFieldStyling(field, remaining);
    }

    updateCounterColor(counter, remaining, limit) {
        const percentage = (remaining / limit) * 100;
        
        if (remaining < 0) {
            counter.style.color = '#dc3545'; // Error red
            counter.style.fontWeight = 'bold';
        } else if (percentage <= 10) {
            counter.style.color = '#fd7e14'; // Warning orange
            counter.style.fontWeight = '600';
        } else if (percentage <= 25) {
            counter.style.color = '#ffc107'; // Warning yellow
            counter.style.fontWeight = '500';
        } else {
            counter.style.color = '#28a745'; // Success green
            counter.style.fontWeight = 'normal';
        }
    }

    updateFieldStyling(field, remaining) {
        // Remove existing warning classes
        field.classList.remove('char-limit-warning', 'char-limit-error');
        
        if (remaining < 0) {
            field.classList.add('char-limit-error');
        } else if (remaining <= 10) {
            field.classList.add('char-limit-warning');
        }
    }

    setupVisualFeedback(field, config) {
        // Add CSS for visual feedback if not already present
        if (!document.getElementById('charLimitStyles')) {
            const style = document.createElement('style');
            style.id = 'charLimitStyles';
            style.textContent = `
                .char-limit-warning {
                    border-color: #ffc107 !important;
                    box-shadow: 0 0 0 0.1rem rgba(255, 193, 7, 0.25) !important;
                }
                .char-limit-error {
                    border-color: #dc3545 !important;
                    box-shadow: 0 0 0 0.1rem rgba(220, 53, 69, 0.25) !important;
                }
                .character-counter {
                    font-family: inherit;
                    user-select: none;
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Public method to manually update a specific field
    updateField(fieldId) {
        const field = document.getElementById(fieldId);
        const counter = document.getElementById(fieldId + 'Counter');
        
        if (field && counter) {
            const maxLength = parseInt(field.getAttribute('maxlength'));
            if (maxLength) {
                const config = { limit: maxLength, type: 'manual' };
                this.updateCounter(field, counter, config);
            }
        }
    }

    // Validation method to check if all fields are within limits
    validateAllFields() {
        const fields = document.querySelectorAll('input[maxlength], textarea[maxlength]');
        const errors = [];

        fields.forEach(field => {
            const maxLength = parseInt(field.getAttribute('maxlength'));
            const currentLength = field.value.length;
            
            if (currentLength > maxLength) {
                const fieldName = field.getAttribute('placeholder') || 
                                field.getAttribute('name') || 
                                field.id || 
                                'Campo sem nome';
                errors.push({
                    field: field,
                    fieldName: fieldName,
                    currentLength: currentLength,
                    maxLength: maxLength,
                    excess: currentLength - maxLength
                });
            }
        });

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    // Method to show validation summary
    showValidationSummary() {
        const validation = this.validateAllFields();
        
        if (!validation.valid) {
            const errorMessages = validation.errors.map(error => 
                `${error.fieldName}: ${error.excess} caracteres excedentes`
            ).join('\n');
            
            alert(`Corrija os seguintes erros antes de continuar:\n\n${errorMessages}`);
            
            // Focus on first error field
            validation.errors[0].field.focus();
        }
        
        return validation.valid;
    }
}

// Initialize the character limit manager
window.characterLimitManager = new CharacterLimitManager();

// Expose validation function globally for form submissions
window.validateCharacterLimits = function() {
    return window.characterLimitManager.showValidationSummary();
};

// Auto-validation on form submission
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Only validate forms that have fields with maxlength
            const hasMaxLengthFields = form.querySelectorAll('[maxlength]').length > 0;
            if (hasMaxLengthFields) {
                const validation = window.characterLimitManager.validateAllFields();
                if (!validation.valid) {
                    e.preventDefault();
                    window.characterLimitManager.showValidationSummary();
                }
            }
        });
    });
});