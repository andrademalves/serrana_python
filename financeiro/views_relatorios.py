"""
Views de Relatórios e Calendário Financeiro
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce, TruncMonth
from datetime import date, timedelta
from decimal import Decimal
import calendar

from .models import ParcelaFinanceira, BaixaFinanceira, TituloFinanceiro
from .services.indicadores import IndicadoresSaudeFinanceira
from .services.ponto_equilibrio import AnalisePontoEquilibrio
from .services.calculadora import ProjecaoFluxoCaixa

# Nomes dos meses em português
MESES_PT = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro'
}


# =========================================
# CALENDÁRIO FINANCEIRO
# =========================================

@login_required
def calendario_financeiro(request):
    """
    Calendário mensal com vencimentos de contas a pagar e receber
    """
    # Pega mês/ano dos parâmetros ou usa atual
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    
    # Valida mês/ano
    if mes < 1:
        mes = 12
        ano -= 1
    elif mes > 12:
        mes = 1
        ano += 1
    
    # Primeiro e último dia do mês
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia_num = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_num)
    
    # Busca parcelas do mês
    parcelas_mes = ParcelaFinanceira.objects.filter(
        titulo__empresa=request.empresa,
        data_vencimento__gte=primeiro_dia,
        data_vencimento__lte=ultimo_dia,
        status__in=['ABERTO', 'PARCIAL', 'QUITADO']
    ).select_related('titulo', 'titulo__pessoa').order_by('data_vencimento')
    
    # Organiza por dia
    eventos_por_dia = {}
    for dia in range(1, ultimo_dia_num + 1):
        eventos_por_dia[dia] = {
            'a_pagar': [],
            'a_receber': [],
            'total_pagar': Decimal('0.00'),
            'total_receber': Decimal('0.00'),
        }
    
    for parcela in parcelas_mes:
        dia = parcela.data_vencimento.day
        
        evento = {
            'parcela': parcela,
            'titulo': parcela.titulo,
            'pessoa': parcela.titulo.pessoa,
            'valor': parcela.saldo_aberto if parcela.status != 'QUITADO' else parcela.valor_original,
            'status': parcela.status,
            'vencida': parcela.esta_vencida()
        }
        
        if parcela.titulo.tipo == 'PAGAR':
            eventos_por_dia[dia]['a_pagar'].append(evento)
            if parcela.status != 'QUITADO':
                eventos_por_dia[dia]['total_pagar'] += parcela.saldo_aberto
        else:
            eventos_por_dia[dia]['a_receber'].append(evento)
            if parcela.status != 'QUITADO':
                eventos_por_dia[dia]['total_receber'] += parcela.saldo_aberto
    
    # Navegação de meses
    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    
    mes_seguinte = mes + 1 if mes < 12 else 1
    ano_seguinte = ano if mes < 12 else ano + 1
    
    # Dias da semana para cabeçalho
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    
    # Monta calendário (semanas) e adiciona eventos
    cal = calendar.monthcalendar(ano, mes)
    
    # Converte eventos_por_dia para lista para facilitar acesso no template
    calendario_com_eventos = []
    for semana in cal:
        semana_eventos = []
        for dia in semana:
            if dia == 0:
                semana_eventos.append({'dia': 0, 'eventos': None})
            else:
                semana_eventos.append({
                    'dia': dia,
                    'eventos': eventos_por_dia[dia]
                })
        calendario_com_eventos.append(semana_eventos)
    
    context = {
        'mes': mes,
        'ano': ano,
        'mes_nome': MESES_PT[mes],
        'eventos_por_dia': eventos_por_dia,
        'calendario': cal,
        'calendario_com_eventos': calendario_com_eventos,
        'dias_semana': dias_semana,
        'mes_anterior': mes_anterior,
        'ano_anterior': ano_anterior,
        'mes_seguinte': mes_seguinte,
        'ano_seguinte': ano_seguinte,
        'hoje': date.today(),
    }
    
    return render(request, 'financeiro/calendario.html', context)


# =========================================
# RELATÓRIOS OPERACIONAIS
# =========================================

@login_required
def relatorio_contas_pagar(request):
    """Relatório de contas a pagar com filtros"""
    status = request.GET.get('status', 'ABERTAS')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    fornecedor_id = request.GET.get('fornecedor')
    categoria_id = request.GET.get('categoria')
    centro_custo_id = request.GET.get('centro_custo')
    
    parcelas = ParcelaFinanceira.objects.filter(
        titulo__empresa=request.empresa,
        titulo__tipo='PAGAR'
    ).select_related('titulo', 'titulo__pessoa', 'titulo__plano_conta', 'titulo__centro_custo')
    
    # Filtros
    if status == 'ABERTAS':
        parcelas = parcelas.filter(status__in=['ABERTO', 'PARCIAL'])
    elif status == 'ATRASADAS':
        parcelas = parcelas.filter(status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=date.today())
    elif status == 'QUITADAS':
        parcelas = parcelas.filter(status='QUITADO')
    
    if data_inicio:
        parcelas = parcelas.filter(data_vencimento__gte=data_inicio)
    if data_fim:
        parcelas = parcelas.filter(data_vencimento__lte=data_fim)
    if fornecedor_id:
        parcelas = parcelas.filter(titulo__pessoa_id=fornecedor_id)
    if categoria_id:
        parcelas = parcelas.filter(titulo__plano_conta_id=categoria_id)
    if centro_custo_id:
        parcelas = parcelas.filter(titulo__centro_custo_id=centro_custo_id)
    
    # Totalizações
    total_original = parcelas.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')
    total_aberto = parcelas.aggregate(Sum('saldo_aberto'))['saldo_aberto__sum'] or Decimal('0.00')
    
    # Dados para filtros
    from cadastros.models import Pessoa
    fornecedores = Pessoa.objects.filter(ativo=True, tipo='FORNECEDOR', empresa=request.empresa).order_by('nome')
    categorias = PlanoConta.objects.filter(ativo=True, empresa=request.empresa).order_by('codigo')
    from .models import CentroCusto
    centros_custo = CentroCusto.objects.filter(ativo=True, empresa=request.empresa).order_by('codigo')
    
    context = {
        'parcelas': parcelas.order_by('data_vencimento'),
        'total_original': total_original,
        'total_aberto': total_aberto,
        'fornecedores': fornecedores,
        'categorias': categorias,
        'centros_custo': centros_custo,
        'filtros': {
            'status': status,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'fornecedor_id': fornecedor_id,
            'categoria_id': categoria_id,
            'centro_custo_id': centro_custo_id,
        }
    }
    
    return render(request, 'financeiro/relatorio_contas_pagar.html', context)


@login_required
def relatorio_contas_receber(request):
    """Relatório de contas a receber com filtros"""
    status = request.GET.get('status', 'ABERTAS')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    cliente_id = request.GET.get('cliente')
    
    parcelas = ParcelaFinanceira.objects.filter(
        titulo__empresa=request.empresa,
        titulo__tipo='RECEBER'
    ).select_related('titulo', 'titulo__pessoa')
    
    # Filtros
    if status == 'ABERTAS':
        parcelas = parcelas.filter(status__in=['ABERTO', 'PARCIAL'])
    elif status == 'ATRASADAS':
        parcelas = parcelas.filter(status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=date.today())
    elif status == 'QUITADAS':
        parcelas = parcelas.filter(status='QUITADO')
    
    if data_inicio:
        parcelas = parcelas.filter(data_vencimento__gte=data_inicio)
    if data_fim:
        parcelas = parcelas.filter(data_vencimento__lte=data_fim)
    if cliente_id:
        parcelas = parcelas.filter(titulo__pessoa_id=cliente_id)
    
    # Totalizações
    total_original = parcelas.aggregate(Sum('valor_original'))['valor_original__sum'] or Decimal('0.00')
    total_aberto = parcelas.aggregate(Sum('saldo_aberto'))['saldo_aberto__sum'] or Decimal('0.00')
    
    # Dados para filtros
    from cadastros.models import Pessoa
    clientes = Pessoa.objects.filter(empresa=request.empresa, ativo=True, tipo='CLIENTE').order_by('nome')
    
    context = {
        'parcelas': parcelas.order_by('data_vencimento'),
        'total_original': total_original,
        'total_aberto': total_aberto,
        'clientes': clientes,
        'filtros': {
            'status': status,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'cliente_id': cliente_id,
        }
    }
    
    return render(request, 'financeiro/relatorio_contas_receber.html', context)


# =========================================
# RELATÓRIOS GERENCIAIS
# =========================================

@login_required
def relatorio_fluxo_caixa(request):
    """Fluxo de caixa previsto x realizado"""
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    
    # Dados do mês
    dados_mes = ProjecaoFluxoCaixa.fluxo_mensal(ano, mes, empresa=request.empresa)
    
    # Meses para navegação (últimos 6 + próximos 6)
    meses_disponiveis = []
    for i in range(-6, 7):
        data_ref = date.today() + timedelta(days=i*30)
        meses_disponiveis.append({
            'mes': data_ref.month,
            'ano': data_ref.year,
            'nome': f'{MESES_PT[data_ref.month]}/{data_ref.year}'
        })
    
    context = {
        'dados': dados_mes,
        'mes': mes,
        'ano': ano,
        'mes_nome': MESES_PT[mes],
        'meses_disponiveis': meses_disponiveis,
    }
    
    return render(request, 'financeiro/relatorio_fluxo_caixa.html', context)


@login_required
def relatorio_dre(request):
    """DRE simplificada por centro de custo"""
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    
    # Receitas por centro de custo
    receitas = BaixaFinanceira.objects.filter(
        parcela__titulo__tipo='RECEBER',
        parcela__titulo__empresa=request.empresa,
        data_pagamento__gte=primeiro_dia,
        data_pagamento__lte=ultimo_dia,
        estornado=False
    ).values('parcela__titulo__centro_custo__nome').annotate(
        total=Sum('valor_liquido')
    ).order_by('-total')
    
    # Despesas por centro de custo
    despesas = BaixaFinanceira.objects.filter(
        parcela__titulo__tipo='PAGAR',
        parcela__titulo__empresa=request.empresa,
        data_pagamento__gte=primeiro_dia,
        data_pagamento__lte=ultimo_dia,
        estornado=False
    ).values('parcela__titulo__centro_custo__nome').annotate(
        total=Sum('valor_liquido')
    ).order_by('-total')
    
    total_receitas = sum([r['total'] for r in receitas]) if receitas else Decimal('0.00')
    total_despesas = sum([d['total'] for d in despesas]) if despesas else Decimal('0.00')
    resultado = total_receitas - total_despesas
    
    context = {
        'mes': mes,
        'ano': ano,
        'mes_nome': MESES_PT[mes],
        'receitas': receitas,
        'despesas': despesas,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'resultado': resultado,
        'margem': (resultado / total_receitas * 100) if total_receitas > 0 else Decimal('0.00')
    }
    
    return render(request, 'financeiro/relatorio_dre.html', context)


@login_required
def relatorio_ponto_equilibrio(request):
    """Análise de ponto de equilíbrio"""
    periodo_meses = int(request.GET.get('periodo', 3))
    
    dados = AnalisePontoEquilibrio.calcular_break_even(periodo_meses, empresa=request.empresa)
    
    context = {
        'dados': dados,
        'periodo_meses': periodo_meses,
    }
    
    return render(request, 'financeiro/relatorio_ponto_equilibrio.html', context)


@login_required
def relatorio_resultado_centro_custo(request):
    """Resultado por centro de custo/obra"""
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
    
    # Agrupa por centro de custo
    from .models import CentroCusto
    centros = CentroCusto.objects.filter(ativo=True, empresa=request.empresa)
    
    resultado_por_centro = []
    
    for centro in centros:
        receitas = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='RECEBER',
            parcela__titulo__centro_custo=centro,
            data_pagamento__gte=primeiro_dia,
            data_pagamento__lte=ultimo_dia,
            estornado=False
        ).aggregate(total=Coalesce(Sum('valor_liquido'), Decimal('0.00')))['total']
        
        despesas = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='PAGAR',
            parcela__titulo__centro_custo=centro,
            data_pagamento__gte=primeiro_dia,
            data_pagamento__lte=ultimo_dia,
            estornado=False
        ).aggregate(total=Coalesce(Sum('valor_liquido'), Decimal('0.00')))['total']
        
        resultado = receitas - despesas
        
        resultado_por_centro.append({
            'centro': centro,
            'receitas': receitas,
            'despesas': despesas,
            'resultado': resultado,
            'margem': (resultado / receitas * 100) if receitas > 0 else Decimal('0.00')
        })
    
    # Ordena por resultado
    resultado_por_centro.sort(key=lambda x: x['resultado'], reverse=True)
    
    context = {
        'mes': mes,
        'ano': ano,
        'mes_nome': MESES_PT[mes],
        'resultados': resultado_por_centro,
    }
    
    return render(request, 'financeiro/relatorio_resultado_centro_custo.html', context)
