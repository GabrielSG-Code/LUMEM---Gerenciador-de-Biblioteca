from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.db import transaction
import json
from datetime import date

# Importações do ReportLab
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .forms import RegisterForm, EmailOrUsernameLoginForm, AddBookForm, LoanForm, ChangePasswordForm, ChangeEmailForm, ChangeUsernameForm, EditBookForm, get_current_year, get_max_book_year, get_max_book_copies, get_default_book_copies
from .models import Livros, User, Emprestimo, LoanConfig, DamageReport, UserRegularization


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao LUMEN.')
            return redirect('home')
        else:
            # Show form validation errors
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailOrUsernameLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = EmailOrUsernameLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    request.session.pop('loan_alerts_shown', None)

    storage = messages.get_messages(request)
    storage.used = True

    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


@login_required
def browse_collection(request):
    import csv
    import os
    from django.conf import settings

    category_icons = {}
    try:
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'categories.csv'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'categories.csv'),
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
    

    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    page_number = request.GET.get('page', 1)

    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1

    livros_query = Livros.objects.all()

    if search_query:
        livros_query = livros_query.filter(
            Q(titulo__icontains=search_query) |
            Q(autor__icontains=search_query)
        )

    if category_filter and category_filter != 'all':
        livros_query = livros_query.filter(genero__icontains=category_filter)

    from django.db.models import Count, Case, When, IntegerField

    # Fast and simple grouping - group only by title and author for consistency
    unique_books_query = livros_query.values(
        'titulo', 'autor'
    ).annotate(
        total_count=Count('id_livro'),
        available_count=Count(
            Case(
                When(status_livro__iexact='disponível', then=1),
                output_field=IntegerField()
            )
        )
    ).order_by('titulo', 'autor')

    total_unique_books = unique_books_query.count()
    total_exemplars = livros_query.count()
    available_exemplars = livros_query.filter(status_livro__iexact='disponível').count()

    # Calculate stats for the stats bar
    from django.utils import timezone
    
    # Count all loans (both active and completed) instead of just borrowed books
    total_loans_count = 0
    try:
        total_loans_count = Emprestimo.objects.count()
    except:
        total_loans_count = 0
    
    # Calculate overdue loans
    overdue_count = 0
    try:
        overdue_loans = Emprestimo.objects.filter(
            data_entrega__lt=timezone.now().date(),
            data_fim__isnull=True
        )
        overdue_count = overdue_loans.count()
    except:
        overdue_count = 0

    stats = {
        'total_books': total_unique_books,
        'available': available_exemplars,
        'borrowed': total_loans_count,  # Now shows total loans instead of borrowed books
        'overdue': overdue_count
    }

    books_per_page = 12
    start_index = (page_number - 1) * books_per_page
    end_index = start_index + books_per_page

    current_page_books = unique_books_query[start_index:end_index]

    # Get representative books for the current page in a single query
    current_page_titles_authors = [(book['titulo'], book['autor']) for book in current_page_books]
    
    if current_page_titles_authors:
        # Build Q objects for filtering
        q_objects = Q()
        for titulo, autor in current_page_titles_authors:
            q_objects |= Q(titulo=titulo, autor=autor)
        
        rep_books_query = livros_query.filter(q_objects).order_by('titulo', 'autor', 'id_livro')
    else:
        rep_books_query = livros_query.none()
    
    # Create a lookup dict for representative books (first book per title/author)
    rep_books_dict = {}
    for book in rep_books_query:
        key = (book.titulo, book.autor)
        if key not in rep_books_dict:
            rep_books_dict[key] = book

    books_list = []
    for book_data in current_page_books:
        # Get the representative book from the dict
        representative_book = rep_books_dict.get((book_data['titulo'], book_data['autor']))
        
        category_name = representative_book.genero or 'Outros' if representative_book else 'Outros'
        
        # Get the appropriate icon for the category with better matching
        icon_url = None
        # Try exact match first
        if category_name in category_icons:
            icon_url = category_icons[category_name]
        else:
            # Try case-insensitive match
            for csv_cat, csv_icon in category_icons.items():
                if csv_cat.lower() == category_name.lower():
                    icon_url = csv_icon
                    break
        
        # Fallback to default icon if no match found
        if not icon_url:
            icon_url = 'https://cdn-icons-png.flaticon.com/512/1146/1146315.png'
        

        processed_book = {
            'id': representative_book.id_livro if representative_book else None,
            'title': book_data['titulo'],
            'author': book_data['autor'],
            'category': category_name,
            'category_lower': category_name.lower(),
            'icon_url': icon_url,
            'year': representative_book.ano if representative_book else None,
            'publisher': representative_book.editora if representative_book else '',
            'description': representative_book.descricao if representative_book else '',
            'total_count': book_data['total_count'],
            'available_count': book_data['available_count'],
            'available': book_data['available_count'] > 0,
            'availability_text': f"{book_data['available_count']}/{book_data['total_count']}"
        }
        books_list.append(processed_book)

    total_pages = (total_unique_books + books_per_page - 1) // books_per_page if total_unique_books > 0 else 1
    has_previous = page_number > 1
    has_next = page_number < total_pages

    start_page = max(1, page_number - 2)
    end_page = min(total_pages, page_number + 2)
    page_range = list(range(start_page, end_page + 1))

    class MockPaginator:
        def __init__(self, books, page_num, total_books, total_pages):
            self.object_list = books
            self.number = page_num
            self.paginator = self
            self.num_pages = total_pages
            self.page_range = page_range
            self.has_previous = lambda: has_previous
            self.has_next = lambda: has_next
            self.previous_page_number = page_num - 1 if has_previous else None
            self.next_page_number = page_num + 1 if has_next else None
            self.start_index = lambda: start_index + 1 if books else 0
            self.end_index = lambda: min(start_index + len(books), total_books)
            self.has_other_pages = total_pages > 1

        def __iter__(self):
            return iter(self.object_list)

        def __len__(self):
            return len(self.object_list)

    books_page = MockPaginator(books_list, page_number, total_unique_books, total_pages)

    # Get unique categories with proper deduplication
    categories_raw = Livros.objects.exclude(genero__isnull=True).exclude(genero='').values_list('genero', flat=True).distinct()


    import unicodedata
    unique_categories = {}
    for category in categories_raw:
        if category and category.strip():
            # Normalize to title case for consistency
            cleaned = category.strip().title()
            # Remove accents for comparison key (ficção -> ficcao)
            normalized_key = unicodedata.normalize('NFD', cleaned.lower())
            normalized_key = ''.join(c for c in normalized_key if unicodedata.category(c) != 'Mn')
            
            # Keep the version with accents if it exists, otherwise use the current one
            if normalized_key not in unique_categories:
                unique_categories[normalized_key] = cleaned
            else:
                # Prefer the version with accents (ç over c)
                existing = unique_categories[normalized_key]
                if 'ç' in cleaned.lower() and 'c' in existing.lower():
                    unique_categories[normalized_key] = cleaned

    categories = sorted(list(unique_categories.values()), key=str.lower)

    
    context = {
        'books': books_page,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'category_icons': category_icons,
        'category_icons_json': json.dumps(category_icons),
        'total_books': total_unique_books,
        'total_exemplars': total_exemplars,
        'available_exemplars': available_exemplars,
        'stats': stats,
        'current_year': get_current_year(),
        'max_book_year': get_max_book_year(),
        'max_book_copies': get_max_book_copies(),
        'default_book_copies': get_default_book_copies()
    }

    return render(request, 'browse_collection.html', context)


@login_required
def manage_users(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.error(request, 'Acesso negado. Apenas administradores podem gerenciar usuários.')
        return redirect('browse_collection')

    users = User.objects.all().order_by('username')

    user_data = []
    for user in users:
        initials = user.username[:2].upper() if user.username else 'NA'
        
        # Determine if this user can be edited by the current user
        can_edit = True
        if user.is_superuser and not request.user.is_superuser:
            can_edit = False
        
        # Get user status based on the unified status field
        user_status = user.get_status_display() if hasattr(user, 'status') else 'Ativo'
        
        # Debug mode: simulate blocked user for testing
        # This makes the first reader appear as blocked for testing the filter
        if request.GET.get('debug_blocked') == '1' and user.role == 'reader' and users.filter(role='reader').first() == user:
            user_status = 'Bloqueado'
        
        user_data.append({
            'id': user.id,
            'initials': initials,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'status': user_status,
            'last_login': user.last_login.strftime('%d/%m/%Y, %H:%M') if user.last_login else 'Nunca',
            'is_superuser': user.is_superuser,
            'can_edit': can_edit
        })

    # Calculate status-based counts safely
    active_count = 0
    inactive_count = 0
    blocked_count = 0
    
    try:
        active_count = users.filter(status=User.Status.ACTIVE).count()
        inactive_count = users.filter(status=User.Status.INACTIVE).count()
        blocked_count = users.filter(status=User.Status.BLOCKED).count()
    except Exception:
        # Fallback to is_active field if status field doesn't exist yet
        active_count = users.filter(is_active=True).count()
        inactive_count = users.filter(is_active=False).count()
        blocked_count = 0
    
    # Debug mode: add 1 to blocked count if simulating blocked user
    if request.GET.get('debug_blocked') == '1':
        blocked_count += 1
        active_count -= 1 if active_count > 0 else 0
    
    stats = {
        'total': users.count(),
        'active': active_count,
        'inactive': inactive_count,
        'blocked': blocked_count
    }

    return render(request, 'manage_users.html', {
        'users': user_data,
        'stats': stats
    })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_user(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado. Apenas administradores podem atualizar usuários.'
        }, status=403)

    try:
        user = get_object_or_404(User, id=user_id)
        
        # Prevent regular admins from editing superusers
        if user.is_superuser and not request.user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'Acesso negado. Apenas superusuários podem editar outros superusuários.'
            }, status=403)
        
        data = json.loads(request.body)

        # Handle regularization workflow for blocked users
        if 'regularization_method' in data and user.status == User.Status.BLOCKED:
            return handle_user_regularization(request, user, data)

        if 'role' in data:
            role_map = {
                'Leitor': 'reader',
                'Bibliotecário': 'librarian',
                'Administrador': 'admin'
            }
            user.role = role_map.get(data['role'], 'reader')

        if 'status' in data:
            status_map = {
                'Ativo': User.Status.ACTIVE,
                'Inativo': User.Status.INACTIVE,
                'Bloqueado': User.Status.BLOCKED
            }
            new_status = status_map.get(data['status'])
            if new_status:
                user.status = new_status
                # Also update is_active based on status for compatibility
                user.is_active = (new_status == User.Status.ACTIVE)

        user.save()

        return JsonResponse({
            'success': True,
            'message': f'Usuário "{user.get_full_name() or user.username}" atualizado com sucesso!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao atualizar usuário: {str(e)}'
        }, status=500)


def handle_user_regularization(request, user, data):
    """Handle the regularization workflow for blocked users"""
    try:
        # Validate regularization method
        regularization_method = data.get('regularization_method')
        if not regularization_method:
            return JsonResponse({
                'success': False,
                'message': 'Método de regularização é obrigatório.'
            }, status=400)
        
        # Get the damage report that caused the block
        try:
            damage_report = DamageReport.objects.filter(user=user).latest('reported_at')
        except DamageReport.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Relatório de dano não encontrado para este usuário.'
            }, status=404)
        
        # Check if already regularized
        if hasattr(damage_report, 'regularization'):
            return JsonResponse({
                'success': False,
                'message': 'Este usuário já foi regularizado anteriormente.'
            }, status=400)
        
        # Begin transaction to ensure data consistency
        with transaction.atomic():
            # Create regularization record
            regularization = UserRegularization.objects.create(
                damage_report=damage_report,
                user=user,
                administrator=request.user,
                method=regularization_method,
                notes=data.get('regularization_notes', '').strip()
            )
            
            # Unblock the user
            user.status = User.Status.ACTIVE
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Usuário "{user.get_full_name() or user.username}" foi regularizado e desbloqueado com sucesso! O usuário já pode realizar novos empréstimos.',
                'regularized': True
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao processar regularização: {str(e)}'
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["GET"])
def get_user_damage_info(request, user_id):
    """Get damage information for a blocked user"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return JsonResponse({
            'success': False,
            'message': 'Acesso negado.'
        }, status=403)

    try:
        user = get_object_or_404(User, id=user_id)
        
        # Only get damage info for blocked users
        if user.status != User.Status.BLOCKED:
            return JsonResponse({
                'success': False,
                'message': 'Este usuário não está bloqueado.'
            }, status=400)
        
        # Get the latest damage report
        try:
            damage_report = DamageReport.objects.filter(user=user).latest('reported_at')
            
            # Check if already regularized
            is_regularized = hasattr(damage_report, 'regularization')
            
            damage_info = {
                'book_title': damage_report.book.titulo,
                'book_author': damage_report.book.autor,
                'description': damage_report.description,
                'reported_date': damage_report.reported_at.strftime('%d/%m/%Y'),
                'reported_by': damage_report.reported_by.username,
                'is_regularized': is_regularized
            }
            
            if is_regularized:
                regularization = damage_report.regularization
                damage_info['regularization_info'] = {
                    'method': regularization.get_method_display(),
                    'regularized_at': regularization.regularized_at.strftime('%d/%m/%Y'),
                    'administrator': regularization.administrator.username,
                    'notes': regularization.notes
                }
            
            return JsonResponse({
                'success': True,
                'damage_info': damage_info
            })
            
        except DamageReport.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Relatório de dano não encontrado.'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter informações: {str(e)}'
        }, status=500)


@login_required
def edit_book(request, book_id):
    """Edit existing book information"""
    if request.user.role == 'reader':
        return JsonResponse({'success': False, 'error': 'Acesso negado. Apenas administradores e bibliotecários podem editar livros.'}, status=403)
    
    try:
        # Get the representative book for this title/author combination
        book = get_object_or_404(Livros, id_livro=book_id)
        
        # Get all books with same title and author to count total copies
        same_books = Livros.objects.filter(titulo=book.titulo, autor=book.autor)
        total_copies = same_books.count()
        
        # Prepare book data for form
        book_data = {
            'titulo': book.titulo,
            'autor': book.autor,
            'ano': book.ano,
            'editora': book.editora,
            'genero': book.genero,
            'descricao': book.descricao,
            'total_count': total_copies
        }
        
        if request.method == 'POST':
            form = EditBookForm(book_data, request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        # Update all books with same title and author
                        title = form.cleaned_data['title']
                        author = form.cleaned_data['author']
                        year = form.cleaned_data['year']
                        publisher = form.cleaned_data['publisher']
                        category = form.cleaned_data['category']
                        description = form.cleaned_data['description']
                        new_copies = form.cleaned_data['copies']
                        
                        # Handle copies count change BEFORE updating existing books
                        current_copies = same_books.count()
                        
                        # Update existing books
                        same_books.update(
                            titulo=title,
                            autor=author,
                            ano=year,
                            editora=publisher,
                            genero=category,
                            descricao=description
                        )
                        
                        if new_copies > current_copies:
                            # Add more copies
                            copies_to_add = new_copies - current_copies
                            for _ in range(copies_to_add):
                                Livros.objects.create(
                                    titulo=title,
                                    autor=author,
                                    ano=year,
                                    editora=publisher,
                                    genero=category,
                                    descricao=description,
                                    status_livro='Disponível'
                                )
                        elif new_copies < current_copies:
                            # Remove excess copies (only available ones)
                            # Re-query the books after update to get the correct status
                            updated_books = Livros.objects.filter(titulo=title, autor=author)
                            copies_to_remove = current_copies - new_copies
                            available_books = updated_books.filter(status_livro='Disponível')
                            
                            if available_books.count() < copies_to_remove:
                                return JsonResponse({
                                    'success': False, 
                                    'error': f'Não é possível remover {copies_to_remove} exemplares. Apenas {available_books.count()} estão disponíveis.'
                                })
                            
                            # Remove the excess available copies
                            books_to_delete = available_books[:copies_to_remove]
                            for book_to_delete in books_to_delete:
                                book_to_delete.delete()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Livro "{title}" atualizado com sucesso!'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Erro ao processar solicitação: {str(e)}'
                    })
            else:
                # Return form errors
                errors = []
                for field, field_errors in form.errors.items():
                    if field == '__all__':
                        errors.extend(field_errors)
                    else:
                        for error in field_errors:
                            errors.append(f'{form[field].label}: {error}')
                
                return JsonResponse({
                    'success': False,
                    'error': '; '.join(errors)
                })
        else:
            form = EditBookForm(book_data)
            
        return JsonResponse({
            'success': True,
            'book_data': book_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao processar solicitação: {str(e)}'
        }, status=500)


@login_required
def add_book(request):
    if request.user.role == 'reader':
        messages.error(request, 'Acesso negado. Apenas administradores e bibliotecários podem adicionar livros.')
        return redirect('browse_collection')
        
    if request.method != 'POST':
        messages.error(request, 'Método não permitido')
        return redirect('browse_collection')

    form = AddBookForm(request.POST)
    

    if not form.is_valid():
        # Extract and format error messages for better display
        error_messages = []
        for field, errors in form.errors.items():
            if field == '__all__':
                # Non-field errors (like our duplicate book check)
                for error in errors:
                    error_messages.append(error)
            else:
                # Field-specific errors
                field_name = form[field].label if hasattr(form[field], 'label') else field
                for error in errors:
                    error_messages.append(f'{field_name}: {error}')
        
        for error_msg in error_messages:
            messages.error(request, error_msg)
        
        return redirect('browse_collection')

    try:
        # Check if this is a new edition of an existing book
        title = form.cleaned_data['title']
        author = form.cleaned_data['author']
        release_year = form.cleaned_data.get('release_year')
        
        existing_editions = Livros.objects.filter(
            titulo__iexact=title.strip(),
            autor__iexact=author.strip()
        )
        
        if release_year and existing_editions.exists():
            other_years = list(existing_editions.filter(ano__isnull=False).exclude(ano=release_year).values_list('ano', flat=True).distinct())
            if other_years:
                is_new_edition = True
            else:
                is_new_edition = False
        else:
            is_new_edition = False
        
        livros_criados = form.save_books()
        
        # Create appropriate success message
        if is_new_edition:
            messages.success(
                request,
                f'{len(livros_criados)} exemplar(es) da nova edição ({release_year}) de "{title}" por "{author}" '
                f'adicionado(s) com sucesso. Outras edições existem nos anos: {", ".join(map(str, sorted(other_years)))}.'
            )
        else:
            messages.success(
                request,
                f'{len(livros_criados)} exemplar(es) do livro "{title}" adicionado(s) com sucesso.'
            )
        
        return redirect('browse_collection')
    except Exception as e:
        messages.error(request, f'Erro ao salvar livros: {str(e)}')
        return redirect('browse_collection')


@login_required
def manage_loans(request):
    
    # Handle loan creation via modal (only for non-readers)
    loan_form = None
    selected_book_id = None
    if request.user.role != 'reader':
        # Check for pre-selected book from URL parameters
        book_title = request.GET.get('book_title')
        book_author = request.GET.get('book_author')
        
        if book_title and book_author:
            # Find an available book with this title and author
            try:
                available_book = Livros.objects.filter(
                    titulo=book_title,
                    autor=book_author,
                    status_livro__iexact='disponível'
                ).first()
                if available_book:
                    selected_book_id = str(available_book.id_livro)
            except:
                pass
        
        # Pass book info to form if coming from browse route
        form_kwargs = {}
        if book_title and book_author:
            form_kwargs['preselected_title'] = book_title
            form_kwargs['preselected_author'] = book_author
        
        loan_form = LoanForm(**form_kwargs)
        
        if request.method == 'POST':
            loan_form = LoanForm(request.POST)
            if loan_form.is_valid():
                loan_form.save()
                messages.success(request, 'Empréstimo criado com sucesso!')
                return redirect('manage_loans')
            # Note: When form has errors, we don't add a general error message
            # The specific errors will be displayed inside the modal
    
    # Filter loans based on user role
    if request.user.role == 'reader':
        # Readers see only their own loans
        emprestimos_queryset = Emprestimo.objects.filter(
            id_usuario=str(request.user.id)
        ).order_by('-data_inicio')
    else:
        # Librarians and admins see all loans
        emprestimos_queryset = Emprestimo.objects.all().order_by('-data_inicio')
    
    # Add pagination
    paginator = Paginator(emprestimos_queryset, 10)  # 10 loans per page
    page_number = request.GET.get('page')
    try:
        emprestimos_page = paginator.page(page_number)
    except PageNotAnInteger:
        emprestimos_page = paginator.page(1)
    except EmptyPage:
        emprestimos_page = paginator.page(paginator.num_pages)
    
    loans_data = []
    for emp in emprestimos_page:
        # Handle user lookup
        try:
            user = User.objects.get(id=emp.id_usuario) if emp.id_usuario else None
            user_name = user.username if user else f'Usuário ID {emp.id_usuario} (não encontrado)'
        except User.DoesNotExist:
            user_name = f'Usuário ID {emp.id_usuario} (não encontrado)'
        except:
            user_name = 'Usuário não encontrado'
        
        # Handle book lookup
        try:
            book = Livros.objects.get(id_livro=emp.id_livro) if emp.id_livro else None
            book_title = book.titulo if book else f'Livro ID {emp.id_livro} (não encontrado)'
        except Livros.DoesNotExist:
            book_title = f'Livro ID {emp.id_livro} (não encontrado)'
        except:
            book_title = 'Livro não encontrado'
        
        # Calculate overdue status using loan-specific overdue_days (grandfathering)
        is_overdue = False
        if emp.data_entrega and not emp.data_fim:
            # Use the overdue_days that were set when this loan was created
            overdue_threshold = emp.data_entrega + timedelta(days=emp.overdue_days or 7)
            is_overdue = timezone.now().date() > overdue_threshold
        
        # Add loan data even if user/book not found
        loans_data.append({
            'id': emp.id,
            'loan_id': emp.id_emprestimo or f'EMP_{emp.id}',
            'user_name': user_name,
            'book_title': book_title,
            'start_date': emp.data_inicio,
            'due_date': emp.data_entrega,
            'return_date': emp.data_fim,
            'is_overdue': is_overdue
        })
    
    # Get current loan configuration
    loan_config = LoanConfig.get_config()
    
    return render(request, 'manage_loans.html', {
        'loans': loans_data,
        'loans_page': emprestimos_page,
        'loan_form': loan_form,
        'is_reader': request.user.role == 'reader',
        'selected_book_id': selected_book_id,
        'loan_config': loan_config
    })


@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def return_book(request, loan_id):
    emprestimo = get_object_or_404(Emprestimo, id=loan_id)

    # Check if reader is trying to return someone else's book
    if request.user.role == 'reader' and str(emprestimo.id_usuario) != str(request.user.id):
        if request.method == 'GET':
            return JsonResponse({
                'success': False,
                'message': 'Você só pode devolver seus próprios livros.'
            }, status=403)
        messages.error(request, 'Você só pode devolver seus próprios livros.')
        return redirect('manage_loans')

    if emprestimo.data_fim:
        if request.method == 'GET':
            return JsonResponse({
                'success': False,
                'message': 'Este livro já foi devolvido.'
            }, status=400)
        messages.warning(request, 'Este livro já foi devolvido.')
        return redirect('manage_loans')

    # GET request: Return modal data for display
    if request.method == 'GET':
        try:
            book = Livros.objects.get(id_livro=emprestimo.id_livro)
            user = User.objects.get(id=emprestimo.id_usuario)
            
            return JsonResponse({
                'success': True,
                'loan_data': {
                    'loan_id': emprestimo.id,
                    'book_title': book.titulo,
                    'book_author': book.autor,
                    'user_name': user.username,
                    'start_date': emprestimo.data_inicio.strftime('%d/%m/%Y') if emprestimo.data_inicio else 'N/A',
                    'due_date': emprestimo.data_entrega.strftime('%d/%m/%Y') if emprestimo.data_entrega else 'N/A'
                }
            })
        except (Livros.DoesNotExist, User.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Dados do empréstimo não encontrados.'
            }, status=404)

    # POST request: Process return with optional damage report
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_damaged = data.get('is_damaged', False)
            damage_description = data.get('damage_description', '').strip()

            # Validate damage description if book is damaged
            if is_damaged and not damage_description:
                return JsonResponse({
                    'success': False,
                    'message': 'A descrição do dano é obrigatória quando o livro é marcado como danificado.'
                }, status=400)

            # Begin transaction to ensure data consistency
            with transaction.atomic():
                # Complete the return
                emprestimo.data_fim = timezone.now().date()
                emprestimo.save()

                # Update book status
                try:
                    book = Livros.objects.get(id_livro=emprestimo.id_livro)
                    book.status_livro = 'Disponível'
                    book.save()
                except Livros.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Livro não encontrado no sistema.'
                    }, status=404)

                # If book is damaged, create damage report and block user
                if is_damaged:
                    try:
                        user = User.objects.get(id=emprestimo.id_usuario)
                        
                        # Create damage report
                        damage_report = DamageReport.objects.create(
                            emprestimo=emprestimo,
                            user=user,
                            book=book,
                            description=damage_description,
                            reported_by=request.user
                        )
                        
                        # Block the user
                        user.status = User.Status.BLOCKED
                        user.save()
                        
                        return JsonResponse({
                            'success': True,
                            'message': f'Livro "{book.titulo}" devolvido com registro de dano. Usuário "{user.username}" foi automaticamente bloqueado.',
                            'user_blocked': True
                        })
                        
                    except User.DoesNotExist:
                        return JsonResponse({
                            'success': False,
                            'message': 'Usuário não encontrado no sistema.'
                        }, status=404)
                else:
                    # Normal return without damage
                    return JsonResponse({
                        'success': True,
                        'message': f'Livro "{book.titulo}" devolvido com sucesso!',
                        'user_blocked': False
                    })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Dados inválidos enviados na requisição.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro interno do servidor: {str(e)}'
            }, status=500)
    
    # Fallback redirect for non-AJAX requests
    return redirect('manage_loans')


@login_required
@require_http_methods(["POST"])
def save_loan_config(request):
    """Save loan configuration settings (only for admins)"""
    
    # Check if user is admin or superuser
    if not (request.user.is_superuser or request.user.role == 'admin'):
        return JsonResponse({'success': False, 'error': 'Acesso negado'}, status=403)
    
    try:
        max_loans_per_reader = request.POST.get('max_loans_per_reader')
        loan_duration_days = request.POST.get('loan_duration_days')
        
        # Validate input
        if not max_loans_per_reader or not loan_duration_days:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        try:
            max_loans_per_reader = int(max_loans_per_reader)
            loan_duration_days = int(loan_duration_days)
        except ValueError:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        if max_loans_per_reader < 1 or loan_duration_days < 1 or loan_duration_days > 365:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        # Get or create config and ensure fresh data
        config = LoanConfig.get_config()
        config.max_loans_per_reader = max_loans_per_reader
        config.loan_duration_days = loan_duration_days
        config.save()
        
        # Force refresh of configuration cache by fetching it again
        LoanConfig.objects.filter(id=config.id).update(
            max_loans_per_reader=max_loans_per_reader,
            loan_duration_days=loan_duration_days
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Configurações salvas com sucesso.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': 'Erro interno do servidor. Tente novamente.'
        })


@login_required
def profile(request):
    """User profile view showing user information and account details with edit forms"""
    
    # Initialize forms
    password_form = ChangePasswordForm(request.user)
    email_form = ChangeEmailForm(request.user)
    username_form = ChangeUsernameForm(request.user)
    form_errors = {}
    submitted_form = None
    
    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        submitted_form = form_type
        
        if form_type == 'password':
            password_form = ChangePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('profile')
            else:
                # Check if form has structured errors
                if hasattr(password_form, '_structured_errors'):
                    form_errors['password'] = password_form._structured_errors
                else:
                    form_errors['password'] = password_form.errors
                    
        elif form_type == 'email':
            email_form = ChangeEmailForm(request.user, request.POST)
            if email_form.is_valid():
                request.user.email = email_form.cleaned_data['new_email']
                request.user.save()
                messages.success(request, 'Email alterado com sucesso!')
                return redirect('profile')
            else:
                # Check if form has structured errors
                if hasattr(email_form, '_structured_errors'):
                    form_errors['email'] = email_form._structured_errors
                else:
                    form_errors['email'] = email_form.errors
                    
        elif form_type == 'username':
            username_form = ChangeUsernameForm(request.user, request.POST)
            if username_form.is_valid():
                request.user.username = username_form.cleaned_data['new_username']
                request.user.save()
                messages.success(request, 'Nome de usuário alterado com sucesso!')
                return redirect('profile')
            else:
                # Check if form has structured errors
                if hasattr(username_form, '_structured_errors'):
                    form_errors['username'] = username_form._structured_errors
                else:
                    form_errors['username'] = username_form.errors
    
    # Get user's loan statistics (only for readers)
    stats = {}
    recent_loans = []
    
    if request.user.role == 'reader':
        user_loans = Emprestimo.objects.filter(id_usuario=str(request.user.id))
        active_loans = user_loans.filter(data_fim__isnull=True).count()
        total_loans = user_loans.count()
        overdue_loans = user_loans.filter(
            data_fim__isnull=True,
            data_entrega__lt=timezone.now().date()
        ).count()
        
        stats = {
            'active_loans': active_loans,
            'total_loans': total_loans,
            'overdue_loans': overdue_loans,
        }
        
        # Get recent loan history (last 5 loans)
        for emp in user_loans.order_by('-data_inicio')[:5]:
            try:
                if emp.id_livro:
                    try:
                        book = Livros.objects.get(id_livro=emp.id_livro)
                        loan_data = {
                            'book_title': book.titulo,
                            'start_date': emp.data_inicio,
                            'due_date': emp.data_entrega,
                            'return_date': emp.data_fim,
                            'is_overdue': emp.data_entrega < timezone.now().date() if emp.data_entrega and not emp.data_fim else False,
                            'status': 'returned' if emp.data_fim else ('overdue' if emp.data_entrega < timezone.now().date() else 'active')
                        }
                        recent_loans.append(loan_data)
                    except Livros.DoesNotExist:
                        loan_data = {
                            'book_title': f'Livro removido (ID: {emp.id_livro})',
                            'start_date': emp.data_inicio,
                            'due_date': emp.data_entrega,
                            'return_date': emp.data_fim,
                            'is_overdue': False,
                            'status': 'returned' if emp.data_fim else 'active'
                        }
                        recent_loans.append(loan_data)
            except Exception:
                continue
    
    context = {
        'user': request.user,
        'stats': stats,
        'recent_loans': recent_loans,
        'password_form': password_form,
        'email_form': email_form,
        'username_form': username_form,
        'form_errors': form_errors,
        'submitted_form': submitted_form,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def verify_password(request):
    """AJAX endpoint to verify current user password"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            current_password = data.get('current_password', '')
            
            # Check if the provided password is correct
            is_valid = request.user.check_password(current_password)
            
            return JsonResponse({'valid': is_valid})
        except json.JSONDecodeError:
            return JsonResponse({'valid': False, 'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'valid': False, 'error': 'Method not allowed'}, status=405)


@login_required
def check_username_availability(request):
    """AJAX endpoint to check username availability"""
    if request.method == 'GET':
        username = request.GET.get('username', '').strip()
        
        if not username:
            return JsonResponse({'available': False, 'error': 'Username is required'})
        
        # Check if username is the same as current user's username
        if username == request.user.username:
            return JsonResponse({'available': False, 'error': 'same_as_current'})
        
        # Check if username is already taken
        is_taken = User.objects.filter(username=username).exclude(id=request.user.id).exists()
        
        # Check for reserved usernames
        reserved_usernames = ['admin', 'root', 'administrator', 'api', 'www', 'mail', 'ftp', 'system', 'support', 'help']
        is_reserved = username.lower() in reserved_usernames
        
        if is_taken:
            return JsonResponse({'available': False, 'error': 'taken'})
        elif is_reserved:
            return JsonResponse({'available': False, 'error': 'reserved'})
        else:
            return JsonResponse({'available': True})
    
    return JsonResponse({'available': False, 'error': 'Method not allowed'}, status=405)


@login_required
def autocomplete_users(request):
    if request.user.role == 'reader':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Get all readers matching search query
    from django.utils import timezone
    today = timezone.now().date()
    
    # Search users by username or email
    users = User.objects.filter(
        role='reader'
    ).filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    )[:20]
    
    user_results = []
    for user in users:
        # Count active loans
        active_loans = Emprestimo.objects.filter(
            id_usuario=str(user.id),
            data_fim__isnull=True
        ).count()
        
        # Check for overdue loans
        overdue_loans = Emprestimo.objects.filter(
            id_usuario=str(user.id),
            data_entrega__lt=today,
            data_fim__isnull=True
        ).count()
        
        # Get current loan configuration
        loan_config = LoanConfig.get_config()
        
        # Determine user status and display text
        status_text = ""
        is_eligible = True
        
        if user.status == User.Status.BLOCKED:
            status_text = " - Bloqueado por dano ❌"
            is_eligible = False
        elif overdue_loans >= 2:
            status_text = f" - {overdue_loans} empréstimos atrasados ❌"
            is_eligible = False
        elif overdue_loans >= 1:
            status_text = f" - {overdue_loans} empréstimo atrasado ⚠️"
            is_eligible = False
        elif active_loans >= loan_config.max_loans_per_reader:
            status_text = f" - {active_loans} empréstimos ativos (limite atingido) ❌"
            is_eligible = False
        elif active_loans == 1:
            status_text = f" - {active_loans} empréstimo ativo ✅"
        else:
            status_text = " - Disponível ✅"
        
        user_results.append({
            'id': user.id,
            'text': f"{user.username} ({user.email}){status_text}",
            'username': user.username,
            'email': user.email,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans,
            'is_eligible': is_eligible
        })
    
    # Sort results: eligible users first, then by username
    user_results.sort(key=lambda x: (not x['is_eligible'], x['username']))
    
    return JsonResponse({'results': user_results})


@login_required
def search_existing_books(request):
    """Search for existing books by title for edit functionality"""
    if request.user.role == 'reader':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Use the same representative book ID logic as browse_collection
    from django.db.models import Count, Min
    
    livros_query = Livros.objects.filter(
        Q(titulo__icontains=query) | Q(autor__icontains=query)
    )
    
    # Get representative books using the same logic as browse_collection
    representative_books = livros_query.values('titulo', 'autor').annotate(
        representative_id=Min('id_livro')
    ).order_by('titulo', 'autor')[:10]
    
    results = []
    for book_group in representative_books:
        # Get the representative book
        representative_book = livros_query.filter(id_livro=book_group['representative_id']).first()
        if representative_book:
            # Count total copies for this title/author
            total_count = livros_query.filter(
                titulo=book_group['titulo'], 
                autor=book_group['autor']
            ).count()
            
            results.append({
                'id': representative_book.id_livro,
                'title': representative_book.titulo,
                'author': representative_book.autor,
                'category': representative_book.genero or '',
                'year': representative_book.ano,
                'publisher': representative_book.editora or '',
                'description': representative_book.descricao or '',
                'total_copies': total_count
            })
    
    return JsonResponse({'results': results})


@login_required  
def autocomplete_books(request):
    if request.user.role == 'reader':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search available books by title or author
    books = Livros.objects.filter(
        Q(status_livro__iexact='disponível') |
        Q(status_livro__iexact='Disponível') |
        Q(status_livro__icontains='disponível') |
        Q(status_livro__icontains='Disponível') |
        Q(status_livro__iexact='available') |
        Q(status_livro__iexact='Available')
    ).filter(
        Q(titulo__icontains=query) | Q(autor__icontains=query)
    ).distinct()[:10]
    
    results = []
    for book in books:
        results.append({
            'id': book.id_livro,
            'text': f"{book.titulo} - {book.autor}",
            'title': book.titulo,
            'author': book.autor,
            'status': book.status_livro
        })
    
    return JsonResponse({'results': results})


@login_required
def exportar_relatorio_pdf(request):
    if request.user.role == 'reader' and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para acessar este relatório.")
        return redirect('dashboard')

    response = HttpResponse(content_type='application/pdf')
    filename = f"relatorio_gerencial_{date.today().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=42,
        bottomMargin=42
    )

    story = []

    data_de = request.GET.get('data_de')
    data_ate = request.GET.get('data_ate')
    categoria = request.GET.get('categoria')
    status_filtro = request.GET.get('status_filtro', 'todos')

    emprestimos = Emprestimo.objects.all()

    if data_de:
        emprestimos = emprestimos.filter(data_inicio__gte=data_de)

    if data_ate:
        emprestimos = emprestimos.filter(data_inicio__lte=data_ate)

    livros = Livros.objects.all()

    if categoria:
        livros = livros.filter(genero__icontains=categoria)

    active_ids = set(
        str(x) for x in emprestimos.filter(data_fim__isnull=True)
        .values_list('id_livro', flat=True)
    )

    overdue_ids = set(
        str(x) for x in emprestimos.filter(
            data_fim__isnull=True,
            data_entrega__lt=date.today()
        ).values_list('id_livro', flat=True)
    )

    if status_filtro == 'disponiveis':
        livros = livros.exclude(id_livro__in=active_ids)

    elif status_filtro == 'atrasados':
        livros = livros.filter(id_livro__in=overdue_ids)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#23395d'),
        alignment=1,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6b7a99'),
        alignment=1,
        spaceAfter=20
    )

    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#23395d'),
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e2a45')
    )

    bold_body_style = ParagraphStyle(
        'BodyTextBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    danger_style = ParagraphStyle(
        'DangerText',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#d32f2f')
    )

    story.append(Paragraph("BIBLIOTECA LUMEN", title_style))

    data_hora = timezone.localtime().strftime('%d/%m/%Y às %H:%M')
    story.append(
        Paragraph(
            f"Relatório Gerencial de Ativos — Gerado em {data_hora}",
            subtitle_style
        )
    )

    line_table = Table([[""]], colWidths=[510], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#23395d'))
    ]))

    story.append(line_table)
    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 1: MÉTRICAS GERAIS
    # ==========================================

    story.append(Paragraph("1. Resumo Executivo e Métricas Gerais", h2_style))

    total_livros = livros.count()

    total_emprestimos_ativos = emprestimos.filter(
        data_fim__isnull=True
    ).count()

    total_atrasados = emprestimos.filter(
        data_fim__isnull=True,
        data_entrega__lt=date.today()
    ).count()

    total_usuarios = User.objects.count()

    total_disponiveis = livros.exclude(
        id_livro__in=active_ids
    ).count()

    dados_metricas = [
        [
            Paragraph("Métrica Gerencial", bold_body_style),
            Paragraph("Quantidade Atual", bold_body_style)
        ],
        [
            Paragraph("Total de Livros Cadastrados", body_style),
            Paragraph(str(total_livros), body_style)
        ],
        [
            Paragraph("Exemplares Disponíveis", body_style),
            Paragraph(str(total_disponiveis), body_style)
        ],
        [
            Paragraph("Exemplares Emprestados", body_style),
            Paragraph(str(total_emprestimos_ativos), body_style)
        ],
        [
            Paragraph("Usuários Registrados", body_style),
            Paragraph(str(total_usuarios), body_style)
        ],
        [
            Paragraph("Livros em Atraso", body_style),
            Paragraph(
                str(total_atrasados),
                danger_style if total_atrasados > 0 else body_style
            )
        ],
    ]

    t_metricas = Table(
        dados_metricas,
        colWidths=[380, 130],
        repeatRows=1
    )

    t_metricas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaeef4')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d3dfee')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(t_metricas)
    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 2: INVENTÁRIO DO ACERVO
    # ==========================================

    story.append(Paragraph("2. Inventário do Acervo", h2_style))

    dados_livros = [[
        Paragraph("ID", bold_body_style),
        Paragraph("Título", bold_body_style),
        Paragraph("Autor", bold_body_style),
        Paragraph("Gênero", bold_body_style),
        Paragraph("Status", bold_body_style),
    ]]

    for livro in livros.order_by('titulo'):
        livro_id = str(livro.id_livro)

        if livro_id in active_ids:
            status = "Emprestado"
        else:
            status = "Disponível"

        dados_livros.append([
            Paragraph(str(livro.id_livro), body_style),
            Paragraph(livro.titulo or "-", body_style),
            Paragraph(livro.autor or "-", body_style),
            Paragraph(livro.genero or "-", body_style),
            Paragraph(status, body_style),
        ])

    if len(dados_livros) > 1:
        t_livros = Table(
            dados_livros,
            colWidths=[45, 180, 115, 85, 85],
            repeatRows=1
        )

        t_livros.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaeef4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d3dfee')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(t_livros)
    else:
        story.append(Paragraph("Nenhum livro encontrado com os filtros selecionados.", body_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 3: RANKING DE LIVROS MAIS EMPRESTADOS
    # ==========================================

    story.append(Paragraph("3. Ranking de Obras Mais Retiradas (Top 5)", h2_style))

    livros_populares = (
        emprestimos
        .values('id_livro')
        .annotate(total_saidas=Count('id'))
        .order_by('-total_saidas')[:5]
    )

    dados_ranking = [[
        Paragraph("Código", bold_body_style),
        Paragraph("Título da Obra / Autor", bold_body_style),
        Paragraph("Total de Retiradas", bold_body_style)
    ]]

    for item in livros_populares:
        id_livro_str = str(item['id_livro'])
        total_saidas = item['total_saidas']

        try:
            livro_obj = Livros.objects.get(id_livro=int(id_livro_str))
            info_livro = (
                f"<b>{livro_obj.titulo}</b><br/>"
                f"<font color='#6b7a99'>{livro_obj.autor}</font>"
            )
        except (Livros.DoesNotExist, ValueError, TypeError):
            info_livro = f"Livro Não Identificado (ID: {id_livro_str})"

        dados_ranking.append([
            Paragraph(id_livro_str, body_style),
            Paragraph(info_livro, body_style),
            Paragraph(f"{total_saidas} vezes", body_style)
        ])

    if len(dados_ranking) > 1:
        t_ranking = Table(
            dados_ranking,
            colWidths=[70, 310, 130],
            repeatRows=1
        )

        t_ranking.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaeef4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d3dfee')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(t_ranking)
    else:
        story.append(Paragraph("Nenhuma movimentação de empréstimo registrada.", body_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 4: USUÁRIOS INADIMPLENTES
    # ==========================================

    story.append(Paragraph("4. Usuários Inadimplentes (Com Devoluções em Atraso)", h2_style))

    emprestimos_atrasados = emprestimos.filter(
        data_fim__isnull=True,
        data_entrega__lt=date.today()
    ).order_by('data_entrega')

    dados_atrasados = [[
        Paragraph("Leitor / Usuário", bold_body_style),
        Paragraph("Obra Retirada", bold_body_style),
        Paragraph("Prazo Limite", bold_body_style),
        Paragraph("Dias de Atraso", bold_body_style)
    ]]

    for emp in emprestimos_atrasados:
        try:
            user_obj = User.objects.get(id=int(emp.id_usuario))
            info_user = (
                f"<b>{user_obj.get_full_name() or user_obj.username}</b><br/>"
                f"<font color='#6b7a99'>{user_obj.email}</font>"
            )
        except (User.DoesNotExist, ValueError, TypeError):
            info_user = f"ID Usuário: {emp.id_usuario}"

        try:
            livro_obj = Livros.objects.get(id_livro=int(emp.id_livro))
            info_livro = livro_obj.titulo
        except (Livros.DoesNotExist, ValueError, TypeError):
            info_livro = f"ID Livro: {emp.id_livro}"

        dias_atraso = (date.today() - emp.data_entrega).days

        dados_atrasados.append([
            Paragraph(info_user, body_style),
            Paragraph(info_livro, body_style),
            Paragraph(emp.data_entrega.strftime("%d/%m/%Y"), body_style),
            Paragraph(f"{dias_atraso} dias", danger_style)
        ])

    if len(dados_atrasados) > 1:
        t_atraso = Table(
            dados_atrasados,
            colWidths=[160, 160, 100, 90],
            repeatRows=1
        )

        t_atraso.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eaeef4')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d3dfee')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(t_atraso)
    else:
        story.append(Paragraph("Nenhum usuário com atraso no momento.", body_style))

    def adicionar_rodape(canvas, doc):
        canvas.saveState()

        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#6b7a99'))

        canvas.setStrokeColor(colors.HexColor('#eaeef4'))
        canvas.setLineWidth(0.5)
        canvas.line(42, 50, 553, 50)

        data_geracao = timezone.localtime().strftime("%d/%m/%Y %H:%M:%S")

        canvas.drawString(42, 38, f"Gerado em: {data_geracao}")
        canvas.drawRightString(553, 38, f"Página {doc.page}")

        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=adicionar_rodape,
        onLaterPages=adicionar_rodape
    )

    return response