from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import Livros, Emprestimo

class Command(BaseCommand):
    help = 'Fix inconsistencies between book statuses and active loans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually fixing',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write('DRY RUN MODE - No data will be changed')
        
        self.stdout.write('Fixing book status and loan inconsistencies...\n')
        
        # Get all books and active loans
        all_books = Livros.objects.all()
        active_loans = Emprestimo.objects.filter(data_fim__isnull=True)
        
        # Get book IDs from active loans
        active_loan_book_ids = set(str(loan.id_livro) for loan in active_loans if loan.id_livro)
        existing_book_ids = set(str(book.id_livro) for book in all_books)
        
        # Find inconsistent books and orphaned loans
        books_to_mark_available = []
        books_to_mark_borrowed = []
        orphaned_loans = []
        
        # Check books
        for book in all_books:
            book_id_str = str(book.id_livro)
            is_available = book.status_livro and book.status_livro.lower() == 'disponível'
            is_in_active_loan = book_id_str in active_loan_book_ids
            
            if not is_available and not is_in_active_loan:
                books_to_mark_available.append(book)
            elif is_available and is_in_active_loan:
                books_to_mark_borrowed.append(book)
        
        # Check loans
        for loan in active_loans:
            if str(loan.id_livro) not in existing_book_ids:
                orphaned_loans.append(loan)
        
        # Show what will be fixed
        self.stdout.write(f'Books to mark as available: {len(books_to_mark_available)}')
        if books_to_mark_available[:5]:
            for book in books_to_mark_available[:5]:
                try:
                    safe_title = book.titulo[:40].encode('ascii', 'ignore').decode('ascii')
                    self.stdout.write(f'  Book ID {book.id_livro}: "{safe_title}" ({book.status_livro} -> Available)')
                except:
                    self.stdout.write(f'  Book ID {book.id_livro}: [title with special chars] ({book.status_livro} -> Available)')
        
        self.stdout.write(f'\\nBooks to mark as borrowed: {len(books_to_mark_borrowed)}')
        if books_to_mark_borrowed[:5]:
            for book in books_to_mark_borrowed[:5]:
                try:
                    safe_title = book.titulo[:40].encode('ascii', 'ignore').decode('ascii')
                    self.stdout.write(f'  Book ID {book.id_livro}: "{safe_title}" ({book.status_livro} -> Borrowed)')
                except:
                    self.stdout.write(f'  Book ID {book.id_livro}: [title with special chars] ({book.status_livro} -> Borrowed)')
        
        self.stdout.write(f'\\nOrphaned loans to delete: {len(orphaned_loans)}')
        if orphaned_loans[:5]:
            for loan in orphaned_loans[:5]:
                self.stdout.write(f'  Loan ID {loan.id}: Book ID {loan.id_livro}, User ID {loan.id_usuario}')
        
        total_changes = len(books_to_mark_available) + len(books_to_mark_borrowed) + len(orphaned_loans)
        
        if total_changes == 0:
            self.stdout.write(self.style.SUCCESS('\\nNo inconsistencies found. Database is already consistent!'))
            return
        
        if not dry_run:
            self.stdout.write(f'\\nAbout to make {total_changes} changes.')
            confirm = input('Are you sure you want to proceed? (yes/no): ')
            
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return
            
            try:
                with transaction.atomic():
                    changes_made = 0
                    
                    # Fix books that should be available
                    if books_to_mark_available:
                        for book in books_to_mark_available:
                            book.status_livro = 'Disponível'
                            book.save()
                            changes_made += 1
                        self.stdout.write(f'Marked {len(books_to_mark_available)} books as available')
                    
                    # Fix books that should be borrowed
                    if books_to_mark_borrowed:
                        for book in books_to_mark_borrowed:
                            book.status_livro = 'Emprestado'
                            book.save()
                            changes_made += 1
                        self.stdout.write(f'Marked {len(books_to_mark_borrowed)} books as borrowed')
                    
                    # Delete orphaned loans
                    if orphaned_loans:
                        for loan in orphaned_loans:
                            loan.delete()
                            changes_made += 1
                        self.stdout.write(f'Deleted {len(orphaned_loans)} orphaned loans')
                    
                    self.stdout.write(self.style.SUCCESS(f'\\nSuccessfully made {changes_made} changes'))
                    
                    # Show final statistics
                    final_available = Livros.objects.filter(status_livro__iexact='disponível').count()
                    final_borrowed = Livros.objects.exclude(status_livro__iexact='disponível').count()
                    final_active_loans = Emprestimo.objects.filter(data_fim__isnull=True).count()
                    
                    self.stdout.write(f'\\nFinal status:')
                    self.stdout.write(f'  Books marked as available: {final_available}')
                    self.stdout.write(f'  Books marked as borrowed: {final_borrowed}')
                    self.stdout.write(f'  Active loans: {final_active_loans}')
                    
                    if final_borrowed == final_active_loans:
                        self.stdout.write(self.style.SUCCESS('Database is now consistent!'))
                    else:
                        self.stdout.write(self.style.WARNING('Some inconsistencies may remain. Re-run check command.'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error making changes: {str(e)}'))
        else:
            self.stdout.write(f'\\nDRY RUN: Would make {total_changes} changes')