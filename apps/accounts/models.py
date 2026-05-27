from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        LIBRARIAN = 'librarian', 'Bibliotecário'
        READER = 'reader', 'Leitor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.READER)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

class LoanConfig(models.Model):
    max_loans_per_reader = models.PositiveIntegerField(default=2, help_text="Máximo de empréstimos por leitor")
    max_overdue_days = models.PositiveIntegerField(default=7, help_text="Máximo de dias em atraso")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração de Empréstimos"
        verbose_name_plural = "Configurações de Empréstimos"

    def __str__(self):
        return f"Config: {self.max_loans_per_reader} empréstimos, {self.max_overdue_days} dias atraso"

    @classmethod
    def get_config(cls):
        """Get the current loan configuration, create default if none exists"""
        config = cls.objects.first()
        if not config:
            config = cls.objects.create()
        return config

class Emprestimo(models.Model):
    id = models.AutoField(primary_key=True)
    id_usuario = models.CharField(max_length=50, blank=True, null=True)
    id_livro = models.CharField(max_length=50, blank=True, null=True)
    id_emprestimo = models.CharField(max_length=50, blank=True, null=True)
    data_inicio = models.DateField(blank=True, null=True)
    data_entrega = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    overdue_days = models.PositiveIntegerField(default=7, help_text="Dias de tolerância para atraso (armazenado na criação do empréstimo)")

    class Meta:
        managed = True
        db_table = 'emprestimo'

class Livros(models.Model):
    id_livro = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    isbn_13 = models.CharField(max_length=13, blank=True, null=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    editora = models.CharField(max_length=255, blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    paginas = models.IntegerField(blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)
    genero = models.CharField(max_length=255, blank=True, null=True)
    status_livro = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'livros'

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    senha = models.CharField(max_length=255)
    privilegio = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'usuarios'
