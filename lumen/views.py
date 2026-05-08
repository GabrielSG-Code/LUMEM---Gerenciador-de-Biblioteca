from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import os
from datetime import datetime, timedelta

def home(request):
    if not request.user.is_authenticated:
        # Show public home page for non-authenticated users
        return render(request, 'public_home.html')
    
    # Show dashboard for authenticated users
    # Get real loans from database for the current user
    try:
        # Import models inside the function to avoid circular imports
        from apps.accounts.models import Emprestimo, Livros
        
        # Get loans for current user using user ID as string
        user_loans = Emprestimo.objects.filter(
            id_usuario=str(request.user.id),
            data_fim__isnull=True  # Only active loans (not returned)
        ).order_by('data_entrega')
        
        loans = []
        for emprestimo in user_loans:
            try:
                # Get book details
                livro = Livros.objects.get(id_livro=emprestimo.id_livro)
                
                # Create loan object with book details and due date
                class BookData:
                    def __init__(self, title, author, category):
                        self.title = title
                        self.author = author
                        self.category = category
                    
                    def get_category_display(self):
                        categories = {
                            'investigacao': 'Investigação',
                            'romance': 'Romance', 
                            'ficcao': 'Ficção',
                            'terror': 'Terror',
                            'historico': 'Histórico',
                            'drama': 'Drama'
                        }
                        return categories.get(self.category, self.category.title() if self.category else 'Sem categoria')
                
                class LoanData:
                    def __init__(self, book_title, book_author, book_category, due_date):
                        self.book = BookData(book_title, book_author, book_category)
                        self.due_date = due_date
                        self.is_overdue = due_date < datetime.now().date() if due_date else False
                
                loan = LoanData(
                    livro.titulo,
                    livro.autor,
                    livro.genero,
                    emprestimo.data_entrega
                )
                loans.append(loan)
                
            except Livros.DoesNotExist:
                # Skip loans for books that don't exist
                continue
                
    except Exception as e:
        # If there's any error, show empty loans list
        print(f"Error loading loans: {e}")
        loans = []
    
    return render(request, 'home.html', {'loans': loans})


