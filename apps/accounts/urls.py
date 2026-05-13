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
    path('profile/', views.profile, name='profile'),
]