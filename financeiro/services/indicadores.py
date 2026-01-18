"""
Serviço de Indicadores de Saúde Financeira
KPIs e métricas gerenciais
"""
from django.db.models import Sum, Avg, Q, F, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date, timedelta


class IndicadoresSaudeFinanceira:
    """Calcula indicadores de saúde financeira"""
    
    @staticmethod
    def inadimplencia(empresa=None):
        """
        Taxa de inadimplência
        (recebíveis vencidos / recebíveis totais) * 100
        """
        from financeiro.models import ParcelaFinanceira
        
        hoje = date.today()
        
        # Filtro base
        filtro_base = {'titulo__tipo': 'RECEBER', 'status__in': ['ABERTO', 'PARCIAL']}
        if empresa:
            filtro_base['titulo__empresa'] = empresa
        
        # Total a receber em aberto
        total_receber = ParcelaFinanceira.objects.filter(
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        # Total vencido
        vencido = ParcelaFinanceira.objects.filter(
            **filtro_base,
            data_vencimento__lt=hoje
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        if total_receber > 0:
            taxa = (vencido / total_receber) * 100
        else:
            taxa = Decimal('0.00')
        
        return {
            'total_receber': total_receber,
            'total_vencido': vencido,
            'taxa_inadimplencia': round(taxa, 2),
            'status': 'CRITICO' if taxa > 10 else 'ALERTA' if taxa > 5 else 'OK'
        }
    
    @staticmethod
    def liquidez_curto_prazo(dias=30, empresa=None):
        """
        Índice de liquidez
        (entradas previstas próximos N dias / saídas previstas próximos N dias)
        """
        from financeiro.models import ParcelaFinanceira
        
        hoje = date.today()
        data_fim = hoje + timedelta(days=dias)
        
        # Filtro base
        filtro_base = {'status__in': ['ABERTO', 'PARCIAL'], 'data_vencimento__gte': hoje, 'data_vencimento__lte': data_fim}
        if empresa:
            filtro_base['titulo__empresa'] = empresa
        
        entradas = ParcelaFinanceira.objects.filter(
            titulo__tipo='RECEBER',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        saidas = ParcelaFinanceira.objects.filter(
            titulo__tipo='PAGAR',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        if saidas > 0:
            indice = entradas / saidas
        else:
            # Se não há saídas, considera liquidez excelente se há entradas, ou neutra se não há movimentação
            indice = Decimal('0.00') if entradas == 0 else Decimal('99.99')
        
        return {
            'periodo_dias': dias,
            'entradas_previstas': entradas,
            'saidas_previstas': saidas,
            'indice_liquidez': round(indice, 2),
            'status': 'OK' if indice >= 1.2 else 'ALERTA' if indice >= 1.0 else 'CRITICO'
        }
    
    @staticmethod
    def prazo_medio_recebimento(empresa=None):
        """
        PMR - Prazo Médio de Recebimento
        Média de dias entre emissão e recebimento
        """
        from financeiro.models import BaixaFinanceira
        
        # Últimos 90 dias
        data_inicio = date.today() - timedelta(days=90)
        
        filtro = {
            'parcela__titulo__tipo': 'RECEBER',
            'data_pagamento__gte': data_inicio,
            'estornado': False
        }
        if empresa:
            filtro['parcela__titulo__empresa'] = empresa
        
        baixas = BaixaFinanceira.objects.filter(**filtro).select_related('parcela__titulo')
        
        if not baixas.exists():
            return {
                'prazo_medio_dias': 0,
                'total_baixas': 0,
                'periodo': '90 dias'
            }
        
        total_dias = 0
        count = 0
        
        for baixa in baixas:
            dias = (baixa.data_pagamento - baixa.parcela.titulo.data_emissao).days
            total_dias += dias
            count += 1
        
        pmr = total_dias / count if count > 0 else 0
        
        return {
            'prazo_medio_dias': round(pmr, 1),
            'total_baixas': count,
            'periodo': '90 dias',
            'status': 'OK' if pmr <= 30 else 'ALERTA' if pmr <= 45 else 'CRITICO'
        }
    
    @staticmethod
    def prazo_medio_pagamento(empresa=None):
        """
        PMP - Prazo Médio de Pagamento
        Média de dias entre emissão e pagamento
        """
        from financeiro.models import BaixaFinanceira
        
        # Últimos 90 dias
        data_inicio = date.today() - timedelta(days=90)
        
        filtro = {
            'parcela__titulo__tipo': 'PAGAR',
            'data_pagamento__gte': data_inicio,
            'estornado': False
        }
        if empresa:
            filtro['parcela__titulo__empresa'] = empresa
        
        baixas = BaixaFinanceira.objects.filter(**filtro
        ).select_related('parcela__titulo')
        
        if not baixas.exists():
            return {
                'prazo_medio_dias': 0,
                'total_baixas': 0,
                'periodo': '90 dias'
            }
        
        total_dias = 0
        count = 0
        
        for baixa in baixas:
            dias = (baixa.data_pagamento - baixa.parcela.titulo.data_emissao).days
            total_dias += dias
            count += 1
        
        pmp = total_dias / count if count > 0 else 0
        
        return {
            'prazo_medio_dias': round(pmp, 1),
            'total_baixas': count,
            'periodo': '90 dias'
        }
    
    @staticmethod
    def resultado_mensal(ano, mes, empresa=None):
        """
        Resultado mensal (recebido - pago)
        DRE simplificada
        """
        from financeiro.models import BaixaFinanceira
        from datetime import datetime
        
        primeiro_dia = date(ano, mes, 1)
        if mes == 12:
            ultimo_dia = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)
        
        filtro_base = {
            'data_pagamento__gte': primeiro_dia,
            'data_pagamento__lte': ultimo_dia,
            'estornado': False
        }
        if empresa:
            filtro_base['parcela__titulo__empresa'] = empresa
        
        recebido = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='RECEBER',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
        
        pago = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='PAGAR',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
        
        resultado = recebido - pago
        
        return {
            'mes': f'{mes:02d}/{ano}',
            'receitas': recebido,
            'despesas': pago,
            'resultado': resultado,
            'margem': round((resultado / recebido * 100), 2) if recebido > 0 else Decimal('0.00')
        }
    
    @staticmethod
    def dashboard_resumo(empresa=None):
        """
        Resumo consolidado para dashboard
        Todos os principais indicadores
        """
        from financeiro.services.calculadora import CalculadoraSaldos, ProjecaoFluxoCaixa
        
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # Primeiro dia do mês/ano atual para cálculo de recebido/pago
        primeiro_dia_mes = date(ano_atual, mes_atual, 1)
        primeiro_dia_ano = date(ano_atual, 1, 1)
        
        return {
            'caixa': {
                'saldo_atual': sum([c['saldo_atual'] for c in CalculadoraSaldos.saldo_contas_resumo(empresa=empresa)]),
                'contas': CalculadoraSaldos.saldo_contas_resumo(empresa=empresa)
            },
            'a_receber': {
                'total_aberto': CalculadoraSaldos.total_a_receber_aberto(empresa=empresa),
                'vencido': CalculadoraSaldos.total_vencido('RECEBER', empresa=empresa),
                'vencer_30d': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=30), empresa=empresa)['entradas_previstas'],
                'recebido_mes': CalculadoraSaldos.total_recebido(empresa=empresa, data_inicio=primeiro_dia_mes, data_fim=hoje),
                'recebido_ano': CalculadoraSaldos.total_recebido(empresa=empresa, data_inicio=primeiro_dia_ano, data_fim=hoje)
            },
            'a_pagar': {
                'total_aberto': CalculadoraSaldos.total_a_pagar_aberto(empresa=empresa),
                'vencido': CalculadoraSaldos.total_vencido('PAGAR', empresa=empresa),
                'vencer_30d': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=30), empresa=empresa)['saidas_previstas'],
                'pago_mes': CalculadoraSaldos.total_pago(empresa=empresa, data_inicio=primeiro_dia_mes, data_fim=hoje),
                'pago_ano': CalculadoraSaldos.total_pago(empresa=empresa, data_inicio=primeiro_dia_ano, data_fim=hoje)
            },
            'projecoes': ProjecaoFluxoCaixa.projecoes_multiplas(empresa=empresa),
            'indicadores': {
                'inadimplencia': IndicadoresSaudeFinanceira.inadimplencia(empresa=empresa),
                'liquidez_30d': IndicadoresSaudeFinanceira.liquidez_curto_prazo(30, empresa=empresa),
                'pmr': IndicadoresSaudeFinanceira.prazo_medio_recebimento(empresa=empresa),
                'pmp': IndicadoresSaudeFinanceira.prazo_medio_pagamento(empresa=empresa),
                'resultado_mes': IndicadoresSaudeFinanceira.resultado_mensal(ano_atual, mes_atual, empresa=empresa)
            }
        }
