#!/usr/bin/env python3
import os
import django
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumen.settings')

django.setup()

from apps.accounts.models import Livros

# Get unique categories from database
categories = Livros.objects.exclude(genero__isnull=True).exclude(genero='').values_list('genero', flat=True).distinct()

print("=== DATABASE CATEGORIES ===")
for cat in sorted(set(categories)):
    print(f"'{cat}'")

print("\n=== TOTAL UNIQUE CATEGORIES ===")
print(f"Count: {len(set(categories))}")