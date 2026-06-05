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
    // Clear all messages on page load/reload
    clearAllMessages();
    
    // Initialize password toggle functionality
    initializePasswordToggles();
    
    // Initialize username availability check
    initializeUsernameAvailabilityCheck();
    
    // Initialize loading states and network monitoring
    initializeLoadingStates();
    initializeNetworkMonitoring();
    
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

    // Password form validation
    const passwordForm = document.querySelector('form input[name="form_type"][value="password"]')?.closest('form');
    if (passwordForm) {
        const oldPasswordField = passwordForm.querySelector('input[name="old_password"]');
        const newPassword1Field = passwordForm.querySelector('input[name="new_password1"]');
        const newPassword2Field = passwordForm.querySelector('input[name="new_password2"]');
        
        passwordForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Always prevent default, we'll submit manually if valid
            
            const submitBtn = this.querySelector('.btn-save');
            const oldPassword = oldPasswordField.value;
            const newPassword1 = newPassword1Field.value;
            const newPassword2 = newPassword2Field.value;
            
            // Clear previous error messages
            clearFormErrors(passwordForm);
            
            // First check if old password is provided
            if (!oldPassword || oldPassword.trim() === '') {
                showValidationErrors(passwordForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                return false;
            }
            
            // Show loading state for password verification
            setLoadingState(submitBtn, true, 'Verificando senha...');
            setInputValidationState(oldPasswordField, 'validating');
            
            try {
                // Verify current password via AJAX
                const isCurrentPasswordValid = await verifyCurrentPassword(oldPassword);
                if (!isCurrentPasswordValid) {
                    setInputValidationState(oldPasswordField, 'invalid');
                    showValidationErrors(passwordForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                    return false;
                }
                
                setInputValidationState(oldPasswordField, 'valid');
                setLoadingState(submitBtn, true, 'Validando nova senha...');
                
                // Check new password requirements
                const newPasswordErrors = validateNewPassword(oldPassword, newPassword1, newPassword2);
                if (newPasswordErrors.length > 0) {
                    setInputValidationState(newPassword1Field, 'invalid');
                    setInputValidationState(newPassword2Field, 'invalid');
                    showValidationErrors(passwordForm, [{type: 'new_password', message: newPasswordErrors}]);
                    return false;
                }
                
                setInputValidationState(newPassword1Field, 'valid');
                setInputValidationState(newPassword2Field, 'valid');
                setLoadingState(submitBtn, true, 'Alterando senha...');
                
                // If all validations pass, submit the form
                this.submit();
            } finally {
                setLoadingState(submitBtn, false);
            }
        });
    }

    // Email form validation
    const emailForm = document.querySelector('form input[name="form_type"][value="email"]')?.closest('form');
    if (emailForm) {
        const currentEmailField = emailForm.querySelector('input[name="new_email"]');
        const passwordField = emailForm.querySelector('input[name="password"]');
        
        emailForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Always prevent default, we'll submit manually if valid
            
            const newEmail = currentEmailField.value;
            const password = passwordField.value;
            
            // Clear previous error messages
            clearFormErrors(emailForm);
            
            // First check if password is provided
            if (!password || password.trim() === '') {
                showValidationErrors(emailForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                return false;
            }
            
            // Verify current password via AJAX
            const isPasswordValid = await verifyCurrentPassword(password);
            if (!isPasswordValid) {
                showValidationErrors(emailForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                return false;
            }
            
            // Check new email requirements
            const newEmailErrors = validateNewEmail(newEmail);
            if (newEmailErrors.length > 0) {
                showValidationErrors(emailForm, [{type: 'new_email', message: newEmailErrors}]);
                return false;
            }
            
            // If all validations pass, submit the form
            this.submit();
        });
    }

    // Username form validation
    const usernameForm = document.querySelector('form input[name="form_type"][value="username"]')?.closest('form');
    if (usernameForm) {
        const newUsernameField = usernameForm.querySelector('input[name="new_username"]');
        const passwordField = usernameForm.querySelector('input[name="password"]');
        
        usernameForm.addEventListener('submit', async function(e) {
            e.preventDefault(); // Always prevent default, we'll submit manually if valid
            
            const newUsername = newUsernameField.value;
            const password = passwordField.value;
            
            // Clear previous error messages
            clearFormErrors(usernameForm);
            
            // First check if password is provided
            if (!password || password.trim() === '') {
                showValidationErrors(usernameForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                return false;
            }
            
            // Verify current password via AJAX
            const isPasswordValid = await verifyCurrentPassword(password);
            if (!isPasswordValid) {
                showValidationErrors(usernameForm, [{type: 'current_password', message: 'Senha atual incorreta.'}]);
                return false;
            }
            
            // Check new username requirements
            const newUsernameErrors = validateNewUsername(newUsername);
            if (newUsernameErrors.length > 0) {
                showValidationErrors(usernameForm, [{type: 'new_username', message: newUsernameErrors}]);
                return false;
            }
            
            // If all validations pass, submit the form
            this.submit();
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

/**
 * Verify current password via AJAX
 * @param {string} currentPassword 
 * @returns {Promise<boolean>}
 */
async function verifyCurrentPassword(currentPassword) {
    try {
        const response = await fetch('/accounts/verify-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                current_password: currentPassword
            })
        });
        
        const data = await response.json();
        return data.valid === true;
    } catch (error) {
        console.error('Error verifying password:', error);
        return false;
    }
}

/**
 * Validate new password requirements
 * @param {string} oldPassword 
 * @param {string} newPassword1 
 * @param {string} newPassword2 
 * @returns {string} Formatted error message or empty string if valid
 */
function validateNewPassword(oldPassword, newPassword1, newPassword2) {
    const passwordErrors = [];
    
    if (newPassword1) {
        // Check length
        if (newPassword1.length < 8) {
            passwordErrors.push('Senha muito curta: É preciso pelo menos 8 caracteres');
        }
        
        // Check if entirely numeric
        if (/^\d+$/.test(newPassword1)) {
            passwordErrors.push('Esta senha é inteiramente numérica');
        }
        
        // Check common passwords (basic check)
        const commonPasswords = ['12345678', 'password', 'senha123', '123456789', 'qwerty123'];
        if (commonPasswords.includes(newPassword1.toLowerCase())) {
            passwordErrors.push('Esta senha é muito comum');
        }
        
        // Check if passwords match
        if (newPassword2 && newPassword1 !== newPassword2) {
            passwordErrors.push('As novas senhas não coincidem');
        }
        
        // Check if different from old password
        if (oldPassword && newPassword1 === oldPassword) {
            passwordErrors.push('A nova senha deve ser diferente da senha atual');
        }
    }
    
    if (passwordErrors.length > 0) {
        if (passwordErrors.length === 1) {
            return passwordErrors[0];
        } else {
            const errorList = passwordErrors.map((error, index) => `${index + 1}. ${error}`).join(';\n');
            return `Por favor, se atente a esses detalhes para a nova senha:\n${errorList}.`;
        }
    }
    
    return '';
}

/**
 * Validate new email requirements
 * @param {string} newEmail 
 * @returns {string} Formatted error message or empty string if valid
 */
function validateNewEmail(newEmail) {
    const emailErrors = [];
    
    if (newEmail) {
        // Check if email format is valid (basic check)
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(newEmail)) {
            emailErrors.push('Formato de email inválido');
        }
        
        // Additional client-side checks can be added here
        // Note: Server-side will check for uniqueness and same email validation
    }
    
    if (emailErrors.length > 0) {
        if (emailErrors.length === 1) {
            return emailErrors[0];
        } else {
            const errorList = emailErrors.map((error, index) => `${index + 1}. ${error}`).join(';\n');
            return `Por favor, se atente a esses detalhes para o novo email:\n${errorList}.`;
        }
    }
    
    return '';
}

/**
 * Validate new username requirements
 * @param {string} newUsername 
 * @returns {string} Formatted error message or empty string if valid
 */
function validateNewUsername(newUsername) {
    const usernameErrors = [];
    
    if (newUsername) {
        // Check if username is different from current (get current username from page)
        const currentUsername = document.querySelector('input[value*="@"]')?.closest('form')?.querySelector('input[disabled]')?.value;
        const displayedUsername = document.querySelector('.profile-username')?.textContent?.replace('@', '');
        if (displayedUsername && newUsername === displayedUsername) {
            return 'O novo nome de usuário deve ser diferente do atual.';
        }
        
        // Check username length
        if (newUsername.length < 3) {
            usernameErrors.push('Nome de usuário muito curto: É preciso pelo menos 3 caracteres');
        } else if (newUsername.length > 150) {
            usernameErrors.push('Nome de usuário muito longo: Máximo de 150 caracteres');
        }
        
        // Check if username contains only valid characters
        const usernameRegex = /^[\w.@+-]+$/;
        if (!usernameRegex.test(newUsername)) {
            usernameErrors.push('Nome de usuário contém caracteres inválidos. Use apenas letras, números e @/./+/-/_');
        }
        
        // Additional client-side checks can be added here
        // Note: Server-side will check for uniqueness validation
    }
    
    if (usernameErrors.length > 0) {
        if (usernameErrors.length === 1) {
            return usernameErrors[0];
        } else {
            const errorList = usernameErrors.map((error, index) => `${index + 1}. ${error}`).join(';\n');
            return `Por favor, se atente a esses detalhes para o novo nome de usuário:\n${errorList}.`;
        }
    }
    
    return '';
}

/**
 * Clear form error messages
 * @param {HTMLElement} form 
 */
function clearFormErrors(form) {
    const existingErrors = form.closest('.setting-content').querySelectorAll('.client-side-error');
    existingErrors.forEach(error => error.remove());
}

/**
 * Show validation errors in the form
 * @param {HTMLElement} form 
 * @param {Array} errors 
 */
function showValidationErrors(form, errors) {
    // Clear existing errors first
    clearFormErrors(form);
    
    // Add new error messages
    const formContent = form.closest('.setting-content');
    const formElement = formContent.querySelector('form');
    
    errors.forEach(error => {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger client-side-error';
        errorDiv.style.whiteSpace = 'pre-line';
        errorDiv.textContent = error.message;
        
        formElement.insertAdjacentElement('beforebegin', errorDiv);
    });
}

/**
 * Clear all messages on page load/reload
 */
function clearAllMessages() {
    // Clear server-side messages
    const serverMessages = document.querySelectorAll('.form-errors .alert, .messages-container .alert');
    serverMessages.forEach(message => {
        message.style.display = 'none';
    });
    
    // Clear client-side messages
    const clientMessages = document.querySelectorAll('.client-side-error');
    clientMessages.forEach(message => message.remove());
    
    // Clear global messages at top of page
    const globalMessages = document.querySelectorAll('.messages-container');
    globalMessages.forEach(container => {
        container.style.display = 'none';
    });
}

/**
 * Initialize password toggle functionality
 */
function initializePasswordToggles() {
    const passwordToggles = document.querySelectorAll('.password-toggle');
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.dataset.target;
            const passwordField = document.getElementById(targetId);
            const eyeIcon = this.querySelector('.eye-icon');
            
            if (passwordField) {
                if (passwordField.type === 'password') {
                    passwordField.type = 'text';
                    // Change to "eye-off" icon (crossed eye)
                    eyeIcon.innerHTML = `
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                        <line x1="1" y1="1" x2="23" y2="23"/>
                    `;
                    this.setAttribute('aria-label', 'Ocultar senha');
                } else {
                    passwordField.type = 'password';
                    // Change to normal "eye" icon
                    eyeIcon.innerHTML = `
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    `;
                    this.setAttribute('aria-label', 'Mostrar senha');
                }
            }
        });
        
        // Set initial aria-label
        toggle.setAttribute('aria-label', 'Mostrar senha');
    });
}

/**
 * Initialize username availability checking
 */
function initializeUsernameAvailabilityCheck() {
    const usernameInput = document.querySelector('input[name="new_username"]');
    const availabilityIndicator = document.getElementById('username-availability');
    
    if (!usernameInput || !availabilityIndicator) return;
    
    let checkTimeout;
    
    usernameInput.addEventListener('input', function() {
        const username = this.value.trim();
        
        // Clear previous timeout
        clearTimeout(checkTimeout);
        
        // Hide indicator if input is empty
        if (!username) {
            hideAvailabilityIndicator(availabilityIndicator);
            return;
        }
        
        // Show checking state
        showAvailabilityIndicator(availabilityIndicator, 'checking', '⏳', 'Verificando...');
        
        // Debounce the API call
        checkTimeout = setTimeout(() => {
            checkUsernameAvailability(username, availabilityIndicator);
        }, 500);
    });
}

/**
 * Check username availability via AJAX
 * @param {string} username 
 * @param {HTMLElement} indicator 
 */
async function checkUsernameAvailability(username, indicator) {
    try {
        const response = await fetch(`/accounts/check-username/?username=${encodeURIComponent(username)}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const data = await response.json();
        
        if (data.available) {
            showAvailabilityIndicator(indicator, 'available', '✓', 'Disponível');
        } else {
            let message = 'Indisponível';
            if (data.error === 'same_as_current') {
                message = 'Mesmo usuário atual';
            } else if (data.error === 'taken') {
                message = 'Já está em uso';
            } else if (data.error === 'reserved') {
                message = 'Nome reservado';
            }
            showAvailabilityIndicator(indicator, 'unavailable', '✗', message);
        }
    } catch (error) {
        console.error('Error checking username availability:', error);
        showAvailabilityIndicator(indicator, 'unavailable', '⚠️', 'Erro na verificação');
    }
}

/**
 * Show availability indicator with status
 * @param {HTMLElement} indicator 
 * @param {string} status 
 * @param {string} icon 
 * @param {string} text 
 */
function showAvailabilityIndicator(indicator, status, icon, text) {
    const iconElement = indicator.querySelector('.availability-icon');
    const textElement = indicator.querySelector('.availability-text');
    
    // Remove all status classes
    indicator.classList.remove('available', 'unavailable', 'checking');
    
    // Add new status class
    indicator.classList.add(status, 'show');
    
    // Update content
    iconElement.textContent = icon;
    textElement.textContent = text;
}

/**
 * Hide availability indicator
 * @param {HTMLElement} indicator 
 */
function hideAvailabilityIndicator(indicator) {
    indicator.classList.remove('show', 'available', 'unavailable', 'checking');
}

/**
 * Initialize loading states for all forms
 */
function initializeLoadingStates() {
    // Store original button texts
    const buttons = document.querySelectorAll('.btn-save');
    buttons.forEach(btn => {
        btn.dataset.originalText = btn.textContent;
    });
}

/**
 * Set loading state for button
 * @param {HTMLElement} button 
 * @param {boolean} loading 
 * @param {string} loadingText 
 */
function setLoadingState(button, loading, loadingText = 'Carregando...') {
    if (loading) {
        button.disabled = true;
        button.classList.add('loading');
        button.textContent = loadingText;
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        button.textContent = button.dataset.originalText || 'Salvar';
    }
}

/**
 * Set validation state for input field
 * @param {HTMLElement} input 
 * @param {string} state - 'validating', 'valid', 'invalid', or null to clear
 */
function setInputValidationState(input, state) {
    // Clear all validation states
    input.classList.remove('validating', 'valid', 'invalid');
    
    // Add new state if provided
    if (state) {
        input.classList.add(state);
    }
}

/**
 * Initialize network monitoring
 */
function initializeNetworkMonitoring() {
    const networkStatus = document.getElementById('network-status');
    const statusIcon = networkStatus.querySelector('.status-icon');
    const statusText = networkStatus.querySelector('.status-text');
    
    // Monitor online/offline status
    window.addEventListener('online', function() {
        networkStatus.classList.remove('offline');
        setTimeout(() => {
            networkStatus.style.display = 'none';
        }, 2000);
    });
    
    window.addEventListener('offline', function() {
        networkStatus.classList.add('offline');
        statusIcon.textContent = '📡';
        statusText.textContent = 'Sem conexão';
        networkStatus.style.display = 'flex';
    });
    
    // Monitor slow connections (timeout after 10 seconds)
    let slowConnectionTimeout;
    
    // Override fetch to monitor request times
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const startTime = Date.now();
        
        // Show slow connection warning after 5 seconds
        slowConnectionTimeout = setTimeout(() => {
            networkStatus.classList.add('slow');
            networkStatus.classList.remove('offline');
            statusIcon.textContent = '🐌';
            statusText.textContent = 'Conexão lenta';
            networkStatus.style.display = 'flex';
        }, 5000);
        
        return originalFetch.apply(this, args).then(response => {
            clearTimeout(slowConnectionTimeout);
            const responseTime = Date.now() - startTime;
            
            // Hide slow connection warning
            networkStatus.classList.remove('slow');
            if (!navigator.onLine) {
                networkStatus.classList.add('offline');
            } else {
                setTimeout(() => {
                    networkStatus.style.display = 'none';
                }, 1000);
            }
            
            return response;
        }).catch(error => {
            clearTimeout(slowConnectionTimeout);
            networkStatus.classList.remove('slow');
            
            // Show offline if it's a network error
            if (!navigator.onLine) {
                networkStatus.classList.add('offline');
                statusIcon.textContent = '📡';
                statusText.textContent = 'Sem conexão';
                networkStatus.style.display = 'flex';
            }
            
            throw error;
        });
    };
}