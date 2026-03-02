"""
Serviço de Métricas e BI do CRM
Toda lógica de cálculo de indicadores, rankings e previsões
"""
from django.db.models import Sum, Count, Q, Avg, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from collections import defaultdict

from crm.models import Oportunidade, EtapaFunil, Pipeline, MetaVendedor, HistoricoEtapa
from django.contrib.auth.models import User


class MetricasCRM:
    """Classe principal para cálculo de métricas do CRM"""
    
    def __init__(self, empresa, usuario=None, is_admin=False):
        """
        Inicializa o serviço de métricas
        
        Args:
            empresa: Empresa ativa
            usuario: Usuário logado (None para admin vendo todos)
            is_admin: Se é admin (bool)
        """
        self.empresa = empresa
        self.usuario = usuario
        self.is_admin = is_admin
    
    def get_base_queryset(self):
        """Retorna queryset base filtrado por permissões"""
        qs = Oportunidade.objects.filter(empresa=self.empresa)
        
        # Se não é admin, filtra apenas oportunidades do vendedor
        if not self.is_admin and self.usuario:
            qs = qs.filter(responsavel=self.usuario)
        
        return qs
    
    def leads_por_etapa(self, pipeline_id=None, vendedor_id=None, data_inicio=None, data_fim=None):
        """
        Retorna quantidade de leads por etapa para gráfico de barras
        
        Returns:
            dict: {
                'labels': ['Etapa 1', 'Etapa 2', ...],
                'data': [10, 5, 3, ...],
                'colors': ['#3498db', '#2ecc71', ...]
            }
        """
        qs = self.get_base_queryset()
        
        # Aplicar filtros
        if pipeline_id:
            qs = qs.filter(pipeline_id=pipeline_id)
        if vendedor_id and self.is_admin:
            qs = qs.filter(responsavel_id=vendedor_id)
        if data_inicio:
            qs = qs.filter(data_entrada__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_entrada__lte=data_fim)
        
        # Agrupar por etapa
        dados = qs.values('etapa__nome', 'etapa__cor', 'etapa__ordem').annotate(
            total=Count('id')
        ).order_by('etapa__ordem')
        
        return {
            'labels': [d['etapa__nome'] for d in dados],
            'data': [d['total'] for d in dados],
            'colors': [d['etapa__cor'] for d in dados]
        }
    
    def ranking_vendedores(self, data_inicio=None, data_fim=None, top=10):
        """
        Retorna ranking de vendedores ordenado por valor fechado
        
        Returns:
            list: [
                {
                    'vendedor_id': 1,
                    'vendedor_nome': 'João Silva',
                    'total_leads': 50,
                    'fechados': 10,
                    'perdidos': 15,
                    'em_andamento': 25,
                    'valor_fechado': Decimal('150000.00'),
                    'taxa_conversao': 20.0,  # %
                },
                ...
            ]
        """
        if not self.is_admin:
            # Vendedor vê apenas sua própria performance
            vendedores = [self.usuario]
        else:
            # Admin vê todos vendedores da empresa
            vendedores = User.objects.filter(
                oportunidades_responsavel__empresa=self.empresa
            ).distinct()
        
        ranking = []
        
        for vendedor in vendedores:
            # Queryset base para este vendedor
            qs = Oportunidade.objects.filter(
                empresa=self.empresa,
                responsavel=vendedor
            )
            
            # Aplicar filtro de data
            if data_inicio:
                qs = qs.filter(data_entrada__gte=data_inicio)
            if data_fim:
                qs = qs.filter(data_entrada__lte=data_fim)
            
            # Calcular métricas
            total_leads = qs.count()
            
            if total_leads == 0:
                continue  # Pula vendedor sem leads no período
            
            fechados = qs.filter(status='ganho').count()
            perdidos = qs.filter(status='perdido').count()
            em_andamento = qs.filter(status__in=['aberto', 'em_andamento']).count()
            
            valor_fechado = qs.filter(status='ganho').aggregate(
                total=Coalesce(Sum('valor_fechado'), Value(Decimal('0'), output_field=DecimalField()))
            )['total']
            
            taxa_conversao = (fechados / total_leads * 100) if total_leads > 0 else 0
            
            ranking.append({
                'vendedor_id': vendedor.id,
                'vendedor_nome': vendedor.get_full_name() or vendedor.username,
                'total_leads': total_leads,
                'fechados': fechados,
                'perdidos': perdidos,
                'em_andamento': em_andamento,
                'valor_fechado': valor_fechado,
                'taxa_conversao': round(taxa_conversao, 2),
            })
        
        # Ordenar por valor fechado (maior primeiro)
        ranking.sort(key=lambda x: x['valor_fechado'], reverse=True)
        
        return ranking[:top]
    
    def grafico_performance(self, data_inicio=None, data_fim=None, vendedor_id=None):
        """
        Retorna dados para gráfico de performance (prospectados, fechados, perdidos)
        
        Returns:
            dict: {
                'labels': ['Prospectados', 'Fechados', 'Perdidos'],
                'data': [100, 20, 30],
                'colors': ['#3498db', '#2ecc71', '#e74c3c']
            }
        """
        qs = self.get_base_queryset()
        
        # Aplicar filtros
        if vendedor_id and self.is_admin:
            qs = qs.filter(responsavel_id=vendedor_id)
        if data_inicio:
            qs = qs.filter(data_entrada__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_entrada__lte=data_fim)
        
        # Contar por status
        prospectados = qs.count()
        fechados = qs.filter(status='ganho').count()
        perdidos = qs.filter(status='perdido').count()
        
        return {
            'labels': ['Prospectados', 'Fechados', 'Perdidos'],
            'data': [prospectados, fechados, perdidos],
            'colors': ['#3498db', '#2ecc71', '#e74c3c']
        }
    
    def grafico_funil(self, pipeline_id=None, data_inicio=None, data_fim=None, vendedor_id=None):
        """
        Retorna dados para gráfico de funil com percentuais de conversão
        
        Returns:
            dict: {
                'etapas': [
                    {
                        'nome': 'Primeiro Contato',
                        'quantidade': 100,
                        'percentual': 100.0,
                        'conversao_proxima': 80.0,  # % que avançou para próxima etapa
                    },
                    ...
                ],
                'conversao_final': 20.0  # % do total que fechou
            }
        """
        qs = self.get_base_queryset()
        
        # Pegar pipeline ativo ou padrão
        if pipeline_id:
            pipeline = Pipeline.objects.get(id=pipeline_id, empresa=self.empresa)
        else:
            pipeline = Pipeline.objects.filter(
                empresa=self.empresa,
                ativo=True
            ).order_by('-padrao', 'id').first()
        
        if not pipeline:
            return {'etapas': [], 'conversao_final': 0}
        
        # Filtrar por pipeline
        qs = qs.filter(pipeline=pipeline)
        
        # Aplicar outros filtros
        if vendedor_id and self.is_admin:
            qs = qs.filter(responsavel_id=vendedor_id)
        if data_inicio:
            qs = qs.filter(data_entrada__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_entrada__lte=data_fim)
        
        total_inicial = qs.count()
        
        if total_inicial == 0:
            return {'etapas': [], 'conversao_final': 0}
        
        # Pegar etapas ordenadas
        etapas = pipeline.etapas.filter(ativo=True).order_by('ordem')
        
        dados_funil = []
        etapa_anterior_qtd = total_inicial
        
        for idx, etapa in enumerate(etapas):
            # Quantidade de oportunidades que passaram por esta etapa
            # (estão nela ou já avançaram)
            qtd_etapa = HistoricoEtapa.objects.filter(
                oportunidade__in=qs,
                etapa_para=etapa
            ).values('oportunidade').distinct().count()
            
            # Se é a primeira etapa, usa total de leads criados
            if idx == 0:
                qtd_etapa = total_inicial
            
            # % em relação ao total inicial
            percentual = (qtd_etapa / total_inicial * 100) if total_inicial > 0 else 0
            
            # % de conversão para próxima etapa
            if idx > 0:
                conversao = (qtd_etapa / etapa_anterior_qtd * 100) if etapa_anterior_qtd > 0 else 0
            else:
                conversao = 100.0
            
            dados_funil.append({
                'nome': etapa.nome,
                'quantidade': qtd_etapa,
                'percentual': round(percentual, 2),
                'conversao_proxima': round(conversao, 2),
                'cor': etapa.cor
            })
            
            etapa_anterior_qtd = qtd_etapa
        
        # Conversão final (% que fechou)
        fechados = qs.filter(status='ganho').count()
        conversao_final = (fechados / total_inicial * 100) if total_inicial > 0 else 0
        
        return {
            'etapas': dados_funil,
            'conversao_final': round(conversao_final, 2)
        }
    
    def meta_vendedor(self, vendedor_id=None, mes=None, ano=None):
        """
        Retorna meta e realizado do vendedor no período
        
        Returns:
            dict: {
                'meta_valor': Decimal,
                'meta_quantidade': int,
                'realizado_valor': Decimal,
                'realizado_quantidade': int,
                'percentual_valor': float,
                'percentual_quantidade': float,
            } ou None se não houver meta
        """
        # Usar mês/ano atual se não especificado
        hoje = date.today()
        mes = mes or hoje.month
        ano = ano or hoje.year
        
        # Determinar vendedor
        if not vendedor_id:
            vendedor_id = self.usuario.id if self.usuario else None
        
        if not vendedor_id:
            return None
        
        # Buscar meta
        try:
            meta = MetaVendedor.objects.get(
                empresa=self.empresa,
                vendedor_id=vendedor_id,
                mes=mes,
                ano=ano,
                ativo=True
            )
        except MetaVendedor.DoesNotExist:
            return None
        
        # Calcular realizado
        realizado = meta.calcular_realizado()
        
        return {
            'meta_valor': meta.meta_valor,
            'meta_quantidade': meta.meta_quantidade,
            'realizado_valor': realizado['valor'],
            'realizado_quantidade': realizado['quantidade'],
            'percentual_valor': round(realizado['percentual_valor'], 2),
            'percentual_quantidade': round(realizado['percentual_quantidade'], 2),
        }
    
    def previsao_faturamento(self, data_inicio=None, data_fim=None, vendedor_id=None):
        """
        Calcula previsão de faturamento baseada em:
        - Leads em andamento
        - Probabilidade de conversão (por etapa ou individual)
        
        Returns:
            dict: {
                'receita_potencial': Decimal,  # Soma de todos os valores previstos
                'receita_provavel': Decimal,   # Ponderada pela probabilidade
                'quantidade_leads': int,       # Quantidade de leads considerados
            }
        """
        qs = self.get_base_queryset()
        
        # Apenas leads em andamento (não fechados/perdidos)
        qs = qs.filter(status__in=['aberto', 'em_andamento'])
        
        # Aplicar filtros
        if vendedor_id and self.is_admin:
            qs = qs.filter(responsavel_id=vendedor_id)
        if data_inicio:
            qs = qs.filter(data_entrada__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_entrada__lte=data_fim)
        
        # Usar valor_previsto (ou valor_estimado como fallback)
        qs = qs.annotate(
            valor_calculado=Coalesce('valor_previsto', 'valor_estimado', Value(Decimal('0'), output_field=DecimalField()))
        )
        
        # Calcular receita potencial (soma direta)
        receita_potencial = qs.aggregate(
            total=Coalesce(Sum('valor_calculado'), Value(Decimal('0'), output_field=DecimalField()))
        )['total']
        
        # Calcular receita provável (ponderada pela probabilidade)
        # valor * (probabilidade / 100)
        receita_provavel = Decimal(0)
        quantidade_leads = 0
        
        for opp in qs.values('id', 'valor_calculado', 'probabilidade_conversao'):
            valor = opp['valor_calculado'] or 0
            prob = opp['probabilidade_conversao'] or 0
            receita_provavel += Decimal(valor) * Decimal(prob) / Decimal(100)
            quantidade_leads += 1
        
        return {
            'receita_potencial': receita_potencial,
            'receita_provavel': round(receita_provavel, 2),
            'quantidade_leads': quantidade_leads,
        }
    
    def kpis_principais(self, data_inicio=None, data_fim=None, vendedor_id=None):
        """
        Retorna KPIs principais para cards do dashboard
        
        Returns:
            dict: {
                'total_leads': int,
                'leads_abertos': int,
                'taxa_conversao': float,
                'ticket_medio': Decimal,
                'tempo_medio_fechamento': float,  # dias
            }
        """
        qs = self.get_base_queryset()
        
        # Aplicar filtros
        if vendedor_id and self.is_admin:
            qs = qs.filter(responsavel_id=vendedor_id)
        if data_inicio:
            qs = qs.filter(data_entrada__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_entrada__lte=data_fim)
        
        total_leads = qs.count()
        leads_abertos = qs.filter(status__in=['aberto', 'em_andamento']).count()
        
        # Taxa de conversão
        fechados = qs.filter(status='ganho').count()
        taxa_conversao = (fechados / total_leads * 100) if total_leads > 0 else 0
        
        # Ticket médio (apenas deals fechados)
        ticket_medio = qs.filter(status='ganho').aggregate(
            media=Avg('valor_fechado')
        )['media'] or Decimal(0)
        
        # Tempo médio de fechamento
        leads_fechados = qs.filter(
            status='ganho',
            data_fechamento__isnull=False
        ).annotate(
            tempo_dias=F('data_fechamento') - F('data_entrada')
        )
        
        tempos = [lead.tempo_dias.days for lead in leads_fechados if lead.tempo_dias]
        tempo_medio = sum(tempos) / len(tempos) if tempos else 0
        
        return {
            'total_leads': total_leads,
            'leads_abertos': leads_abertos,
            'taxa_conversao': round(taxa_conversao, 2),
            'ticket_medio': round(ticket_medio, 2),
            'tempo_medio_fechamento': round(tempo_medio, 1),
        }
