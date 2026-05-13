// Get Django user data - this will be populated by the template
let allUsers = [];

let currentFilter = 'Todos';
let currentSearch = '';
let editingIndex = null;
let currentPage = 1;
const usersPerPage = 10;

function getFilteredUsers() {
  const query = currentSearch.toLowerCase();
  return allUsers.filter(u => {
    const matchFilter = currentFilter === 'Todos' || u.role === currentFilter;
    const matchSearch = u.name.toLowerCase().includes(query) || u.email.toLowerCase().includes(query);
    return matchFilter && matchSearch;
  });
}

function renderTable() {
  const tbody = document.getElementById('userTable');
  const filteredUsers = getFilteredUsers();
  
  // Calculate pagination
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
  const startIndex = (currentPage - 1) * usersPerPage;
  const endIndex = startIndex + usersPerPage;
  const pageUsers = filteredUsers.slice(startIndex, endIndex);

  // Render table rows
  tbody.innerHTML = pageUsers.map((u) => `
    <tr>
      <td>
        <div class="user-cell">
          <div class="avatar ${u.avatarClass}">${u.initials}</div>
          <div>
            <div class="user-name">${u.name}</div>
            <div class="user-email">${u.email}</div>
          </div>
        </div>
      </td>
      <td><span class="badge ${u.badgeClass}">${u.role}</span></td>
      <td>
        <div class="status">
          <span class="status-dot ${u.active ? 'active' : 'inactive'}"></span>
          ${u.active ? 'Ativo' : 'Inativo'}
        </div>
      </td>
      <td><span class="last-access">${u.lastAccess}</span></td>
      <td><button class="btn-edit" onclick="openEdit(${allUsers.indexOf(u)})">Editar perfil</button></td>
    </tr>
  `).join('');

  // Render pagination
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const pagination = document.querySelector('.pagination');
  let paginationHTML = '';
  
  // Previous button
  if (currentPage > 1) {
    paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage - 1})">‹</button>`;
  }
  
  // Page numbers
  for (let i = 1; i <= totalPages; i++) {
    if (i === currentPage) {
      paginationHTML += `<button class="page-btn active" onclick="goToPage(${i})">${i}</button>`;
    } else if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 1) {
      paginationHTML += `<button class="page-btn" onclick="goToPage(${i})">${i}</button>`;
    } else if (i === currentPage - 2 || i === currentPage + 2) {
      paginationHTML += `<span class="page-ellipsis">...</span>`;
    }
  }
  
  // Next button
  if (currentPage < totalPages) {
    paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage + 1})">›</button>`;
  }
  
  pagination.innerHTML = paginationHTML;
}

function goToPage(page) {
  const filteredUsers = getFilteredUsers();
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
  
  if (page >= 1 && page <= totalPages) {
    currentPage = page;
    renderTable();
  }
}

function setFilter(f, btn) {
  currentFilter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentPage = 1; // Reset to first page when filter changes
  renderTable();
}

function filterUsers() {
  currentSearch = document.getElementById('searchInput').value;
  currentPage = 1; // Reset to first page when search changes
  renderTable();
}

function openEdit(idx) {
  editingIndex = idx;
  const u = allUsers[idx];
  document.getElementById('editUserName').textContent = u.name;
  document.getElementById('editUserRole').value = u.role;
  document.getElementById('editUserStatus').checked = u.active;
  updateToggleLabel();
  const modal = document.getElementById('editUserModal');
  modal.style.display = 'block';
}

function closeEditUserModal() {
  editingIndex = null;
  document.getElementById('editUserModal').style.display = 'none';
  // Reset form
  document.querySelector('.user-form').reset();
}

function updateToggleLabel() {
  const on = document.getElementById('editUserStatus').checked;
  document.getElementById('toggleLabel').textContent = on ? 'Ativo' : 'Inativo';
}

function handleEditUser(event) {
  event.preventDefault();
  
  if (editingIndex === null) return;
  
  // Get form data
  const formData = new FormData(event.target);
  const role = formData.get('role');
  const status = formData.get('status') === 'on';
  
  const u = allUsers[editingIndex];
  
  // Send AJAX request to Django backend
  fetch(`/accounts/users/update/${u.id}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      role: role,
      active: status
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Update local data
      u.role = role;
      u.active = status;
      
      // Update badge class
      const map = { 'Leitor':'badge-leitor', 'Administrador':'badge-admin', 'Bibliotecário':'badge-biblio' };
      u.badgeClass = map[u.role] || 'badge-leitor';
      
      // Re-render table, update statistics, and close modal
      updateStatistics();
      renderTable();
      closeEditUserModal();
      
      // Show success message
      alert(data.message);
    } else {
      alert(`Erro: ${data.message}`);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Erro ao atualizar usuário. Tente novamente.');
  });
}

// Close modal when clicking outside of it
window.onclick = function(event) {
  const modal = document.getElementById('editUserModal');
  if (event.target === modal) {
    closeEditUserModal();
  }
}

function updateStatistics() {
  const totalUsers = allUsers.length;
  const adminCount = allUsers.filter(u => u.role === 'Administrador').length;
  const librarianCount = allUsers.filter(u => u.role === 'Bibliotecário').length;
  const readerCount = allUsers.filter(u => u.role === 'Leitor').length;

  document.getElementById('total-users').textContent = totalUsers;
  document.getElementById('admin-count').textContent = adminCount;
  document.getElementById('librarian-count').textContent = librarianCount;
  document.getElementById('reader-count').textContent = readerCount;
}

// Initialize table on page load
document.addEventListener('DOMContentLoaded', function() {
  updateStatistics();
  renderTable();
});