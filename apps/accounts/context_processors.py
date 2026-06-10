import csv
import os
from django.conf import settings
from django.utils import timezone
from .models import Emprestimo, Livros

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

def loan_due_alerts(request):
    if not request.user.is_authenticated:
        return {}

    if request.user.role != 'reader':
        return {}

    if request.path != '/':
        return {}

    if request.session.get('loan_alerts_shown'):
        return {}

    today = timezone.now().date()

    emprestimos = Emprestimo.objects.filter(
        id_usuario=str(request.user.id),
        data_fim__isnull=True
    )

    atrasados = []
    vence_hoje = []
    proximos = []

    for emp in emprestimos:
        if not emp.data_entrega:
            continue

        try:
            livro = Livros.objects.get(id_livro=int(emp.id_livro))
            titulo = livro.titulo
        except:
            titulo = f"ID Livro: {emp.id_livro}"

        dias = (emp.data_entrega - today).days

        if dias < 0:
            atrasados.append({
                "tipo": "atrasado",
                "mensagem": (
                    f"Aviso: O empréstimo do livro '{titulo}' está em atraso. "
                    f"Dias em atraso: {abs(dias)}. Realize a devolução para "
                    f"regularizar sua situação e voltar a pegar novos empréstimos."
                )
            })

        elif dias == 0:
            vence_hoje.append({
                "tipo": "vence_hoje",
                "mensagem": (
                    f"Lembrete: O empréstimo do livro '{titulo}' vence hoje. "
                    f"Realize a devolução para evitar atrasos e não ficar "
                    f"impossibilitado de realizar novos empréstimos."
                )
            })

        elif dias <= 2:
            proximos.append({
                "tipo": "proximo",
                "mensagem": (
                    f"Lembrete: O empréstimo do livro '{titulo}' está próximo "
                    f"da data de devolução. Dias restantes: {dias}. Programe "
                    f"a devolução para evitar atrasos e não ficar impossibilitado "
                    f"de realizar novos empréstimos."
                )
            })

    alerts = atrasados + vence_hoje + proximos

    if alerts:
        request.session['loan_alerts_shown'] = True

    return {
        'loan_due_alerts': alerts
    }