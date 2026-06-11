# Blocked User Functionality - Testing Guide

This document explains how to test the blocked user functionality before and after database migration.

## Issues Fixed

### 1. Empty Table on "Bloqueado" Filter
**Problem**: When selecting "Bloqueado" filter, table showed empty even if blocked users existed.
**Root Cause**: Views.py was defaulting all users to "Ativo" status because the status field didn't exist yet.
**Solution**: Added proper status field detection and handling in views.py.

### 2. Incorrect Status Display
**Problem**: Blocked users still showing as "Active" in status column.
**Root Cause**: Status column was showing account active/inactive instead of user blocked/normal status.
**Solution**: Updated table rendering to show correct status and added proper status detection.

## Testing Methods

### Before Migration (Current State)
Since the database hasn't been migrated yet and no users are blocked, use debug mode:

1. **Access Debug Mode**: Add `?debug_blocked=1` to the user management URL:
   ```
   http://localhost:8000/accounts/users/?debug_blocked=1
   ```

2. **Expected Behavior**:
   - First reader user will appear as "Bloqueado" 
   - Blocked users count will show "1"
   - "Bloqueado" filter will show one user
   - Status column will show "Bloqueado" with red dot

3. **Alternative JavaScript Test**: In browser console:
   ```javascript
   testBlockedUser()  // Sets first user as blocked temporarily
   ```

### After Migration (Production)
1. **Run Migration**:
   ```bash
   python manage.py migrate
   ```

2. **Create Blocked User**: Use the return modal to report a damaged book
   - Go to Loan Management
   - Click "Devolver" on any active loan
   - Select "Livro foi devolvido com danos"
   - Add damage description
   - Confirm return
   - User will be automatically blocked

3. **Verify Functionality**:
   - Check User Management for blocked status
   - Test "Bloqueado" filter
   - Try creating new loan for blocked user (should fail)

## Expected Results

### User Management Screen
- **Statistics**: Shows correct count of blocked users
- **Filter**: "Bloqueado" button works and shows blocked users
- **Status Column**: Shows "Bloqueado" with red indicator
- **Account Column**: Shows "Ativa/Inativa" for account status

### Loan Creation
- **Blocked User**: Cannot create loans
- **Error Message**: "Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado."

### User Autocomplete
- **Status Indicator**: "- Bloqueado por dano ❌"
- **Eligibility**: Not eligible for new loans

## Code Changes Made

### 1. views.py (manage_users)
```python
# Get user status - handle case where status field doesn't exist yet
user_status = 'Ativo'  # default
if hasattr(user, 'status'):
    if user.status == 'blocked':
        user_status = 'Bloqueado'
    else:
        user_status = 'Ativo'

# Debug mode for testing
if request.GET.get('debug_blocked') == '1' and user.role == 'reader' and users.filter(role='reader').first() == user:
    user_status = 'Bloqueado'
```

### 2. manage_users.js (filtering)
```javascript
function getFilteredUsers() {
  return allUsers.filter(u => {
    let matchFilter = false;
    if (currentFilter === 'Todos') {
      matchFilter = true;
    } else if (currentFilter === 'Bloqueado') {
      matchFilter = u.status === 'Bloqueado';  // Fixed filtering
    } else {
      matchFilter = u.role === currentFilter;
    }
    // ... rest of filter logic
  });
}
```

### 3. Table Rendering (manage_users.js)
```javascript
// Account Status Column
<td>
  <div class="status">
    <span class="status-dot ${u.active ? 'active' : 'inactive'}"></span>
    ${u.active ? 'Ativa' : 'Inativa'}
  </div>
</td>

// User Status Column (NEW)
<td>
  <div class="status">
    <span class="status-dot ${u.status === 'Bloqueado' ? 'blocked' : 'normal'}"></span>
    ${u.status === 'Bloqueado' ? 'Bloqueado' : 'Normal'}
  </div>
</td>
```

## Debugging Commands

### Browser Console Commands
```javascript
// Test blocked user simulation
testBlockedUser()

// Check all users status
allUsers.forEach(u => console.log(`${u.name}: ${u.status}`))

// Check current filter
console.log('Current filter:', currentFilter)

// Check filtered results
console.log('Filtered users:', getFilteredUsers())
```

### Django Debug
```python
# In Django shell
from apps.accounts.models import User
users = User.objects.all()
for user in users:
    status = getattr(user, 'status', 'no_field')
    print(f"{user.username}: {status}")
```

## Removal Instructions

After testing is complete and database is migrated, remove debug code:

1. **Remove from views.py**:
   ```python
   # Remove these lines:
   if request.GET.get('debug_blocked') == '1' and user.role == 'reader' and users.filter(role='reader').first() == user:
       user_status = 'Bloqueado'
   ```

2. **Remove from manage_users.js**:
   ```javascript
   // Remove testBlockedUser function
   window.testBlockedUser = function() { ... };
   ```

The functionality will work normally with real blocked users created through the damage reporting system.