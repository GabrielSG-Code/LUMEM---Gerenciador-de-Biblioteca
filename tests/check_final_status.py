#!/usr/bin/env python
"""
Quick status check after book unification
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumen.settings')
django.setup()

from apps.accounts.models import Livros
from django.db.models import Count

def check_status():
    """Check current status"""
    
    # Get total count
    total_books = Livros.objects.count()
    print(f'Total books: {total_books}')
    
    # Count duplicates
    duplicates = Livros.objects.values('titulo').annotate(count=Count('titulo')).filter(count__gt=1)
    duplicate_count = len(duplicates)
    
    print(f'Duplicate title groups: {duplicate_count}')
    
    if duplicate_count > 0:
        total_duplicate_books = sum((dup["count"] - 1) for dup in duplicates)
        print(f'Total duplicate books remaining: {total_duplicate_books}')
        print(f'Unique books after full unification: {total_books - total_duplicate_books}')
    else:
        print('No duplicates remaining!')
        print(f'All books are unique: {total_books}')

if __name__ == "__main__":
    check_status()