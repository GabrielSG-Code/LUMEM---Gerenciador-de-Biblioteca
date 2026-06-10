from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Livros, Emprestimo

class Command(BaseCommand):
    help = 'Check consistency between book statuses and active loans'

    def handle(self, *args, **options):
        self.stdout.write('Checking book status vs loan consistency...\n')
        
        # Get all books
        all_books = Livros.objects.all()
        total_books = all_books.count()
        self.stdout.write(f'Total books: {total_books}')
        
        # Count books by status
        status_counts = {}
        for book in all_books:
            status = book.status_livro or 'NULL'
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.stdout.write('\\nBook status distribution:')
        for status, count in sorted(status_counts.items()):
            self.stdout.write(f'  {status}: {count}')
        
        # Get active loans (loans without data_fim - end date)
        active_loans = Emprestimo.objects.filter(data_fim__isnull=True)
        active_loan_count = active_loans.count()
        self.stdout.write(f'\\nActive loans (no end date): {active_loan_count}')
        
        # Get all loans
        all_loans = Emprestimo.objects.all()
        total_loans = all_loans.count()
        self.stdout.write(f'Total loans (including completed): {total_loans}')
        
        # Check for books marked as borrowed but not in active loans
        non_available_books = all_books.exclude(status_livro__iexact='disponível')
        self.stdout.write(f'\\nBooks NOT marked as available: {non_available_books.count()}')
        
        # Get book IDs from active loans
        active_loan_book_ids = set(str(loan.id_livro) for loan in active_loans if loan.id_livro)
        self.stdout.write(f'Unique books in active loans: {len(active_loan_book_ids)}')
        
        # Find books marked as borrowed but not in active loans
        inconsistent_books = []
        available_but_in_loans = []
        
        for book in all_books:
            book_id_str = str(book.id_livro)
            is_available = book.status_livro and book.status_livro.lower() == 'disponível'
            is_in_active_loan = book_id_str in active_loan_book_ids
            
            if not is_available and not is_in_active_loan:
                inconsistent_books.append(book)
            elif is_available and is_in_active_loan:
                available_but_in_loans.append(book)
        
        self.stdout.write(f'\\nInconsistent books (marked as borrowed but no active loan): {len(inconsistent_books)}')
        if inconsistent_books[:5]:  # Show first 5 examples
            for book in inconsistent_books[:5]:
                self.stdout.write(f'  Book ID {book.id_livro}: "{book.titulo}" - Status: {book.status_livro}')
        
        self.stdout.write(f'\\nBooks marked available but have active loans: {len(available_but_in_loans)}')
        if available_but_in_loans[:5]:  # Show first 5 examples
            for book in available_but_in_loans[:5]:
                self.stdout.write(f'  Book ID {book.id_livro}: "{book.titulo}" - Status: {book.status_livro}')
        
        # Check for orphaned active loans (loans for books that don't exist)
        existing_book_ids = set(str(book.id_livro) for book in all_books)
        orphaned_loans = [loan for loan in active_loans if str(loan.id_livro) not in existing_book_ids]
        
        self.stdout.write(f'\\nOrphaned active loans (book doesn\'t exist): {len(orphaned_loans)}')
        if orphaned_loans[:5]:  # Show first 5 examples
            for loan in orphaned_loans[:5]:
                self.stdout.write(f'  Loan ID {loan.id}: Book ID {loan.id_livro}, User ID {loan.id_usuario}')
        
        # Summary
        self.stdout.write('\\n' + '='*50)
        self.stdout.write('SUMMARY:')
        self.stdout.write(f'Books marked as borrowed: {non_available_books.count()}')
        self.stdout.write(f'Active loans: {active_loan_count}')
        self.stdout.write(f'Inconsistent books (should be available): {len(inconsistent_books)}')
        self.stdout.write(f'Books needing status update (should be borrowed): {len(available_but_in_loans)}')
        self.stdout.write(f'Orphaned loans to clean up: {len(orphaned_loans)}')
        
        if len(inconsistent_books) > 0 or len(available_but_in_loans) > 0 or len(orphaned_loans) > 0:
            self.stdout.write(self.style.WARNING('\\nDatabase inconsistencies found! Consider running fix command.'))
        else:
            self.stdout.write(self.style.SUCCESS('\\nDatabase is consistent!'))