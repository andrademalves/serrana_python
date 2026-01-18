"""
Tarefas Assíncronas Celery para Cobrança
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from financeiro.models import LogCobranca
from financeiro.services.regua_service import ReguaService
from financeiro.services.email_service import EmailService
from usuarios.models import Empresa
import logging

logger = logging.getLogger(__name__)


@shared_task
def processar_reguas_diarias():
    """
    Tarefa agendada para processar réguas de cobrança diariamente
    Executar todos os dias às 08:00
    """
    logger.info("Iniciando processamento diário de réguas de cobrança")
    
    total_enfileirados = 0
    
    # Processar para cada empresa
    empresas = Empresa.objects.filter(ativo=True)
    
    for empresa in empresas:
        logger.info(f"Processando empresa: {empresa.razao_social}")
        
        # Buscar parcelas que precisam de cobrança
        parcelas = ReguaService.buscar_parcelas_para_processar(empresa)
        
        for parcela in parcelas:
            # Atualizar status antes de processar
            ReguaService.atualizar_status_cobranca(parcela)
            
            # Verificar se pode enviar cobrança
            if not parcela.pode_enviar_cobranca():
                continue
            
            # Calcular etapas disponíveis
            etapas = ReguaService.calcular_etapas_disponiveis(parcela)
            
            for etapa in etapas:
                # Verificar se deve disparar
                if ReguaService.deve_disparar_etapa(parcela, etapa):
                    # Criar log (enfileirar)
                    try:
                        log = ReguaService.criar_log_cobranca(
                            parcela=parcela,
                            etapa=etapa,
                            canal='EMAIL'
                        )
                        
                        # Enfileirar envio assíncrono
                        enviar_email_task.delay(log.id)
                        
                        total_enfileirados += 1
                        logger.info(f"Enfileirado: Parcela {parcela.id} - Etapa {etapa.nome}")
                        
                    except ValueError as e:
                        logger.warning(f"Erro ao enfileirar parcela {parcela.id}: {str(e)}")
    
    logger.info(f"Processamento concluído: {total_enfileirados} e-mails enfileirados")
    
    return {
        'empresas_processadas': empresas.count(),
        'emails_enfileirados': total_enfileirados
    }


@shared_task(bind=True, max_retries=3)
def enviar_email_task(self, log_id):
    """
    Tarefa para enviar e-mail de forma assíncrona
    """
    try:
        logger.info(f"Enviando e-mail: Log {log_id}")
        
        sucesso = EmailService.enviar_cobranca(log_id)
        
        if not sucesso:
            # Tentar novamente
            raise Exception("Falha ao enviar e-mail")
        
        return {'log_id': log_id, 'status': 'enviado'}
        
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail (Log {log_id}): {str(e)}")
        
        # Retry com backoff exponencial
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error(f"Máximo de tentativas excedido: Log {log_id}")


@shared_task
def reprocessar_falhas_task():
    """
    Reprocessa logs com falha que ainda podem ser retentados
    """
    logger.info("Reprocessando e-mails com falha")
    
    # Buscar logs com falha que podem ser reprocessados
    logs_falha = LogCobranca.objects.filter(
        status='FALHA',
        tentativas__lt=3,
        data_criacao__gte=timezone.now() - timedelta(days=7)
    )
    
    reprocessados = 0
    
    for log in logs_falha:
        if log.pode_reprocessar():
            # Enfileirar novamente
            enviar_email_task.delay(log.id)
            reprocessados += 1
    
    logger.info(f"{reprocessados} e-mails com falha reenfileirados")
    
    return {'reprocessados': reprocessados}


@shared_task
def limpar_logs_antigos():
    """
    Remove logs de cobrança antigos (>90 dias)
    """
    data_limite = timezone.now() - timedelta(days=90)
    
    deletados = LogCobranca.objects.filter(
        data_criacao__lt=data_limite
    ).delete()
    
    logger.info(f"Logs antigos removidos: {deletados[0]}")
    
    return {'deletados': deletados[0]}


# ============================================================================
# TAREFAS DE BUDGET E LUCRATIVIDADE
# ============================================================================

@shared_task
def verificar_budgets_criticos_diario():
    """
    Tarefa agendada para verificar budgets em situação crítica
    Executar todos os dias às 08:30
    """
    from financeiro.signals import verificar_budgets_zona_critica
    
    logger.info("Iniciando verificação diária de budgets críticos")
    
    resultado = verificar_budgets_zona_critica()
    
    logger.info(f"Verificação concluída: {resultado}")
    
    return resultado


@shared_task
def verificar_budgets_atrasados_diario():
    """
    Tarefa agendada para verificar budgets atrasados
    Executar todos os dias às 09:00
    """
    from financeiro.signals import verificar_budgets_atrasados
    
    logger.info("Iniciando verificação diária de budgets atrasados")
    
    resultado = verificar_budgets_atrasados()
    
    logger.info(f"Verificação concluída: {resultado}")
    
    return resultado

