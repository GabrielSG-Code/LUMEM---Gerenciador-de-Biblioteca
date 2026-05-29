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
import json

# Importações do ReportLab
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from .forms import RegisterForm, EmailOrUsernameLoginForm, AddBookForm, LoanForm, ChangePasswordForm, ChangeEmailForm, ChangeUsernameForm
from .models import Livros, User, Emprestimo, LoanConfig


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

    unique_books_query = livros_query.values(
        'titulo', 'autor', 'genero', 'ano', 'editora', 'descricao'
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
    borrowed_exemplars = livros_query.exclude(status_livro__iexact='disponível').count()
    
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
        'borrowed': borrowed_exemplars,
        'overdue': overdue_count
    }

    books_per_page = 12
    start_index = (page_number - 1) * books_per_page
    end_index = start_index + books_per_page

    current_page_books = unique_books_query[start_index:end_index]

    books_list = []
    for book_data in current_page_books:
        representative_book = livros_query.filter(
            titulo=book_data['titulo'],
            autor=book_data['autor']
        ).first()

        category_name = book_data['genero'] or 'Outros'
        
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
            'year': book_data['ano'],
            'publisher': book_data['editora'],
            'description': book_data['descricao'],
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
        'stats': stats
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
        
        user_data.append({
            'id': user.id,
            'initials': initials,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'active': user.is_active,
            'last_login': user.last_login.strftime('%d/%m/%Y, %H:%M') if user.last_login else 'Nunca',
            'is_superuser': user.is_superuser,
            'can_edit': can_edit
        })

    stats = {
        'total': users.count(),
        'admin': users.filter(role='admin').count(),
        'librarian': users.filter(role='librarian').count(),
        'reader': users.filter(role='reader').count()
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

        if 'role' in data:
            role_map = {
                'Leitor': 'reader',
                'Bibliotecário': 'librarian',
                'Administrador': 'admin'
            }
            user.role = role_map.get(data['role'], 'reader')

        if 'active' in data:
            user.is_active = data['active']

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
def return_book(request, loan_id):
    emprestimo = get_object_or_404(Emprestimo, id=loan_id)

    # Check if reader is trying to return someone else's book
    if request.user.role == 'reader' and str(emprestimo.id_usuario) != str(request.user.id):
        messages.error(request, 'Você só pode devolver seus próprios livros.')
        return redirect('manage_loans')

    if emprestimo.data_fim:
        messages.warning(request, 'Este livro já foi devolvido.')
        return redirect('manage_loans')

    emprestimo.data_fim = timezone.now().date()
    emprestimo.save()

    try:
        book = Livros.objects.get(id_livro=emprestimo.id_livro)
        book.status_livro = 'Disponível'
        book.save()
        messages.success(request, f'Livro "{book.titulo}" devolvido com sucesso!')
    except Livros.DoesNotExist:
        messages.success(request, 'Empréstimo finalizado.')
    
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
        max_overdue_days = request.POST.get('max_overdue_days')
        
        # Validate input
        if not max_loans_per_reader or not max_overdue_days:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        try:
            max_loans_per_reader = int(max_loans_per_reader)
            max_overdue_days = int(max_overdue_days)
        except ValueError:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        if max_loans_per_reader < 1 or max_overdue_days < 1:
            return JsonResponse({
                'success': False, 
                'error': 'Não é possível salvar: preencha todos os campos com valores válidos.'
            })
        
        # Get or create config
        config = LoanConfig.get_config()
        config.max_loans_per_reader = max_loans_per_reader
        config.max_overdue_days = max_overdue_days
        config.save()
        
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
    
    # Handle form submissions
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'password':
            password_form = ChangePasswordForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('profile')
            else:
                for error in password_form.errors.values():
                    messages.error(request, error)
                    
        elif form_type == 'email':
            email_form = ChangeEmailForm(request.user, request.POST)
            if email_form.is_valid():
                request.user.email = email_form.cleaned_data['new_email']
                request.user.save()
                messages.success(request, 'Email alterado com sucesso!')
                return redirect('profile')
            else:
                for error in email_form.errors.values():
                    messages.error(request, error)
                    
        elif form_type == 'username':
            username_form = ChangeUsernameForm(request.user, request.POST)
            if username_form.is_valid():
                request.user.username = username_form.cleaned_data['new_username']
                request.user.save()
                messages.success(request, 'Nome de usuário alterado com sucesso!')
                return redirect('profile')
            else:
                for error in username_form.errors.values():
                    messages.error(request, error)
    
    
    # Initialize forms for display
    password_form = ChangePasswordForm(request.user)
    email_form = ChangeEmailForm(request.user)
    username_form = ChangeUsernameForm(request.user)
    
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
    }
    
    return render(request, 'accounts/profile.html', context)


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
        
        if overdue_loans >= 2:
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
def generate_pdf_report(request):
    # Segurança: Apenas administrador ou bibliotecário
    if request.user.role == 'reader':
        return HttpResponse("Acesso Negado: Privilégios insuficientes.", status=403)

    # 1. CAPTURA DOS FILTROS DO MODAL GET
    data_de = request.GET.get('data_de')
    data_ate = request.GET.get('data_ate')
    categoria = request.GET.get('categoria')
    status_filtro = request.GET.get('status_filtro')

    hoje = timezone.now().date()

    # 2. CONFIGURAÇÃO DA RESPOSTA HTTP (DOWNLOAD DIRETO)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Relatorio_LUMEN_{hoje.strftime("%d_%m_%Y")}.pdf"'

    # 3. CRIAÇÃO DO DOCUMENTO EM MEMÓRIA
    doc = SimpleDocTemplate(
        response, 
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=50
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, 
        textColor=colors.HexColor('#23395d'), alignment=1, spaceAfter=15
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=11, 
        textColor=colors.HexColor('#444444'), alignment=1, spaceAfter=20
    )
    h2_style = ParagraphStyle(
        'H2Style', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, 
        textColor=colors.HexColor('#23395d'), spaceBefore=15, spaceAfter=10
    )
    body_style = ParagraphStyle(
        'BodyStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.black
    )
    danger_style = ParagraphStyle(
        'DangerStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#c0392b')
    )
    filter_style = ParagraphStyle(
        'FilterStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#555555')
    )

    story = []

    # Cabeçalho
    story.append(Paragraph("LUMEN — BIBLIOTECA DIGITAL", title_style))
    story.append(Paragraph("Relatório de Auditoria e Apoio à Tomada de Decisão", subtitle_style))
    
    p_de = data_de if data_de else "Início"
    p_ate = data_ate if data_ate else "Hoje"
    cat_txt = categoria if categoria else "Todas"
    story.append(Paragraph(f"<b>Filtros Ativos:</b> Período: {p_de} até {p_ate} | Gênero: {cat_txt}", filter_style))
    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 1: SITUAÇÃO DE LIVROS (QUANTITATIVOS)
    # ==========================================
    story.append(Paragraph("1. Situação de Inventário e Volumes Disponíveis", h2_style))
    
    livros_qs = Livros.objects.all()
    if categoria:
        livros_qs = livros_qs.filter(genero__icontains=categoria)

    dados_livros = [["Livro / Autor", "Gênero", "Total", "Disponível", "Emprestada"]]
    
    # Mapeamento simples na memória para evitar Joins complexos que dão erro 500
    todos_emprestimos_ativos = Emprestimo.objects.filter(data_fim__isnull=True)
    
    for livro in livros_qs:
        # Conta quantos empréstimos ativos existem para o ID deste livro
        total_emprestado = todos_emprestimos_ativos.filter(id_livro=livro.id_livro).count()
        total_exemplares = 5 
        disponivel = max(0, total_exemplares - total_emprestado)
        
        if status_filtro == 'disponiveis' and disponivel == 0:
            continue

        p_livro = Paragraph(f"<b>{livro.titulo}</b><br/><font color='#666666'>{livro.autor}</font>", body_style)
        dados_livros.append([
            p_livro, 
            livro.genero if livro.genero else "-", 
            str(total_exemplares), 
            str(disponivel), 
            str(total_emprestado)
        ])

    if len(dados_livros) > 1:
        t_livros = Table(dados_livros, colWidths=[200, 110, 60, 70, 70])
        t_livros.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaeef4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#23395d')),
            ('ALIGN', (2,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d3dfee')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_livros)
    else:
        story.append(Paragraph("Nenhum registro de acervo compatível.", body_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 2: LIVROS MAIS EMPRESTADOS (RANKING)
    # ==========================================
    story.append(Paragraph("2. Livros Mais Emprestados (Top de Circulação)", h2_style))
    
    historico_emprestimos = Emprestimo.objects.all()
    if data_de:
        historico_emprestimos = historico_emprestimos.filter(data_inicio__gte=data_de)
    if data_ate:
        historico_emprestimos = historico_emprestimos.filter(data_inicio__lte=data_ate)

    # Agrupamos os IDs mais emprestados de forma totalmente compatível com o seu banco
    ranking_ids = (
        historico_emprestimos.values('id_livro')
        .annotate(total_saidas=Count('id_emprestimo'))
        .order_by('-total_saidas')[:5]
    )

    dados_rank = [["Posição", "Livro / Autor", "Gênero", "Total Saídas"]]
    for idx, r in enumerate(ranking_ids, start=1):
        try:
            livro_obj = Livros.objects.get(id_livro=r['id_livro'])
            p_rank = Paragraph(f"<b>{livro_obj.titulo}</b><br/><font color='#666666'>{livro_obj.autor}</font>", body_style)
            dados_rank.append([
                f"{idx}º", 
                p_rank, 
                livro_obj.genero if livro_obj.genero else "-", 
                f"{r['total_saidas']} saídas"
            ])
        except Livros.DoesNotExist:
            continue

    if len(dados_rank) > 1:
        t_rank = Table(dados_rank, colWidths=[60, 250, 110, 90])
        t_rank.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaeef4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#23395d')),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (3,0), (3,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d3dfee')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_rank)
    else:
        story.append(Paragraph("Não houve movimentações de saída para estes critérios.", body_style))

    story.append(Spacer(1, 15))

    # ==========================================
    # SEÇÃO 3: USUÁRIOS COM DEVOLUÇÃO EM ATRASO
    # ==========================================
    story.append(Paragraph("3. Usuários Inadimplentes (Com Devoluções em Atraso)", h2_style))
    
    dados_atrasados = [["Leitor / Contato", "Obra Alocada", "Data Vencimento", "Dias em Atraso"]]
    
    # Coleta empréstimos abertos cujo prazo de entrega já expirou
    emprestimos_atrasados_qs = Emprestimo.objects.filter(data_fim__isnull=True, data_entrega__lt=hoje)
    
    for emp in emprestimos_atrasados_qs:
        dias = (hoje - emp.data_entrega).days
        
        # Fazemos a busca manual e controlada por ID (Livre de Erros 500 de FK)
        u_nome = "Desconhecido"
        u_email = "Sem e-mail"
        if emp.id_usuario_id:
            try:
                usr = User.objects.get(id=emp.id_usuario_id)
                u_nome = usr.username
                u_email = usr.email
            except User.DoesNotExist:
                pass
                
        livro_tit = "Desconhecido"
        if emp.id_livro_id:
            try:
                livro_tit = Livros.objects.get(id_livro=emp.id_livro_id).titulo
            except Livros.DoesNotExist:
                pass
        
        p_user = Paragraph(f"<b>{u_nome}</b><br/><font color='#666666'>{u_email}</font>", body_style)
        
        dados_atrasados.append([
            p_user, 
            livro_tit, 
            emp.data_entrega.strftime("%d/%m/%Y"), 
            Paragraph(f"{dias} dias", danger_style)
        ])

    if len(dados_atrasados) > 1:
        t_atraso = Table(dados_atrasados, colWidths=[160, 160, 100, 90])
        t_atraso.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaeef4')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#23395d')),
            ('ALIGN', (2,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d3dfee')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_atraso)
    else:
        story.append(Paragraph("Nenhuma pendência ou atraso crítico listado no momento.", body_style))

    # Rodapé Dinâmico
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#555555'))
        canvas.drawString(40, 30, "LUMEN — Sistema de Gerenciamento de Biblioteca")
        
        agora_str = timezone.now().strftime("%d/%m/%Y %H:%M")
        canvas.drawRightString(A4[0] - 40, 30, f"Gerado em: {agora_str} — Página {doc.page}")
        canvas.restoreState()

    # Compilação
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    
    return response