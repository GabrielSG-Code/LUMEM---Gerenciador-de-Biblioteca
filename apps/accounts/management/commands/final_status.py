from django.core.management.base import BaseCommand
from django.db.models import Count
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Check final status after book unification'

    def handle(self, *args, **options):
        # Get total count
        total_books = Livros.objects.count()
        self.stdout.write(f'Total books: {total_books}')
        
        # Count duplicates
        duplicates = list(Livros.objects.values('titulo').annotate(count=Count('titulo')).filter(count__gt=1))
        duplicate_count = len(duplicates)
        
        self.stdout.write(f'Duplicate title groups: {duplicate_count}')
        
        if duplicate_count > 0:
            total_duplicate_books = sum((dup["count"] - 1) for dup in duplicates)
            self.stdout.write(f'Total duplicate books remaining: {total_duplicate_books}')
            self.stdout.write(f'Unique books after full unification: {total_books - total_duplicate_books}')
            
            # Show some examples
            self.stdout.write('\nRemaining duplicates (sample):')
            for dup in duplicates[:5]:
                try:
                    title = dup["titulo"][:40].encode('ascii', 'ignore').decode('ascii')
                    self.stdout.write(f'  "{title}...": {dup["count"]} copies')
                except:
                    self.stdout.write(f'  [title with special chars]: {dup["count"]} copies')
        else:
            self.stdout.write(self.style.SUCCESS('No duplicates remaining!'))
            self.stdout.write(f'All books are unique: {total_books}')