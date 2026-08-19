from django.urls import path
from . import views
from .views_pdf import gerar_documento_retirada_pdf
from .views_relatorios_pdf import relatorio_consolidado_pdf, relatorio_analitico_pdf, listar_itens_pdf, relatorio_estoque_atual_pdf, relatorio_estoque_atual_pdf

app_name = 'estoque'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Itens

    # Locais de Estoque
    path('locais/', views.listar_locais, name='listar_locais'),
    path('locais/criar/', views.criar_local, name='criar_local'),
    path('locais/editar/<int:id>/', views.editar_local, name='editar_local'),
    path('itens/', views.listar_itens, name='listar_itens'),
    path('itens/pdf/', listar_itens_pdf, name='listar_itens_pdf'),
    path('itens/criar/', views.criar_item, name='criar_item'),
    path('itens/editar/<int:id>/', views.editar_item, name='editar_item'),
    path('itens/excluir/<int:id>/', views.excluir_item, name='excluir_item'),
    
    # Movimentações
    path('movimentacoes/', views.listar_movimentacoes, name='listar_movimentacoes'),
    path('movimentacoes/criar/', views.criar_movimentacao, name='criar_movimentacao'),
    path('movimentacoes/<int:pk>/pdf/', gerar_documento_retirada_pdf, name='gerar_documento_retirada_pdf'),
    
    # Relatórios
    path('relatorios/estoque-atual/', views.relatorio_estoque_atual, name='relatorio_estoque_atual'),
    path('relatorios/movimentacoes/', views.relatorio_movimentacoes, name='relatorio_movimentacoes'),
    path('relatorios/materiais-obra-consolidado/', views.relatorio_materiais_obra_consolidado, name='relatorio_materiais_obra_consolidado'),
    path('relatorios/materiais-obra-analitico/', views.relatorio_materiais_obra_analitico, name='relatorio_materiais_obra_analitico'),
    
    # PDFs dos Relatórios
    path('relatorios/estoque-atual/pdf/', relatorio_estoque_atual_pdf, name='relatorio_estoque_atual_pdf'),
    path('relatorios/materiais-obra-consolidado/pdf/', relatorio_consolidado_pdf, name='relatorio_consolidado_pdf'),
    path('relatorios/materiais-obra-analitico/pdf/', relatorio_analitico_pdf, name='relatorio_analitico_pdf'),
]
