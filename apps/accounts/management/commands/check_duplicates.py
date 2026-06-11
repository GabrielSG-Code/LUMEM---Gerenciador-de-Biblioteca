from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Check for duplicate books in the database'

    def handle(self, *args, **options):
        # Get total count
        total_books = Livros.objects.count()
        self.stdout.write(f'Total books: {total_books}')
        
        # Quick count of duplicates
        duplicates = list(
            Livros.objects
            .values('titulo')
            .annotate(count=Count('titulo'))
            .filter(count__gt=1)
            .order_by('-count')
        )
        
        self.stdout.write(f'Duplicate title groups: {len(duplicates)}')
        
        if len(duplicates) > 0:
            self.stdout.write('\nTop 10 duplicate groups:')
            for dup in duplicates[:10]:
                title = dup["titulo"][:50] + "..." if len(dup["titulo"]) > 50 else dup["titulo"]
                self.stdout.write(f'  "{title}": {dup["count"]} copies')
            
            total_duplicates = sum(dup["count"] - 1 for dup in duplicates)
            self.stdout.write(f'\nTotal duplicate books that could be removed: {total_duplicates}')
            self.stdout.write(f'Books after unification: {total_books - total_duplicates}')
            
            # Sample some books for detailed view
            if duplicates:
                sample_title = duplicates[0]["titulo"]
                sample_books = list(Livros.objects.filter(titulo__iexact=sample_title))
                
                self.stdout.write(f'\n--- Sample duplicate group: "{sample_title}" ---')
                for book in sample_books:
                    self.stdout.write(f'ID {book.id_livro}: {book.autor or "No author"} | {book.editora or "No publisher"} | {book.ano or "No year"}')
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate titles found!'))