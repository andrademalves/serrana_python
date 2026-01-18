"""
URLS - MÓDULO ORÇAMENTOS E VENDAS
==================================
"""

from django.urls import path
from . import views

app_name = 'vendas'

urlpatterns = [
    # Orçamentos - CRUD
    path('orcamentos/', views.orcamento_list, name='orcamento_list'),
    path('orcamentos/novo/', views.orcamento_create, name='orcamento_create'),
    path('orcamentos/<int:pk>/', views.orcamento_detail, name='orcamento_detail'),
    path('orcamentos/<int:pk>/editar/', views.orcamento_edit, name='orcamento_edit'),
    
    # Orçamentos - Ações
    path('orcamentos/<int:pk>/mudar-status/', views.orcamento_mudar_status, name='orcamento_mudar_status'),
    path('orcamentos/<int:pk>/aprovar/', views.orcamento_aprovar, name='orcamento_aprovar'),
    path('orcamentos/<int:pk>/reprovar/', views.orcamento_reprovar, name='orcamento_reprovar'),
    path('orcamentos/<int:pk>/pdf/', views.orcamento_pdf, name='orcamento_pdf'),
    
    # Itens - AJAX
    path('orcamentos/<int:pk>/adicionar-item/', views.orcamento_add_item, name='orcamento_add_item'),
    path('orcamentos/<int:pk>/remover-item/<int:item_id>/', views.orcamento_remove_item, name='orcamento_remove_item'),
    
    # Relatórios
    path('relatorios/funil-vendas/', views.relatorio_funil_vendas, name='relatorio_funil'),
    path('relatorios/conversao-vendedor/', views.relatorio_conversao_vendedor, name='relatorio_conversao'),
    path('relatorios/backlog/', views.relatorio_backlog, name='relatorio_backlog'),
]
