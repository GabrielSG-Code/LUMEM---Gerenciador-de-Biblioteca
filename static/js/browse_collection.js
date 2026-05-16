// Search functionality with server-side filtering
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;

    if (searchInput) {
        // Search functionality - submit form on input with debounce
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const form = this.closest('form');
                if (form) {
                    form.submit();
                }
            }, 500); // 500ms delay to avoid too many requests
        });

        // Submit form on Enter key
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(searchTimeout);
                const form = this.closest('form');
                if (form) {
                    form.submit();
                }
            }
        });
    }

    // Setup book form event listeners
    const bookForm = document.querySelector('.book-form');
    if (bookForm) {
        // Form validation listeners
        const inputs = bookForm.querySelectorAll('input[required], select[required]');
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                clearTimeout(window.validationTimeout);
                window.validationTimeout = setTimeout(() => {
                    updateSubmitButton('validating');
                    setTimeout(() => validateForm(), 300);
                }, 200);
            });
        });
        
        // Form submission handler
        bookForm.addEventListener('submit', function(e) {
            console.log('Form submission started, formState:', formState);
            
            if (formState === 'submitting') {
                console.log('Form already submitting, preventing duplicate submission');
                e.preventDefault();
                return;
            }
            
            // Validate form before submission
            if (!validateForm()) {
                console.log('Form validation failed');
                e.preventDefault();
                updateSubmitButton('error', 'Preencha todos os campos obrigatórios');
                return;
            }
            
            console.log('Form is valid, proceeding with submission');
            updateSubmitButton('submitting');
            // Allow form to submit normally - don't prevent default
        });
    }
});

// Book Detail Modal Functions
function openBookDetailModal(title, author, category, year, publisher, exemplary, description, availableCount) {
    document.getElementById('detailTitle').textContent = title;
    document.getElementById('detailAuthor').textContent = `por ${author}`;
    document.getElementById('detailYear').textContent = year;
    document.getElementById('detailPublisher').textContent = publisher;
    document.getElementById('detailCategory').textContent = getCategoryDisplayName(category);
    
    // Handle exemplary count display
    if (exemplary === 1) {
        document.getElementById('detailExemplary').textContent = '1 exemplar';
    } else {
        document.getElementById('detailExemplary').textContent = `${exemplary} exemplares`;
    }
    
    document.getElementById('detailDescription').textContent = description;
    
    // Store available count for borrowBook function
    window.currentBookAvailableCount = availableCount || 0;
    
    document.getElementById('bookDetailModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeBookDetailModal() {
    document.getElementById('bookDetailModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function borrowBook() {
    // Check if book has available copies
    if (window.currentBookAvailableCount <= 0) {
        alert('Não é possível realizar o empréstimo: não há exemplares disponíveis para este livro no momento.');
        return;
    }
    
    const title = document.getElementById('detailTitle').textContent;
    const author = document.getElementById('detailAuthor').textContent.replace('por ', '');
    
    // Redirect to loans page with book pre-selected
    const params = new URLSearchParams({
        book_title: title,
        book_author: author
    });
    window.location.href = `/accounts/loans/?${params.toString()}`;
}

// Helper function for category display names
function getCategoryDisplayName(category) {
    // Simply return the category as-is since we now use proper category names from the database
    // The category names are already in the correct format from the database
    return category || 'Outros';
}

// SVG Icons for different states
const SVG_ICONS = {
    add: '<path d="M12 5V19M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    loading: '<circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"><animate attributeName="stroke-dasharray" values="0 18.84;9.42 9.42;0 18.84" dur="1.5s" repeatCount="indefinite"/><animate attributeName="stroke-dashoffset" values="0;-9.42;-18.84" dur="1.5s" repeatCount="indefinite"/></circle>',
    success: '<path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    error: '<path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
};

// Form state management
let formState = 'idle'; // idle, validating, submitting, success, error

function updateSubmitButton(state, message = null) {
    const submitBtn = document.getElementById('submitBtn');
    const submitIcon = document.getElementById('submitIcon');
    const submitText = document.getElementById('submitText');
    
    if (!submitBtn || !submitIcon || !submitText) return;
    
    formState = state;
    
    switch(state) {
        case 'validating':
            submitIcon.innerHTML = SVG_ICONS.loading;
            submitText.textContent = 'Validando...';
            submitBtn.disabled = true;
            submitBtn.classList.add('validating');
            break;
        case 'submitting':
            submitIcon.innerHTML = SVG_ICONS.loading;
            submitText.textContent = 'Adicionando...';
            submitBtn.disabled = true;
            submitBtn.classList.add('submitting');
            break;
        case 'success':
            submitIcon.innerHTML = SVG_ICONS.success;
            submitText.textContent = message || 'Livro Adicionado!';
            submitBtn.disabled = true;
            submitBtn.classList.add('success');
            setTimeout(() => resetSubmitButton(), 2000);
            break;
        case 'error':
            submitIcon.innerHTML = SVG_ICONS.error;
            submitText.textContent = message || 'Erro ao Adicionar';
            submitBtn.disabled = false;
            submitBtn.classList.add('error');
            setTimeout(() => resetSubmitButton(), 3000);
            break;
        case 'valid':
            submitIcon.innerHTML = SVG_ICONS.success;
            submitText.textContent = 'Adicionar Livro';
            submitBtn.disabled = false;
            submitBtn.classList.add('valid');
            break;
        default: // idle
            resetSubmitButton();
    }
}

function resetSubmitButton() {
    const submitBtn = document.getElementById('submitBtn');
    const submitIcon = document.getElementById('submitIcon');
    const submitText = document.getElementById('submitText');
    
    if (!submitBtn || !submitIcon || !submitText) return;
    
    submitIcon.innerHTML = SVG_ICONS.add;
    submitText.textContent = 'Adicionar Livro';
    submitBtn.disabled = false;
    submitBtn.className = 'btn-primary';
    formState = 'idle';
}

// Form validation
function validateForm() {
    const form = document.querySelector('.book-form');
    if (!form) return false;
    
    const title = form.querySelector('#bookTitle').value.trim();
    const author = form.querySelector('#bookAuthor').value.trim();
    const category = form.querySelector('#bookCategory').value;
    const exemplary = form.querySelector('#bookExemplary').value;
    
    const isValid = title && author && category && exemplary && parseInt(exemplary) > 0;
    
    if (isValid) {
        updateSubmitButton('valid');
    } else {
        updateSubmitButton('idle');
    }
    
    return isValid;
}

// Add Book Modal Functions
function openAddBookModal() {
    document.getElementById('addBookModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
    resetSubmitButton();
}

function closeAddBookModal() {
    document.getElementById('addBookModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Reset form and button
    const form = document.querySelector('.book-form');
    if (form) {
        form.reset();
    }
    resetSubmitButton();
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const addModal = document.getElementById('addBookModal');
    const detailModal = document.getElementById('bookDetailModal');
    
    if (event.target === addModal) {
        closeAddBookModal();
    }
    
    if (event.target === detailModal) {
        closeBookDetailModal();
    }
});