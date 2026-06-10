from django.core.management.base import BaseCommand
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Remove half of the books from the database'

    def handle(self, *args, **options):
        # Get total count
        total_books = Livros.objects.count()
        self.stdout.write(f'Total books before: {total_books}')
        
        if total_books == 0:
            self.stdout.write(self.style.WARNING('No books found in database'))
            return
        
        # Calculate half count  
        half_count = total_books // 2
        self.stdout.write(f'Will remove: {half_count} books')
        
        if half_count > 0:
            # Get the first half of books by ID
            books_to_delete = Livros.objects.all().order_by('id_livro')[:half_count]
            book_ids = [book.id_livro for book in books_to_delete]
            
            self.stdout.write(f'Removing books with IDs: {book_ids[:5]}...' + (f' and {len(book_ids)-5} more' if len(book_ids) > 5 else ''))
            
            # Delete the selected books
            deleted_count, _ = Livros.objects.filter(id_livro__in=book_ids).delete()
            
            # Check remaining count
            remaining_books = Livros.objects.count()
            self.stdout.write(f'Total books after: {remaining_books}')
            self.stdout.write(self.style.SUCCESS(f'Successfully removed {deleted_count} books'))
            
        else:
            self.stdout.write(self.style.WARNING('No books to remove'))