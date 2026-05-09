from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model

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
    title = forms.CharField(max_length=255)
    author = forms.CharField(max_length=255)
    description = forms.CharField(required=False, widget=forms.Textarea)
    release_year = forms.IntegerField(required=False, min_value=1000, max_value=2100)
    category = forms.CharField(max_length=255)
    publisher = forms.CharField(max_length=255, required=False)
    exemplary = forms.IntegerField(min_value=1)

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
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        empty_label="Selecione um usuário",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    book = forms.ModelChoiceField(
        queryset=Livros.objects.filter(status_livro='Disponível'),
        empty_label="Selecione um livro",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    data_entrega = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    reserva = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Emprestimo
        fields = ['data_inicio', 'data_entrega', 'reserva']

    def save(self, commit=True):
        emprestimo = super().save(commit=False)
        emprestimo.id_usuario = str(self.cleaned_data['user'].id)
        emprestimo.id_livro = str(self.cleaned_data['book'].id_livro)
        emprestimo.id_emprestimo = f"EMP_{emprestimo.id_usuario}_{emprestimo.id_livro}_{emprestimo.data_inicio.strftime('%Y%m%d')}"
        
        if commit:
            emprestimo.save()
            # Update book status
            book = self.cleaned_data['book']
            book.status_livro = 'Emprestado'
            book.save()
        
        return emprestimo
