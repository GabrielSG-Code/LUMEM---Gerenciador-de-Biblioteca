from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db import transaction
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Fast unification of books with the same title (batch processing)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be unified without making changes',
        )

    def score_book_completeness(self, book):
        """Score a book based on data completeness"""
        score = 10  # Base score
        
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
            
        # Length bonuses
        if book.descricao and len(book.descricao.strip()) > 50:
            score += 2
        if book.editora and len(book.editora.strip()) > 5:
            score += 1
            
        return score

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get duplicate titles with counts
        duplicate_titles = list(
            Livros.objects
            .values('titulo')
            .annotate(count=Count('titulo'))
            .filter(count__gt=1)
            .order_by('-count')
        )
        
        self.stdout.write(f'Found {len(duplicate_titles)} duplicate title groups')
        
        total_removed = 0
        total_groups_processed = 0
        
        # Process in batches
        with transaction.atomic():
            for i, title_data in enumerate(duplicate_titles):
                title = title_data['titulo']
                count = title_data['count']
                
                if i % 50 == 0:
                    self.stdout.write(f'Processing group {i+1}/{len(duplicate_titles)} - "{title[:30]}..." ({count} copies)')
                
                # Get all books with this title
                books = list(Livros.objects.filter(titulo=title).order_by('id_livro'))
                
                if len(books) <= 1:
                    continue
                
                # Find the best book (highest score, then lowest ID)
                best_book = max(books, key=lambda b: (self.score_book_completeness(b), -b.id_livro))
                duplicates = [b for b in books if b.id_livro != best_book.id_livro]
                
                if not dry_run:
                    # Fill missing data in best book from duplicates
                    updated = False
                    for dup in duplicates:
                        if not best_book.editora and dup.editora:
                            best_book.editora = dup.editora
                            updated = True
                        if not best_book.ano and dup.ano:
                            best_book.ano = dup.ano
                            updated = True
                        if not best_book.genero and dup.genero:
                            best_book.genero = dup.genero
                            updated = True
                        if not best_book.descricao and dup.descricao:
                            best_book.descricao = dup.descricao
                            updated = True
                        if not best_book.isbn_13 and dup.isbn_13:
                            best_book.isbn_13 = dup.isbn_13
                            updated = True
                        if not best_book.isbn_10 and dup.isbn_10:
                            best_book.isbn_10 = dup.isbn_10
                            updated = True
                        if not best_book.paginas and dup.paginas:
                            best_book.paginas = dup.paginas
                            updated = True
                    
                    if updated:
                        best_book.save()
                    
                    # Delete duplicates
                    duplicate_ids = [d.id_livro for d in duplicates]
                    deleted_count = Livros.objects.filter(id_livro__in=duplicate_ids).delete()[0]
                    total_removed += deleted_count
                else:
                    total_removed += len(duplicates)
                
                total_groups_processed += 1
                
                # Show progress for large groups
                if count > 10:
                    score = self.score_book_completeness(best_book)
                    self.stdout.write(f'  -> Kept ID {best_book.id_livro} (score: {score}), removed {len(duplicates)} duplicates')
        
        # Final summary
        self.stdout.write(f'\n{"-"*50}')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN SUMMARY:'))
            self.stdout.write(f'Would process {total_groups_processed} duplicate groups')
            self.stdout.write(f'Would remove {total_removed} duplicate books')
        else:
            self.stdout.write(self.style.SUCCESS('UNIFICATION COMPLETE:'))
            self.stdout.write(f'Processed {total_groups_processed} duplicate groups')
            self.stdout.write(f'Removed {total_removed} duplicate books')
            
            final_count = Livros.objects.count()
            self.stdout.write(f'Final book count: {final_count}')