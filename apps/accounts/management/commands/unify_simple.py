from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Simple and fast book unification using SQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Process only first N duplicate groups (default: 100)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write('Getting duplicate titles...')
        
        # Get duplicate titles using raw SQL for speed
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT titulo, COUNT(*) as count_books
                FROM livros 
                GROUP BY titulo 
                HAVING COUNT(*) > 1 
                ORDER BY COUNT(*) DESC
                LIMIT %s
            """, [limit])
            
            duplicate_titles = cursor.fetchall()
        
        self.stdout.write(f'Found {len(duplicate_titles)} duplicate groups to process')
        
        total_removed = 0
        
        for i, (title, count) in enumerate(duplicate_titles):
            self.stdout.write(f'Processing {i+1}/{len(duplicate_titles)}: "{title[:40]}..." ({count} copies)')
            
            # Get all books with this title
            books = list(Livros.objects.filter(titulo=title).order_by('id_livro'))
            
            if len(books) <= 1:
                continue
            
            # Keep the first one (lowest ID), remove the rest
            keep_book = books[0]
            remove_books = books[1:]
            
            self.stdout.write(f'  Keeping ID {keep_book.id_livro}, removing {len(remove_books)} duplicates')
            
            # Delete duplicates
            if remove_books:
                remove_ids = [book.id_livro for book in remove_books]
                deleted_count = Livros.objects.filter(id_livro__in=remove_ids).delete()[0]
                total_removed += deleted_count
                
        self.stdout.write(f'\nCompleted! Removed {total_removed} duplicate books')
        
        final_count = Livros.objects.count()
        self.stdout.write(f'Final book count: {final_count}')