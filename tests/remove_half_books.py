#!/usr/bin/env python
"""
Script to remove half of the books from the LUMEN database
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumen.settings')
django.setup()

from apps.accounts.models import Livros

def remove_half_books():
    """Remove half of the books from the database"""
    
    # Get total count
    total_books = Livros.objects.count()
    print(f'Total books before: {total_books}')
    
    if total_books == 0:
        print('No books found in database')
        return
    
    # Calculate half count  
    half_count = total_books // 2
    print(f'Will remove: {half_count} books')
    
    if half_count > 0:
        # Get the first half of books by ID
        books_to_delete = Livros.objects.all().order_by('id_livro')[:half_count]
        book_ids = [book.id_livro for book in books_to_delete]
        
        print(f'Removing books with IDs: {book_ids[:5]}...' + (f' and {len(book_ids)-5} more' if len(book_ids) > 5 else ''))
        
        # Delete the selected books
        deleted_count, _ = Livros.objects.filter(id_livro__in=book_ids).delete()
        
        # Check remaining count
        remaining_books = Livros.objects.count()
        print(f'Total books after: {remaining_books}')
        print(f'Successfully removed {deleted_count} books')
        
        return deleted_count
    else:
        print('No books to remove')
        return 0

if __name__ == "__main__":
    removed = remove_half_books()
    print(f'\nOperation completed: {removed} books removed from database')