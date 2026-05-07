from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('browse-collection/', views.browse_collection, name='browse_collection'),
    path('books/add/', views.add_book, name='add_book'),
]