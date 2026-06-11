from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Emprestimo, User

class Command(BaseCommand):
    help = 'Delete loans (emprestimos) that reference non-existent users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write('DRY RUN MODE - No data will be deleted')
        
        # Get all existing user IDs
        existing_user_ids = set(str(user_id) for user_id in User.objects.values_list('id', flat=True))
        self.stdout.write(f'Found {len(existing_user_ids)} existing users')
        
        # Get all loans
        all_loans = Emprestimo.objects.all()
        total_loans = all_loans.count()
        self.stdout.write(f'Total loans in database: {total_loans}')
        
        # Find orphaned loans
        orphaned_loans = []
        valid_loans = []
        null_user_loans = []
        
        for loan in all_loans:
            if not loan.id_usuario:  # Null or empty user ID
                null_user_loans.append(loan)
            elif str(loan.id_usuario) not in existing_user_ids:
                orphaned_loans.append(loan)
            else:
                valid_loans.append(loan)
        
        self.stdout.write(f'Valid loans (user exists): {len(valid_loans)}')
        self.stdout.write(f'Loans with null/empty user ID: {len(null_user_loans)}')
        self.stdout.write(f'Orphaned loans (user doesn\'t exist): {len(orphaned_loans)}')
        
        # Show some examples of orphaned loans
        if orphaned_loans:
            self.stdout.write('\\nSample orphaned loans:')
            for i, loan in enumerate(orphaned_loans[:5]):
                self.stdout.write(f'  Loan ID {loan.id}: User ID {loan.id_usuario}, Book ID {loan.id_livro}, Date: {loan.data_inicio}')
                if i >= 4:
                    break
        
        if null_user_loans:
            self.stdout.write('\\nSample null user loans:')
            for i, loan in enumerate(null_user_loans[:5]):
                self.stdout.write(f'  Loan ID {loan.id}: Book ID {loan.id_livro}, Date: {loan.data_inicio}')
                if i >= 4:
                    break
        
        # Ask for confirmation if not dry run
        loans_to_delete = orphaned_loans + null_user_loans
        total_to_delete = len(loans_to_delete)
        
        if total_to_delete == 0:
            self.stdout.write(self.style.SUCCESS('No orphaned loans found. Database is clean!'))
            return
        
        if not dry_run:
            self.stdout.write(f'\\nAbout to delete {total_to_delete} orphaned loans.')
            confirm = input('Are you sure you want to proceed? (yes/no): ')
            
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return
            
            # Delete orphaned loans
            try:
                with transaction.atomic():
                    deleted_count = 0
                    for loan in loans_to_delete:
                        loan.delete()
                        deleted_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} orphaned loans'))
                    
                    # Show final statistics
                    remaining_loans = Emprestimo.objects.count()
                    self.stdout.write(f'Remaining loans in database: {remaining_loans}')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error deleting loans: {str(e)}'))
        else:
            self.stdout.write(f'\\nDRY RUN: Would delete {total_to_delete} orphaned loans')