"""
Serviço de Cálculos Financeiros
Saldos, totalizações e agregações
"""
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date, timedelta


class CalculadoraSaldos:
    """Calcula saldos de contas e títulos"""
    
    @staticmethod
    def saldo_conta(conta_id, data_ref=None):
        """
        Calcula saldo de uma conta financeira até uma data
        """
        from financeiro.models import ContaFinanceira, MovimentacaoConta
        
        conta = ContaFinanceira.objects.get(pk=conta_id)
        
        # Saldo inicial
        saldo = conta.saldo_inicial
        
        # Movimentações
        filtro = Q(conta_financeira=conta, estornado=False)
        if data_ref:
            filtro &= Q(data_movimentacao__lte=data_ref)
        
        movs = MovimentacaoConta.objects.filter(filtro).aggregate(
            entradas=Coalesce(Sum('valor', filter=Q(tipo='ENTRADA')), Decimal('0.00')),
            saidas=Coalesce(Sum('valor', filter=Q(tipo='SAIDA')), Decimal('0.00'))
        )
        
        saldo += movs['entradas'] - movs['saidas']
        return saldo
    
    @staticmethod
    def saldo_contas_resumo(empresa=None):
        """Retorna resumo de saldo de todas as contas ativas"""
        from financeiro.models import ContaFinanceira
        
        filtro = {'ativo': True}
        if empresa:
            filtro['empresa'] = empresa
        
        contas = ContaFinanceira.objects.filter(**filtro)
        resultado = []
        
        for conta in contas:
            resultado.append({
                'conta': conta,
                'saldo_atual': CalculadoraSaldos.saldo_conta(conta.id),
                'limite_credito': conta.limite_credito,
                'saldo_disponivel': conta.saldo_inicial + conta.limite_credito
            })
        
        return resultado
    
    @staticmethod
    def total_a_pagar_aberto(empresa=None):
        """Total de contas a pagar em aberto"""
        from financeiro.models import ParcelaFinanceira
        
        filtro = {'titulo__tipo': 'PAGAR', 'status__in': ['ABERTO', 'PARCIAL']}
        if empresa:
            filtro['titulo__empresa'] = empresa
        
        return ParcelaFinanceira.objects.filter(**filtro).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
    
    @staticmethod
    def total_a_receber_aberto(empresa=None):
        """Total de contas a receber em aberto"""
        from financeiro.models import ParcelaFinanceira
        
        filtro = {'titulo__tipo': 'RECEBER', 'status__in': ['ABERTO', 'PARCIAL']}
        if empresa:
            filtro['titulo__empresa'] = empresa
        
        return ParcelaFinanceira.objects.filter(**filtro).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
    
    @staticmethod
    def total_recebido(empresa=None, data_inicio=None, data_fim=None):
        """Total efetivamente recebido (baixas realizadas)"""
        from financeiro.models import BaixaFinanceira
        
        filtro = {'parcela__titulo__tipo': 'RECEBER', 'estornado': False}
        if empresa:
            filtro['parcela__titulo__empresa'] = empresa
        if data_inicio:
            filtro['data_pagamento__gte'] = data_inicio
        if data_fim:
            filtro['data_pagamento__lte'] = data_fim
        
        return BaixaFinanceira.objects.filter(**filtro).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
    
    @staticmethod
    def total_pago(empresa=None, data_inicio=None, data_fim=None):
        """Total efetivamente pago (baixas realizadas)"""
        from financeiro.models import BaixaFinanceira
        
        filtro = {'parcela__titulo__tipo': 'PAGAR', 'estornado': False}
        if empresa:
            filtro['parcela__titulo__empresa'] = empresa
        if data_inicio:
            filtro['data_pagamento__gte'] = data_inicio
        if data_fim:
            filtro['data_pagamento__lte'] = data_fim
        
        return BaixaFinanceira.objects.filter(**filtro).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
    
    @staticmethod
    def total_vencido(tipo, empresa=None, data_ref=None):
        """Total vencido (a pagar ou receber)"""
        from financeiro.models import ParcelaFinanceira
        
        if data_ref is None:
            data_ref = date.today()
        
        filtro = {'titulo__tipo': tipo, 'status__in': ['ABERTO', 'PARCIAL'], 'data_vencimento__lt': data_ref}
        if empresa:
            filtro['titulo__empresa'] = empresa
        
        return ParcelaFinanceira.objects.filter(**filtro).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']


class ProjecaoFluxoCaixa:
    """Projeções de fluxo de caixa"""
    
    @staticmethod
    def projecao_periodo(data_inicio, data_fim, empresa=None):
        """
        Projeta fluxo de caixa para um período
        Retorna previsão de entradas, saídas e saldo
        """
        from financeiro.models import ParcelaFinanceira
        
        filtro_base = {'status__in': ['ABERTO', 'PARCIAL'], 'data_vencimento__gte': data_inicio, 'data_vencimento__lte': data_fim}
        if empresa:
            filtro_base['titulo__empresa'] = empresa
        
        # Parcelas a receber no período
        receber = ParcelaFinanceira.objects.filter(
            titulo__tipo='RECEBER',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        # Parcelas a pagar no período
        pagar = ParcelaFinanceira.objects.filter(
            titulo__tipo='PAGAR',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('saldo_aberto'), Decimal('0.00'))
        )['total']
        
        return {
            'periodo': f'{data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}',
            'entradas_previstas': receber,
            'saidas_previstas': pagar,
            'saldo_previsto': receber - pagar
        }
    
    @staticmethod
    def projecoes_multiplas(empresa=None):
        """Retorna projeções para 7, 30, 60, 90 dias"""
        hoje = date.today()
        
        return {
            '7_dias': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=7), empresa=empresa),
            '30_dias': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=30), empresa=empresa),
            '60_dias': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=60), empresa=empresa),
            '90_dias': ProjecaoFluxoCaixa.projecao_periodo(hoje, hoje + timedelta(days=90), empresa=empresa),
        }
    
    @staticmethod
    def fluxo_mensal(ano, mes, empresa=None):
        """
        Fluxo realizado vs previsto para um mês específico
        """
        from financeiro.models import ParcelaFinanceira, BaixaFinanceira
        from datetime import datetime
        
        primeiro_dia = date(ano, mes, 1)
        if mes == 12:
            ultimo_dia = date(ano + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(ano, mes + 1, 1) - timedelta(days=1)
        
        # Filtro base
        filtro_base = {}
        if empresa:
            filtro_base['titulo__empresa'] = empresa
        
        # PREVISTO: parcelas com vencimento no mês
        previsto_receber = ParcelaFinanceira.objects.filter(
            titulo__tipo='RECEBER',
            data_vencimento__gte=primeiro_dia,
            data_vencimento__lte=ultimo_dia,
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('valor_original'), Decimal('0.00'))
        )['total']
        
        previsto_pagar = ParcelaFinanceira.objects.filter(
            titulo__tipo='PAGAR',
            data_vencimento__gte=primeiro_dia,
            data_vencimento__lte=ultimo_dia,
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('valor_original'), Decimal('0.00'))
        )['total']
        
        # REALIZADO: baixas efetuadas no mês
        realizado_receber = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='RECEBER',
            data_pagamento__gte=primeiro_dia,
            data_pagamento__lte=ultimo_dia,
            estornado=False,
            **{f'parcela__{k}': v for k, v in filtro_base.items()}
        ).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
        
        realizado_pagar = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='PAGAR',
            data_pagamento__gte=primeiro_dia,
            data_pagamento__lte=ultimo_dia,
            estornado=False,
            **{f'parcela__{k}': v for k, v in filtro_base.items()}
        ).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
        
        return {
            'mes': f'{mes:02d}/{ano}',
            'previsto': {
                'receber': previsto_receber,
                'pagar': previsto_pagar,
                'saldo': previsto_receber - previsto_pagar
            },
            'realizado': {
                'receber': realizado_receber,
                'pagar': realizado_pagar,
                'saldo': realizado_receber - realizado_pagar
            },
            'diferenca': {
                'receber': realizado_receber - previsto_receber,
                'pagar': realizado_pagar - previsto_pagar,
                'saldo': (realizado_receber - realizado_pagar) - (previsto_receber - previsto_pagar)
            }
        }
