from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.modulos, name='home_modulos'),
    path('home/', views.dashboard, name='dashboard'),  # Dashboard inicial (módulos)
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/criar/', views.criar_usuario, name='criar_usuario'),
    path('usuarios/<int:user_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:user_id>/ativar-desativar/', views.alternar_status_usuario, name='alternar_status_usuario'),
    path('usuarios/<int:user_id>/permissoes/', views.gerenciar_permissoes, name='gerenciar_permissoes'),
    
    # Gestão de Empresas
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('empresas/criar/', views.criar_empresa, name='criar_empresa'),
    path('empresas/<int:empresa_id>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/<int:empresa_id>/vincular-usuario/', views.vincular_usuario_empresa, name='vincular_usuario_empresa'),
    path('empresas/<int:empresa_id>/testar-smtp/', views.testar_smtp, name='testar_smtp'),
    
    # Configuração de Impostos da Empresa
    path('empresas/<int:empresa_id>/impostos/', views.configurar_impostos_empresa, name='configurar_impostos_empresa'),
    path('empresas/<int:empresa_id>/impostos/criar/', views.criar_aliquota_empresa, name='criar_aliquota_empresa'),
    path('empresas/<int:empresa_id>/impostos/<int:aliquota_id>/editar/', views.editar_aliquota_empresa, name='editar_aliquota_empresa'),
    path('empresas/<int:empresa_id>/impostos/<int:aliquota_id>/excluir/', views.excluir_aliquota_empresa, name='excluir_aliquota_empresa'),
    path('empresas/<int:empresa_id>/impostos/mudar-regime/', views.mudar_regime_empresa, name='mudar_regime_empresa'),
    
    # Seleção e Troca de Empresa
    path('empresas/selecionar/', views.selecionar_empresa, name='selecionar_empresa'),
    path('empresas/trocar/<int:empresa_id>/', views.trocar_empresa, name='trocar_empresa'),
]
