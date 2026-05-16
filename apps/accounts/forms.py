from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from django.db import models

from .models import Livros, Emprestimo

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailOrUsernameLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email ou nome de usuário'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    'Email/usuário ou senha inválidos.',
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class AddBookForm(forms.Form):
    title = forms.CharField(max_length=255, label="Título")
    author = forms.CharField(max_length=255, label="Autor")
    description = forms.CharField(required=False, widget=forms.Textarea, label="Descrição")
    release_year = forms.IntegerField(required=False, min_value=1000, max_value=2100, label="Ano de Lançamento")
    category = forms.CharField(max_length=255, label="Categoria")
    publisher = forms.CharField(max_length=255, required=False, label="Editora")
    exemplary = forms.IntegerField(min_value=1, label="Número de Exemplares")
    force_duplicate = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        author = cleaned_data.get('author')
        release_year = cleaned_data.get('release_year')
        force_duplicate = cleaned_data.get('force_duplicate', False)
        
        
        if title and author and not force_duplicate:
            # Normalize title and author for comparison
            title_normalized = title.strip().lower()
            author_normalized = author.strip().lower()
            
            
            # Check for exact matches including year (if year is provided)
            exact_matches_query = Livros.objects.filter(
                titulo__iexact=title.strip(),
                autor__iexact=author.strip()
            )
            
            # If year is provided, check for exact match with same year
            if release_year:
                exact_matches_with_year = exact_matches_query.filter(ano=release_year)
                if exact_matches_with_year.exists():
                    existing_count = exact_matches_with_year.count()
                    existing_book = exact_matches_with_year.first()
                    
                    
                    # Create detailed error message for same edition
                    error_msg = (
                        f'LIVRO DUPLICADO: "{title}" de "{author}" ({release_year}) já existe no sistema '
                        f'com {existing_count} exemplar(es) cadastrado(s).'
                    )
                    
                    # Add existing book details
                    details = []
                    if existing_book.editora:
                        details.append(f'Editora: {existing_book.editora}')
                    if existing_book.genero:
                        details.append(f'Categoria: {existing_book.genero}')
                    
                    if details:
                        error_msg += f' [{", ".join(details)}]'
                    
                    error_msg += ' Para adicionar mais exemplares desta mesma edição, use a funcionalidade de gestão de exemplares.'
                    
                    raise forms.ValidationError(error_msg)
                
                # Check if there are other editions (same title/author, different year)
                other_editions = exact_matches_query.exclude(ano=release_year).filter(ano__isnull=False)
                if other_editions.exists():
                    editions_list = list(other_editions.values_list('ano', flat=True).distinct())
                    
                    # This is allowed - just show info message about other editions
                    info_msg = (
                        f'INFORMAÇÃO: Já existem outras edições de "{title}" de "{author}" '
                        f'nos anos: {", ".join(map(str, sorted(editions_list)))}. '
                        f'A nova edição de {release_year} será adicionada como um livro separado.'
                    )
                    # We don't raise an error here - just log the info
                    
            else:
                # No year provided - check if any edition exists
                if exact_matches_query.exists():
                    existing_book = exact_matches_query.first()
                    existing_years = list(exact_matches_query.filter(ano__isnull=False).values_list('ano', flat=True).distinct())
                    
                    warning_msg = (
                        f'ATENÇÃO: "{title}" de "{author}" já existe no sistema'
                    )
                    
                    if existing_years:
                        warning_msg += f' com edições dos anos: {", ".join(map(str, sorted(existing_years)))}'
                    
                    warning_msg += (
                        '. Como você não especificou o ano de lançamento, '
                        'verifique se não está duplicando uma edição existente. '
                        'Recomenda-se informar o ano para diferenciar edições.'
                    )
                    
                    raise forms.ValidationError(warning_msg)
                
            # Also check for very similar titles (potential typos) - only if no year conflicts
            similar_books = Livros.objects.filter(
                autor__iexact=author.strip()
            ).filter(
                titulo__icontains=title.strip()[:10] if len(title.strip()) > 10 else title.strip()
            ).exclude(
                titulo__iexact=title.strip()  # Exclude exact title matches already checked above
            )
            
            
            if similar_books.exists():
                similar_book = similar_books.first()
                warning_msg = (
                    f'POSSÍVEL DUPLICATA: Encontrado livro similar "{similar_book.titulo}" '
                    f'do mesmo autor "{author}". Verifique se não é o mesmo livro com grafia ligeiramente diferente.'
                )
                raise forms.ValidationError(warning_msg)
        
        return cleaned_data

    def save_books(self):
        title = self.cleaned_data['title']
        author = self.cleaned_data['author']
        description = self.cleaned_data.get('description')
        release_year = self.cleaned_data.get('release_year')
        category = self.cleaned_data['category']
        publisher = self.cleaned_data.get('publisher')
        exemplary = self.cleaned_data['exemplary']

        livros_criados = []
        for _ in range(exemplary):
            livro = Livros.objects.create(
                titulo=title,
                autor=author,
                descricao=description,
                ano=release_year,
                genero=category,
                editora=publisher,
                status_livro='Disponível'
            )
            livros_criados.append(livro)

        return livros_criados


class LoanForm(forms.ModelForm):
    user_search = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control autocomplete-input',
            'placeholder': 'Digite o nome ou email do usuário...',
            'data-autocomplete-url': '/accounts/autocomplete/users/',
            'data-target': 'user'
        }),
        label="Usuário"
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.HiddenInput(),
        required=False
    )
    book_search = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control autocomplete-input',
            'placeholder': 'Digite o título ou autor do livro...',
            'data-autocomplete-url': '/accounts/autocomplete/books/',
            'data-target': 'book'
        }),
        label="Livro"
    )
    book = forms.ModelChoiceField(
        queryset=Livros.objects.filter(status_livro='Disponível'),
        widget=forms.HiddenInput(),
        required=False
    )
    reserva = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Emprestimo
        fields = ['reserva']

    def __init__(self, *args, **kwargs):
        # Extract pre-selected book info if passed
        preselected_title = kwargs.pop('preselected_title', None)
        preselected_author = kwargs.pop('preselected_author', None)
        
        super().__init__(*args, **kwargs)
        
        try:
            # Get eligible users (readers with < 2 active loans and no overdue loans)
            today = timezone.now().date()
            
            all_readers = User.objects.filter(role='reader')
            eligible_users = []
            
            for user in all_readers:
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
                
                # User is eligible if < 2 active loans and no overdue loans
                if active_loans < 2 and overdue_loans == 0:
                    eligible_users.append(user.id)
            
            self.fields['user'].queryset = User.objects.filter(id__in=eligible_users)
            
            # Simple book queryset - available books only
            all_books = Livros.objects.all()
            
            # Check what status values exist
            statuses = Livros.objects.values_list('status_livro', flat=True).distinct()
            
            # Try multiple status variations
            available_books = Livros.objects.filter(
                Q(status_livro__iexact='disponível') |
                Q(status_livro__iexact='Disponível') |
                Q(status_livro__icontains='disponível') |
                Q(status_livro__icontains='Disponível') |
                Q(status_livro__iexact='available') |
                Q(status_livro__iexact='Available')
            )
            
            # If no books found with status filter, show first 5 books as fallback
            if available_books.count() == 0:
                available_books = Livros.objects.all()[:10]  # Limit to 10 for testing
            
            self.fields['book'].queryset = available_books
            self.fields['book'].label_from_instance = lambda obj: f"{obj.titulo} - {obj.autor} (Status: {obj.status_livro})"
            
            # If we have pre-selected book info, try to find and set initial value
            if preselected_title and preselected_author:
                try:
                    # Find the first available book matching title and author
                    available_book = Livros.objects.filter(
                        titulo=preselected_title,
                        autor=preselected_author,
                        status_livro='Disponível'
                    ).first()
                    
                    if available_book:
                        self.fields['book'].initial = available_book
                except Exception as e:
                    pass
            
        except Exception as e:
            # Fallback to basic querysets if there's an error
            self.fields['user'].queryset = User.objects.filter(role='reader')
            self.fields['book'].queryset = Livros.objects.all()[:10]  # Show first 10 books as fallback

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        book = cleaned_data.get('book')
        
        if not user:
            raise forms.ValidationError('Por favor, selecione um usuário válido.')
        
        if not book:
            raise forms.ValidationError('Por favor, selecione um livro válido.')
        
        return cleaned_data

    def save(self, commit=True):
        emprestimo = super().save(commit=False)
        emprestimo.id_usuario = str(self.cleaned_data['user'].id)
        
        # Get the selected book object (now it's a ModelChoiceField)
        book = self.cleaned_data['book']
        
        emprestimo.id_livro = str(book.id_livro)
        
        # Set 7-day loan period automatically
        emprestimo.data_inicio = timezone.now().date()
        emprestimo.data_entrega = emprestimo.data_inicio + timedelta(days=7)
        
        emprestimo.id_emprestimo = f"EMP_{emprestimo.id_usuario}_{emprestimo.id_livro}_{emprestimo.data_inicio.strftime('%Y%m%d')}"
        
        if commit:
            emprestimo.save()
            
            # Update book status
            book.status_livro = 'Emprestado'
            book.save()
        
        return emprestimo
