"""
VIEWS - DASHBOARD BI
====================

Views para renderização do dashboard e endpoints AJAX.

Autor: Sistema BI Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator

# Reportes
from django.template.loader import render_to_string
import json

# Services
from .services_kpi import (
    EstoqueKPIService,
    ObrasKPIService,
    FinanceiroKPIService,
    DashboardService
)


# ==============================================================================
# 1. DASHBOARD PRINCIPAL
# ==============================================================================

@login_required
def dashboard_principal(request):
    """
    View principal do dashboard BI.
    Renderiza a página com KPIs e gráficos.
    """
    # Parâmetros de filtro
    periodo = request.GET.get('periodo', '30')  # dias
    local_id = request.GET.get('local')
    
    # Coletar KPIs principais
    kpis = DashboardService.get_kpis_principais()
    alertas = DashboardService.get_alertas_criticos()
    
    context = {
        'kpis': kpis,
        'alertas': alertas,
        'periodo_selecionado': periodo,
        'local_selecionado': local_id,
        'data_atualizacao': timezone.now(),
        'titulo_pagina': 'Dashboard Gerencial'
    }
    
    return render(request, 'dashboard/principal.html', context)


# ==============================================================================
# 2. ENDPOINTS AJAX - ESTOQUE
# ==============================================================================

@login_required
@require_http_methods(["GET"])
def api_estoque_kpis(request):
    """
    API: Retorna KPIs de estoque em JSON.
    """
    local_id = request.GET.get('local')
    
    data = {
        'valor_total': EstoqueKPIService.get_valor_total_estoque(local_id),
        'itens_criticos': EstoqueKPIService.get_itens_abaixo_minimo(),
        'giro': EstoqueKPIService.get_giro_estoque(),
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def api_curva_abc(request):
    """
    API: Retorna dados para gráfico de Pareto (Curva ABC).
    """
    limite = int(request.GET.get('limite', 50))
    
    curva_abc = EstoqueKPIService.get_curva_abc(limite=limite)
    
    # Formatar para Chart.js
    labels = [f"{p['produto__codigo']} - {p['produto__descricao'][:30]}" for p in curva_abc]
    valores = [float(p['valor_total']) for p in curva_abc]
    percentuais_acumulados = [float(p['percentual_acumulado']) for p in curva_abc]
    classes = [p['classe_abc'] for p in curva_abc]
    
    chartjs_data = {
        'labels': labels,
        'datasets': [
            {
                'type': 'bar',
                'label': 'Valor Imobilizado (R$)',
                'data': valores,
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.7)' if c == 'A' else
                    'rgba(255, 206, 86, 0.7)' if c == 'B' else
                    'rgba(75, 192, 192, 0.7)'
                    for c in classes
                ],
                'borderColor': [
                    'rgb(255, 99, 132)' if c == 'A' else
                    'rgb(255, 206, 86)' if c == 'B' else
                    'rgb(75, 192, 192)'
                    for c in classes
                ],
                'borderWidth': 1,
                'yAxisID': 'y'
            },
            {
                'type': 'line',
                'label': '% Acumulado',
                'data': percentuais_acumulados,
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                'borderWidth': 2,
                'fill': True,
                'yAxisID': 'y1',
                'tension': 0.4
            }
        ]
    }
    
    return JsonResponse(chartjs_data)


@login_required
@require_http_methods(["GET"])
def api_consumo_medio(request):
    """
    API: Retorna consumo médio mensal.
    """
    limite = int(request.GET.get('limite', 20))
    
    consumo = EstoqueKPIService.get_consumo_medio_mensal(limite=limite)
    
    # Formatar para DataTables
    data = {
        'data': [
            {
                'produto': f"{c['codigo']} - {c['descricao']}",
                'consumo_medio': float(c['consumo_medio_mensal']),
                'desvio_padrao': float(c['desvio_padrao']),
                'tendencia': c['tendencia'],
                'meses': c['meses_com_consumo']
            }
            for c in consumo
        ]
    }
    
    return JsonResponse(data)


# ==============================================================================
# 3. ENDPOINTS AJAX - OBRAS
# ==============================================================================

@login_required
@require_http_methods(["GET"])
def api_obras_status(request):
    """
    API: Retorna distribuição de obras por status.
    Para gráfico de pizza.
    """
    status = ObrasKPIService.get_status_obras()
    
    # Formatar para Chart.js (pie chart)
    chartjs_data = {
        'labels': [],
        'datasets': [{
            'label': 'Obras por Status',
            'data': [],
            'backgroundColor': [
                'rgba(255, 206, 86, 0.7)',   # Orçamento - Amarelo
                'rgba(54, 162, 235, 0.7)',    # Em Execução - Azul
                'rgba(75, 192, 192, 0.7)',    # Concluída - Verde
            ],
            'borderColor': [
                'rgb(255, 206, 86)',
                'rgb(54, 162, 235)',
                'rgb(75, 192, 192)',
            ],
            'borderWidth': 1
        }]
    }
    
    for key, value in status.items():
        if key != 'total' and key != 'data_atualizacao':
            chartjs_data['labels'].append(key.replace('_', ' ').title())
            chartjs_data['datasets'][0]['data'].append(value['quantidade'])
    
    return JsonResponse(chartjs_data)


@login_required
@require_http_methods(["GET"])
def api_obras_analise_financeira(request):
    """
    API: Retorna análise financeira de obras.
    Para tabela DataTables com lucro competência x caixa.
    """
    obra_id = request.GET.get('obra_id')
    
    obras = ObrasKPIService.get_analise_financeira_obras(obra_id)
    
    data = {
        'data': [
            {
                'codigo': o['codigo'],
                'nome': o['nome'],
                'valor_contrato': float(o['valor_contrato']),
                'custo_realizado': float(o['custo_realizado']),
                'lucro_competencia': float(o['lucro_competencia']),
                'lucro_caixa': float(o['lucro_caixa']),
                'margem_competencia': (o['lucro_competencia'] / o['valor_contrato'] * 100) if o['valor_contrato'] > 0 else 0,
                'margem_caixa': (o['lucro_caixa'] / o['valor_contrato'] * 100) if o['valor_contrato'] > 0 else 0
            }
            for o in obras
        ]
    }
    
    return JsonResponse(data)


# ==============================================================================
# 4. ENDPOINTS AJAX - FINANCEIRO
# ==============================================================================

@login_required
@require_http_methods(["GET"])
def api_fluxo_caixa(request):
    """
    API: Retorna fluxo de caixa projetado.
    Para gráfico de linha (Chart.js).
    """
    dias = int(request.GET.get('dias', 90))
    
    fluxo = FinanceiroKPIService.get_fluxo_caixa_projetado(dias=dias)
    
    # Formatar para Chart.js
    chartjs_data = {
        'labels': [f['data'].strftime('%d/%m') for f in fluxo],
        'datasets': [
            {
                'label': 'Entradas (R$)',
                'data': [float(f['entradas']) for f in fluxo],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'borderWidth': 2,
                'fill': True
            },
            {
                'label': 'Saídas (R$)',
                'data': [float(f['saidas']) for f in fluxo],
                'borderColor': 'rgb(255, 99, 132)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'borderWidth': 2,
                'fill': True
            },
            {
                'label': 'Saldo Acumulado (R$)',
                'data': [float(f['saldo_acumulado']) for f in fluxo],
                'borderColor': 'rgb(54, 162, 235)',
                'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                'borderWidth': 3,
                'fill': False,
                'tension': 0.4
            }
        ]
    }
    
    return JsonResponse(chartjs_data)


@login_required
@require_http_methods(["GET"])
def api_dre_mensal(request):
    """
    API: Retorna DRE mensal.
    Para gráfico de barras agrupadas.
    """
    meses = int(request.GET.get('meses', 12))
    
    dre = FinanceiroKPIService.get_resultado_mensal(meses=meses)
    
    # Formatar para Chart.js
    chartjs_data = {
        'labels': [d['mes'].strftime('%b/%Y') for d in dre],
        'datasets': [
            {
                'label': 'Receita (R$)',
                'data': [float(d['receita']) for d in dre],
                'backgroundColor': 'rgba(75, 192, 192, 0.7)',
                'borderColor': 'rgb(75, 192, 192)',
                'borderWidth': 1
            },
            {
                'label': 'Despesa (R$)',
                'data': [float(d['despesa']) for d in dre],
                'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                'borderColor': 'rgb(255, 99, 132)',
                'borderWidth': 1
            },
            {
                'label': 'Lucro (R$)',
                'data': [float(d['lucro']) for d in dre],
                'backgroundColor': 'rgba(54, 162, 235, 0.7)',
                'borderColor': 'rgb(54, 162, 235)',
                'borderWidth': 1
            }
        ]
    }
    
    return JsonResponse(chartjs_data)


@login_required
@require_http_methods(["GET"])
def api_contas_vencidas(request):
    """
    API: Retorna títulos vencidos a receber.
    Para tabela DataTables.
    """
    contas = FinanceiroKPIService.get_contas_pagar_receber()
    
    # Aqui você buscaria os títulos detalhados
    # Por enquanto, retornar estrutura
    
    data = {
        'data': [],
        'resumo': contas
    }
    
    return JsonResponse(data)


# ==============================================================================
# 5. DASHBOARDS ESPECÍFICOS
# ==============================================================================

@login_required
def dashboard_estoque(request):
    """
    Dashboard detalhado de estoque.
    """
    local_id = request.GET.get('local')
    
    context = {
        'valor_total': EstoqueKPIService.get_valor_total_estoque(local_id),
        'itens_criticos': EstoqueKPIService.get_itens_abaixo_minimo(),
        'giro': EstoqueKPIService.get_giro_estoque(),
        'local_selecionado': local_id,
        'titulo_pagina': 'Dashboard - Estoque'
    }
    
    return render(request, 'dashboard/estoque_detalhado.html', context)


@login_required
def dashboard_obras(request):
    """
    Dashboard detalhado de obras.
    """
    context = {
        'status': ObrasKPIService.get_status_obras(),
        'titulo_pagina': 'Dashboard - Obras'
    }
    
    return render(request, 'dashboard/obras_detalhado.html', context)


@login_required
def dashboard_financeiro(request):
    """
    Dashboard detalhado financeiro.
    """
    context = {
        'caixa': FinanceiroKPIService.get_saldo_caixa(),
        'contas': FinanceiroKPIService.get_contas_pagar_receber(),
        'inadimplencia': FinanceiroKPIService.get_inadimplencia(),
        'titulo_pagina': 'Dashboard - Financeiro'
    }
    
    return render(request, 'dashboard/financeiro_detalhado.html', context)


# ==============================================================================
# 6. EXPORTAÇÕES
# ==============================================================================

@login_required
def exportar_dashboard_pdf(request):
    """
    Exporta dashboard completo em PDF.
    """
    # Implementar com ReportLab ou WeasyPrint
    
    from io import BytesIO
    from django.http import FileResponse
    
    # Coletar dados
    kpis = DashboardService.get_kpis_principais()
    
    # Gerar PDF (simplificado)
    buffer = BytesIO()
    
    # IMPLEMENTAR: Geração do PDF com ReportLab
    # from reportlab.pdfgen import canvas
    # p = canvas.Canvas(buffer)
    # p.drawString(100, 750, "Dashboard Gerencial")
    # ...
    # p.save()
    
    buffer.seek(0)
    
    filename = f'dashboard_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename)


@login_required
def exportar_dashboard_excel(request):
    """
    Exporta dashboard completo em Excel.
    """
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    from django.http import HttpResponse
    
    # Coletar dados
    kpis = DashboardService.get_kpis_principais()
    
    # Criar workbook
    wb = Workbook()
    
    # Aba 1: KPIs Principais
    ws_kpis = wb.active
    ws_kpis.title = "KPIs Principais"
    ws_kpis['A1'] = 'Dashboard Gerencial'
    ws_kpis['A2'] = f"Gerado em: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
    
    # Adicionar KPIs
    row = 4
    ws_kpis[f'A{row}'] = 'ESTOQUE'
    row += 1
    ws_kpis[f'A{row}'] = 'Valor Total'
    ws_kpis[f'B{row}'] = float(kpis['estoque']['valor_total']['valor_atual'])
    
    # ... adicionar mais dados
    
    # Aba 2: Curva ABC
    ws_abc = wb.create_sheet("Curva ABC")
    curva_abc = EstoqueKPIService.get_curva_abc()
    
    headers = ['Código', 'Descrição', 'Quantidade', 'Custo Médio', 'Valor Total', '% Acumulado', 'Classe']
    for col, header in enumerate(headers, 1):
        ws_abc.cell(1, col, header)
    
    for row, produto in enumerate(curva_abc, 2):
        ws_abc.cell(row, 1, produto['produto__codigo'])
        ws_abc.cell(row, 2, produto['produto__descricao'])
        ws_abc.cell(row, 3, float(produto['quantidade_total']))
        ws_abc.cell(row, 4, float(produto['custo_medio']))
        ws_abc.cell(row, 5, float(produto['valor_total']))
        ws_abc.cell(row, 6, float(produto['percentual_acumulado']))
        ws_abc.cell(row, 7, produto['classe_abc'])
    
    # Salvar
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'dashboard_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


# ==============================================================================
# 7. UTILITÁRIOS
# ==============================================================================

@login_required
@require_http_methods(["POST"])
def atualizar_cache_dashboard(request):
    """
    Força atualização do cache do dashboard.
    Usar após alterações significativas nos dados.
    """
    DashboardService.limpar_cache_dashboard()
    
    return JsonResponse({
        'success': True,
        'message': 'Cache atualizado com sucesso',
        'timestamp': timezone.now().isoformat()
    })


# ==============================================================================
# 8. VIEWS DETALHADAS
# ==============================================================================

@login_required
def estoque_detalhado(request):
    """
    Dashboard detalhado de estoque com análise ABC, movimentações e previsões.
    """
    empresa = request.user.empresa_ativa
    if not empresa:
        messages.warning(request, 'Você precisa estar em uma empresa para acessar esta página.')
        return redirect('dashboard:principal')
    
    context = {
        'empresa': empresa,
        'titulo': 'Estoque Detalhado',
    }
    return render(request, 'dashboard/estoque_detalhado.html', context)


@login_required
def obras_detalhado(request):
    """
    Dashboard detalhado de obras/projetos com análise financeira e orçamentária.
    """
    empresa = request.user.empresa_ativa
    if not empresa:
        messages.warning(request, 'Você precisa estar em uma empresa para acessar esta página.')
        return redirect('dashboard:principal')
    
    context = {
        'empresa': empresa,
        'titulo': 'Obras e Projetos Detalhado',
    }
    return render(request, 'dashboard/obras_detalhado.html', context)


@login_required
def financeiro_detalhado(request):
    """
    Dashboard detalhado financeiro com fluxo de caixa, DRE e análise de inadimplência.
    """
    empresa = request.user.empresa_ativa
    if not empresa:
        messages.warning(request, 'Você precisa estar em uma empresa para acessar esta página.')
        return redirect('dashboard:principal')
    
    context = {
        'empresa': empresa,
        'titulo': 'Financeiro Detalhado',
    }
    return render(request, 'dashboard/financeiro_detalhado.html', context)
