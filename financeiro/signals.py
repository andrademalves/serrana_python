"""
SIGNALS - ETAPA 2
Sistema de monitoramento automático de Budget
Dispara ações quando limites são atingidos
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

from .models import ProjectExpense, ProjectBudget, JustificativaBudget
from .notifications import NotificadorBudget


# ============================================================================
# SIGNALS DE PROJECT EXPENSE
# ============================================================================

@receiver(post_save, sender=ProjectExpense)
def atualizar_budget_apos_despesa(sender, instance, created, **kwargs):
    """
    Atualiza semáforo do budget após salvar/aprovar despesa
    Dispara notificações quando necessário
    """
    budget = instance.budget
    
    # Recalcular percentual de uso
    budget.atualizar_semaforo()
    budget.save(update_fields=['percentual_uso_budget', 'semaforo', 'bloqueado'])
    
    # Se despesa foi aprovada e budget entrou em zona crítica
    if instance.status == 'APROVADO':
        percentual = budget.percentual_uso_budget
        
        # Notificação AMARELA (80-95%)
        if 80 <= percentual < 95 and budget.semaforo == 'AMARELO':
            NotificadorBudget.notificar_zona_amarela(budget, instance)
        
        # Notificação VERMELHA (>95%)
        elif percentual >= 95 and budget.semaforo == 'VERMELHO':
            NotificadorBudget.notificar_zona_vermelha(budget, instance)
            
            # Registrar log
            print(f"⚠️  BUDGET BLOQUEADO: {budget.codigo} - {percentual:.1f}% de uso")


@receiver(pre_save, sender=ProjectExpense)
def validar_despesa_antes_salvar(sender, instance, **kwargs):
    """
    Validação antes de salvar despesa
    Bloqueia se budget estiver bloqueado
    """
    from django.core.exceptions import ValidationError
    from .services_budget import ValidadorBudget
    
    # Apenas validar em criação ou mudança de valor
    if instance.pk:
        old_instance = ProjectExpense.objects.filter(pk=instance.pk).first()
        if old_instance and old_instance.valor == instance.valor:
            return
    
    # Validar se pode lançar
    pode, msg = ValidadorBudget.validar_lancamento_despesa(
        instance.budget,
        instance.valor
    )
    
    if not pode:
        raise ValidationError(f"Despesa bloqueada: {msg}")


# ============================================================================
# SIGNALS DE PROJECT BUDGET
# ============================================================================

@receiver(post_save, sender=ProjectBudget)
def notificar_criacao_budget(sender, instance, created, **kwargs):
    """
    Notifica responsáveis quando budget é criado ou aprovado
    """
    if created:
        NotificadorBudget.notificar_novo_budget(instance)
        print(f"✓ Budget criado: {instance.codigo}")
    
    # Se mudou para EM_EXECUCAO
    if instance.status == 'EM_EXECUCAO':
        old_instance = ProjectBudget.objects.filter(pk=instance.pk).first()
        if old_instance and old_instance.status != 'EM_EXECUCAO':
            NotificadorBudget.notificar_inicio_execucao(instance)


@receiver(post_save, sender=ProjectBudget)
def alertar_margem_negativa(sender, instance, **kwargs):
    """
    Alerta se budget tem margem negativa (prejuízo)
    """
    if instance.margem_prevista_percentual < 0:
        NotificadorBudget.alertar_venda_prejuizo(instance)
        print(f"⚠️  PREJUÍZO DETECTADO: {instance.codigo} - Margem: {instance.margem_prevista_percentual}%")


# ============================================================================
# SIGNALS DE JUSTIFICATIVA BUDGET
# ============================================================================

@receiver(post_save, sender=JustificativaBudget)
def notificar_justificativa(sender, instance, created, **kwargs):
    """
    Notifica quando justificativa é criada ou respondida
    """
    if created:
        # Nova justificativa criada - notificar gestores
        NotificadorBudget.notificar_nova_justificativa(instance)
        print(f"📝 Nova justificativa: Budget {instance.budget.codigo}")
    
    else:
        # Justificativa respondida
        if instance.status == 'APROVADO':
            NotificadorBudget.notificar_justificativa_aprovada(instance)
            print(f"✓ Justificativa aprovada: Budget {instance.budget.codigo} desbloqueado")
        
        elif instance.status == 'REJEITADO':
            NotificadorBudget.notificar_justificativa_rejeitada(instance)
            print(f"✗ Justificativa rejeitada: Budget {instance.budget.codigo}")


# ============================================================================
# SIGNALS DE MONITORAMENTO PERIÓDICO
# ============================================================================

def verificar_budgets_atrasados():
    """
    Função auxiliar para verificar budgets atrasados
    Pode ser chamada via Celery/Cron
    """
    from datetime import date
    
    budgets_atrasados = ProjectBudget.objects.filter(
        status='EM_EXECUCAO',
        data_termino_prevista__lt=date.today()
    )
    
    for budget in budgets_atrasados:
        NotificadorBudget.alertar_budget_atrasado(budget)
    
    return budgets_atrasados.count()


def verificar_budgets_zona_critica():
    """
    Verifica budgets em zona crítica (amarela/vermelha)
    Dispara relatório diário
    """
    budgets_criticos = ProjectBudget.objects.filter(
        status='EM_EXECUCAO',
        semaforo__in=['AMARELO', 'VERMELHO']
    )
    
    if budgets_criticos.exists():
        NotificadorBudget.relatorio_budgets_criticos(budgets_criticos)
    
    return budgets_criticos.count()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def desabilitar_signals_temporariamente():
    """
    Context manager para desabilitar signals temporariamente
    Útil para imports em massa ou testes
    """
    from django.db.models.signals import post_save, pre_save
    
    class DisableSignals:
        def __enter__(self):
            post_save.disconnect(atualizar_budget_apos_despesa, sender=ProjectExpense)
            pre_save.disconnect(validar_despesa_antes_salvar, sender=ProjectExpense)
            post_save.disconnect(notificar_criacao_budget, sender=ProjectBudget)
            post_save.disconnect(notificar_justificativa, sender=JustificativaBudget)
        
        def __exit__(self, *args):
            post_save.connect(atualizar_budget_apos_despesa, sender=ProjectExpense)
            pre_save.connect(validar_despesa_antes_salvar, sender=ProjectExpense)
            post_save.connect(notificar_criacao_budget, sender=ProjectBudget)
            post_save.connect(notificar_justificativa, sender=JustificativaBudget)
    
    return DisableSignals()
