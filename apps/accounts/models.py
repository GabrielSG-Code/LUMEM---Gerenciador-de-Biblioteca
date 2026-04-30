from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        LIBRARIAN = 'librarian', 'Bibliotecário'
        READER = 'reader', 'Leitor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.READER)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'