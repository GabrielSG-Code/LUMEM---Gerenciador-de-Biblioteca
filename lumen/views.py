from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'home.html')

def create_super(request):
    from accounts.models import User
    User.objects.filter(username='admin_lumen').delete()
    User.objects.create_superuser(
        username='admin_lumen',
        email='seu@email.com',
        password='sua_nova_senha'
    )
    return HttpResponse('Superusuário criado com sucesso!')