from django.urls import path
from . import views_new as views

app_name = 'estoque'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Itens
    path('itens/', views.listar_itens, name='listar_itens'),
    path('itens/novo/', views.criar_item, name='criar_item'),
    path('itens/<int:pk>/editar/', views.editar_item, name='editar_item'),
    path('itens/<int:pk>/', views.detalhe_item, name='detalhe_item'),
    
    # Locais
    path('locais/', views.listar_locais, name='listar_locais'),
    path('locais/novo/', views.criar_local, name='criar_local'),
    path('locais/<int:pk>/editar/', views.editar_local, name='editar_local'),
    
    # Destinos
    path('destinos/', views.listar_destinos, name='listar_destinos'),
    path('destinos/novo/', views.criar_destino, name='criar_destino'),
    
    # Movimentações
    path('movimentos/', views.listar_movimentos, name='listar_movimentos'),
    path('movimentos/entrada/', views.entrada_estoque, name='entrada_estoque'),
    path('movimentos/saida/', views.saida_estoque, name='saida_estoque'),
    path('movimentos/transferencia/', views.transferencia_estoque, name='transferencia_estoque'),
    path('movimentos/ajuste/', views.ajuste_estoque, name='ajuste_estoque'),
    
    # Relatórios
    path('relatorios/posicao/', views.relatorio_posicao_estoque, name='relatorio_posicao'),
    path('relatorios/minimo/', views.relatorio_itens_minimo, name='relatorio_minimo'),
    path('relatorios/valorizacao/', views.relatorio_valorizacao, name='relatorio_valorizacao'),
    path('relatorios/projeto/', views.relatorio_consumo_projeto, name='relatorio_consumo_projeto'),
    path('relatorios/projeto/<int:projeto_id>/', views.relatorio_consumo_projeto, name='relatorio_consumo_projeto_id'),
    
    # API / AJAX
    path('api/saldo/<int:item_id>/<int:local_id>/', views.api_saldo_item, name='api_saldo_item'),
]
