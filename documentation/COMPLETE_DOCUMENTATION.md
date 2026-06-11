# LUMEN - Complete Project Documentation

This document consolidates all project documentation (excluding README.md) for the LUMEN Library Management System.

---

# Tests Directory - LUMEN Library Management System

This directory contains all automated tests for validating the character limits implementation and dynamic features.

## Test Files

### Character Limits Tests
- **`test_character_limits.py`** - Comprehensive character limits validation
- **`validate_limits.py`** - Quick validation script for all field limits

### Dynamic Features Tests  
- **`test_dynamic_year.py`** - Tests dynamic year calculation for book forms
- **`test_dynamic_copies.py`** - Tests dynamic copy limits for book forms (if created)

## Running Tests

```bash
# Run individual tests
python tests/test_character_limits.py
python tests/test_dynamic_year.py  
python tests/validate_limits.py

# Or run from project root
./venv/Scripts/python.exe tests/test_character_limits.py
./venv/Scripts/python.exe tests/test_dynamic_year.py
./venv/Scripts/python.exe tests/validate_limits.py
```

## What These Tests Validate

✅ **Model character limits are correctly implemented**  
✅ **Form validation works with new limits**  
✅ **Dynamic year calculation functions properly**  
✅ **Dynamic copy limits are enforced**  
✅ **All field constraints are properly set**

---

# Damaged Book Registration Implementation Summary

This document summarizes the implementation of the RF10.1 - Damaged Books Registration feature for the LUMEN Library Management System.

## Overview

The feature successfully replaces the simple return confirmation popup with a comprehensive return modal that supports damaged book registration, automatic user blocking, and maintains formal records of damage occurrences.

## ✅ Implemented Features

### 1. Database Changes
- **User Model Enhancement**: Added `status` field with choices:
  - `ACTIVE = 'active'` (default)
  - `BLOCKED = 'blocked'`
- **New DamageReport Model**: Tracks all damage incidents with:
  - Link to loan (`emprestimo`)
  - Link to affected user
  - Link to damaged book
  - Damage description (mandatory, max 1000 chars)
  - Timestamp and reporting librarian
- **Migration Created**: `0009_user_status_damagereport.py`

### 2. Updated Return Workflow
- **AJAX-Based Return Modal**: Replaces simple confirmation popup
- **Dual Mode Support**:
  - GET: Loads loan data for display
  - POST: Processes return with optional damage registration
- **Transactional Consistency**: Ensures all operations (return, damage report, user blocking) complete atomically
- **Error Handling**: Comprehensive validation and error messages

### 3. User Interface Enhancements
- **New Return Modal** (`manage_loans.html`):
  - Displays loan information
  - Radio buttons for book condition
  - Conditional damage description field
  - Warning about user blocking consequences
  - Loading states and error handling
- **JavaScript Functionality**:
  - Dynamic form behavior
  - Client-side validation
  - AJAX communication
  - Success/error feedback

### 4. User Management Integration
- **Enhanced User Management Screen**:
  - New "Blocked" status column
  - "Blocked" filter button
  - Statistics for blocked users
  - Red status indicators for blocked users
- **Updated Statistics**: Shows count of blocked users
- **CSS Enhancements**: Added red dot and blocked status styling

### 5. Business Logic Implementation
- **Loan Validation**: Blocks loan creation for blocked users with specific error message:
  ```
  "Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado."
  ```
- **User Autocomplete**: Shows blocked status in user selection dropdown
- **Automatic Status Changes**: Users automatically blocked upon damage confirmation

### 6. Validation Rules
- **Client-Side**:
  - Mandatory damage description when damage is reported
  - Form state validation
  - Real-time feedback
- **Server-Side**:
  - Damage description required for damaged returns
  - User status validation for loan creation
  - Transaction integrity checks

## 📁 Modified Files

### Backend
- `apps/accounts/models.py`: Added User.status and DamageReport model
- `apps/accounts/views.py`: Updated return_book, manage_users, autocomplete_users
- `apps/accounts/forms.py`: Added blocked user validation to LoanForm
- `apps/accounts/migrations/0009_user_status_damagereport.py`: Database migration

### Frontend
- `templates/manage_loans.html`: New return modal and JavaScript
- `templates/manage_users.html`: Added blocked status column and filter
- `static/js/manage_users.js`: Updated for blocked user filtering and display
- `static/css/manage_users.css`: Added blocked status styling

### Testing
- `tests/test_damage_tracking.py`: Comprehensive test suite

## 🎯 Acceptance Criteria Compliance

| Criteria | Status | Implementation |
|----------|---------|----------------|
| AC1 - Return Modal | ✅ | Modal opens instead of confirmation popup |
| AC2 - Damage Selection | ✅ | Radio buttons for book condition |
| AC3 - Return Without Damage | ✅ | Normal return flow preserved |
| AC4 - Return With Damage | ✅ | Conditional damage description field |
| AC5 - Mandatory Description | ✅ | Client and server validation |
| AC6 - User Blocking | ✅ | Automatic blocking with damage report |
| AC7 - User Management Reflection | ✅ | Blocked status visible in user management |
| AC8 - Loan Restriction | ✅ | Exact error message implemented |

## 🔧 Technical Implementation Details

### Return Process Flow
1. Librarian clicks "Devolver" button
2. Modal opens with loan information (AJAX GET)
3. Librarian selects book condition
4. If damaged, description field becomes mandatory
5. Upon confirmation, AJAX POST with damage data
6. Server processes return, creates damage report if needed
7. User automatically blocked if damage reported
8. Success message shown and page refreshed

### User Blocking Mechanism
```python
if is_damaged:
    # Create damage report
    DamageReport.objects.create(
        emprestimo=emprestimo,
        user=user,
        book=book,
        description=damage_description,
        reported_by=request.user
    )
    
    # Block user automatically
    user.status = User.Status.BLOCKED
    user.save()
```

### Loan Validation
```python
if user.status == User.Status.BLOCKED:
    raise forms.ValidationError(
        'Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado.'
    )
```

## 🧪 Testing

The implementation includes a comprehensive test suite that validates:
- User blocking after damage reports
- Loan validation for blocked users
- Damage description validation
- Return process with and without damage
- Business rule enforcement

All tests pass successfully.

## 🚀 Deployment Notes

1. **Database Migration Required**: Run `python manage.py migrate` to apply the new database schema
2. **Static Files**: Ensure updated CSS and JS files are deployed
3. **Browser Cache**: Clear browser cache for updated frontend assets
4. **Backward Compatibility**: Existing return functionality preserved for non-JavaScript clients

## 📊 Benefits Delivered

1. **Formal Damage Tracking**: All damage incidents formally recorded with descriptions
2. **Automatic User Management**: No manual intervention needed for blocking problematic users
3. **Audit Trail**: Complete history of who reported what damage when
4. **User Experience**: Intuitive modal interface with clear visual feedback
5. **Data Integrity**: Transactional consistency ensures reliable state management
6. **Administrative Visibility**: Blocked users clearly identified in management interface

The implementation successfully fulfills all requirements of RF10.1 while maintaining the existing system's reliability and extending its capabilities for better library asset management.

---

# Project Architecture Overview

## System Components

### Backend (Django)
- **Models**: User management, book catalog, loan tracking, damage reports
- **Views**: CRUD operations, business logic, API endpoints
- **Forms**: Data validation, user input handling
- **URL Routing**: RESTful endpoint design

### Frontend
- **Templates**: Server-side rendered HTML with Bootstrap
- **JavaScript**: Dynamic behavior, AJAX communication
- **CSS**: Custom styling with responsive design
- **Static Assets**: Images, icons, fonts

### Database
- **SQLite**: Development database
- **Models**: Normalized schema with proper relationships
- **Migrations**: Version-controlled schema changes

## Key Features

1. **User Management**
   - Role-based access control (Admin, Librarian, Reader)
   - User status tracking (Active, Blocked)
   - Profile management with validation

2. **Book Catalog**
   - Multi-copy inventory tracking
   - Category management with icons
   - Advanced search and filtering
   - Duplicate detection and edition handling

3. **Loan Management**
   - Configurable loan duration and limits
   - Overdue tracking with grandfathering
   - Return processing with damage tracking
   - PDF reporting capabilities

4. **Damage Tracking**
   - Formal incident reporting
   - Automatic user blocking
   - Audit trail maintenance
   - Administrative oversight

## Security Features

- **CSRF Protection**: All forms protected against cross-site request forgery
- **Authentication**: Required for all operations
- **Authorization**: Role-based access control
- **Data Validation**: Client and server-side validation
- **SQL Injection Prevention**: ORM-based database access

## Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: Feature workflow testing
- **Validation Tests**: Business rule compliance
- **Manual Testing**: User acceptance testing

---

# Development Guidelines

## Code Style
- Python: PEP 8 compliance
- JavaScript: ES6+ standards
- CSS: BEM methodology where applicable
- HTML: Semantic markup

## Database Design
- Normalized schema design
- Foreign key relationships
- Proper indexing
- Migration-based schema evolution

## Error Handling
- Graceful degradation
- User-friendly error messages
- Comprehensive logging
- Transaction rollback on failures

## Performance
- Efficient database queries
- Static file optimization
- Client-side caching
- Pagination for large datasets

---

This documentation provides a comprehensive overview of the LUMEN Library Management System, including testing procedures, implementation details, and architectural decisions. For the most current information, refer to individual source files and the git commit history.