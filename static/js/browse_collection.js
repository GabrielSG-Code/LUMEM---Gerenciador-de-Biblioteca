// Search functionality with server-side filtering
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;

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

// Add Book Modal Functions
function openAddBookModal() {
    document.getElementById('addBookModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeAddBookModal() {
    document.getElementById('addBookModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    
    // Reset form
    document.querySelector('.book-form').reset();
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