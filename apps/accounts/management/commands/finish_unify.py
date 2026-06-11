from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Finish book unification without debug output'

    def handle(self, *args, **options):
        self.stdout.write('Finishing book unification...')
        
        # Get all duplicate titles
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT titulo, COUNT(*) as count_books
                FROM livros 
                GROUP BY titulo 
                HAVING COUNT(*) > 1 
                ORDER BY COUNT(*) DESC
            """)
            
            duplicate_titles = cursor.fetchall()
        
        self.stdout.write(f'Processing {len(duplicate_titles)} remaining duplicate groups...')
        
        total_removed = 0
        
        for i, (title, count) in enumerate(duplicate_titles):
            if i % 50 == 0:
                self.stdout.write(f'Progress: {i}/{len(duplicate_titles)}')
            
            # Get all books with this title
            books = list(Livros.objects.filter(titulo=title).order_by('id_livro'))
            
            if len(books) <= 1:
                continue
            
            # Keep the first one, remove the rest
            keep_book = books[0]
            remove_books = books[1:]
            
            # Delete duplicates
            if remove_books:
                remove_ids = [book.id_livro for book in remove_books]
                deleted_count = Livros.objects.filter(id_livro__in=remove_ids).delete()[0]
                total_removed += deleted_count
                
        self.stdout.write(f'Completed! Removed {total_removed} duplicate books')
        
        final_count = Livros.objects.count()
        self.stdout.write(f'Final book count: {final_count}')