from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Emprestimo, Livros, Usuarios, LoanConfig, DamageReport, UserRegularization


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'status', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'status', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('User Information', {'fields': ('role', 'status')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('User Information', {'fields': ('role', 'status')}),
    )


@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('id_emprestimo', 'id_usuario', 'id_livro', 'data_inicio', 'data_entrega', 'data_fim')
    list_filter = ('data_inicio', 'data_entrega', 'data_fim')
    search_fields = ('id_emprestimo', 'id_usuario', 'id_livro')
    date_hierarchy = 'data_inicio'
    ordering = ('-data_inicio',)
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('id_emprestimo', 'id_usuario', 'id_livro')
        }),
        ('Dates', {
            'fields': ('data_inicio', 'data_entrega', 'data_fim')
        }),
    )


@admin.register(Livros)
class LivrosAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'editora', 'ano', 'genero', 'status_livro')
    list_filter = ('genero', 'status_livro', 'ano', 'editora')
    search_fields = ('titulo', 'autor', 'isbn_13', 'isbn_10')
    ordering = ('titulo',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('titulo', 'autor', 'descricao')
        }),
        ('Publication Details', {
            'fields': ('editora', 'ano', 'paginas')
        }),
        ('Classification', {
            'fields': ('genero', 'status_livro')
        }),
        ('ISBN', {
            'fields': ('isbn_13', 'isbn_10'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'privilegio', 'status')
    list_filter = ('privilegio', 'status')
    search_fields = ('username', 'email')
    ordering = ('username',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'senha')
        }),
        ('Permissions', {
            'fields': ('privilegio', 'status')
        }),
    )


@admin.register(LoanConfig)
class LoanConfigAdmin(admin.ModelAdmin):
    list_display = ('max_loans_per_reader', 'max_overdue_days', 'loan_duration_days', 'updated_at')
    
    fieldsets = (
        ('Loan Settings', {
            'fields': ('max_loans_per_reader', 'loan_duration_days', 'max_overdue_days')
        }),
    )


@admin.register(DamageReport)
class DamageReportAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'reported_at', 'reported_by', 'has_regularization')
    list_filter = ('reported_at', 'reported_by')
    search_fields = ('book__titulo', 'user__username', 'description')
    readonly_fields = ('reported_at',)
    ordering = ('-reported_at',)
    
    fieldsets = (
        ('Informações do Dano', {
            'fields': ('emprestimo', 'user', 'book', 'description')
        }),
        ('Informações de Controle', {
            'fields': ('reported_by', 'reported_at')
        }),
    )
    
    def has_regularization(self, obj):
        return hasattr(obj, 'regularization')
    has_regularization.boolean = True
    has_regularization.short_description = 'Regularizado'


@admin.register(UserRegularization)
class UserRegularizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'damage_report', 'method', 'administrator', 'regularized_at')
    list_filter = ('method', 'regularized_at', 'administrator')
    search_fields = ('user__username', 'damage_report__book__titulo')
    readonly_fields = ('regularized_at',)
    ordering = ('-regularized_at',)
    
    fieldsets = (
        ('Regularização', {
            'fields': ('damage_report', 'user', 'method', 'notes')
        }),
        ('Informações de Controle', {
            'fields': ('administrator', 'regularized_at')
        }),
    )