from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Q, Count
from django.db import models
from django.core.exceptions import ValidationError

from .models import Livros, Emprestimo, LoanConfig

# Dynamic year calculation
def get_current_year():
    """Get current year for dynamic form validation"""
    return datetime.now().year

def get_max_book_year():
    """Get maximum allowed year for book publication (current year only)"""
    return get_current_year()

def get_max_book_copies():
    """Get maximum allowed number of book copies for reasonable library management"""
    return 9999  # Maximum 4 characters, 9999 copies limit

def get_default_book_copies():
    """Get default number of copies when adding a new book"""
    return 1

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        max_length=320,
        required=True,
        error_messages={
            'invalid': 'Insira um endereço de e-mail válido.',
            'required': 'Este campo é obrigatório.'
        }
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize password field error messages
        self.fields['password1'].error_messages = {
            'required': 'Este campo é obrigatório.'
        }
        self.fields['password2'].error_messages = {
            'required': 'Este campo é obrigatório.'
        }
        
        # Customize username field
        self.fields['username'].error_messages = {
            'required': 'Este campo é obrigatório.',
            'unique': 'Este nome de usuário já está em uso.'
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Custom validation with Portuguese messages
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                # Translate common password validation errors
                translated_errors = []
                for msg in error.messages:
                    if 'too similar to the username' in msg.lower():
                        translated_errors.append('A senha é muito similar ao nome de usuário.')
                    elif 'too short' in msg.lower() and 'at least 8 characters' in msg.lower():
                        translated_errors.append('Esta senha é muito curta. Ela deve conter pelo menos 8 caracteres.')
                    elif 'too common' in msg.lower():
                        translated_errors.append('Esta senha é muito comum.')
                    elif 'entirely numeric' in msg.lower():
                        translated_errors.append('Esta senha é inteiramente numérica.')
                    else:
                        translated_errors.append(msg)
                raise forms.ValidationError(translated_errors)
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Only check password confirmation if both passwords are provided and password1 passed validation
        if password1 and password2:
            if password1 != password2:
                # Only add this error to password2 field, not both
                self.add_error('password2', 'As senhas não coincidem.')
        
        return cleaned_data
    

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailOrUsernameLoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=320,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email ou nome de usuário'
        }),
        error_messages={
            'required': 'Este campo é obrigatório.'
        }
    )
    
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        }),
        error_messages={
            'required': 'Este campo é obrigatório.'
        }
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
    title = forms.CharField(max_length=200, min_length=1, label="Título")
    author = forms.CharField(max_length=150, min_length=1, label="Autor")
    description = forms.CharField(max_length=2000, required=False, widget=forms.Textarea(attrs={'rows': 6}), label="Descrição")
    release_year = forms.IntegerField(required=False, min_value=1000, label="Ano de Lançamento")
    category = forms.CharField(max_length=50, label="Categoria")
    publisher = forms.CharField(max_length=100, required=False, label="Editora")
    exemplary = forms.IntegerField(min_value=1, label="Número de Exemplares")
    force_duplicate = forms.BooleanField(required=False, widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set dynamic max_value for release_year
        self.fields['release_year'].max_value = get_max_book_year()
        self.fields['release_year'].widget.attrs.update({
            'max': get_max_book_year(),
            'placeholder': str(get_current_year())
        })
        
        # Set dynamic max_value for exemplary (copies)
        self.fields['exemplary'].max_value = get_max_book_copies()
        self.fields['exemplary'].widget.attrs.update({
            'max': get_max_book_copies(),
            'placeholder': str(get_default_book_copies())
        })

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
        max_length=100,
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
        max_length=150,
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
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'readonly': 'readonly'
        }),
        initial=timezone.now().date,
        label="Data de Início"
    )
    data_entrega = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'readonly': 'readonly'
        }),
        label="Data de Entrega"
    )
    class Meta:
        model = Emprestimo
        fields = ['data_inicio', 'data_entrega']

    def __init__(self, *args, **kwargs):
        # Extract pre-selected book info if passed
        preselected_title = kwargs.pop('preselected_title', None)
        preselected_author = kwargs.pop('preselected_author', None)
        
        super().__init__(*args, **kwargs)
        
        # Set initial values for date fields
        today = timezone.now().date()
        loan_config, _ = LoanConfig.objects.get_or_create()
        self.fields['data_inicio'].initial = today
        self.fields['data_entrega'].initial = today + timedelta(days=loan_config.loan_duration_days)
        
        try:
            # Get all readers - we'll show all but validate restrictions during form submission
            all_readers = User.objects.filter(role='reader')
            self.fields['user'].queryset = all_readers
            
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
                        autor=preselected_author
                    ).filter(
                        Q(status_livro__iexact='disponível') |
                        Q(status_livro__iexact='Disponível') |
                        Q(status_livro__icontains='disponível') |
                        Q(status_livro__icontains='Disponível') |
                        Q(status_livro__iexact='available') |
                        Q(status_livro__iexact='Available')
                    ).first()
                    
                    if available_book:
                        self.fields['book'].initial = available_book
                        # Also set the search field with the book title and author
                        self.fields['book_search'].initial = f"{preselected_title} - {preselected_author}"
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
        
        # Validate user loan restrictions
        if user:
            today = timezone.now().date()
            
            # Count active loans
            active_loans = Emprestimo.objects.filter(
                id_usuario=str(user.id),
                data_fim__isnull=True
            ).count()
            
            # Count overdue loans
            overdue_loans = Emprestimo.objects.filter(
                id_usuario=str(user.id),
                data_entrega__lt=today,
                data_fim__isnull=True
            ).count()
            
            # Get current loan configuration
            loan_config = LoanConfig.get_config()
            
            # Check restrictions and provide specific error messages
            if overdue_loans >= 1:
                raise forms.ValidationError(
                    'Não é possível realizar o empréstimo: o leitor possui empréstimos em atraso.'
                )
            elif active_loans >= loan_config.max_loans_per_reader:
                raise forms.ValidationError(
                    'Não é possível realizar o empréstimo: o leitor atingiu o limite de empréstimos permitidos.'
                )
        
        # No need to validate delivery date since it's automatically calculated
        
        return cleaned_data

    def save(self, commit=True):
        emprestimo = super().save(commit=False)
        emprestimo.id_usuario = str(self.cleaned_data['user'].id)
        
        # Get the selected book object (now it's a ModelChoiceField)
        book = self.cleaned_data['book']
        
        emprestimo.id_livro = str(book.id_livro)
        
        # Always use today's date as start date and calculate delivery date based on configuration
        today = timezone.now().date()
        emprestimo.data_inicio = today
        
        # Get loan configuration for duration
        loan_config = LoanConfig.get_config()
        emprestimo.data_entrega = today + timedelta(days=loan_config.loan_duration_days)
        
        # Store current overdue days setting for this loan (grandfathering)
        emprestimo.overdue_days = loan_config.max_overdue_days
        
        emprestimo.id_emprestimo = f"EMP_{emprestimo.id_usuario}_{emprestimo.id_livro}_{emprestimo.data_inicio.strftime('%Y%m%d')}"
        
        if commit:
            emprestimo.save()
            
            # Update book status
            book.status_livro = 'Emprestado'
            book.save()
        
        return emprestimo


class ChangePasswordForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling and enhanced validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set Portuguese labels
        self.fields['old_password'].label = 'Senha Atual'
        self.fields['new_password1'].label = 'Nova Senha'
        self.fields['new_password2'].label = 'Confirmar Nova Senha'
        
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Senha atual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nova senha'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar nova senha'
        })

    def clean(self):
        """Custom validation with hierarchical error messages"""
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        # Create structured error storage
        structured_errors = {}
        
        # 1. First priority: Check old password
        if old_password and not self.user.check_password(old_password):
            structured_errors['current_password'] = 'Senha atual incorreta.'
        
        # 2. Second priority: Validate new password requirements (only if old password is correct)
        elif new_password1:
            password_errors = []
            
            # Check password validation
            from django.contrib.auth.password_validation import validate_password
            from django.core.exceptions import ValidationError
            
            try:
                validate_password(new_password1, self.user)
            except ValidationError as error:
                for msg in error.messages:
                    if 'too similar to the username' in msg.lower() or 'too similar to the email' in msg.lower():
                        password_errors.append('Esta senha é muito parecida com o email.')
                    elif 'too short' in msg.lower() and 'at least 8 characters' in msg.lower():
                        password_errors.append('Senha muito curta: É preciso pelo menos 8 caracteres.')
                    elif 'too common' in msg.lower():
                        password_errors.append('Esta senha é muito comum.')
                    elif 'entirely numeric' in msg.lower():
                        password_errors.append('Esta senha é inteiramente numérica.')
                    else:
                        password_errors.append(msg)
            
            # Check if new passwords match
            if new_password2 and new_password1 != new_password2:
                password_errors.append('As novas senhas não coincidem.')
            
            # Check if new password is different from current password
            if old_password and new_password1 == old_password:
                password_errors.append('A nova senha deve ser diferente da senha atual.')
            
            # If there are password errors, create structured message
            if password_errors:
                if len(password_errors) == 1:
                    structured_errors['new_password'] = password_errors[0]
                else:
                    error_list = []
                    for i, error in enumerate(password_errors, 1):
                        error_list.append(f"{i}. {error}")
                    
                    structured_errors['new_password'] = f"Por favor, se atente a esses detalhes para a nova senha:\n" + ";\n".join(error_list) + "."
        
        # Store structured errors in form
        if structured_errors:
            self._structured_errors = structured_errors
            # Raise a generic error to prevent form submission
            raise forms.ValidationError("Existem erros nos dados fornecidos.")
        
        return cleaned_data


class ChangeEmailForm(forms.Form):
    """Form for changing user email"""
    new_email = forms.EmailField(
        max_length=320,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Novo email'
        }),
        label="Novo Email"
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha atual para confirmar'
        }),
        label="Senha Atual"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Custom validation with hierarchical error messages for email change"""
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        password = cleaned_data.get('password')
        
        # Create structured error storage
        structured_errors = {}
        
        # 1. First priority: Check current password
        if password and not self.user.check_password(password):
            structured_errors['current_password'] = 'Senha atual incorreta.'
        
        # 2. Second priority: Validate email requirements (only if password is correct)
        elif new_email:
            email_errors = []
            
            # Check if email is different from current
            if new_email == self.user.email:
                email_errors.append('O novo email deve ser diferente do email atual.')
            
            # Check if email is already in use
            if User.objects.filter(email=new_email).exclude(id=self.user.id).exists():
                email_errors.append('Este email já está em uso por outro usuário.')
            
            # If there are email errors, create structured message
            if email_errors:
                if len(email_errors) == 1:
                    structured_errors['new_email'] = email_errors[0]
                else:
                    error_list = []
                    for i, error in enumerate(email_errors, 1):
                        error_list.append(f"{i}. {error}")
                    
                    structured_errors['new_email'] = f"Por favor, se atente a esses detalhes para o novo email:\n" + ";\n".join(error_list) + "."
        
        # Store structured errors in form
        if structured_errors:
            self._structured_errors = structured_errors
            # Raise a generic error to prevent form submission
            raise forms.ValidationError("Existem erros nos dados fornecidos.")
        
        return cleaned_data


class EditBookForm(forms.Form):
    """Form for editing book information with validation for unchanged data"""
    title = forms.CharField(max_length=200, min_length=1, label="Título")
    author = forms.CharField(max_length=150, min_length=1, label="Autor") 
    year = forms.IntegerField(required=False, min_value=1000, label="Ano de Lançamento")
    publisher = forms.CharField(max_length=100, required=False, label="Editora")
    category = forms.CharField(max_length=50, label="Categoria")
    description = forms.CharField(max_length=2000, required=False, label="Descrição", widget=forms.Textarea(attrs={'rows': 4}))
    copies = forms.IntegerField(min_value=1, label="Exemplares")
    
    def __init__(self, book_data=None, *args, **kwargs):
        self.original_data = book_data
        super().__init__(*args, **kwargs)
        
        # Set dynamic max_value for year
        self.fields['year'].max_value = get_max_book_year()
        self.fields['year'].widget.attrs.update({
            'max': get_max_book_year()
        })
        
        # Set dynamic max_value for copies
        self.fields['copies'].max_value = get_max_book_copies()
        self.fields['copies'].widget.attrs.update({
            'max': get_max_book_copies()
        })
        
        # Pre-fill fields with existing data
        if book_data:
            self.fields['title'].initial = book_data.get('titulo', '')
            self.fields['author'].initial = book_data.get('autor', '')
            self.fields['year'].initial = book_data.get('ano', '')
            self.fields['publisher'].initial = book_data.get('editora', '')
            self.fields['category'].initial = book_data.get('genero', '')
            self.fields['description'].initial = book_data.get('descricao', '')
            self.fields['copies'].initial = book_data.get('total_count', 1)
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.original_data:
            # Check if any data has changed
            title_changed = cleaned_data.get('title') != self.original_data.get('titulo', '')
            author_changed = cleaned_data.get('author') != self.original_data.get('autor', '')
            year_changed = cleaned_data.get('year') != self.original_data.get('ano')
            publisher_changed = cleaned_data.get('publisher') != self.original_data.get('editora', '')
            category_changed = cleaned_data.get('category') != self.original_data.get('genero', '')
            description_changed = cleaned_data.get('description') != self.original_data.get('descricao', '')
            copies_changed = cleaned_data.get('copies') != self.original_data.get('total_count', 1)
            
            # If no changes were made, raise validation error
            if not (title_changed or author_changed or year_changed or publisher_changed or category_changed or description_changed or copies_changed):
                raise forms.ValidationError('Nenhuma alteração foi detectada. Modifique pelo menos um campo para salvar as alterações.')
        
        return cleaned_data


class ChangeUsernameForm(forms.Form):
    """Form for changing username"""
    new_username = forms.CharField(
        max_length=30,
        min_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Novo nome de usuário'
        }),
        label="Novo Nome de Usuário"
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha atual para confirmar'
        }),
        label="Senha Atual"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Custom validation with hierarchical error messages for username change"""
        cleaned_data = super().clean()
        new_username = cleaned_data.get('new_username')
        password = cleaned_data.get('password')
        
        # Create structured error storage
        structured_errors = {}
        
        # 1. First priority: Check current password
        if password and not self.user.check_password(password):
            structured_errors['current_password'] = 'Senha atual incorreta.'
        
        # 2. Second priority: Validate username requirements (only if password is correct)
        elif new_username:
            username_errors = []
            
            # Check if username is different from current
            if new_username == self.user.username:
                # Return early with specific message for same username
                structured_errors['new_username'] = 'O novo nome de usuário deve ser diferente do atual.'
                self._structured_errors = structured_errors
                raise forms.ValidationError("Existem erros nos dados fornecidos.")
                return cleaned_data
            
            # Check username length
            if len(new_username) < 3:
                username_errors.append('Nome de usuário muito curto: É preciso pelo menos 3 caracteres.')
            elif len(new_username) > 30:
                username_errors.append('Nome de usuário muito longo: Máximo de 30 caracteres.')
            
            # Check if username contains only valid characters
            import re
            if not re.match(r'^[\w.@+-]+$', new_username):
                username_errors.append('Nome de usuário contém caracteres inválidos. Use apenas letras, números e @/./+/-/_.')
            
            # Check if username is already in use
            if User.objects.filter(username=new_username).exclude(id=self.user.id).exists():
                username_errors.append('Este nome de usuário já está em uso.')
            
            # If there are username errors, create structured message
            if username_errors:
                if len(username_errors) == 1:
                    structured_errors['new_username'] = username_errors[0]
                else:
                    error_list = []
                    for i, error in enumerate(username_errors, 1):
                        error_list.append(f"{i}. {error}")
                    
                    structured_errors['new_username'] = f"Por favor, se atente a esses detalhes para o novo nome de usuário:\n" + ";\n".join(error_list) + "."
        
        # Store structured errors in form
        if structured_errors:
            self._structured_errors = structured_errors
            # Raise a generic error to prevent form submission
            raise forms.ValidationError("Existem erros nos dados fornecidos.")
        
        return cleaned_data
