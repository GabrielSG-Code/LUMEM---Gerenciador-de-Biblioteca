"""
Test suite for User Regularization Workflow (RF10.2)

This test suite validates all aspects of the user regularization functionality,
ensuring that blocked users can be properly regularized by administrators.
"""

import json
from datetime import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import Livros, Emprestimo, DamageReport, UserRegularization

User = get_user_model()


class UserRegularizationTestCase(TestCase):
    """Test cases for user regularization workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.blocked_user = User.objects.create_user(
            username='blocked_reader',
            email='blocked@test.com',
            password='testpass123',
            role='reader',
            status=User.Status.BLOCKED
        )
        
        self.normal_user = User.objects.create_user(
            username='normal_reader',
            email='normal@test.com',
            password='testpass123',
            role='reader'
        )
        
        # Create test book
        self.book = Livros.objects.create(
            titulo='Test Book',
            autor='Test Author',
            status_livro='Disponível'
        )
        
        # Create test loan
        self.loan = Emprestimo.objects.create(
            id_usuario=str(self.blocked_user.id),
            id_livro=str(self.book.id_livro),
            data_inicio=timezone.now().date(),
            data_entrega=timezone.now().date(),
            data_fim=timezone.now().date()  # Loan is returned
        )
        
        # Create damage report that caused the block
        self.damage_report = DamageReport.objects.create(
            emprestimo=self.loan,
            user=self.blocked_user,
            book=self.book,
            description='Páginas rasgadas e capa danificada',
            reported_by=self.admin_user
        )
        
        self.client = Client()

    def test_ac1_display_blocked_users(self):
        """AC1 - Display Blocked Users
        
        Given there are users blocked due to damaged book returns
        When an administrator accesses User Management
        Then the system must display those users with status Blocked.
        """
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Access user management
        response = self.client.get(reverse('manage_users'))
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'blocked_reader')
        
        # Check that blocked count is properly displayed
        self.assertEqual(response.context['stats']['blocked'], 1)
        
        # Verify blocked user appears in the user data
        users_data = response.context['users']
        blocked_users = [u for u in users_data if u['status'] == 'Bloqueado']
        self.assertEqual(len(blocked_users), 1)
        self.assertEqual(blocked_users[0]['name'], 'blocked_reader')

    def test_ac2_display_damage_details(self):
        """AC2 - Display Damage Details
        
        Given a blocked user is selected
        When the administrator opens the Edit User modal
        Then the system must display:
        * Book title
        * Damage description
        * Occurrence date
        * Current status
        """
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Get damage info for blocked user
        response = self.client.get(reverse('get_user_damage_info', args=[self.blocked_user.id]))
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        damage_info = data['damage_info']
        
        # Verify all required information is present
        self.assertEqual(damage_info['book_title'], 'Test Book')
        self.assertEqual(damage_info['book_author'], 'Test Author')
        self.assertEqual(damage_info['description'], 'Páginas rasgadas e capa danificada')
        self.assertIsNotNone(damage_info['reported_date'])
        self.assertEqual(damage_info['reported_by'], 'admin_test')
        self.assertFalse(damage_info['is_regularized'])

    def test_ac3_mandatory_regularization_method(self):
        """AC3 - Mandatory Regularization Method
        
        Given the administrator is regularizing a blocked user
        When attempting to save without selecting a regularization method
        Then the system must:
        * Prevent saving
        * Display validation feedback
        """
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Attempt regularization without method
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': '',  # Empty method
                'regularization_notes': 'Test notes'
            }),
            content_type='application/json'
        )
        
        # Verify validation error
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('Método de regularização é obrigatório', data['message'])

    def test_ac4_successful_regularization(self):
        """AC4 - Successful Regularization
        
        Given the administrator selected a valid regularization method
        When confirming the regularization
        Then the system must:
        * Register the regularization
        * Change the user status from Blocked to Active
        * Save the regularization method
        * Allow new loans for that user
        """
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Verify user is initially blocked
        self.assertEqual(self.blocked_user.status, User.Status.BLOCKED)
        
        # Perform regularization
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'financial',
                'regularization_notes': 'Reembolso via PIX realizado'
            }),
            content_type='application/json'
        )
        
        # Verify success
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertTrue(data.get('regularized'))
        self.assertIn('regularizado e desbloqueado', data['message'])
        
        # Refresh user from database
        self.blocked_user.refresh_from_db()
        
        # Verify user status changed to Active
        self.assertEqual(self.blocked_user.status, User.Status.ACTIVE)
        
        # Verify regularization record was created
        self.assertTrue(UserRegularization.objects.filter(
            user=self.blocked_user,
            damage_report=self.damage_report,
            administrator=self.admin_user,
            method='financial'
        ).exists())
        
        regularization = UserRegularization.objects.get(
            user=self.blocked_user,
            damage_report=self.damage_report
        )
        self.assertEqual(regularization.notes, 'Reembolso via PIX realizado')

    def test_ac5_loan_availability_restored(self):
        """AC5 - Loan Availability Restored
        
        Given a user was previously blocked
        When the regularization process is completed
        Then the user must be able to receive new loans normally
        """
        # First, regularize the blocked user
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'replacement',
                'regularization_notes': 'Novo livro entregue'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh user from database
        self.blocked_user.refresh_from_db()
        self.assertEqual(self.blocked_user.status, User.Status.ACTIVE)
        
        # Now test that user can receive new loans
        # In a real scenario, this would involve testing the loan creation logic
        # For this test, we verify the user status allows loan eligibility
        
        # The user should no longer be blocked
        self.assertNotEqual(self.blocked_user.status, User.Status.BLOCKED)
        
        # Create a new book for lending test
        new_book = Livros.objects.create(
            titulo='New Test Book',
            autor='New Author',
            status_livro='Disponível'
        )
        
        # User should be eligible for new loans (status is Active)
        self.assertEqual(self.blocked_user.status, User.Status.ACTIVE)

    def test_business_rule_1_only_admins_can_regularize(self):
        """BR1 - Only administrators may perform regularizations"""
        # Try to access as regular user (should fail)
        self.client.login(username='normal_reader', password='testpass123')
        
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'financial',
                'regularization_notes': 'Should not work'
            }),
            content_type='application/json'
        )
        
        # Should be denied access
        self.assertEqual(response.status_code, 403)
        
        # User should still be blocked
        self.blocked_user.refresh_from_db()
        self.assertEqual(self.blocked_user.status, User.Status.BLOCKED)

    def test_business_rule_2_only_blocked_users_can_be_regularized(self):
        """BR2 - Only users with status Blocked may be regularized"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Try to regularize a normal (non-blocked) user
        response = self.client.get(reverse('get_user_damage_info', args=[self.normal_user.id]))
        
        # Should return error for non-blocked user
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('não está bloqueado', data['message'])

    def test_business_rule_4_audit_record_creation(self):
        """BR4 - The unblock action must create an audit record"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Initial state - no regularization exists
        self.assertFalse(UserRegularization.objects.filter(user=self.blocked_user).exists())
        
        # Perform regularization
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'other',
                'regularization_notes': 'Acordo especial'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify audit record was created
        self.assertTrue(UserRegularization.objects.filter(user=self.blocked_user).exists())
        
        regularization = UserRegularization.objects.get(user=self.blocked_user)
        self.assertEqual(regularization.administrator, self.admin_user)
        self.assertEqual(regularization.method, 'other')
        self.assertEqual(regularization.notes, 'Acordo especial')
        self.assertIsNotNone(regularization.regularized_at)

    def test_business_rule_5_damage_history_preserved(self):
        """BR5 - The damage history must remain preserved after regularization"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Verify damage report exists before regularization
        self.assertTrue(DamageReport.objects.filter(user=self.blocked_user).exists())
        original_damage_report = DamageReport.objects.get(user=self.blocked_user)
        
        # Perform regularization
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'financial',
                'regularization_notes': 'Reembolso completo'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify damage report still exists after regularization
        self.assertTrue(DamageReport.objects.filter(user=self.blocked_user).exists())
        preserved_damage_report = DamageReport.objects.get(user=self.blocked_user)
        
        # Verify damage report data is unchanged
        self.assertEqual(preserved_damage_report.id, original_damage_report.id)
        self.assertEqual(preserved_damage_report.description, original_damage_report.description)
        self.assertEqual(preserved_damage_report.book, original_damage_report.book)
        self.assertEqual(preserved_damage_report.reported_at, original_damage_report.reported_at)

    def test_duplicate_regularization_prevention(self):
        """Prevent duplicate regularization of the same damage report"""
        self.client.login(username='admin_test', password='testpass123')
        
        # First regularization
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'financial',
                'regularization_notes': 'First regularization'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh user and simulate re-blocking for testing
        self.blocked_user.refresh_from_db()
        self.blocked_user.status = User.Status.BLOCKED
        self.blocked_user.save()
        
        # Attempt second regularization of same damage report
        response = self.client.post(
            reverse('update_user', args=[self.blocked_user.id]),
            data=json.dumps({
                'regularization_method': 'replacement',
                'regularization_notes': 'Second attempt'
            }),
            content_type='application/json'
        )
        
        # Should fail because damage report is already regularized
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('já foi regularizado', data['message'])

    def test_regularization_methods_validation(self):
        """Test all valid regularization methods"""
        self.client.login(username='admin_test', password='testpass123')
        
        valid_methods = ['financial', 'replacement', 'other']
        
        for method in valid_methods:
            # Create a new blocked user for each test
            new_blocked_user = User.objects.create_user(
                username=f'blocked_user_{method}',
                email=f'blocked_{method}@test.com',
                password='testpass123',
                role='reader',
                status=User.Status.BLOCKED
            )
            
            # Create corresponding damage report
            new_loan = Emprestimo.objects.create(
                id_usuario=str(new_blocked_user.id),
                id_livro=str(self.book.id_livro),
                data_inicio=timezone.now().date(),
                data_entrega=timezone.now().date(),
                data_fim=timezone.now().date()
            )
            
            new_damage_report = DamageReport.objects.create(
                emprestimo=new_loan,
                user=new_blocked_user,
                book=self.book,
                description=f'Damage for {method} test',
                reported_by=self.admin_user
            )
            
            # Test regularization with this method
            response = self.client.post(
                reverse('update_user', args=[new_blocked_user.id]),
                data=json.dumps({
                    'regularization_method': method,
                    'regularization_notes': f'Testing {method} method'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200, f'Method {method} failed')
            
            # Verify regularization was created with correct method
            regularization = UserRegularization.objects.get(user=new_blocked_user)
            self.assertEqual(regularization.method, method)

    def tearDown(self):
        """Clean up test data"""
        # Django's TestCase handles database rollback automatically
        pass


class UserRegularizationUITestCase(TestCase):
    """Test cases for user regularization user interface"""
    
    def setUp(self):
        """Set up test data for UI tests"""
        self.admin_user = User.objects.create_user(
            username='ui_admin',
            email='ui_admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.blocked_user = User.objects.create_user(
            username='ui_blocked',
            email='ui_blocked@test.com',
            password='testpass123',
            role='reader',
            status=User.Status.BLOCKED
        )
        
        self.book = Livros.objects.create(
            titulo='UI Test Book',
            autor='UI Author',
            status_livro='Disponível'
        )
        
        self.loan = Emprestimo.objects.create(
            id_usuario=str(self.blocked_user.id),
            id_livro=str(self.book.id_livro),
            data_inicio=timezone.now().date(),
            data_entrega=timezone.now().date(),
            data_fim=timezone.now().date()
        )
        
        self.damage_report = DamageReport.objects.create(
            emprestimo=self.loan,
            user=self.blocked_user,
            book=self.book,
            description='UI test damage description',
            reported_by=self.admin_user
        )
        
        self.client = Client()

    def test_blocked_status_visual_indicator(self):
        """Test that blocked status is visually distinguishable"""
        self.client.login(username='ui_admin', password='testpass123')
        
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        
        # Check that blocked user data includes correct status
        users_data = response.context['users']
        blocked_user_data = next(u for u in users_data if u['id'] == self.blocked_user.id)
        
        self.assertEqual(blocked_user_data['status'], 'Bloqueado')

    def test_regularization_form_elements_present(self):
        """Test that regularization form elements are present in template"""
        self.client.login(username='ui_admin', password='testpass123')
        
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        
        # Check for regularization form elements in template
        self.assertContains(response, 'damageSection')
        self.assertContains(response, 'regularizationSection')
        self.assertContains(response, 'regularizationMethod')
        self.assertContains(response, 'regularizationNotes')
        self.assertContains(response, 'Informações do Dano')
        self.assertContains(response, 'Regularização')


if __name__ == '__main__':
    # Run tests with: python manage.py test tests.test_user_regularization
    pass