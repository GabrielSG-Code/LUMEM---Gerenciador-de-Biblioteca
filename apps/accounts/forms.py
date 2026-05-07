from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

from .models import Usuarios

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

        if Usuarios.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado na base legada.')

        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')

        if Usuarios.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está cadastrado na base legada.')

        return username

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            Usuarios.objects.create(
                username=self.cleaned_data['username'],
                senha=make_password(self.cleaned_data['password1']),
                privilegio='leitor',
                status='ativo',
                email=self.cleaned_data['email']
            )

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