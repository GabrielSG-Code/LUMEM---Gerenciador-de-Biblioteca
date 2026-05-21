from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import os
from datetime import datetime, timedelta, date
from accounts.models import Emprestimo, Livros

def home(request):
    if not request.user.is_authenticated:
        # Show public home page for non-authenticated users
        return render(request, 'public_home.html')
    
    # Load category icons from CSV
    import csv
    from django.conf import settings
    
    category_icons = {}
    try:
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'categories.csv'),
            os.path.join(os.path.dirname(__file__), '..', 'categories.csv'),
            'categories.csv'
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
                
        if csv_path:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Category' in row and 'SVG Icon URL' in row:
                        category_icons[row['Category']] = row['SVG Icon URL']
    except Exception as e:
        pass
    
    # Show dashboard for authenticated users
    # Get real loans from database for the current user (only for readers)
    loans = []
    if request.user.role == 'reader':
        try:
            # Get all loans for current user
            all_user_loans = Emprestimo.objects.filter(id_usuario=str(request.user.id))
            all_user_loans_int = Emprestimo.objects.filter(id_usuario=request.user.id)
            
            # If we found loans for this user
            if all_user_loans.exists() or all_user_loans_int.exists():
                # Use whichever query found loans
                user_loans_query = all_user_loans if all_user_loans.exists() else all_user_loans_int
                
                # Get active loans only (not returned)
                active_user_loans = user_loans_query.filter(data_fim__isnull=True).order_by('data_entrega')
                
                for emprestimo in active_user_loans:
                    try:
                        if emprestimo.id_livro:
                            try:
                                livro = Livros.objects.get(id_livro=emprestimo.id_livro)
                                
                                # Get icon URL for this category
                                category_name = livro.genero or 'outros'
                                icon_url = category_icons.get(category_name, 'https://cdn-icons-png.flaticon.com/512/3145/3145765.png')
                                
                                # Simple loan data structure
                                loan_data = {
                                    'book': {
                                        'title': livro.titulo,
                                        'author': livro.autor,
                                        'category': category_name,
                                        'icon_url': icon_url
                                    },
                                    'due_date': emprestimo.data_entrega,
                                    'is_overdue': emprestimo.data_entrega < date.today() if emprestimo.data_entrega else False
                                }
                                loans.append(type('LoanData', (), loan_data))
                                
                            except Livros.DoesNotExist:
                                # Add placeholder for deleted book
                                default_icon = 'https://cdn-icons-png.flaticon.com/512/3145/3145765.png'
                                loan_data = {
                                    'book': {
                                        'title': f'Livro removido (ID: {emprestimo.id_livro})',
                                        'author': 'Autor desconhecido',
                                        'category': 'outros',
                                        'icon_url': default_icon
                                    },
                                    'due_date': emprestimo.data_entrega,
                                    'is_overdue': emprestimo.data_entrega < date.today() if emprestimo.data_entrega else False
                                }
                                loans.append(type('LoanData', (), loan_data))
                        else:
                            continue
                            
                    except Exception as book_error:
                        continue
                    
        except Exception as e:
            loans = []
    
    # Get ALL loans for the history section (only for readers)
    all_loans = []
    if request.user.role == 'reader':
        try:
            # Get all loans for current user (including returned ones)
            all_user_loans = Emprestimo.objects.filter(id_usuario=str(request.user.id))
            all_user_loans_int = Emprestimo.objects.filter(id_usuario=request.user.id)
            
            # If we found loans for this user
            if all_user_loans.exists() or all_user_loans_int.exists():
                # Use whichever query found loans
                user_loans_query = all_user_loans if all_user_loans.exists() else all_user_loans_int
                
                # Get ALL loans (active and returned) ordered by start date (most recent first)
                all_user_loans_ordered = user_loans_query.order_by('-data_inicio')
                
                for emprestimo in all_user_loans_ordered:
                    try:
                        if emprestimo.id_livro:
                            try:
                                livro = Livros.objects.get(id_livro=emprestimo.id_livro)
                                
                                # Determine loan status
                                if emprestimo.data_fim:
                                    status = 'returned'
                                elif emprestimo.data_entrega and emprestimo.data_entrega < date.today():
                                    status = 'overdue'
                                else:
                                    status = 'active'
                                
                                # Simple loan data structure for history
                                loan_data = {
                                    'book_title': livro.titulo,
                                    'book_category': livro.genero or 'outros',
                                    'start_date': emprestimo.data_inicio,
                                    'due_date': emprestimo.data_entrega,
                                    'return_date': emprestimo.data_fim,
                                    'status': status
                                }
                                all_loans.append(type('LoanHistoryData', (), loan_data))
                                
                            except Livros.DoesNotExist:
                                # Add placeholder for deleted book
                                status = 'returned' if emprestimo.data_fim else ('overdue' if emprestimo.data_entrega and emprestimo.data_entrega < date.today() else 'active')
                                loan_data = {
                                    'book_title': f'Livro removido (ID: {emprestimo.id_livro})',
                                    'book_category': 'outros',
                                    'start_date': emprestimo.data_inicio,
                                    'due_date': emprestimo.data_entrega,
                                    'return_date': emprestimo.data_fim,
                                    'status': status
                                }
                                all_loans.append(type('LoanHistoryData', (), loan_data))
                        else:
                            continue
                            
                    except Exception as book_error:
                        continue
                    
        except Exception as e:
            all_loans = []

    # Pagination for all_loans (5 loans per page)
    loans_page = None
    if all_loans:
        paginator = Paginator(all_loans, 5)  # Show 5 loans per page
        page_number = request.GET.get('loans_page', 1)
        try:
            loans_page = paginator.get_page(page_number)
        except:
            loans_page = paginator.get_page(1)

    return render(request, 'home.html', {
        'loans': loans, 
        'all_loans': all_loans,
        'loans_page': loans_page,
        'category_icons': category_icons
    })


