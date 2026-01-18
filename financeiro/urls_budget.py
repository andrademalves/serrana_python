"""
URLs para módulo de Budget
"""

from django.urls import path
from . import views_budget

app_name = 'budget'

urlpatterns = [
    # ========================================================================
    # DASHBOARD
    # ========================================================================
    path('dashboard/', views_budget.dashboard_budget, name='dashboard'),
    path('budget/<int:budget_id>/', views_budget.detalhe_budget, name='detalhe'),
    
    # ========================================================================
    # API - DESPESAS
    # ========================================================================
    path('api/despesa/lancar/', views_budget.api_lancar_despesa, name='api_lancar_despesa'),
    path('api/despesa/<int:despesa_id>/aprovar/', views_budget.api_aprovar_despesa, name='api_aprovar_despesa'),
    path('api/despesa/<int:despesa_id>/rejeitar/', views_budget.api_rejeitar_despesa, name='api_rejeitar_despesa'),
    
    # ========================================================================
    # API - JUSTIFICATIVAS
    # ========================================================================
    path('api/justificativa/criar/', views_budget.api_criar_justificativa, name='api_criar_justificativa'),
    path('api/justificativa/<int:justificativa_id>/aprovar/', views_budget.api_aprovar_justificativa, name='api_aprovar_justificativa'),
    path('api/justificativa/<int:justificativa_id>/rejeitar/', views_budget.api_rejeitar_justificativa, name='api_rejeitar_justificativa'),
    
    # ========================================================================
    # API - CONSULTAS
    # ========================================================================
    path('api/budget/<int:budget_id>/status/', views_budget.api_status_budget, name='api_status_budget'),
    path('api/budgets/criticos/', views_budget.api_budgets_criticos, name='api_budgets_criticos'),
    
    # ========================================================================
    # RELATÓRIOS (ETAPA 3)
    # ========================================================================
    path('relatorio/vendedores/', views_budget.relatorio_vendedores, name='relatorio_vendedores'),
    path('relatorio/instaladores/', views_budget.relatorio_instaladores, name='relatorio_instaladores'),
    path('relatorio/lucratividade/', views_budget.relatorio_lucratividade, name='relatorio_lucratividade'),
]
