from django.shortcuts import render
from apps.accounts import models
import os

def home(request):
    return render(request, 'home.html')

def create_super(request):
    from models import User
    User.objects.filter(username='admin_lumen').delete()
    User.objects.create_superuser(
        username=os.getenv('SUPERUSER_NAME'),
        email=os.getenv('SUPERUSER_EMAIL'),
        password=os.getenv('SUPERUSER_PASSW')
    )
    from django.http import HttpResponse
    return HttpResponse('Superusuário criado com sucesso!')