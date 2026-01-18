"""
SERVICES - DASHBOARD BI
=======================

Serviços para cálculo de KPIs e indicadores gerenciais.
Otimizado com cache e queries eficientes.

Autor: Sistema BI Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from django.db import models, connection
from django.db.models import (
    Sum, Avg, Count, Q, F, Case, When, 
    Value, DecimalField, FloatField, IntegerField
)
from django.db.models.functions import Coalesce, TruncMonth, TruncDay
from django.core.cache import cache
from django.utils import timezone

# Imports dos models - ajustar conforme sua estrutura
from cadastros.models import Pessoa, Produto
from estoque.models import SaldoEstoque, MovimentoEstoque, LocalEstoque
# from projetos.models import Obra
# from financeiro.models import Titulo, Baixa


# ==============================================================================
# 1. SERVIÇO DE KPIs DE ESTOQUE
# ==============================================================================

class EstoqueKPIService:
    """
    Serviço para cálculo de KPIs de estoque.
    """
    
    @staticmethod
    def get_valor_total_estoque(local_id: Optional[int] = None) -> Dict:
        """
        Retorna valor total do estoque com variação.
        
        Returns:
            {
                'valor_atual': Decimal,
                'variacao_mes_anterior': Decimal,
                'percentual_variacao': Decimal,
                'por_tipo': {...}
            }
        """
        cache_key = f'kpi:estoque:valor_total:{local_id or "all"}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Valor atual
        query = SaldoEstoque.objects.filter(quantidade__gt=0)
        if local_id:
            query = query.filter(local_id=local_id)
        
        valor_atual = query.aggregate(
            total=Coalesce(
                Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField()),
                Decimal('0')
            )
        )['total']
        
        # Valor mês anterior (seria de view materializada ou histórico)
        # Por simplicidade, usar último cálculo em cache ou estimar
        valor_mes_anterior = cache.get(f'kpi:estoque:valor_total_mes_anterior:{local_id or "all"}') or valor_atual
        
        variacao = valor_atual - valor_mes_anterior
        percentual = (variacao / valor_mes_anterior * 100) if valor_mes_anterior > 0 else Decimal('0')
        
        # Por tipo de item (se houver campo tipo em Item)
        por_tipo = {}
        from estoque.models import Item
        if hasattr(Item, 'tipo'):
            por_tipo = query.values('item__tipo').annotate(
                total=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
            )
            por_tipo = {item['item__tipo']: item['total'] for item in por_tipo}
        
        resultado = {
            'valor_atual': valor_atual,
            'variacao_mes_anterior': variacao,
            'percentual_variacao': percentual,
            'por_tipo': por_tipo,
            'data_atualizacao': timezone.now()
        }
        
        cache.set(cache_key, resultado, timeout=3600)  # 1 hora
        return resultado
    
    @staticmethod
    def get_itens_abaixo_minimo() -> Dict:
        """
        Retorna produtos abaixo do estoque mínimo.
        
        Returns:
            {
                'quantidade_total': int,
                'percentual_total': float,
                'produtos': [...]
            }
        """
        cache_key = 'kpi:estoque:abaixo_minimo'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Produtos com saldo total abaixo do mínimo
        produtos_com_saldo = SaldoEstoque.objects.values('item').annotate(
            saldo_total=Sum('quantidade')
        ).values_list('item_id', 'saldo_total')
        
        produtos_criticos = []
        total_produtos = 0
        
        for produto_id, saldo_total in produtos_com_saldo:
            try:
                produto = Produto.objects.get(pk=produto_id, ativo=True)
                total_produtos += 1
                
                if hasattr(produto, 'estoque_minimo') and saldo_total < produto.estoque_minimo:
                    falta = produto.estoque_minimo - saldo_total
                    criticidade = (falta / produto.estoque_minimo * 100) if produto.estoque_minimo > 0 else 0
                    
                    produtos_criticos.append({
                        'produto_id': produto.id,
                        'codigo': produto.codigo,
                        'descricao': produto.descricao,
                        'saldo_atual': saldo_total,
                        'estoque_minimo': produto.estoque_minimo,
                        'falta': falta,
                        'criticidade': criticidade,
                        'unidade': produto.unidade
                    })
            except Produto.DoesNotExist:
                continue
        
        # Ordenar por criticidade
        produtos_criticos.sort(key=lambda x: x['criticidade'], reverse=True)
        
        resultado = {
            'quantidade_total': len(produtos_criticos),
            'percentual_total': (len(produtos_criticos) / total_produtos * 100) if total_produtos > 0 else 0,
            'produtos': produtos_criticos[:20],  # Top 20
            'data_atualizacao': timezone.now()
        }
        
        cache.set(cache_key, resultado, timeout=1800)  # 30 minutos
        return resultado
    
    @staticmethod
    def get_giro_estoque(periodo_dias: int = 30) -> Dict:
        """
        Calcula giro de estoque do período.
        
        Args:
            periodo_dias: Período de análise
        
        Returns:
            {
                'giro': Decimal,
                'dias_cobertura': Decimal,
                'consumo_periodo': Decimal,
                'estoque_medio': Decimal
            }
        """
        data_inicio = timezone.now() - timedelta(days=periodo_dias)
        
        # Consumo do período (saídas)
        consumo = MovimentoEstoque.objects.filter(
            tipo_movimento='SAIDA',
            data_movimento__gte=data_inicio
        ).exclude(
            tipo_movimento='ESTORNO'
        ).aggregate(
            total=Coalesce(
                Sum(F('quantidade') * F('custo_unitario'), output_field=DecimalField()),
                Decimal('0')
            )
        )['total']
        
        # Estoque médio (aproximação: média atual + inicial / 2)
        estoque_atual = EstoqueKPIService.get_valor_total_estoque()['valor_atual']
        estoque_medio = estoque_atual  # Simplificação - idealmente usar histórico
        
        # Giro = Consumo / Estoque Médio
        giro = (consumo / estoque_medio) if estoque_medio > 0 else Decimal('0')
        
        # Dias de cobertura = Período / Giro
        dias_cobertura = (Decimal(str(periodo_dias)) / giro) if giro > 0 else Decimal('999')
        
        return {
            'giro': giro.quantize(Decimal('0.01')),
            'dias_cobertura': dias_cobertura.quantize(Decimal('0')),
            'consumo_periodo': consumo,
            'estoque_medio': estoque_medio,
            'periodo_dias': periodo_dias
        }
    
    @staticmethod
    def get_curva_abc(limite: int = 50) -> List[Dict]:
        """
        Retorna curva ABC de produtos por valor imobilizado.
        
        Args:
            limite: Quantidade máxima de produtos
        
        Returns:
            Lista de produtos com classificação ABC
        """
        cache_key = f'kpi:estoque:curva_abc:{limite}'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Estoque valorizado
        produtos = SaldoEstoque.objects.filter(
            quantidade__gt=0
        ).values(
            'item__id',
            'item__codigo',
            'item__descricao',
            'item__unidade'
        ).annotate(
            quantidade_total=Sum('quantidade'),
            custo_medio=Avg('custo_medio'),
            valor_total=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
        ).order_by('-valor_total')[:limite]
        
        # Converter para lista
        produtos_list = list(produtos)
        
        # Calcular valor total geral
        valor_total_geral = sum(p['valor_total'] for p in produtos_list)
        
        # Calcular percentuais e classificação ABC
        valor_acumulado = Decimal('0')
        for produto in produtos_list:
            valor_acumulado += produto['valor_total']
            percentual_acumulado = (valor_acumulado / valor_total_geral * 100) if valor_total_geral > 0 else 0
            
            produto['percentual_valor'] = (produto['valor_total'] / valor_total_geral * 100) if valor_total_geral > 0 else 0
            produto['percentual_acumulado'] = percentual_acumulado
            
            # Classificação ABC
            if percentual_acumulado <= 80:
                produto['classe_abc'] = 'A'
            elif percentual_acumulado <= 95:
                produto['classe_abc'] = 'B'
            else:
                produto['classe_abc'] = 'C'
        
        cache.set(cache_key, produtos_list, timeout=3600)
        return produtos_list
    
    @staticmethod
    def get_consumo_medio_mensal(limite: int = 20) -> List[Dict]:
        """
        Retorna Top N produtos por consumo médio mensal.
        
        Returns:
            Lista com consumo médio dos últimos 6 meses
        """
        data_inicio = timezone.now() - timedelta(days=180)  # 6 meses
        
        # Consumo por produto e mês
        consumo_mensal = MovimentoEstoque.objects.filter(
            tipo_movimento='SAIDA',
            data_movimento__gte=data_inicio
        ).exclude(
            tipo_movimento='ESTORNO'
        ).annotate(
            mes=TruncMonth('data_movimento')
        ).values(
            'item__id',
            'item__codigo',
            'item__descricao',
            'mes'
        ).annotate(
            quantidade=Sum('quantidade')
        )
        
        # Agrupar por produto e calcular média
        consumo_por_produto = {}
        for registro in consumo_mensal:
            produto_id = registro['item__id']
            
            if produto_id not in consumo_por_produto:
                consumo_por_produto[produto_id] = {
                    'produto_id': produto_id,
                    'codigo': registro['item__codigo'],
                    'descricao': registro['item__descricao'],
                    'meses': [],
                    'quantidades': []
                }
            
            consumo_por_produto[produto_id]['meses'].append(registro['mes'])
            consumo_por_produto[produto_id]['quantidades'].append(float(registro['quantidade']))
        
        # Calcular médias e desvio
        resultados = []
        for produto_id, dados in consumo_por_produto.items():
            if len(dados['quantidades']) > 0:
                media = sum(dados['quantidades']) / len(dados['quantidades'])
                
                # Desvio padrão simples
                variancia = sum((x - media) ** 2 for x in dados['quantidades']) / len(dados['quantidades'])
                desvio = variancia ** 0.5
                
                resultados.append({
                    'produto_id': produto_id,
                    'codigo': dados['codigo'],
                    'descricao': dados['descricao'],
                    'consumo_medio_mensal': Decimal(str(media)).quantize(Decimal('0.001')),
                    'desvio_padrao': Decimal(str(desvio)).quantize(Decimal('0.001')),
                    'meses_com_consumo': len(dados['meses']),
                    'tendencia': 'ESTÁVEL'  # Calcular tendência real com regressão linear se necessário
                })
        
        # Ordenar por consumo médio
        resultados.sort(key=lambda x: x['consumo_medio_mensal'], reverse=True)
        
        return resultados[:limite]


# ==============================================================================
# 2. SERVIÇO DE KPIs DE OBRAS
# ==============================================================================

class ObrasKPIService:
    """
    Serviço para cálculo de KPIs de obras.
    """
    
    @staticmethod
    def get_status_obras() -> Dict:
        """
        Retorna quantidade e valor de obras por status.
        
        Returns:
            {
                'orcamento': {'quantidade': int, 'valor': Decimal},
                'em_execucao': {...},
                'concluida': {...},
                'total': {...}
            }
        """
        # AJUSTAR: import do model Obra
        # from projetos.models import Obra
        
        # Por enquanto, retornar estrutura vazia
        # Implementar quando model Obra estiver disponível
        
        return {
            'orcamento': {'quantidade': 0, 'valor': Decimal('0')},
            'em_execucao': {'quantidade': 0, 'valor': Decimal('0')},
            'concluida': {'quantidade': 0, 'valor': Decimal('0')},
            'total': {'quantidade': 0, 'valor': Decimal('0')},
            'data_atualizacao': timezone.now()
        }
        
        # IMPLEMENTAÇÃO REAL:
        """
        cache_key = 'kpi:obras:status'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        status_counts = Obra.objects.filter(ativo=True).values('status').annotate(
            quantidade=Count('id'),
            valor_total=Sum('valor_contrato')
        )
        
        resultado = {}
        total_qtd = 0
        total_valor = Decimal('0')
        
        for item in status_counts:
            status = item['status'].lower()
            resultado[status] = {
                'quantidade': item['quantidade'],
                'valor': item['valor_total'] or Decimal('0')
            }
            total_qtd += item['quantidade']
            total_valor += item['valor_total'] or Decimal('0')
        
        resultado['total'] = {
            'quantidade': total_qtd,
            'valor': total_valor
        }
        resultado['data_atualizacao'] = timezone.now()
        
        cache.set(cache_key, resultado, timeout=1800)
        return resultado
        """
    
    @staticmethod
    def get_analise_financeira_obras(obra_id: Optional[int] = None) -> List[Dict]:
        """
        Análise financeira completa de obras.
        Retorna lucro por competência e caixa.
        
        Returns:
            Lista de obras com análise financeira
        """
        # IMPLEMENTAÇÃO COMPLETA quando models estiverem prontos
        return []
        
        """
        # Query SQL complexa (ver DASHBOARD_BI_DESIGN.md - KPI 2.2)
        with connection.cursor() as cursor:
            cursor.execute('''
                WITH custos_obra AS (
                    SELECT 
                        obra_id,
                        SUM(CASE WHEN origem = 'ESTOQUE' THEN valor ELSE 0 END) AS custo_material,
                        SUM(CASE WHEN categoria = 'MAO_OBRA' THEN valor ELSE 0 END) AS custo_mao_obra,
                        SUM(CASE WHEN categoria = 'TERCEIRO' THEN valor ELSE 0 END) AS custo_terceiro,
                        SUM(CASE WHEN categoria = 'IMPOSTO' THEN valor ELSE 0 END) AS custo_imposto,
                        SUM(valor) AS custo_total
                    FROM custos_obra
                    GROUP BY obra_id
                ),
                receitas_obra AS (
                    SELECT 
                        centro_custo_id AS obra_id,
                        SUM(valor_pago) AS receita_recebida
                    FROM financeiro_titulo
                    WHERE tipo = 'RECEBER' AND situacao = 'PAGO'
                    GROUP BY centro_custo_id
                ),
                despesas_obra AS (
                    SELECT 
                        centro_custo_id AS obra_id,
                        SUM(valor_pago) AS despesa_paga
                    FROM financeiro_titulo
                    WHERE tipo = 'PAGAR' AND situacao = 'PAGO'
                    GROUP BY centro_custo_id
                )
                SELECT 
                    o.id, o.codigo, o.nome, o.valor_contrato,
                    COALESCE(c.custo_total, 0) AS custo_realizado,
                    COALESCE(r.receita_recebida, 0) AS receita_recebida,
                    COALESCE(d.despesa_paga, 0) AS despesa_paga,
                    o.valor_contrato - COALESCE(c.custo_total, 0) AS lucro_competencia,
                    COALESCE(r.receita_recebida, 0) - COALESCE(d.despesa_paga, 0) AS lucro_caixa
                FROM projetos_obra o
                LEFT JOIN custos_obra c ON c.obra_id = o.id
                LEFT JOIN receitas_obra r ON r.obra_id = o.id
                LEFT JOIN despesas_obra d ON d.obra_id = o.id
                WHERE o.ativo = TRUE
                {} 
                ORDER BY o.data_inicio DESC
            '''.format('AND o.id = %s' if obra_id else ''), [obra_id] if obra_id else [])
            
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        """
    
    @staticmethod
    def get_budget_realizado() -> List[Dict]:
        """
        Retorna obras com análise de budget x realizado.
        Identifica estouros.
        """
        return []
        # Implementar quando models estiverem disponíveis


# ==============================================================================
# 3. SERVIÇO DE KPIs FINANCEIROS
# ==============================================================================

class FinanceiroKPIService:
    """
    Serviço para cálculo de KPIs financeiros.
    """
    
    @staticmethod
    def get_saldo_caixa() -> Dict:
        """
        Retorna saldo de caixa atual com variação.
        """
        # IMPLEMENTAR quando model Titulo estiver disponível
        return {
            'saldo_atual': Decimal('0'),
            'variacao_dia_anterior': Decimal('0'),
            'variacao_mes': Decimal('0'),
            'percentual_variacao_mes': Decimal('0'),
            'data_atualizacao': timezone.now()
        }
        
        """
        cache_key = 'kpi:financeiro:saldo_caixa'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Saldo = Recebimentos - Pagamentos
        saldo = Titulo.objects.filter(
            situacao='PAGO',
            data_pagamento__lte=timezone.now().date()
        ).aggregate(
            recebido=Coalesce(
                Sum('valor_pago', filter=Q(tipo='RECEBER')),
                Decimal('0')
            ),
            pago=Coalesce(
                Sum('valor_pago', filter=Q(tipo='PAGAR')),
                Decimal('0')
            )
        )
        
        saldo_atual = saldo['recebido'] - saldo['pago']
        
        # Variação D-1 e mês (simplificado - usar histórico real)
        saldo_dia_anterior = cache.get('kpi:financeiro:saldo_caixa:d-1') or saldo_atual
        saldo_mes_anterior = cache.get('kpi:financeiro:saldo_caixa:mes-1') or saldo_atual
        
        resultado = {
            'saldo_atual': saldo_atual,
            'variacao_dia_anterior': saldo_atual - saldo_dia_anterior,
            'variacao_mes': saldo_atual - saldo_mes_anterior,
            'percentual_variacao_mes': ((saldo_atual - saldo_mes_anterior) / saldo_mes_anterior * 100) if saldo_mes_anterior != 0 else Decimal('0'),
            'data_atualizacao': timezone.now()
        }
        
        cache.set(cache_key, resultado, timeout=300)  # 5 minutos
        cache.set('kpi:financeiro:saldo_caixa:d-1', saldo_atual, timeout=86400)
        return resultado
        """
    
    @staticmethod
    def get_contas_pagar_receber() -> Dict:
        """
        Retorna totais de contas a pagar e a receber com vencimentos.
        """
        return {
            'a_receber': {
                'vencido': Decimal('0'),
                'proximos_7_dias': Decimal('0'),
                'proximos_30_dias': Decimal('0'),
                'total_aberto': Decimal('0')
            },
            'a_pagar': {
                'vencido': Decimal('0'),
                'proximos_7_dias': Decimal('0'),
                'proximos_30_dias': Decimal('0'),
                'total_aberto': Decimal('0')
            },
            'data_atualizacao': timezone.now()
        }
        
        """
        cache_key = 'kpi:financeiro:contas_pagar_receber'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        hoje = timezone.now().date()
        
        # A RECEBER
        a_receber = Titulo.objects.filter(
            tipo='RECEBER',
            situacao__in=['ABERTO', 'PARCIAL']
        ).aggregate(
            vencido=Coalesce(
                Sum('valor' - F('valor_pago'), filter=Q(vencimento__lt=hoje)),
                Decimal('0')
            ),
            proximos_7=Coalesce(
                Sum('valor' - F('valor_pago'), filter=Q(vencimento__gte=hoje, vencimento__lte=hoje + timedelta(days=7))),
                Decimal('0')
            ),
            proximos_30=Coalesce(
                Sum('valor' - F('valor_pago'), filter=Q(vencimento__gte=hoje + timedelta(days=8), vencimento__lte=hoje + timedelta(days=30))),
                Decimal('0')
            ),
            total=Coalesce(
                Sum('valor' - F('valor_pago')),
                Decimal('0')
            )
        )
        
        # A PAGAR (mesma estrutura)
        a_pagar = Titulo.objects.filter(...).aggregate(...)
        
        resultado = {
            'a_receber': {
                'vencido': a_receber['vencido'],
                'proximos_7_dias': a_receber['proximos_7'],
                'proximos_30_dias': a_receber['proximos_30'],
                'total_aberto': a_receber['total']
            },
            'a_pagar': {...},
            'data_atualizacao': timezone.now()
        }
        
        cache.set(cache_key, resultado, timeout=1800)
        return resultado
        """
    
    @staticmethod
    def get_fluxo_caixa_projetado(dias: int = 90) -> List[Dict]:
        """
        Retorna fluxo de caixa projetado para os próximos X dias.
        
        Returns:
            Lista com entradas, saídas e saldo acumulado por dia
        """
        return []
        # Implementar query complexa do DASHBOARD_BI_DESIGN.md - KPI 3.3
    
    @staticmethod
    def get_resultado_mensal(meses: int = 12) -> List[Dict]:
        """
        Retorna DRE simplificada mensal.
        
        Returns:
            Lista com receita, despesa, lucro e margem por mês
        """
        return []
        # Implementar quando model Titulo estiver disponível
    
    @staticmethod
    def get_inadimplencia() -> Dict:
        """
        Calcula taxa de inadimplência.
        """
        return {
            'total_aberto': Decimal('0'),
            'total_vencido': Decimal('0'),
            'titulos_abertos': 0,
            'titulos_vencidos': 0,
            'percentual_titulos': Decimal('0'),
            'percentual_valor': Decimal('0'),
            'dias_atraso_medio': 0,
            'data_atualizacao': timezone.now()
        }


# ==============================================================================
# 4. SERVIÇO UNIFICADO DE DASHBOARD
# ==============================================================================

class DashboardService:
    """
    Serviço principal que consolida todos os KPIs.
    """
    
    @staticmethod
    def get_kpis_principais() -> Dict:
        """
        Retorna todos os KPIs principais para o dashboard.
        Usado nos cards superiores.
        """
        cache_key = 'dashboard:kpis_principais'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Coletar KPIs de cada módulo
        estoque_kpis = {
            'valor_total': EstoqueKPIService.get_valor_total_estoque(),
            'itens_criticos': EstoqueKPIService.get_itens_abaixo_minimo()['quantidade_total'],
            'giro': EstoqueKPIService.get_giro_estoque()
        }
        
        obras_kpis = {
            'status': ObrasKPIService.get_status_obras()
        }
        
        financeiro_kpis = {
            'caixa': FinanceiroKPIService.get_saldo_caixa(),
            'contas': FinanceiroKPIService.get_contas_pagar_receber()
        }
        
        resultado = {
            'estoque': estoque_kpis,
            'obras': obras_kpis,
            'financeiro': financeiro_kpis,
            'data_atualizacao': timezone.now()
        }
        
        cache.set(cache_key, resultado, timeout=1800)  # 30 minutos
        return resultado
    
    @staticmethod
    def get_alertas_criticos() -> List[Dict]:
        """
        Retorna lista de alertas críticos para exibição.
        
        Returns:
            Lista de alertas com tipo, mensagem e ação
        """
        alertas = []
        
        # Alerta: Produtos abaixo do mínimo
        itens_criticos = EstoqueKPIService.get_itens_abaixo_minimo()
        if itens_criticos['quantidade_total'] > 0:
            alertas.append({
                'tipo': 'ESTOQUE',
                'severidade': 'CRITICO' if itens_criticos['quantidade_total'] > 10 else 'AVISO',
                'icone': '📦',
                'mensagem': f"{itens_criticos['quantidade_total']} produtos abaixo do estoque mínimo",
                'acao_url': '/estoque/relatorios/abaixo-minimo/',
                'acao_texto': 'Ver Lista'
            })
        
        # Alerta: Títulos vencidos a receber
        inadimplencia = FinanceiroKPIService.get_inadimplencia()
        if inadimplencia['total_vencido'] > 0:
            alertas.append({
                'tipo': 'FINANCEIRO',
                'severidade': 'CRITICO' if inadimplencia['total_vencido'] > 50000 else 'AVISO',
                'icone': '💰',
                'mensagem': f"R$ {inadimplencia['total_vencido']:,.2f} em títulos vencidos a receber",
                'acao_url': '/financeiro/titulos/vencidos/',
                'acao_texto': 'Cobrar'
            })
        
        # Mais alertas...
        
        return alertas
    
    @staticmethod
    def limpar_cache_dashboard():
        """
        Limpa todo cache do dashboard.
        Usar após alterações significativas nos dados.
        """
        patterns = [
            'dashboard:*',
            'kpi:estoque:*',
            'kpi:obras:*',
            'kpi:financeiro:*'
        ]
        
        for pattern in patterns:
            cache.delete_pattern(pattern)
