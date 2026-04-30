from django.shortcuts import render
from django.http import HttpResponse
import os
from datetime import datetime, timedelta

def home(request):
    # Mock loan data for now - replace with actual model queries later
    loans = []
    if request.user.is_authenticated:
        # Create mock loan objects
        class MockBook:
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
                return categories.get(self.category, self.category.title())
        
        class MockLoan:
            def __init__(self, book, due_date):
                self.book = book
                self.due_date = due_date
                self.is_overdue = due_date < datetime.now().date()
        
        # Sample loans
        loans = [
            MockLoan(MockBook("1984", "George Orwell", "drama"), datetime.now().date() + timedelta(days=5)),
            MockLoan(MockBook("O Código Da Vinci", "Dan Brown", "investigacao"), datetime.now().date() - timedelta(days=2)),
        ]
    
    return render(request, 'home.html', {'loans': loans})

def browse_collection(request):
    # Mock book collection data - replace with actual model queries later
    class MockBook:
        def __init__(self, title, author, category, available=True):
            self.title = title
            self.author = author
            self.category = category
            self.available = available
        
        def get_category_display(self):
            categories = {
                'investigacao': 'Investigação',
                'romance': 'Romance', 
                'ficcao': 'Ficção',
                'terror': 'Terror',
                'historico': 'Histórico',
                'drama': 'Drama'
            }
            return categories.get(self.category, self.category.title())
    
    # Sample collection
    books = [
        MockBook("O Nome da Rosa", "Umberto Eco", "investigacao", True),
        MockBook("Orgulho e Preconceito", "Jane Austen", "romance", True),
        MockBook("Duna", "Frank Herbert", "ficcao", False),
        MockBook("It — A Coisa", "Stephen King", "terror", True),
        MockBook("Sapiens", "Yuval Harari", "historico", True),
        MockBook("A Menina que Roubava Livros", "Markus Zusak", "drama", False),
        MockBook("O Código Da Vinci", "Dan Brown", "investigacao", True),
        MockBook("1984", "George Orwell", "ficcao", True),
        MockBook("Dom Casmurro", "Machado de Assis", "drama", True),
        MockBook("O Cortiço", "Aluísio Azevedo", "historico", True),
        MockBook("A Metamorfose", "Franz Kafka", "ficcao", True),
        MockBook("O Pequeno Príncipe", "Antoine de Saint-Exupéry", "drama", True),
    ]
    
    return render(request, 'browse_collection.html', {'books': books})

