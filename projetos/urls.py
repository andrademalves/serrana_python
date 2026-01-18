from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Orçamentos
    path('orcamentos/', views.listar_orcamentos, name='listar_orcamentos'),
    path('orcamentos/criar/', views.criar_orcamento, name='criar_orcamento'),
    path('orcamentos/<int:pk>/', views.visualizar_orcamento, name='visualizar_orcamento'),
    path('orcamentos/<int:pk>/editar/', views.editar_orcamento, name='editar_orcamento'),
    path('orcamentos/<int:pk>/aprovar/', views.aprovar_orcamento, name='aprovar_orcamento'),
    path('orcamentos/<int:pk>/rejeitar/', views.rejeitar_orcamento, name='rejeitar_orcamento'),
    path('orcamentos/<int:pk>/pdf/', views.imprimir_orcamento_pdf, name='imprimir_orcamento_pdf'),
    path('api/buscar-itens-por-tipo/', views.buscar_itens_por_tipo, name='buscar_itens_por_tipo'),
    path('api/buscar-dados-item/', views.buscar_dados_item, name='buscar_dados_item'),
    path('api/orcamento/<int:orcamento_id>/visitas/', views.buscar_dados_visitas_orcamento, name='buscar_dados_visitas_orcamento'),
    
    # Projetos
    path('projetos/', views.listar_projetos, name='listar_projetos'),
    path('projetos/criar/', views.criar_projeto, name='criar_projeto'),
    path('projetos/<int:pk>/', views.visualizar_projeto, name='visualizar_projeto'),
    path('projetos/<int:pk>/editar/', views.editar_projeto, name='editar_projeto'),
    
    # Diário da Obra
    path('projetos/<int:projeto_id>/diario/', views.listar_diario_obra, name='listar_diario_obra'),
    path('projetos/<int:projeto_id>/diario/adicionar/', views.adicionar_diario_obra, name='adicionar_diario_obra'),
    path('diario/<int:pk>/', views.visualizar_diario_obra, name='visualizar_diario_obra'),
    path('diario/<int:pk>/editar/', views.editar_diario_obra, name='editar_diario_obra'),
    path('diario/<int:pk>/deletar/', views.deletar_diario_obra, name='deletar_diario_obra'),
    
    # Vendas Diretas
    path('vendas/', views.listar_vendas, name='listar_vendas'),
    path('vendas/criar/', views.criar_venda, name='criar_venda'),
    
    # Visitas Técnicas
    path('visitas-tecnicas/', views.listar_visitas_tecnicas, name='listar_visitas_tecnicas'),
    path('visitas-tecnicas/criar/', views.criar_visita_tecnica, name='criar_visita_tecnica'),
    path('visitas-tecnicas/<int:pk>/', views.visualizar_visita_tecnica, name='visualizar_visita_tecnica'),
    path('visitas-tecnicas/<int:pk>/editar/', views.editar_visita_tecnica, name='editar_visita_tecnica'),
    path('visitas-tecnicas/<int:pk>/cancelar/', views.cancelar_visita_tecnica, name='cancelar_visita_tecnica'),
    path('visitas-tecnicas/<int:pk>/marcar-realizada/', views.marcar_visita_realizada, name='marcar_visita_realizada'),
]
