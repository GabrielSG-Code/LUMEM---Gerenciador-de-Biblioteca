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
function openBookDetailModal(title, author, category, year, publisher, exemplary, description, availableCount, bookId) {
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
    
    // Store available count for borrowBook function only
    window.currentBookAvailableCount = availableCount || 0;
    
    document.getElementById('bookDetailModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeBookDetailModal() {
    document.getElementById('bookDetailModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Clear only book detail related data
    window.currentBookAvailableCount = null;
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

// Edit Book Modal Functions
function openEditBookModal() {
    // Clear all form fields - don't pre-fill anything
    document.getElementById('editBookTitle').value = '';
    document.getElementById('editBookAuthor').value = '';
    document.getElementById('editBookYear').value = '';
    document.getElementById('editBookPublisher').value = '';
    document.getElementById('editBookCategory').value = '';
    document.getElementById('editBookCopies').value = '';
    document.getElementById('editBookDescription').value = '';
    
    // Clear any existing search results
    hideSearchResults();
    
    // Show edit modal independently
    document.getElementById('editBookModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Clear current book data since we're starting fresh
    window.currentBookData = null;
    window.originalBookData = null;
}

function closeEditBookModal() {
    document.getElementById('editBookModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Clear form data
    window.currentBookData = null;
    window.originalBookData = null;
    hideSearchResults();
}

// Handle edit book form submission
document.addEventListener('DOMContentLoaded', function() {
    const editBookForm = document.getElementById('editBookForm');
    if (editBookForm) {
        editBookForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitEditBookForm();
        });
    }
});

function submitEditBookForm() {
    const form = document.getElementById('editBookForm');
    const submitBtn = document.getElementById('editSubmitBtn');
    
    // Get form data
    const formData = new FormData(form);
    const title = formData.get('title').trim();
    const author = formData.get('author').trim();
    const year = formData.get('year') || '';
    const publisher = formData.get('publisher') || '';
    const category = formData.get('category') || '';
    const description = formData.get('description') || '';
    const copies = parseInt(formData.get('copies')) || 1;
    
    // Validate required fields
    if (!title || !author || !category) {
        alert('Por favor, preencha todos os campos obrigatórios.');
        return;
    }
    
    // Check if a book has been selected from search
    if (!window.currentBookData || !window.currentBookData.id) {
        alert('Por favor, selecione um livro existente usando a pesquisa no campo título.');
        return;
    }
    
    // Check if any data has changed - using the same logic as Django EditBookForm
    if (!window.originalBookData) {
        alert('Erro: dados originais não encontrados.');
        return;
    }
    
    const originalData = window.originalBookData;
    
    // Match exactly the Django form validation logic (forms.py lines 658-664)
    const titleChanged = title !== (originalData.titulo || '');
    const authorChanged = author !== (originalData.autor || '');
    
    // Handle year comparison carefully - convert empty string to null for comparison
    const currentYear = year === '' ? null : (year ? parseInt(year) : null);
    const originalYear = originalData.ano || null;
    const yearChanged = currentYear !== originalYear;
    
    const publisherChanged = publisher !== (originalData.editora || '');
    const categoryChanged = category !== (originalData.genero || '');
    const descriptionChanged = description !== (originalData.descricao || '');
    const copiesChanged = copies !== (originalData.total_count || 1);
    
    const hasChanges = titleChanged || authorChanged || yearChanged || publisherChanged || categoryChanged || descriptionChanged || copiesChanged;
    
    if (!hasChanges) {
        alert('Nenhuma alteração foi detectada. Modifique pelo menos um campo para salvar as alterações.');
        return;
    }
    
    // Disable submit button and show loading
    submitBtn.disabled = true;
    submitBtn.querySelector('span').textContent = 'Salvando...';
    
    // Use the selected book ID
    const bookId = window.currentBookData.id;
    
    // Submit the form data
    fetch(`/accounts/edit_book/${bookId}/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            submitBtn.querySelector('span').textContent = 'Salvo!';
            submitBtn.classList.add('success');
            
            // Update current book data
            window.currentBookData = {
                id: bookId,
                title: formData.get('title'),
                author: formData.get('author'),
                year: formData.get('year'),
                publisher: formData.get('publisher'),
                category: formData.get('category'),
                exemplary: parseInt(formData.get('copies'))
            };
            
            // Close modal and refresh page after short delay
            setTimeout(() => {
                closeEditBookModal();
                location.reload(); // Refresh to show updated data
            }, 1000);
        } else {
            // Show error message
            alert('Erro ao salvar: ' + data.error);
            submitBtn.disabled = false;
            submitBtn.querySelector('span').textContent = 'Salvar Alterações';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro de conexão. Tente novamente.');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').textContent = 'Salvar Alterações';
    });
}

// Helper function to get book ID (we'll need to modify template to include this)
function getBookIdFromData(title, author) {
    // This is a placeholder - we'll need to include book IDs in the template
    return 1; // This should be replaced with actual book ID logic
}

// Search functionality for existing books
let searchTimeout;
function searchExistingBooks(query) {
    clearTimeout(searchTimeout);
    
    if (!query || query.length < 2) {
        hideSearchResults();
        return;
    }
    
    searchTimeout = setTimeout(() => {
        // Search for existing books using the API endpoint
        fetch(`/accounts/search-books/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.results) {
                    displaySearchResults(data.results);
                } else {
                    hideSearchResults();
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                hideSearchResults();
            });
    }, 300);
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById('bookSearchResults');
    
    if (results.length === 0) {
        hideSearchResults();
        return;
    }
    
    let html = '';
    results.forEach(result => {
        const escapedTitle = result.title.replace(/'/g, "\\'");
        const escapedAuthor = result.author.replace(/'/g, "\\'");
        const escapedCategory = result.category.replace(/'/g, "\\'");
        const escapedPublisher = (result.publisher || '').replace(/'/g, "\\'");
        
        const escapedDescription = (result.description || '').replace(/'/g, "\\'");
        
        html += `
            <div class="search-result-item" onclick="selectSearchResult('${escapedTitle}', '${escapedAuthor}', '${escapedCategory}', ${result.year || 'null'}, '${escapedPublisher}', '${escapedDescription}', ${result.total_copies || 1}, ${result.id})">
                <div class="result-title">${result.title}</div>
                <div class="result-author">por ${result.author}</div>
                <div class="result-category">${result.category} • ${result.total_copies} exemplar(es)</div>
            </div>
        `;
    });
    
    resultsContainer.innerHTML = html;
    resultsContainer.style.display = 'block';
}

function selectSearchResult(title, author, category, year, publisher, description, copies, bookId) {
    // Fill form with selected book data
    document.getElementById('editBookTitle').value = title;
    document.getElementById('editBookAuthor').value = author;
    
    // Set category dropdown value - find exact match or closest match
    const categorySelect = document.getElementById('editBookCategory');
    const categoryOptions = categorySelect.options;
    let foundMatch = false;
    
    // First try exact match
    for (let i = 0; i < categoryOptions.length; i++) {
        if (categoryOptions[i].value === category) {
            categorySelect.selectedIndex = i;
            foundMatch = true;
            break;
        }
    }
    
    // If no exact match, try case-insensitive match
    if (!foundMatch) {
        for (let i = 0; i < categoryOptions.length; i++) {
            if (categoryOptions[i].value.toLowerCase() === category.toLowerCase()) {
                categorySelect.selectedIndex = i;
                foundMatch = true;
                break;
            }
        }
    }
    
    // If still no match, log warning but continue
    if (!foundMatch) {
        console.warn(`Category "${category}" not found in dropdown options`);
        categorySelect.selectedIndex = 0; // Select "Selecione uma categoria"
    }
    
    document.getElementById('editBookYear').value = year || '';
    document.getElementById('editBookPublisher').value = publisher || '';
    document.getElementById('editBookDescription').value = description || '';
    document.getElementById('editBookCopies').value = copies || 1;
    
    // Set up the current book data with the selected book information
    window.currentBookData = {
        id: bookId,
        title: title,
        author: author,
        category: category,
        year: year,
        publisher: publisher,
        description: description,
        exemplary: copies
    };
    
    // Store original data in the format expected by Django form validation
    // This matches the field names used in the Django EditBookForm
    window.originalBookData = {
        titulo: title,           // matches Django field 'titulo' 
        autor: author,           // matches Django field 'autor'
        genero: category,        // matches Django field 'genero'
        ano: year,               // matches Django field 'ano'
        editora: publisher,      // matches Django field 'editora'
        descricao: description,  // matches Django field 'descricao'
        total_count: copies      // matches Django field 'total_count'
    };
    
    hideSearchResults();
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('bookSearchResults');
    resultsContainer.style.display = 'none';
    resultsContainer.innerHTML = '';
}

// Close search results when clicking outside
document.addEventListener('click', function(e) {
    const searchContainer = document.querySelector('.search-input-container');
    if (searchContainer && !searchContainer.contains(e.target)) {
        hideSearchResults();
    }
});

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const addModal = document.getElementById('addBookModal');
    const detailModal = document.getElementById('bookDetailModal');
    const editModal = document.getElementById('editBookModal');
    
    if (event.target === addModal) {
        closeAddBookModal();
    }
    
    if (event.target === detailModal) {
        closeBookDetailModal();
    }
    
    if (event.target === editModal) {
        closeEditBookModal();
    }
});