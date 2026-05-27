import csv
import os
from django.conf import settings


def profile_icon(request):
    """
    Context processor to add profile icon based on user role
    """
    if not request.user.is_authenticated:
        return {}
    
    # Load category icons from CSV
    category_icons = {}
    try:
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'categories.csv'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'categories.csv'),
            'categories.csv'
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
                
        if csv_path:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'Category' in row and 'SVG Icon URL' in row:
                        category_icons[row['Category']] = row['SVG Icon URL']
    except Exception:
        pass
    
    # Get profile icon based on user role
    role_icons = {
        'reader': category_icons.get('Reader', 'https://cdn-icons-png.flaticon.com/512/456/456283.png'),
        'librarian': category_icons.get('Librarian', 'https://cdn-icons-png.flaticon.com/512/11227/11227582.png'),
        'admin': category_icons.get('Admin', 'https://cdn-icons-png.flaticon.com/512/17279/17279527.png'),
    }
    
    profile_icon_url = role_icons.get(request.user.role, role_icons['reader'])
    
    return {
        'profile_icon': profile_icon_url
    }