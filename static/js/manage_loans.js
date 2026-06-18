// Auto-close alerts after 5 seconds
setTimeout(function() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const bsAlert = new bootstrap.Alert(alert);
    bsAlert.close();
  });
}, 5000);

// Filter button functionality — submits the form with the selected status
function setFilter(button, filter) {
  const allButtons = document.querySelectorAll('.fbtn');
  allButtons.forEach(btn => btn.classList.remove('active-todos'));
  button.classList.add('active-todos');

  const statusInput = document.getElementById('statusInput');
  if (statusInput) statusInput.value = filter;

  const form = document.getElementById('loansFilterForm');
  if (form) {
    const pageInput = form.querySelector('input[name="page"]');
    if (pageInput) pageInput.remove();
    form.submit();
  }
}

function initializeLoansSearch() {
  const searchInput = document.getElementById('loansSearchInput');
  if (!searchInput) return;

  let debounceTimer;
  searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const form = document.getElementById('loansFilterForm');
      if (form) {
        const pageInput = form.querySelector('input[name="page"]');
        if (pageInput) pageInput.remove();
        form.submit();
      }
    }, 400);
  });
}

// Auto-open modal if book is pre-selected or there are form errors
document.addEventListener('DOMContentLoaded', function() {
  // Initialize search functionality
  initializeLoansSearch();
  
  const shouldOpenModal = (window.preselectedBookTitle && window.preselectedBookAuthor) || window.hasFormErrors;
  
  if (shouldOpenModal) {
    const modal = new bootstrap.Modal(document.getElementById('newLoanModal'));
    modal.show();
    
    // Set up the book field when the modal is shown (only if preselected)
    if (window.preselectedBookTitle && window.preselectedBookAuthor) {
      const modalElement = document.getElementById('newLoanModal');
      modalElement.addEventListener('shown.bs.modal', function () {
        setupPreselectedBook();
      });
    }
  }
});

function setupPreselectedBook() {
  const bookTitle = window.preselectedBookTitle;
  const bookAuthor = window.preselectedBookAuthor;
  const bookId = window.preselectedBookId;
  
  if (bookTitle && bookAuthor) {
    const bookSearchInput = document.querySelector('input[name="book_search"]');
    const bookHiddenInput = document.querySelector('input[name="book"]');
    
    if (bookSearchInput && bookHiddenInput) {
      // Set the visible search input
      const displayText = `${bookTitle} - ${bookAuthor}`;
      bookSearchInput.value = displayText;
      
      // If we have the book ID from backend, use it directly
      if (bookId) {
        bookHiddenInput.value = bookId;
        bookSearchInput.classList.add('has-selection');
        
        // Trigger change events for validation
        bookSearchInput.dispatchEvent(new Event('change', { bubbles: true }));
        bookHiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        // Fallback: search for the book ID via AJAX
        fetch(`/accounts/autocomplete/books/?q=${encodeURIComponent(bookTitle)}`, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
          }
        })
        .then(response => response.json())
        .then(data => {
          const results = data.results || [];
          // Find exact match by title and author
          const exactMatch = results.find(book => 
            book.title === bookTitle && book.author === bookAuthor
          );
          
          if (exactMatch) {
            bookHiddenInput.value = exactMatch.id;
            bookSearchInput.classList.add('has-selection');
            
            // Trigger change events for validation
            bookSearchInput.dispatchEvent(new Event('change', { bubbles: true }));
            bookHiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
          }
        })
        .catch(error => {
          console.error('Error fetching book data:', error);
        });
      }
    }
  }
}