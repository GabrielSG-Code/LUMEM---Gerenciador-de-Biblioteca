from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model

from .models import Livros

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