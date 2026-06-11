from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        LIBRARIAN = 'librarian', 'Bibliotecário'
        READER = 'reader', 'Leitor'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Ativo'
        INACTIVE = 'inactive', 'Inativo'
        BLOCKED = 'blocked', 'Bloqueado'

    role = models.CharField(max_length=15, choices=Role.choices, default=Role.READER)
    email = models.EmailField(max_length=320, unique=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

class LoanConfig(models.Model):
    max_loans_per_reader = models.PositiveIntegerField(default=2, help_text="Máximo de empréstimos por leitor")
    max_overdue_days = models.PositiveIntegerField(default=7, help_text="Máximo de dias em atraso")
    loan_duration_days = models.PositiveIntegerField(default=7, help_text="Duração do empréstimo em dias")
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
    id_usuario = models.CharField(max_length=20, blank=True, null=True)
    id_livro = models.CharField(max_length=20, blank=True, null=True)
    id_emprestimo = models.CharField(max_length=25, blank=True, null=True)
    data_inicio = models.DateField(blank=True, null=True)
    data_entrega = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    overdue_days = models.PositiveIntegerField(default=7, help_text="Dias de tolerância para atraso (armazenado na criação do empréstimo)")

    class Meta:
        managed = True
        db_table = 'emprestimo'

class Livros(models.Model):
    id_livro = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200, validators=[MinLengthValidator(1)])
    autor = models.CharField(max_length=150, validators=[MinLengthValidator(1)])
    isbn_13 = models.CharField(max_length=13, blank=True, null=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True)
    editora = models.CharField(max_length=100, blank=True, null=True)
    ano = models.IntegerField(blank=True, null=True)
    paginas = models.IntegerField(blank=True, null=True)
    descricao = models.TextField(max_length=2000, blank=True, null=True)
    genero = models.CharField(max_length=50, blank=True, null=True)
    status_livro = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'livros'

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=30)
    senha = models.CharField(max_length=128)
    privilegio = models.CharField(max_length=15, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=320, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'usuarios'


class DamageReport(models.Model):
    emprestimo = models.ForeignKey(Emprestimo, on_delete=models.CASCADE, related_name='damage_reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='damage_reports')
    book = models.ForeignKey(Livros, on_delete=models.CASCADE, related_name='damage_reports')
    description = models.TextField(max_length=1000, help_text="Descrição do dano relatado")
    reported_at = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_damages')

    class Meta:
        verbose_name = "Relatório de Dano"
        verbose_name_plural = "Relatórios de Danos"
        ordering = ['-reported_at']

    def __str__(self):
        return f"Dano - {self.book.titulo} por {self.user.username}"


class UserRegularization(models.Model):
    class RegularizationMethod(models.TextChoices):
        FINANCIAL_REIMBURSEMENT = 'financial', 'Reembolso financeiro'
        BOOK_REPLACEMENT = 'replacement', 'Substituição do livro'
        OTHER = 'other', 'Outro'

    damage_report = models.OneToOneField(
        DamageReport, 
        on_delete=models.CASCADE, 
        related_name='regularization',
        help_text="Relatório de dano que está sendo regularizado"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='regularizations',
        help_text="Usuário que estava bloqueado"
    )
    administrator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='performed_regularizations',
        help_text="Administrador que realizou a regularização"
    )
    method = models.CharField(
        max_length=20, 
        choices=RegularizationMethod.choices,
        help_text="Método usado para regularizar a situação"
    )
    notes = models.TextField(
        max_length=500, 
        blank=True, 
        null=True,
        help_text="Observações adicionais sobre a regularização"
    )
    regularized_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Regularização de Usuário"
        verbose_name_plural = "Regularizações de Usuários"
        ordering = ['-regularized_at']

    def __str__(self):
        return f"Regularização - {self.user.username} em {self.regularized_at.strftime('%d/%m/%Y')}"
