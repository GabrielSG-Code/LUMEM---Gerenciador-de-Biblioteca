from django.core.management.base import BaseCommand
from django.db import connection
from accounts.models import Livros

class Command(BaseCommand):
    help = 'Fix the auto-increment sequence for id_livro'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get the maximum id_livro value
            cursor.execute("SELECT MAX(id_livro) FROM livros")
            max_id = cursor.fetchone()[0] or 0
            
            self.stdout.write(f'Current max id_livro: {max_id}')
            
            # Reset the sequence to start from max_id + 1
            # This works for PostgreSQL - adjust for other databases if needed
            try:
                cursor.execute(f"SELECT setval('livros_id_livro_seq', {max_id + 1}, false)")
                self.stdout.write(self.style.SUCCESS(f'Sequence reset to start from {max_id + 1}'))
            except Exception as e:
                # If PostgreSQL sequence doesn't exist, try SQLite approach
                self.stdout.write(f'PostgreSQL sequence not found, trying SQLite approach: {e}')
                
                # For SQLite, we need to update the sqlite_sequence table
                try:
                    cursor.execute(f"UPDATE sqlite_sequence SET seq = {max_id} WHERE name = 'livros'")
                    self.stdout.write(self.style.SUCCESS(f'SQLite sequence updated to {max_id}'))
                except Exception as e2:
                    self.stdout.write(f'Error updating sequence: {e2}')
                    
        # Verify the fix
        total_books = Livros.objects.count()
        self.stdout.write(f'Total books in database: {total_books}')