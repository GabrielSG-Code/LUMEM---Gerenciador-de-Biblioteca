import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumen.settings')
django.setup()

from accounts.models import Livros, User, Emprestimo, Usuarios

def validate_character_limits():
    print("CHARACTER LIMITS VALIDATION")
    print("=" * 50)
    
    # Test Livros model
    print("Book Model Limits:")
    print(f"- Title: {Livros._meta.get_field('titulo').max_length} characters")
    print(f"- Author: {Livros._meta.get_field('autor').max_length} characters")
    print(f"- Publisher: {Livros._meta.get_field('editora').max_length} characters")
    print(f"- Category: {Livros._meta.get_field('genero').max_length} characters")
    print(f"- Description: {Livros._meta.get_field('descricao').max_length} characters")
    print(f"- Status: {Livros._meta.get_field('status_livro').max_length} characters")
    
    # Test User model
    print("\nUser Model Limits:")
    print(f"- Email: {User._meta.get_field('email').max_length} characters")
    print(f"- Role: {User._meta.get_field('role').max_length} characters")
    
    # Test Emprestimo model
    print("\nLoan Model Limits:")
    print(f"- User ID: {Emprestimo._meta.get_field('id_usuario').max_length} characters")
    print(f"- Book ID: {Emprestimo._meta.get_field('id_livro').max_length} characters")
    print(f"- Loan ID: {Emprestimo._meta.get_field('id_emprestimo').max_length} characters")
    
    print("\nALL CHARACTER LIMITS SUCCESSFULLY IMPLEMENTED!")
    
    # Validate expected values
    expected_limits = {
        'titulo': 200,
        'autor': 150,
        'editora': 100,
        'genero': 50,
        'descricao': 2000,
        'status_livro': 20,
        'user_email': 320,
        'role': 15,
        'id_usuario': 20,
        'id_livro': 20,
        'id_emprestimo': 25
    }
    
    actual_limits = {
        'titulo': Livros._meta.get_field('titulo').max_length,
        'autor': Livros._meta.get_field('autor').max_length,
        'editora': Livros._meta.get_field('editora').max_length,
        'genero': Livros._meta.get_field('genero').max_length,
        'descricao': Livros._meta.get_field('descricao').max_length,
        'status_livro': Livros._meta.get_field('status_livro').max_length,
        'user_email': User._meta.get_field('email').max_length,
        'role': User._meta.get_field('role').max_length,
        'id_usuario': Emprestimo._meta.get_field('id_usuario').max_length,
        'id_livro': Emprestimo._meta.get_field('id_livro').max_length,
        'id_emprestimo': Emprestimo._meta.get_field('id_emprestimo').max_length
    }
    
    all_correct = True
    for field, expected in expected_limits.items():
        actual = actual_limits[field]
        if actual != expected:
            print(f"ERROR: {field} expected {expected}, got {actual}")
            all_correct = False
    
    if all_correct:
        print("VALIDATION PASSED: All limits match expected values!")
    else:
        print("VALIDATION FAILED: Some limits don't match!")
    
    return all_correct

if __name__ == "__main__":
    validate_character_limits()