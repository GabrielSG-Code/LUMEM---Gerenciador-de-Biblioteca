#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumen.settings')
django.setup()

from apps.accounts.models import User, Usuarios

def debug_users():
    print("=== DEBUGGING USER MANAGEMENT ISSUE ===\n")
    
    # Check Django User model
    print("1. Django User Model (AUTH_USER_MODEL):")
    try:
        users = User.objects.all()
        print(f"   Count: {users.count()}")
        
        for user in users[:5]:
            print(f"   - ID: {user.id}")
            print(f"     Username: {user.username}")
            print(f"     Email: {user.email}")
            print(f"     Role: {user.role}")
            print(f"     Role Display: {user.get_role_display()}")
            print(f"     Is Active: {user.is_active}")
            print(f"     Last Login: {user.last_login}")
            print("     ---")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n2. Legacy Usuarios Table:")
    try:
        usuarios = Usuarios.objects.all()
        print(f"   Count: {usuarios.count()}")
        
        for usuario in usuarios[:5]:
            print(f"   - ID: {usuario.id_usuario}")
            print(f"     Username: {usuario.username}")
            print(f"     Email: {usuario.email}")
            print(f"     Privilege: {usuario.privilegio}")
            print(f"     Status: {usuario.status}")
            print("     ---")
            
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n3. Testing manage_users view logic:")
    try:
        users = User.objects.all().order_by('username')
        user_data = []
        
        for user in users:
            try:
                initials = user.username[:2].upper() if user.username else 'NA'
                user_info = {
                    'id': user.id,
                    'initials': initials,
                    'name': user.get_full_name() or user.username,
                    'email': user.email,
                    'role': user.get_role_display(),
                    'active': user.is_active,
                    'last_login': user.last_login.strftime('%d/%m/%Y, %H:%M') if user.last_login else 'Nunca'
                }
                user_data.append(user_info)
                print(f"   ✓ Processed user: {user.username}")
            except Exception as e:
                print(f"   ✗ Error processing user {user.username}: {e}")
                continue
        
        print(f"\n   Successfully processed {len(user_data)} users out of {users.count()}")
        
        # Test stats
        stats = {
            'total': users.count(),
            'admin': users.filter(role='admin').count(),
            'librarian': users.filter(role='librarian').count(),
            'reader': users.filter(role='reader').count()
        }
        print(f"   Stats: {stats}")
        
    except Exception as e:
        print(f"   ERROR in view logic: {e}")

if __name__ == "__main__":
    debug_users()