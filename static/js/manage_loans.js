// Auto-close alerts after 5 seconds
setTimeout(function() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const bsAlert = new bootstrap.Alert(alert);
    bsAlert.close();
  });
}, 5000);

// Dynamic search and filter functionality
let allLoansRows = [];
let filteredRows = [];
let searchQuery = '';
let currentFilter = 'todos';

// Initialize search functionality when DOM is loaded
function initializeLoansSearch() {
  const searchInput = document.getElementById('loansSearchInput');
  const tableBody = document.querySelector('.table tbody');
  
  if (!searchInput || !tableBody) return;
  
  // Store original table rows
  allLoansRows = Array.from(tableBody.children);
  filteredRows = [...allLoansRows];
  
  // Add real-time search event
  searchInput.addEventListener('input', function(e) {
    searchQuery = e.target.value.toLowerCase().trim();
    filterLoansTable();
  });
}

function filterLoansTable() {
  const tableBody = document.querySelector('.table tbody');
  if (!tableBody) return;
  
  // Apply both search and status filters
  filteredRows = allLoansRows.filter(row => {
    // Check search query match - only search in username column (1st column, index 0)
    let matchesSearch = true;
    if (searchQuery !== '') {
      const usernameCell = row.cells[0]; // Username column (1st column, 0-indexed)
      const username = usernameCell ? usernameCell.textContent.toLowerCase() : '';
      matchesSearch = username.includes(searchQuery);
    }
    
    // Check status filter match
    const matchesStatus = getStatusMatch(row, currentFilter);
    
    return matchesSearch && matchesStatus;
  });
  
  // Update table display
  updateTableDisplay();
}

function getStatusMatch(row, filter) {
  if (filter === 'todos') {
    return true; // Show all statuses
  }
  
  const statusCell = row.cells[5]; // Status column (6th column, 0-indexed)
  if (!statusCell) return false;
  
  const statusText = statusCell.textContent.toLowerCase().trim();
  
  switch (filter) {
    case 'ativo':
      return statusText === 'ativo';
    case 'atrasado':
      return statusText === 'atrasado';
    case 'devolvido':
      return statusText === 'devolvido';
    default:
      return true;
  }
}

function updateTableDisplay() {
  const tableBody = document.querySelector('.table tbody');
  if (!tableBody) return;
  
  // Clear current table
  tableBody.innerHTML = '';
  
  if (filteredRows.length > 0) {
    // Add filtered rows
    filteredRows.forEach(row => {
      tableBody.appendChild(row.cloneNode(true));
    });
  } else {
    // Show no results message
    const noResultsRow = document.createElement('tr');
    noResultsRow.innerHTML = `
      <td colspan="7" style="text-align: center; padding: 40px 20px; color: var(--muted); font-style: italic;">
        ${searchQuery ? `Nenhum empréstimo encontrado para "${searchQuery}"` : 'Nenhum empréstimo encontrado'}
      </td>
    `;
    tableBody.appendChild(noResultsRow);
  }
  
  // Update event listeners for action buttons in filtered rows
  updateActionButtonListeners();
}

function updateActionButtonListeners() {
  // Re-attach event listeners to return buttons in filtered results
  const returnButtons = document.querySelectorAll('.btn-return');
  returnButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      if (!confirm('Confirmar devolução?')) {
        e.preventDefault();
      }
    });
  });
}

// Filter button functionality
function setFilter(button, filter) {
  // Update current filter
  currentFilter = filter;
  
  // Update button states
  const allButtons = document.querySelectorAll('.fbtn');
  allButtons.forEach(btn => btn.classList.remove('active-todos'));
  button.classList.add('active-todos');
  
  // Apply filters
  filterLoansTable();
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