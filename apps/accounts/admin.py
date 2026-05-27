from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Emprestimo, Livros, Usuarios


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
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