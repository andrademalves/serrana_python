"""
URLs - DASHBOARD BI
===================

Rotas para o dashboard e APIs AJAX.

Autor: Sistema BI Profissional
Data: Dezembro 2025
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Principal
    path('', views.dashboard_principal, name='principal'),
    
    # Dashboards Específicos
    path('estoque/', views.dashboard_estoque, name='estoque'),
    path('obras/', views.dashboard_obras, name='obras'),
    path('financeiro/', views.dashboard_financeiro, name='financeiro'),
    
    # Dashboards Detalhados
    path('estoque-detalhado/', views.estoque_detalhado, name='estoque_detalhado'),
    path('obras-detalhado/', views.obras_detalhado, name='obras_detalhado'),
    path('financeiro-detalhado/', views.financeiro_detalhado, name='financeiro_detalhado'),
    
    # APIs AJAX - Estoque
    path('api/estoque/kpis/', views.api_estoque_kpis, name='api_estoque_kpis'),
    path('api/estoque/curva-abc/', views.api_curva_abc, name='api_curva_abc'),
    path('api/estoque/consumo-medio/', views.api_consumo_medio, name='api_consumo_medio'),
    
    # APIs AJAX - Obras
    path('api/obras/status/', views.api_obras_status, name='api_obras_status'),
    path('api/obras/analise-financeira/', views.api_obras_analise_financeira, name='api_obras_analise_financeira'),
    
    # APIs AJAX - Financeiro
    path('api/financeiro/fluxo-caixa/', views.api_fluxo_caixa, name='api_fluxo_caixa'),
    path('api/financeiro/dre-mensal/', views.api_dre_mensal, name='api_dre_mensal'),
    path('api/financeiro/contas-vencidas/', views.api_contas_vencidas, name='api_contas_vencidas'),
    
    # Exportações
    path('exportar/pdf/', views.exportar_dashboard_pdf, name='exportar_pdf'),
    path('exportar/excel/', views.exportar_dashboard_excel, name='exportar_excel'),
    
    # Utilitários
    path('atualizar-cache/', views.atualizar_cache_dashboard, name='atualizar_cache'),
]
