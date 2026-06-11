// Get Django user data - this will be populated by the template
let allUsers = window.allUsers || [];

let currentTypeFilter = 'Todos';
let currentStatusFilter = 'Todos';
let currentSearch = '';
let editingIndex = null;
let currentPage = 1;
const usersPerPage = 10;

function getStatusClass(status) {
  switch(status) {
    case 'Ativo': return 'active';
    case 'Inativo': return 'inactive';
    case 'Bloqueado': return 'blocked';
    default: return 'active';
  }
}

function getFilteredUsers() {
  const query = currentSearch.toLowerCase();
  return allUsers.filter(u => {
    // Check type filter
    let matchType = true;
    if (currentTypeFilter !== 'Todos') {
      matchType = u.role === currentTypeFilter;
    }
    
    // Check status filter
    let matchStatus = true;
    if (currentStatusFilter !== 'Todos') {
      matchStatus = u.status === currentStatusFilter;
    }
    
    // Check search query
    const matchSearch = u.name.toLowerCase().includes(query) || u.email.toLowerCase().includes(query);
    
    return matchType && matchStatus && matchSearch;
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
  if (pageUsers.length > 0) {
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
        <td>
          <span class="badge ${u.badgeClass}">${u.role}</span>
          ${u.isSuperuser ? '<span class="superuser-badge">SUPER</span>' : ''}
        </td>
        <td>
          <div class="status">
            <span class="status-dot ${getStatusClass(u.status)}"></span>
            ${u.status}
          </div>
        </td>
        <td><span class="last-access">${u.lastAccess}</span></td>
        <td>
          ${u.canEdit 
            ? `<button class="btn-edit" onclick="openEdit(${allUsers.indexOf(u)})">Editar perfil</button>` 
            : `<button class="btn-edit btn-disabled" disabled title="Apenas superusuários podem editar outros superusuários">Protegido</button>`
          }
        </td>
      </tr>
    `).join('');
  } else {
    // Show empty state
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 40px 20px;">
          <div style="color: #6b7a99;">
            ${allUsers.length === 0 ? 'Nenhum usuário encontrado' : 'Nenhum usuário corresponde aos critérios de busca'}
          </div>
        </td>
      </tr>
    `;
  }

  // Render pagination
  renderPagination(totalPages);
}

function renderPagination(totalPages) {
  const pagination = document.querySelector('.pagination');
  let paginationHTML = '';
  
  // Only show pagination if there are multiple pages
  if (totalPages > 1) {
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

function applyFilters() {
  currentTypeFilter = document.getElementById('userTypeFilter').value;
  currentStatusFilter = document.getElementById('userStatusFilter').value;
  currentPage = 1; // Reset to first page when filter changes
  renderTable();
}

function resetFilters() {
  document.getElementById('userTypeFilter').value = 'Todos';
  document.getElementById('userStatusFilter').value = 'Todos';
  document.getElementById('searchInput').value = '';
  currentTypeFilter = 'Todos';
  currentStatusFilter = 'Todos';
  currentSearch = '';
  currentPage = 1;
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
  
  const statusSelect = document.getElementById('editUserStatus');
  
  // Handle blocked users - show damage and regularization sections
  const isBlocked = u.status === 'Bloqueado';
  const damageSection = document.getElementById('damageSection');
  const regularizationSection = document.getElementById('regularizationSection');
  const standardWarning = document.getElementById('standardWarning');
  const saveBtn = document.getElementById('saveChangesBtn');
  
  if (isBlocked) {
    // For blocked users, disable status dropdown and show only current status
    statusSelect.value = u.status;
    statusSelect.disabled = true;
    
    // Show damage and regularization sections
    damageSection.style.display = 'block';
    regularizationSection.style.display = 'block';
    standardWarning.style.display = 'none';
    
    // Update button text for regularization
    saveBtn.textContent = 'Regularizar Usuário';
    
    // Load damage information
    loadDamageInfo(u.id);
    
    // Reset regularization form
    document.getElementById('regularizationMethod').value = '';
    document.getElementById('regularizationNotes').value = '';
    
    // Make regularization method required
    document.getElementById('regularizationMethod').required = true;
    
    clearValidationErrors();
  } else {
    // For non-blocked users, enable status dropdown but remove "Bloqueado" option
    statusSelect.disabled = false;
    
    // Remove "Bloqueado" option if it exists
    const blockedOption = statusSelect.querySelector('option[value="Bloqueado"]');
    if (blockedOption) {
      blockedOption.remove();
    }
    
    // Ensure we have the basic options (Ativo, Inativo)
    if (!statusSelect.querySelector('option[value="Ativo"]')) {
      const ativoOption = document.createElement('option');
      ativoOption.value = 'Ativo';
      ativoOption.textContent = 'Ativo';
      statusSelect.appendChild(ativoOption);
    }
    if (!statusSelect.querySelector('option[value="Inativo"]')) {
      const inativoOption = document.createElement('option');
      inativoOption.value = 'Inativo';
      inativoOption.textContent = 'Inativo';
      statusSelect.appendChild(inativoOption);
    }
    
    statusSelect.value = u.status;
    
    // Hide damage and regularization sections for normal users
    damageSection.style.display = 'none';
    regularizationSection.style.display = 'none';
    standardWarning.style.display = 'block';
    
    // Remove required attribute from regularization method
    document.getElementById('regularizationMethod').required = false;
    
    // Reset button text
    saveBtn.textContent = 'Salvar Alterações';
  }
  
  const modal = document.getElementById('editUserModal');
  modal.style.display = 'block';
}

function closeEditUserModal() {
  editingIndex = null;
  document.getElementById('editUserModal').style.display = 'none';
  
  // Reset status dropdown to original state
  const statusSelect = document.getElementById('editUserStatus');
  statusSelect.disabled = false;
  statusSelect.innerHTML = `
    <option value="Ativo">Ativo</option>
    <option value="Inativo">Inativo</option>
    <option value="Bloqueado">Bloqueado</option>
  `;
  
  // Reset form
  document.querySelector('.user-form').reset();
  clearValidationErrors();
}

// Function removed - no longer using toggle for status

function handleEditUser(event) {
  event.preventDefault();
  
  if (editingIndex === null) return;
  
  // Get form data
  const formData = new FormData(event.target);
  const role = formData.get('role');
  const status = formData.get('status');
  
  const u = allUsers[editingIndex];
  
  // Handle regularization for blocked users
  if (u.status === 'Bloqueado') {
    return handleRegularization(formData, u);
  }
  
  // Check if user is editing their own role
  const isEditingSelf = u.id === window.currentUserId;
  const isChangingRole = u.role !== role;
  
  if (isEditingSelf && isChangingRole) {
    const roleChangeWarning = `⚠️ ATENÇÃO: Você está alterando seu próprio perfil de "${u.role}" para "${role}".

Isso pode afetar suas permissões no sistema e você pode perder acesso a funcionalidades administrativas.

Tem certeza de que deseja continuar?`;
    
    if (!confirm(roleChangeWarning)) {
      return; // User cancelled the operation
    }
  }
  
  // Send AJAX request to Django backend
  fetch(`/accounts/users/update/${u.id}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      role: role,
      status: status
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Check if user edited their own role
      if (isEditingSelf && isChangingRole) {
        alert(`${data.message}\n\nA página será recarregada para aplicar as mudanças de permissão.`);
        // Force page reload when user changes their own role
        window.location.reload();
        return;
      }
      
      // Update local data
      u.role = role;
      u.status = status;
      
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
  // Only update if we have users in JavaScript, otherwise keep Django template values
  if (allUsers.length > 0) {
    const totalUsers = allUsers.length;
    const activeCount = allUsers.filter(u => u.status === 'Ativo').length;
    const inactiveCount = allUsers.filter(u => u.status === 'Inativo').length;
    const blockedCount = allUsers.filter(u => u.status === 'Bloqueado').length;

    document.getElementById('total-users').textContent = totalUsers;
    document.getElementById('active-count').textContent = activeCount;
    document.getElementById('inactive-count').textContent = inactiveCount;
    document.getElementById('blocked-count').textContent = blockedCount;
  }
}

// Initialize table on page load
document.addEventListener('DOMContentLoaded', function() {
  // Initialize dropdowns to default values
  document.getElementById('userTypeFilter').value = 'Todos';
  document.getElementById('userStatusFilter').value = 'Todos';
  
  updateStatistics();
  renderTable();
  
  // Debug function to test blocked user functionality
  // This can be called from browser console: testBlockedUser()
  window.testBlockedUser = function() {
    if (allUsers.length > 0) {
      console.log('Setting first user as blocked for testing...');
      allUsers[0].status = 'Bloqueado';
      updateStatistics();
      renderTable();
      console.log('First user is now blocked. Try the "Bloqueado" filter.');
    }
  };
});

// Helper functions for regularization workflow

function loadDamageInfo(userId) {
  fetch(`/accounts/users/${userId}/damage-info/`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const info = data.damage_info;
      document.getElementById('damageBookTitle').textContent = `${info.book_title} - ${info.book_author}`;
      document.getElementById('damageDescription').textContent = info.description;
      document.getElementById('damageDate').textContent = info.reported_date;
    } else {
      console.error('Error loading damage info:', data.message);
      // Show default error state
      document.getElementById('damageBookTitle').textContent = 'Erro ao carregar informações';
      document.getElementById('damageDescription').textContent = 'Não foi possível carregar os detalhes do dano';
      document.getElementById('damageDate').textContent = '-';
    }
  })
  .catch(error => {
    console.error('Error:', error);
    // Show default error state
    document.getElementById('damageBookTitle').textContent = 'Erro ao carregar informações';
    document.getElementById('damageDescription').textContent = 'Não foi possível carregar os detalhes do dano';
    document.getElementById('damageDate').textContent = '-';
  });
}

function handleRegularization(formData, user) {
  // Clear previous validation errors
  clearValidationErrors();
  
  const regularizationMethod = formData.get('regularization_method');
  const regularizationNotes = formData.get('regularization_notes') || '';
  
  // Validate required fields
  if (!regularizationMethod) {
    showFieldError('regularizationMethodError', 'O método de regularização é obrigatório.');
    return;
  }
  
  // Confirm regularization action
  const confirmMessage = `Confirmar regularização do usuário "${user.name}"?

Método: ${getMethodDisplayName(regularizationMethod)}
${regularizationNotes ? `Observações: ${regularizationNotes}` : ''}

Esta ação irá desbloquear o usuário permanentemente e não pode ser desfeita.`;
  
  if (!confirm(confirmMessage)) {
    return;
  }
  
  // Send regularization request
  fetch(`/accounts/users/update/${user.id}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      regularization_method: regularizationMethod,
      regularization_notes: regularizationNotes
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Update local user data
      user.status = 'Normal'; // User is now unblocked
      
      // Update statistics and table
      updateStatistics();
      renderTable();
      
      // Close modal
      closeEditUserModal();
      
      // Show success message
      alert(data.message);
    } else {
      alert(`Erro: ${data.message}`);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Erro ao processar regularização. Tente novamente.');
  });
}

function getMethodDisplayName(method) {
  const methods = {
    'financial': 'Reembolso financeiro',
    'replacement': 'Substituição do livro',
    'other': 'Outro'
  };
  return methods[method] || method;
}

function showFieldError(errorElementId, message) {
  const errorElement = document.getElementById(errorElementId);
  if (errorElement) {
    errorElement.textContent = message;
    errorElement.style.display = 'block';
  }
}

function clearValidationErrors() {
  const errorElements = document.querySelectorAll('.field-error');
  errorElements.forEach(element => {
    element.textContent = '';
    element.style.display = 'none';
  });
}