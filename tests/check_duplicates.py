#!/usr/bin/env python
"""
Quick script to check duplicate books in the database
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

def check_duplicates():
    """Check for duplicate books"""
    
    # Get total count
    total_books = Livros.objects.count()
    print(f'Total books: {total_books}')
    
    # Quick count of duplicates
    duplicates = list(Livros.objects.values('titulo').annotate(count=Count('titulo')).filter(count__gt=1).order_by('-count'))
    
    print(f'Duplicate title groups: {len(duplicates)}')
    
    if len(duplicates) > 0:
        print('\nFirst 10 duplicate groups:')
        for dup in duplicates[:10]:
            print(f'  "{dup["titulo"][:50]}...": {dup["count"]} copies')
        
        total_duplicates = sum(dup["count"] - 1 for dup in duplicates)
        print(f'\nTotal duplicate books that could be removed: {total_duplicates}')
        print(f'Books after unification: {total_books - total_duplicates}')
    else:
        print('No duplicate titles found!')

if __name__ == "__main__":
    check_duplicates()