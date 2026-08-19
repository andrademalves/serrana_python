"""
Middleware de Empresa Ativa
Injeta request.empresa em todas as requests e garante isolamento de dados
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Empresa, UsuarioEmpresa


class EmpresaAtivaMiddleware:
    """
    Middleware que garante que o usuário sempre tenha uma empresa ativa no contexto.
    
    Funcionalidade:
    - Busca empresa_ativa_id na sessão
    - Valida se empresa existe e está ativa
    - Valida se usuário tem acesso à empresa
    - Injeta request.empresa para uso nas views
    - Redireciona para seleção se necessário
    """
    
    # URLs que não requerem empresa (login, logout, seleção de empresa)
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/empresas/',  # Gestão de empresas (listar, criar, editar)
        '/empresas/selecionar/',
        '/empresas/trocar/',
        '/static/',
        '/media/',
        '/usuarios/',  # Painel de módulos e gestão de usuários
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs isentas não precisam de empresa
        if self._is_exempt_url(request.path):
            return self.get_response(request)
        
        # Usuário não autenticado - deixar passar (login vai capturar)
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Buscar empresa ativa na sessão
        empresa_id = request.session.get('empresa_ativa_id')
        
        if empresa_id:
            try:
                empresa = Empresa.objects.get(pk=empresa_id, ativa=True)
                
                # Verificar se usuário tem acesso a esta empresa
                if self._usuario_tem_acesso(request.user, empresa):
                    request.empresa = empresa
                    return self.get_response(request)
                else:
                    # Usuário perdeu acesso - limpar sessão
                    del request.session['empresa_ativa_id']
                    messages.warning(request, 'Você não tem mais acesso a esta empresa.')
                    return self._redirecionar_selecao_empresa(request)
                    
            except Empresa.DoesNotExist:
                # Empresa foi deletada ou desativada
                del request.session['empresa_ativa_id']
                messages.error(request, 'A empresa selecionada não está mais disponível.')
                return self._redirecionar_selecao_empresa(request)
        
        # Nenhuma empresa na sessão - tentar selecionar automaticamente
        empresa_auto = self._selecionar_empresa_automatica(request.user)
        
        if empresa_auto:
            # Salvar na sessão e continuar
            request.session['empresa_ativa_id'] = empresa_auto.id
            request.empresa = empresa_auto
            return self.get_response(request)
        
        # Não conseguiu selecionar automaticamente
        # Se for superuser e estiver acessando gestão de empresas, permitir sem empresa ativa
        if request.user.is_superuser and request.path.startswith('/empresas/'):
            request.empresa = None  # Explicitamente None para superuser gerenciar empresas
            return self.get_response(request)
        
        # Para outros casos, redirecionar para seleção
        return self._redirecionar_selecao_empresa(request)
    
    def _is_exempt_url(self, path):
        """Verifica se URL está isenta de validação de empresa"""
        return any(path.startswith(url) for url in self.EXEMPT_URLS)
    
    def _usuario_tem_acesso(self, user, empresa):
        """Verifica se usuário tem acesso à empresa"""
        # Superuser tem acesso a tudo
        if user.is_superuser:
            return True
        
        # Verificar via PerfilUsuario.empresa_padrao
        if hasattr(user, 'perfilusuario'):
            if user.perfilusuario.empresa_padrao == empresa:
                return True
        
        # Verificar via UsuarioEmpresa (M2M)
        return UsuarioEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            ativo=True
        ).exists()
    
    def _selecionar_empresa_automatica(self, user):
        """
        Tenta selecionar automaticamente uma empresa para o usuário.
        Retorna a empresa se conseguir selecionar, None caso contrário.
        """
        # Superuser: seleciona a primeira empresa ativa (matriz se houver)
        if user.is_superuser:
            return Empresa.objects.filter(ativa=True).order_by('-empresa_matriz', 'nome_fantasia').first()
        
        # Usuário comum: buscar empresas vinculadas
        empresas_disponiveis = Empresa.objects.filter(
            empresa_usuarios__usuario=user,
            empresa_usuarios__ativo=True,
            ativa=True
        ).distinct().order_by('-empresa_matriz', 'nome_fantasia')
        
        # Se tiver apenas uma empresa, selecionar automaticamente
        if empresas_disponiveis.count() == 1:
            return empresas_disponiveis.first()
        
        # Se tiver múltiplas empresas, não selecionar automaticamente
        # Usuário precisa escolher
        return None
    
    def _redirecionar_selecao_empresa(self, request):
        """Redireciona para página de seleção de empresa"""
        return redirect('usuarios:selecionar_empresa')


def empresa_context_processor(request):
    """
    Context processor que adiciona empresa ao template context.
    Permite usar {{ empresa_ativa }} em todos os templates.
    """
    empresa = getattr(request, 'empresa', None)
    if empresa:
        return {
            'empresa_ativa': empresa,
            'empresa_nome': empresa.nome_fantasia,
            'empresa_logo': empresa.logo.url if empresa.logo else None,
            'empresa_slug': empresa.slug,
        }
    return {
        'empresa_ativa': None,
        'empresa_nome': '',
        'empresa_logo': None,
        'empresa_slug': '',
    }
