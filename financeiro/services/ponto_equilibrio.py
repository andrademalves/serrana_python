"""
Serviço de Análise de Ponto de Equilíbrio
Break-even Point e Margem de Contribuição
"""
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import date, timedelta


class AnalisePontoEquilibrio:
    """Calcula ponto de equilíbrio e margem de contribuição"""
    
    @staticmethod
    def classificacao_custos_periodo(data_inicio, data_fim, empresa=None):
        """
        Classifica receitas e custos do período em fixos/variáveis
        """
        from financeiro.models import BaixaFinanceira, CategoriaCustoVariabilidade, CentroCusto
        
        # Filtro base
        filtro_base = {
            'data_pagamento__gte': data_inicio,
            'data_pagamento__lte': data_fim,
            'estornado': False
        }
        if empresa:
            filtro_base['parcela__titulo__empresa'] = empresa
        
        # Receitas do período
        receitas = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='RECEBER',
            **filtro_base
        ).aggregate(
            total=Coalesce(Sum('valor_liquido'), Decimal('0.00'))
        )['total']
        
        # Despesas por centro de custo
        despesas_query = BaixaFinanceira.objects.filter(
            parcela__titulo__tipo='PAGAR',
            **filtro_base
        ).values('parcela__titulo__centro_custo').annotate(
            total=Sum('valor_liquido')
        )
        
        custos_fixos = Decimal('0.00')
        custos_variaveis = Decimal('0.00')
        detalhamento = []
        
        for desp in despesas_query:
            centro_custo_id = desp['parcela__titulo__centro_custo']
            valor = desp['total']
            
            # Por padrão, considera custos como MISTO (50% fixo, 50% variável)
            # TODO: Implementar classificação por categoria quando PlanoContas for criado
            tipo = 'MISTO'
            perc_var = Decimal('50.00')
            
            if tipo == 'FIXO':
                custos_fixos += valor
                valor_fixo = valor
                valor_variavel = Decimal('0.00')
            elif tipo == 'VARIAVEL':
                custos_variaveis += valor
                valor_fixo = Decimal('0.00')
                valor_variavel = valor
            else:  # MISTO
                valor_variavel = valor * (perc_var / 100)
                valor_fixo = valor - valor_variavel
                custos_variaveis += valor_variavel
                custos_fixos += valor_fixo
            
            # Busca nome do centro de custo
            if centro_custo_id:
                try:
                    centro = CentroCusto.objects.get(pk=centro_custo_id)
                    categoria_nome = centro.nome
                except CentroCusto.DoesNotExist:
                    categoria_nome = 'Sem classificação'
            else:
                categoria_nome = 'Sem classificação'
                
            detalhamento.append({
                'categoria': categoria_nome,
                'tipo': tipo,
                'total': valor,
                'fixo': valor_fixo,
                'variavel': valor_variavel
            })
        
        return {
            'receitas': receitas,
            'custos_fixos': custos_fixos,
            'custos_variaveis': custos_variaveis,
            'custos_totais': custos_fixos + custos_variaveis,
            'detalhamento': detalhamento
        }
    
    @staticmethod
    def calcular_break_even(periodo_meses=3, empresa=None):
        """
        Calcula ponto de equilíbrio baseado nos últimos N meses
        
        Fórmulas:
        - Margem de Contribuição = (Receitas - Custos Variáveis) / Receitas
        - Ponto de Equilíbrio = Custos Fixos / Margem de Contribuição
        """
        hoje = date.today()
        data_inicio = hoje - timedelta(days=periodo_meses * 30)
        
        dados = AnalisePontoEquilibrio.classificacao_custos_periodo(data_inicio, hoje, empresa=empresa)
        
        receitas = dados['receitas']
        custos_fixos = dados['custos_fixos']
        custos_variaveis = dados['custos_variaveis']
        
        # Margem de Contribuição
        if receitas > 0:
            margem_contribuicao_valor = receitas - custos_variaveis
            margem_contribuicao_percentual = (margem_contribuicao_valor / receitas) * 100
        else:
            margem_contribuicao_valor = Decimal('0.00')
            margem_contribuicao_percentual = Decimal('0.00')
        
        # Ponto de Equilíbrio (em R$)
        if margem_contribuicao_percentual > 0:
            break_even_valor = (custos_fixos / margem_contribuicao_percentual) * 100
        else:
            break_even_valor = Decimal('0.00')
        
        # Média mensal
        receita_media_mensal = receitas / periodo_meses if periodo_meses > 0 else receitas
        
        # Status
        if receita_media_mensal > 0:
            percentual_atingido = (receita_media_mensal / break_even_valor * 100) if break_even_valor > 0 else Decimal('100.00')
        else:
            percentual_atingido = Decimal('0.00')
        
        status = 'OK' if percentual_atingido >= 120 else 'ALERTA' if percentual_atingido >= 100 else 'CRITICO'
        
        return {
            'periodo_analise': f'Últimos {periodo_meses} meses',
            'receitas_periodo': receitas,
            'receita_media_mensal': receita_media_mensal,
            'custos': {
                'fixos': custos_fixos,
                'variaveis': custos_variaveis,
                'totais': custos_fixos + custos_variaveis
            },
            'margem_contribuicao': {
                'valor': margem_contribuicao_valor,
                'percentual': round(margem_contribuicao_percentual, 2)
            },
            'ponto_equilibrio': {
                'valor_mensal': round(break_even_valor, 2),
                'percentual_atingido': round(percentual_atingido, 2),
                'status': status
            },
            'detalhamento_custos': dados['detalhamento']
        }
    
    @staticmethod
    def projecao_break_even_futuro(receita_projetada_mensal):
        """
        Projeta se a receita projetada atingirá o ponto de equilíbrio
        """
        dados_historicos = AnalisePontoEquilibrio.calcular_break_even()
        
        break_even_mensal = dados_historicos['ponto_equilibrio']['valor_mensal']
        margem_contrib_perc = dados_historicos['margem_contribuicao']['percentual']
        
        # Resultado projetado
        if margem_contrib_perc > 0:
            custos_variaveis_proj = receita_projetada_mensal * ((100 - margem_contrib_perc) / 100)
        else:
            custos_variaveis_proj = Decimal('0.00')
        
        custos_fixos_proj = dados_historicos['custos']['fixos'] / 3  # Média mensal
        
        lucro_projetado = receita_projetada_mensal - custos_variaveis_proj - custos_fixos_proj
        
        return {
            'receita_projetada': receita_projetada_mensal,
            'break_even_necessario': break_even_mensal,
            'diferenca': receita_projetada_mensal - break_even_mensal,
            'atinge_break_even': receita_projetada_mensal >= break_even_mensal,
            'lucro_projetado': round(lucro_projetado, 2),
            'margem_seguranca': round(((receita_projetada_mensal - break_even_mensal) / receita_projetada_mensal * 100), 2) if receita_projetada_mensal > 0 else Decimal('0.00')
        }
