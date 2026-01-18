from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import PermissaoMenu, Menu


def require_empresa(view_func):
    """
    Decorator que garante que o usuário tem uma empresa ativa na sessão
    Redireciona para seleção de empresa se necessário
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        empresa_id = request.session.get('empresa_ativa_id')
        
        if not empresa_id:
            # Tentar definir empresa padrão do usuário
            from usuarios.models import UsuarioEmpresa
            vinculo = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                ativo=True
            ).select_related('empresa').first()
            
            if vinculo:
                request.session['empresa_ativa_id'] = vinculo.empresa_id
                request.empresa = vinculo.empresa
            else:
                messages.warning(request, 'Por favor, selecione uma empresa para continuar.')
                return redirect('usuarios:selecionar_empresa')
        else:
            from usuarios.models import Empresa
            try:
                request.empresa = Empresa.objects.get(id=empresa_id, ativa=True)
            except Empresa.DoesNotExist:
                messages.error(request, 'Empresa inválida ou inativa.')
                del request.session['empresa_ativa_id']
                return redirect('usuarios:selecionar_empresa')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def verificar_permissao_menu(url_menu):
    """
    Decorator para verificar se o usuário tem permissão para acessar um menu específico
    
    Uso:
    @verificar_permissao_menu('/dashboard/')
    def minha_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Você precisa estar autenticado.')
                return redirect('login')
            
            # Superusuário tem acesso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verifica se o menu existe
            try:
                menu = Menu.objects.get(url=url_menu, ativo=True)
            except Menu.DoesNotExist:
                messages.warning(request, f'Menu "{url_menu}" não encontrado ou inativo.')
                return redirect('usuarios:home_modulos')
            
            # Verifica permissão do usuário
            tem_permissao = PermissaoMenu.objects.filter(
                usuario=request.user,
                menu=menu,
                pode_visualizar=True
            ).exists()
            
            # Se não tem permissão direta, verifica permissão por grupo
            if not tem_permissao:
                grupos_usuario = request.user.groups.all()
                tem_permissao = PermissaoMenu.objects.filter(
                    grupo__in=grupos_usuario,
                    menu=menu,
                    pode_visualizar=True
                ).exists()
            
            if not tem_permissao:
                messages.error(request, 'Você não tem permissão para acessar este recurso.')
                return redirect('usuarios:home_modulos')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def verificar_permissao_acao(url_menu, acao):
    """
    Decorator para verificar permissões específicas (criar, editar, excluir)
    
    Uso:
    @verificar_permissao_acao('/usuarios/', 'criar')
    def criar_usuario(request):
        ...
    
    Ações disponíveis: 'criar', 'editar', 'excluir'
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Você precisa estar autenticado.')
                return redirect('login')
            
            # Superusuário tem acesso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Verifica se o menu existe
            try:
                menu = Menu.objects.get(url=url_menu, ativo=True)
            except Menu.DoesNotExist:
                messages.warning(request, f'Menu "{url_menu}" não encontrado ou inativo.')
                return redirect('usuarios:home_modulos')
            
            # Mapeia a ação para o campo do modelo
            campos_acao = {
                'criar': 'pode_criar',
                'editar': 'pode_editar',
                'excluir': 'pode_excluir'
            }
            
            if acao not in campos_acao:
                messages.error(request, 'Ação inválida.')
                return redirect('usuarios:home_modulos')
            
            campo = campos_acao[acao]
            
            # Verifica permissão do usuário
            filtro = {
                'usuario': request.user,
                'menu': menu,
                campo: True
            }
            tem_permissao = PermissaoMenu.objects.filter(**filtro).exists()
            
            # Se não tem permissão direta, verifica permissão por grupo
            if not tem_permissao:
                grupos_usuario = request.user.groups.all()
                filtro['grupo__in'] = grupos_usuario
                del filtro['usuario']
                tem_permissao = PermissaoMenu.objects.filter(**filtro).exists()
            
            if not tem_permissao:
                messages.error(request, f'Você não tem permissão para {acao} neste recurso.')
                return redirect('usuarios:home_modulos')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permissao_menu_required(url_menu, acao='visualizar'):
    """
    Decorator unificado para verificar permissões de menu
    
    Uso:
    @permissao_menu_required('/financeiro/', 'visualizar')
    def minha_view(request):
        ...
    
    Ações disponíveis: 'visualizar', 'criar', 'editar', 'excluir'
    """
    if acao == 'visualizar':
        return verificar_permissao_menu(url_menu)
    else:
        return verificar_permissao_acao(url_menu, acao)
