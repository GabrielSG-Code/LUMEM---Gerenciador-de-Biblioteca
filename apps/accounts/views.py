from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponse


from .forms import RegisterForm, EmailOrUsernameLoginForm, AddBookForm
from .models import Livros


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
        form = EmailOrUsernameLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Email/usuário ou senha inválidos.')
    else:
        form = EmailOrUsernameLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


@login_required
def browse_collection(request):
    livros_db = Livros.objects.all().order_by('titulo')

    books = []
    for livro in livros_db:
        books.append({
            'id': livro.id_livro,
            'title': livro.titulo,
            'author': livro.autor,
            'category': (livro.genero or 'outros').lower(),
            'available': (livro.status_livro or '').lower() == 'disponível',
            'year': livro.ano,
            'publisher': livro.editora,
            'description': livro.descricao,
        })

    return render(request, 'browse_collection.html', {'books': books})


@login_required
def add_book(request):
    if request.method != 'POST':
        return HttpResponse('Método não permitido')

    print('POST RECEBIDO EM add_book')
    print('DADOS:', request.POST)

    form = AddBookForm(request.POST)

    if not form.is_valid():
        print('ERROS DO FORM:', form.errors)
        return HttpResponse(f'ERROS DO FORM: {form.errors}', status=400)

    try:
        livros_criados = form.save_books()
        print('LIVROS CRIADOS COM SUCESSO:', len(livros_criados))
        messages.success(
            request,
            f'{len(livros_criados)} exemplar(es) do livro "{form.cleaned_data["title"]}" adicionado(s) com sucesso.'
        )
        return redirect('browse_collection')
    except Exception as e:
        import traceback
        print('ERRO AO SALVAR LIVROS:')
        traceback.print_exc()
        return HttpResponse(f'ERRO AO SALVAR LIVROS: {repr(e)}', status=500)