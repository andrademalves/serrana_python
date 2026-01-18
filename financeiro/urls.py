"""
URLs do Módulo Financeiro
"""
from django.urls import path
from . import views, views_relatorios, relatorios_pdf, views_cobranca

app_name = 'financeiro'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard_alt'),
    
    # Títulos
    path('titulos/', views.listar_titulos, name='listar_titulos'),
    path('titulos/criar/', views.criar_titulo, name='criar_titulo'),
    path('titulos/<int:titulo_id>/', views.detalhe_titulo, name='detalhe_titulo'),
    path('titulos/<int:titulo_id>/editar/', views.editar_titulo, name='editar_titulo'),
    
    # Contas a Pagar
    path('contas-pagar/', views.listar_parcelas, {'tipo': 'PAGAR'}, name='contas_pagar'),
    
    # Contas a Receber
    path('contas-receber/', views.listar_parcelas, {'tipo': 'RECEBER'}, name='contas_receber'),
    
    # Parcelas
    path('parcelas/', views.listar_parcelas, name='listar_parcelas'),
    path('parcelas/<int:parcela_id>/baixar/', views.baixar_parcela, name='baixar_parcela'),
    
    # Baixas
    path('baixas/<int:baixa_id>/estornar/', views.estornar_baixa, name='estornar_baixa'),
    
    # Contas Financeiras
    path('contas-financeiras/', views.listar_contas_financeiras, name='listar_contas_financeiras'),
    path('contas-financeiras/criar/', views.criar_conta_financeira, name='criar_conta_financeira'),
    path('contas-financeiras/<int:pk>/editar/', views.editar_conta_financeira, name='editar_conta_financeira'),
    path('contas-financeiras/<int:pk>/excluir/', views.excluir_conta_financeira, name='excluir_conta_financeira'),
    path('contas-financeiras/<int:conta_id>/extrato/', views.extrato_conta, name='extrato_conta'),
    path('contas-financeiras/<int:conta_id>/extrato/pdf/', views.extrato_conta_pdf, name='extrato_conta_pdf'),
    path('contas-financeiras/transferencia/', views.criar_transferencia, name='criar_transferencia'),
    path('contas-financeiras/transferencias/', views.listar_transferencias, name='listar_transferencias'),
    path('contas-financeiras/transferencia/<int:transferencia_id>/estornar/', views.estornar_transferencia, name='estornar_transferencia'),
    
    # Bancos
    path('bancos/', views.listar_bancos, name='listar_bancos'),
    path('bancos/criar/', views.criar_banco, name='criar_banco'),
    path('bancos/<int:banco_id>/editar/', views.editar_banco, name='editar_banco'),
    path('bancos/<int:banco_id>/excluir/', views.excluir_banco, name='excluir_banco'),
    
    # Centros de Custo
    path('centros-custo/', views.listar_centros_custo, name='listar_centros_custo'),
    path('centros-custo/criar/', views.criar_centro_custo, name='criar_centro_custo'),
    path('centros-custo/<int:centro_id>/editar/', views.editar_centro_custo, name='editar_centro_custo'),
    path('centros-custo/<int:centro_id>/excluir/', views.excluir_centro_custo, name='excluir_centro_custo'),
    
    # Formas de Pagamento
    path('formas-pagamento/', views.listar_formas_pagamento, name='listar_formas_pagamento'),
    path('formas-pagamento/criar/', views.criar_forma_pagamento, name='criar_forma_pagamento'),
    path('formas-pagamento/<int:forma_id>/editar/', views.editar_forma_pagamento, name='editar_forma_pagamento'),
    path('formas-pagamento/<int:forma_id>/excluir/', views.excluir_forma_pagamento, name='excluir_forma_pagamento'),
    
    # Regimes Tributários
    path('regimes-tributarios/', views.listar_regimes_tributarios, name='listar_regimes_tributarios'),
    path('regimes-tributarios/criar/', views.criar_regime_tributario, name='criar_regime_tributario'),
    path('regimes-tributarios/<int:regime_id>/editar/', views.editar_regime_tributario, name='editar_regime_tributario'),
    path('regimes-tributarios/<int:regime_id>/excluir/', views.excluir_regime_tributario, name='excluir_regime_tributario'),
    
    # Categorias de Custo
    path('categorias-custo/', views.listar_categorias_custo, name='listar_categorias_custo'),
    path('categorias-custo/criar/', views.criar_categoria_custo, name='criar_categoria_custo'),
    path('categorias-custo/<int:categoria_id>/editar/', views.editar_categoria_custo, name='editar_categoria_custo'),
    path('categorias-custo/<int:categoria_id>/excluir/', views.excluir_categoria_custo, name='excluir_categoria_custo'),
    
    # Plano de Contas
    path('plano-contas/', views.listar_plano_contas, name='listar_plano_contas'),
    path('plano-contas/criar/', views.criar_plano_conta, name='criar_plano_conta'),
    path('plano-contas/<int:conta_id>/editar/', views.editar_plano_conta, name='editar_plano_conta'),
    path('plano-contas/<int:conta_id>/excluir/', views.excluir_plano_conta, name='excluir_plano_conta'),
    
    # Calendário
    path('calendario/', views_relatorios.calendario_financeiro, name='calendario'),
    path('calendario/pdf/', relatorios_pdf.calendario_financeiro_pdf, name='calendario_pdf'),
    
    # Relatórios Operacionais
    path('relatorios/contas-pagar/', views_relatorios.relatorio_contas_pagar, name='relatorio_contas_pagar'),
    path('relatorios/contas-receber/', views_relatorios.relatorio_contas_receber, name='relatorio_contas_receber'),
    
    # Relatórios Gerenciais
    path('relatorios/fluxo-caixa/', views_relatorios.relatorio_fluxo_caixa, name='relatorio_fluxo_caixa'),
    path('relatorios/fluxo-caixa/pdf/', relatorios_pdf.relatorio_fluxo_caixa_pdf, name='relatorio_fluxo_caixa_pdf'),
    path('relatorios/dre/', views_relatorios.relatorio_dre, name='relatorio_dre'),
    path('relatorios/dre/pdf/', relatorios_pdf.relatorio_dre_pdf, name='relatorio_dre_pdf'),
    path('relatorios/ponto-equilibrio/', views_relatorios.relatorio_ponto_equilibrio, name='relatorio_ponto_equilibrio'),
    path('relatorios/ponto-equilibrio/pdf/', relatorios_pdf.relatorio_ponto_equilibrio_pdf, name='relatorio_ponto_equilibrio_pdf'),
    path('relatorios/resultado-centro-custo/', views_relatorios.relatorio_resultado_centro_custo, name='relatorio_resultado_centro_custo'),
    
    # ============================================
    # RÉGUA DE COBRANÇA
    # ============================================
    path('cobranca/', views_cobranca.painel_cobranca, name='painel_cobranca'),
    path('cobranca/reguas/', views_cobranca.listar_reguas, name='listar_reguas'),
    path('cobranca/reguas/criar/', views_cobranca.criar_regua, name='criar_regua'),
    path('cobranca/reguas/<int:regua_id>/editar/', views_cobranca.editar_regua, name='editar_regua'),
    path('cobranca/disparar/<int:parcela_id>/', views_cobranca.disparar_cobranca_manual, name='disparar_cobranca'),
    path('cobranca/reenviar/<int:parcela_id>/', views_cobranca.reenviar_cobranca_manual, name='reenviar_cobranca'),
    path('cobranca/ativar-regua/<int:parcela_id>/', views_cobranca.ativar_regua_parcela, name='ativar_regua_parcela'),
    path('cobranca/desativar-regua/<int:parcela_id>/', views_cobranca.desativar_regua_parcela, name='desativar_regua_parcela'),
    path('cobranca/pausar/<int:parcela_id>/', views_cobranca.pausar_regua, name='pausar_regua'),
    path('cobranca/retomar/<int:parcela_id>/', views_cobranca.retomar_regua, name='retomar_regua'),
    path('cobranca/promessa/<int:parcela_id>/', views_cobranca.marcar_promessa, name='marcar_promessa'),
    path('cobranca/negociacao/<int:parcela_id>/', views_cobranca.marcar_negociacao, name='marcar_negociacao'),
    path('cobranca/normal/<int:parcela_id>/', views_cobranca.marcar_normal, name='marcar_normal'),
    path('cobranca/reprocessar-falhas/', views_cobranca.reprocessar_falhas, name='reprocessar_falhas'),
    path('cobranca/historico/<int:parcela_id>/', views_cobranca.historico_cobranca, name='historico_cobranca'),
]
