from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
import json

from .forms import RegisterForm, EmailOrUsernameLoginForm, AddBookForm, LoanForm
from .models import Livros, User, Emprestimo
from django.contrib.auth.forms import AuthenticationForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao LUMEN.')
            return redirect('home')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


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
            os.path.join(os.path.dirname(_file_), '..', '..', 'categories.csv'),
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
    except Exception:
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
        icon_url = category_icons.get(category_name, 'https://cdn-icons-png.flaticon.com/512/1146/1146315.png')

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
        def _init_(self, books, page_num, total_books, total_pages):
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

        def _iter_(self):
            return iter(self.object_list)

        def _len_(self):
            return len(self.object_list)

    books_page = MockPaginator(books_list, page_number, total_unique_books, total_pages)

    categories_raw = Livros.objects.exclude(genero__isnull=True).exclude(genero='').values_list('genero', flat=True)

    unique_categories = {}
    for category in categories_raw:
        if category and category.strip():
            cleaned = category.strip()
            key = cleaned.lower()
            if key not in unique_categories:
                unique_categories[key] = cleaned

    categories = sorted(unique_categories.values(), key=str.lower)

    context = {
        'books': books_page,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'category_icons': category_icons,
        'total_books': total_unique_books,
        'total_exemplars': total_exemplars,
        'available_exemplars': available_exemplars
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
        user_data.append({
            'id': user.id,
            'initials': initials,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': user.get_role_display(),
            'active': user.is_active,
            'last_login': user.last_login.strftime('%d/%m/%Y, %H:%M') if user.last_login else 'Nunca'
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
    if request.method != 'POST':
        return HttpResponse('Método não permitido')

    form = AddBookForm(request.POST)

    if not form.is_valid():
        return HttpResponse(f'ERROS DO FORM: {form.errors}', status=400)

    try:
        livros_criados = form.save_books()
        messages.success(
            request,
            f'{len(livros_criados)} exemplar(es) do livro "{form.cleaned_data["title"]}" adicionado(s) com sucesso.'
        )
        return redirect('browse_collection')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return HttpResponse(f'ERRO AO SALVAR LIVROS: {repr(e)}', status=500)


@login_required
def manage_loans(request):
    loan_form = LoanForm()
    if request.method == 'POST':
        loan_form = LoanForm(request.POST)
        if loan_form.is_valid():
            loan_form.save()
            messages.success(request, 'Empréstimo criado com sucesso!')
            return redirect('manage_loans')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')

    emprestimos = Emprestimo.objects.all().order_by('-data_inicio')

    loans_data = []
    for emp in emprestimos:
        try:
            user = User.objects.get(id=emp.id_usuario) if emp.id_usuario else None
            book = Livros.objects.get(id_livro=emp.id_livro) if emp.id_livro else None

            loans_data.append({
                'id': emp.id,
                'loan_id': emp.id_emprestimo,
                'user_name': user.username if user else 'Usuário não encontrado',
                'book_title': book.titulo if book else 'Livro não encontrado',
                'start_date': emp.data_inicio,
                'due_date': emp.data_entrega,
                'return_date': emp.data_fim,
                'is_reservation': emp.reserva,
                'is_overdue': emp.data_entrega and emp.data_entrega < timezone.now().date() and not emp.data_fim if emp.data_entrega else False
            })
        except (User.DoesNotExist, Livros.DoesNotExist):
            continue

    return render(request, 'manage_loans.html', {
        'loans': loans_data,
        'loan_form': loan_form
    })


@login_required
def return_book(request, loan_id):
    emprestimo = get_object_or_404(Emprestimo, id=loan_id)

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
