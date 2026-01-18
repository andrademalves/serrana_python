"""
CELERY TASKS - DASHBOARD BI
============================

Tasks assíncronas para atualização de KPIs e cache.

Autor: Sistema BI Profissional
Data: Dezembro 2025
"""

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(name='dashboard.atualizar_kpis')
def atualizar_kpis_dashboard():
    """
    Atualiza todos os KPIs do dashboard.
    Executar a cada 1 hora via Celery Beat.
    
    Configuração no settings.py:
    
    CELERY_BEAT_SCHEDULE = {
        'atualizar-dashboard-hourly': {
            'task': 'dashboard.atualizar_kpis',
            'schedule': crontab(minute=0),  # A cada hora
        },
    }
    """
    logger.info("Iniciando atualização de KPIs do dashboard")
    
    try:
        from .services_kpi import (
            EstoqueKPIService,
            ObrasKPIService,
            FinanceiroKPIService,
            DashboardService
        )
        
        # 1. Limpar cache antigo
        DashboardService.limpar_cache_dashboard()
        logger.info("Cache limpo")
        
        # 2. Pré-calcular KPIs principais (aquece cache)
        kpis = DashboardService.get_kpis_principais()
        logger.info("KPIs principais calculados")
        
        # 3. Pré-calcular curva ABC
        curva_abc = EstoqueKPIService.get_curva_abc()
        logger.info(f"Curva ABC calculada: {len(curva_abc)} produtos")
        
        # 4. Pré-calcular alertas
        alertas = DashboardService.get_alertas_criticos()
        logger.info(f"Alertas gerados: {len(alertas)}")
        
        # 5. Salvar timestamp da última atualização
        cache.set('dashboard:ultima_atualizacao', timezone.now(), timeout=None)
        
        logger.info("Atualização de KPIs concluída com sucesso")
        
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'kpis_atualizados': len(kpis),
            'alertas_gerados': len(alertas)
        }
        
    except Exception as e:
        logger.error(f"Erro ao atualizar KPIs: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='dashboard.refresh_materialized_views')
def refresh_materialized_views():
    """
    Atualiza views materializadas do PostgreSQL.
    Executar diariamente às 00:00.
    
    IMPORTANTE: Criar as views materializadas primeiro:
    
    CREATE MATERIALIZED VIEW mv_estoque_historico AS
    SELECT 
        DATE(data_operacao) AS data,
        produto_id,
        SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN quantidade ELSE 0 END) AS entradas,
        SUM(CASE WHEN tipo_movimento = 'SAIDA' THEN quantidade ELSE 0 END) AS saidas,
        SUM(quantidade * custo_unitario_aplicado) AS valor_movimentado
    FROM estoque_movimentoestoque
    WHERE estornado = FALSE
    GROUP BY DATE(data_operacao), produto_id;
    
    CREATE UNIQUE INDEX ON mv_estoque_historico (data, produto_id);
    """
    logger.info("Iniciando refresh de materialized views")
    
    try:
        from django.db import connection
        
        views = [
            'mv_estoque_historico',
            'mv_obras_financeiro',
            'mv_fluxo_caixa_mensal'
        ]
        
        with connection.cursor() as cursor:
            for view in views:
                try:
                    cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                    logger.info(f"View {view} atualizada")
                except Exception as e:
                    logger.warning(f"Erro ao atualizar {view}: {str(e)}")
                    # Continuar com as outras views
        
        logger.info("Refresh de views concluído")
        
        return {
            'status': 'success',
            'views_atualizadas': views,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao atualizar views materializadas: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='dashboard.gerar_relatorio_gerencial')
def gerar_relatorio_gerencial_email(destinatarios: list):
    """
    Gera relatório gerencial e envia por email.
    Executar semanalmente às segundas 08:00.
    
    Args:
        destinatarios: Lista de emails
    """
    logger.info(f"Gerando relatório gerencial para {len(destinatarios)} destinatários")
    
    try:
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        from .services_kpi import DashboardService
        
        # Coletar dados
        kpis = DashboardService.get_kpis_principais()
        alertas = DashboardService.get_alertas_criticos()
        
        # Renderizar HTML
        html_content = render_to_string('dashboard/email_relatorio_gerencial.html', {
            'kpis': kpis,
            'alertas': alertas,
            'data_geracao': timezone.now()
        })
        
        # Criar email
        email = EmailMessage(
            subject=f'Relatório Gerencial - {timezone.now().strftime("%d/%m/%Y")}',
            body=html_content,
            from_email='sistema@serranaesquadrias.com.br',
            to=destinatarios
        )
        email.content_subtype = 'html'
        
        # Enviar
        email.send()
        
        logger.info(f"Relatório enviado com sucesso para {len(destinatarios)} destinatários")
        
        return {
            'status': 'success',
            'destinatarios': len(destinatarios),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar relatório: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='dashboard.calcular_previsao_estoque')
def calcular_previsao_estoque():
    """
    Calcula previsão de ruptura de estoque usando consumo médio.
    Gera alertas proativos.
    
    Executar diariamente.
    """
    logger.info("Iniciando cálculo de previsão de estoque")
    
    try:
        from cadastros.models import Produto
        from estoque.models import SaldoEstoque
        from .services_kpi import EstoqueKPIService
        from datetime import timedelta
        
        consumo_medio = EstoqueKPIService.get_consumo_medio_mensal(limite=100)
        
        alertas_ruptura = []
        
        for item in consumo_medio:
            produto_id = item['produto_id']
            consumo_mensal = item['consumo_medio_mensal']
            consumo_diario = consumo_mensal / 30
            
            # Saldo atual
            saldo = SaldoEstoque.objects.filter(
                produto_id=produto_id
            ).aggregate(
                total=Sum('saldo_quantidade')
            )['total'] or Decimal('0')
            
            if consumo_diario > 0:
                dias_cobertura = saldo / consumo_diario
                
                # Se menos de 7 dias, alertar
                if dias_cobertura < 7:
                    alertas_ruptura.append({
                        'produto_id': produto_id,
                        'codigo': item['codigo'],
                        'descricao': item['descricao'],
                        'saldo_atual': float(saldo),
                        'consumo_diario': float(consumo_diario),
                        'dias_cobertura': float(dias_cobertura),
                        'data_ruptura_prevista': (timezone.now() + timedelta(days=float(dias_cobertura))).date()
                    })
        
        # Salvar alertas em cache
        cache.set('dashboard:alertas_ruptura', alertas_ruptura, timeout=86400)
        
        logger.info(f"Previsão calculada: {len(alertas_ruptura)} produtos em risco de ruptura")
        
        return {
            'status': 'success',
            'produtos_em_risco': len(alertas_ruptura),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular previsão: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }
