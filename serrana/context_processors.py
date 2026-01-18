"""
Context Processors Globais
Injetam variáveis em todos os templates do projeto
"""

def current_module(request):
    """
    Detecta o módulo atual baseado na URL/namespace
    Retorna: {'current_module': 'financeiro'|'estoque'|'obras'|'vendas'|'cadastros'|'dashboard'|'relatorios'}
    """
    module = 'dashboard'  # padrão
    
    # Tentar detectar pelo namespace da URL
    if hasattr(request, 'resolver_match') and request.resolver_match:
        namespace = request.resolver_match.namespace
        if namespace:
            module = namespace
        else:
            # Se não tem namespace, detectar pelo path
            path = request.path.strip('/')
            
            if path.startswith('financeiro'):
                module = 'financeiro'
            elif path.startswith('estoque'):
                module = 'estoque'
            elif path.startswith('projetos'):
                module = 'obras'
            elif path.startswith('vendas') or path.startswith('orcamentos'):
                module = 'vendas'
            elif path.startswith('cadastros'):
                module = 'cadastros'
            elif path.startswith('usuarios'):
                module = 'usuarios'
            elif 'relatorio' in path:
                module = 'relatorios'
            elif path == '' or path == 'dashboard':
                module = 'dashboard'
    
    return {
        'current_module': module,
        'current_path': request.path,
    }


def user_permissions(request):
    """
    Expõe permissões úteis do usuário incluindo acesso a módulos
    """
    if not request.user.is_authenticated:
        return {
            'is_admin': False,
            'can_manage_users': False,
            'user_groups': [],
            'user_menus': [],
            'has_financeiro': False,
            'has_estoque': False,
            'has_projetos': False,
            'has_vendas': False,
            'has_cadastros': False,
        }
    
    # Superuser tem acesso a tudo
    if request.user.is_superuser:
        return {
            'is_admin': True,
            'can_manage_users': True,
            'user_groups': list(request.user.groups.values_list('name', flat=True)),
            'user_menus': [],
            'has_financeiro': True,
            'has_estoque': True,
            'has_projetos': True,
            'has_vendas': True,
            'has_cadastros': True,
        }
    
    # Buscar menus que o usuário tem permissão
    from usuarios.models import PermissaoMenu, Menu
    
    # Permissões diretas do usuário
    menus_usuario = Menu.objects.filter(
        permissoes__usuario=request.user,
        permissoes__pode_visualizar=True,
        ativo=True
    ).distinct()
    
    # Permissões por grupo
    menus_grupo = Menu.objects.filter(
        permissoes__grupo__in=request.user.groups.all(),
        permissoes__pode_visualizar=True,
        ativo=True
    ).distinct()
    
    # Combinar permissões
    menus_permitidos = (menus_usuario | menus_grupo).distinct()
    urls_permitidas = list(menus_permitidos.values_list('url', flat=True))
    
    # Verificar acesso aos módulos principais
    has_financeiro = any('/financeiro' in url for url in urls_permitidas)
    has_estoque = any('/estoque' in url for url in urls_permitidas)
    has_projetos = any('/projetos' in url or '/obras' in url for url in urls_permitidas)
    has_vendas = any('/vendas' in url or '/orcamentos' in url for url in urls_permitidas)
    has_cadastros = any('/cadastros' in url for url in urls_permitidas)
    
    return {
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'can_manage_users': request.user.is_staff,
        'user_groups': list(request.user.groups.values_list('name', flat=True)),
        'user_menus': urls_permitidas,
        'has_financeiro': has_financeiro,
        'has_estoque': has_estoque,
        'has_projetos': has_projetos,
        'has_vendas': has_vendas,
        'has_cadastros': has_cadastros,
    }
