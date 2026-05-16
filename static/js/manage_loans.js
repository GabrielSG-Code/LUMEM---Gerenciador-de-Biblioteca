// Auto-close alerts after 5 seconds
setTimeout(function() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const bsAlert = new bootstrap.Alert(alert);
    bsAlert.close();
  });
}, 5000);

// Auto-open modal if book is pre-selected (check URL params)
document.addEventListener('DOMContentLoaded', function() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('book_title') && urlParams.has('book_author')) {
    const modal = new bootstrap.Modal(document.getElementById('newLoanModal'));
    modal.show();
  }
});