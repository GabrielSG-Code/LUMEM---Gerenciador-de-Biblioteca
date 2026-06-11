from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Unify books with the same title, keeping the one with more complete data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be unified without making changes',
        )

    def score_book_completeness(self, book):
        """Score a book based on data completeness"""
        score = 0
        
        # Basic required fields (already have title/author)
        score += 10  # Base score for having title/author
        
        # Optional but valuable fields
        if book.editora and book.editora.strip():
            score += 3
        if book.ano:
            score += 3
        if book.genero and book.genero.strip():
            score += 2
        if book.descricao and book.descricao.strip():
            score += 4
        if book.isbn_13 and book.isbn_13.strip():
            score += 5
        if book.isbn_10 and book.isbn_10.strip():
            score += 3
        if book.paginas:
            score += 2
            
        # Length bonuses for detailed fields
        if book.descricao and len(book.descricao.strip()) > 50:
            score += 2
        if book.editora and len(book.editora.strip()) > 5:
            score += 1
            
        return score

    def get_duplicate_groups(self):
        """Find books with the same title, grouped together - batch processing"""
        # Get titles that appear more than once (case insensitive)
        duplicate_titles = (
            Livros.objects
            .values('titulo')
            .annotate(count=Count('titulo'))
            .filter(count__gt=1)
            .order_by('-count')
            .values_list('titulo', flat=True)
        )
        
        self.stdout.write(f'Found {len(duplicate_titles)} duplicate title groups to process...')
        
        duplicate_groups = []
        for i, title in enumerate(duplicate_titles):
            if i % 100 == 0:
                self.stdout.write(f'Processing group {i+1}/{len(duplicate_titles)}...')
            
            # Get all books with this title (exact match for efficiency)
            books = list(Livros.objects.filter(titulo=title).order_by('id_livro'))
            if len(books) > 1:
                duplicate_groups.append(books)
                
        return duplicate_groups

    def choose_master_book(self, book_group):
        """Choose which book should be the master (kept) from a group of duplicates"""
        best_book = None
        best_score = -1
        
        for book in book_group:
            # Calculate completeness score
            completeness_score = self.score_book_completeness(book)
            
            # Choose book with highest completeness score
            # If tied, choose the one with the lowest ID (first created)
            is_better = (
                completeness_score > best_score or 
                (completeness_score == best_score and (best_book is None or book.id_livro < best_book.id_livro))
            )
            
            if is_better:
                best_book = book
                best_score = completeness_score
                
        return best_book, best_score

    def merge_book_data(self, master_book, duplicate_books):
        """Merge data from duplicate books into master book, filling missing fields"""
        updated = False
        original_data = {
            'editora': master_book.editora,
            'ano': master_book.ano,
            'genero': master_book.genero,
            'descricao': master_book.descricao,
            'isbn_13': master_book.isbn_13,
            'isbn_10': master_book.isbn_10,
            'paginas': master_book.paginas,
        }
        
        for dup_book in duplicate_books:
            # Fill missing fields from duplicates
            if not master_book.editora and dup_book.editora:
                master_book.editora = dup_book.editora
                updated = True
            if not master_book.ano and dup_book.ano:
                master_book.ano = dup_book.ano
                updated = True
            if not master_book.genero and dup_book.genero:
                master_book.genero = dup_book.genero
                updated = True
            if not master_book.descricao and dup_book.descricao:
                master_book.descricao = dup_book.descricao
                updated = True
            if not master_book.isbn_13 and dup_book.isbn_13:
                master_book.isbn_13 = dup_book.isbn_13
                updated = True
            if not master_book.isbn_10 and dup_book.isbn_10:
                master_book.isbn_10 = dup_book.isbn_10
                updated = True
            if not master_book.paginas and dup_book.paginas:
                master_book.paginas = dup_book.paginas
                updated = True
                
            # Use longer/more detailed versions if master has shorter ones
            if (master_book.descricao and dup_book.descricao and 
                len(dup_book.descricao) > len(master_book.descricao)):
                master_book.descricao = dup_book.descricao
                updated = True
                
        return updated, original_data

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Finding books with duplicate titles...')
        
        duplicate_groups = self.get_duplicate_groups()
        
        if not duplicate_groups:
            self.stdout.write(self.style.SUCCESS('No duplicate titles found!'))
            return
            
        self.stdout.write(f'Found {len(duplicate_groups)} groups of duplicate titles')
        
        total_books_to_remove = 0
        total_books_updated = 0
        
        for i, book_group in enumerate(duplicate_groups, 1):
            title = book_group[0].titulo
            self.stdout.write(f'\n--- Group {i}: "{title}" ({len(book_group)} copies) ---')
            
            # Choose master book
            master_book, master_score = self.choose_master_book(book_group)
            duplicate_books = [b for b in book_group if b.id_livro != master_book.id_livro]
            
            self.stdout.write(f'Master book: ID {master_book.id_livro} (score: {master_score})')
            
            # Show simplified details for large groups
            if len(book_group) <= 5:
                # Show details for small groups
                for book in book_group:
                    score = self.score_book_completeness(book)
                    status = "MASTER" if book.id_livro == master_book.id_livro else "duplicate"
                    self.stdout.write(f'  - ID {book.id_livro}: score={score} [{status}] {book.autor or "No author"} | {book.ano or "No year"}')
            else:
                # Just show summary for large groups
                self.stdout.write(f'  -> {len(duplicate_books)} duplicates will be removed')
                    
            if not dry_run:
                # Merge data from duplicates into master
                data_updated, original_data = self.merge_book_data(master_book, duplicate_books)
                
                if data_updated:
                    master_book.save()
                    total_books_updated += 1
                    self.stdout.write(f'  -> Updated master book with merged data')
                
                # Delete duplicate books
                duplicate_ids = [book.id_livro for book in duplicate_books]
                deleted_count, _ = Livros.objects.filter(id_livro__in=duplicate_ids).delete()
                total_books_to_remove += deleted_count
                
                self.stdout.write(f'  -> Removed {deleted_count} duplicate books')
            else:
                self.stdout.write(f'  -> Would remove {len(duplicate_books)} duplicate books')
                total_books_to_remove += len(duplicate_books)
        
        # Summary
        self.stdout.write(f'\n{"-"*50}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN SUMMARY:'))
            self.stdout.write(f'Would process {len(duplicate_groups)} duplicate groups')
            self.stdout.write(f'Would remove {total_books_to_remove} duplicate books')
            self.stdout.write(f'Would update master books with merged data')
        else:
            self.stdout.write(self.style.SUCCESS('UNIFICATION COMPLETE:'))
            self.stdout.write(f'Processed {len(duplicate_groups)} duplicate groups')
            self.stdout.write(f'Removed {total_books_to_remove} duplicate books')
            self.stdout.write(f'Updated {total_books_updated} master books with merged data')
            
            # Show final count
            final_count = Livros.objects.count()
            self.stdout.write(f'Final book count: {final_count}')