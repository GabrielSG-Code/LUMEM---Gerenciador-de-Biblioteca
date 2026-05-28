from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('browse-collection/', views.browse_collection, name='browse_collection'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('users/update/<int:user_id>/', views.update_user, name='update_user'),
    path('books/add/', views.add_book, name='add_book'),
    path('loans/', views.manage_loans, name='manage_loans'),
    path('loans/return/<int:loan_id>/', views.return_book, name='return_book'),
    path('loans/config/', views.save_loan_config, name='save_loan_config'),
    path('profile/', views.profile, name='profile'),
    path('autocomplete/users/', views.autocomplete_users, name='autocomplete_users'),
    path('autocomplete/books/', views.autocomplete_books, name='autocomplete_books'),
    path('loans/report/pdf/', views.generate_pdf_report, name='generate_pdf_report'),
]