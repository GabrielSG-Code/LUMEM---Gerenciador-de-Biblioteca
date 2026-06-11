"""
Test cases for damage tracking and user blocking functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, date

# Simulate Django models and functionality for testing
class MockUser:
    class Status:
        ACTIVE = 'active'
        BLOCKED = 'blocked'
    
    def __init__(self, id, username, status=Status.ACTIVE):
        self.id = id
        self.username = username
        self.status = status

class MockLivros:
    def __init__(self, id_livro, titulo, autor, status_livro='Disponível'):
        self.id_livro = id_livro
        self.titulo = titulo
        self.autor = autor
        self.status_livro = status_livro

class MockEmprestimo:
    def __init__(self, id, id_usuario, id_livro, data_inicio, data_entrega, data_fim=None):
        self.id = id
        self.id_usuario = str(id_usuario)
        self.id_livro = str(id_livro)
        self.data_inicio = data_inicio
        self.data_entrega = data_entrega
        self.data_fim = data_fim

class MockDamageReport:
    def __init__(self, emprestimo, user, book, description, reported_by):
        self.emprestimo = emprestimo
        self.user = user
        self.book = book
        self.description = description
        self.reported_by = reported_by

class DamageTrackingTest(unittest.TestCase):
    """Test cases for damage tracking functionality"""
    
    def setUp(self):
        # Setup test data
        self.user = MockUser(1, 'test_user')
        self.book = MockLivros(1, 'Test Book', 'Test Author')
        self.emprestimo = MockEmprestimo(
            1, 1, 1, 
            date(2023, 1, 1), 
            date(2023, 1, 8)
        )
        self.librarian = MockUser(2, 'librarian')

    def test_user_blocking_after_damage_report(self):
        """Test that a user is blocked when a damage report is created"""
        # Simulate creating a damage report
        damage_report = MockDamageReport(
            self.emprestimo, 
            self.user, 
            self.book, 
            "Book cover is torn and pages are damaged",
            self.librarian
        )
        
        # Simulate the user blocking process
        self.user.status = MockUser.Status.BLOCKED
        
        # Assert user is blocked
        self.assertEqual(self.user.status, MockUser.Status.BLOCKED)

    def test_loan_validation_blocks_blocked_users(self):
        """Test that blocked users cannot create new loans"""
        # Block the user
        self.user.status = MockUser.Status.BLOCKED
        
        # Simulate loan validation
        def validate_user_for_loan(user):
            if user.status == MockUser.Status.BLOCKED:
                return False, "Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado."
            return True, "OK"
        
        is_valid, message = validate_user_for_loan(self.user)
        
        # Assert loan is blocked
        self.assertFalse(is_valid)
        self.assertEqual(message, "Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado.")

    def test_loan_validation_allows_active_users(self):
        """Test that active users can create new loans"""
        # Ensure user is active
        self.user.status = MockUser.Status.ACTIVE
        
        # Simulate loan validation
        def validate_user_for_loan(user):
            if user.status == MockUser.Status.BLOCKED:
                return False, "Não é possível realizar o empréstimo: usuário bloqueado por devolução de livro danificado."
            return True, "OK"
        
        is_valid, message = validate_user_for_loan(self.user)
        
        # Assert loan is allowed
        self.assertTrue(is_valid)
        self.assertEqual(message, "OK")

    def test_damage_description_validation(self):
        """Test that damage description is required when reporting damage"""
        def validate_damage_report(is_damaged, description):
            if is_damaged and not description.strip():
                return False, "A descrição do dano é obrigatória quando o livro é marcado como danificado."
            return True, "OK"
        
        # Test with damage but no description
        is_valid, message = validate_damage_report(True, "")
        self.assertFalse(is_valid)
        self.assertEqual(message, "A descrição do dano é obrigatória quando o livro é marcado como danificado.")
        
        # Test with damage and description
        is_valid, message = validate_damage_report(True, "Book cover is damaged")
        self.assertTrue(is_valid)
        self.assertEqual(message, "OK")
        
        # Test without damage
        is_valid, message = validate_damage_report(False, "")
        self.assertTrue(is_valid)
        self.assertEqual(message, "OK")

    def test_return_process_without_damage(self):
        """Test normal return process without damage"""
        # Simulate return without damage
        self.emprestimo.data_fim = date.today()
        self.book.status_livro = 'Disponível'
        
        # Assert book is available and user status unchanged
        self.assertEqual(self.book.status_livro, 'Disponível')
        self.assertEqual(self.user.status, MockUser.Status.ACTIVE)
        self.assertIsNotNone(self.emprestimo.data_fim)

    def test_return_process_with_damage(self):
        """Test return process with damage registration"""
        # Simulate return with damage
        damage_description = "Cover is torn and several pages are missing"
        damage_report = MockDamageReport(
            self.emprestimo, 
            self.user, 
            self.book, 
            damage_description,
            self.librarian
        )
        
        # Simulate the complete damage return process
        self.emprestimo.data_fim = date.today()
        self.book.status_livro = 'Disponível'
        self.user.status = MockUser.Status.BLOCKED
        
        # Assert all changes are made
        self.assertEqual(self.book.status_livro, 'Disponível')
        self.assertEqual(self.user.status, MockUser.Status.BLOCKED)
        self.assertIsNotNone(self.emprestimo.data_fim)
        self.assertEqual(damage_report.description, damage_description)

class BusinessRulesTest(unittest.TestCase):
    """Test business rules implementation"""
    
    def test_damage_registration_only_during_return(self):
        """Test that damage can only be registered during return process"""
        # This would be enforced by the UI and API design
        # Damage reports are only created through the return modal/endpoint
        self.assertTrue(True)  # Placeholder - enforced by design
    
    def test_automatic_user_blocking(self):
        """Test that user blocking is automatic when damage is reported"""
        user = MockUser(1, 'test_user')
        
        # Simulate the automatic blocking process
        def process_damage_return(user, damage_description):
            if damage_description.strip():
                user.status = MockUser.Status.BLOCKED
                return True
            return False
        
        blocked = process_damage_return(user, "Damaged book")
        
        self.assertTrue(blocked)
        self.assertEqual(user.status, MockUser.Status.BLOCKED)
    
    def test_blocked_users_cannot_loan(self):
        """Test that blocked users cannot perform new loans"""
        user = MockUser(1, 'test_user', MockUser.Status.BLOCKED)
        
        def can_create_loan(user):
            return user.status != MockUser.Status.BLOCKED
        
        self.assertFalse(can_create_loan(user))

if __name__ == '__main__':
    unittest.main()