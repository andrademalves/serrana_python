"""
NOTIFICAÇÕES - ETAPA 2
Sistema de notificações por e-mail, SMS e in-app
Alertas automáticos de budget
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class NotificadorBudget:
    """
    Classe responsável por enviar notificações relacionadas a Budget
    """
    
    @staticmethod
    def _get_destinatarios_budget(budget):
        """
        Retorna lista de e-mails dos responsáveis pelo budget
        """
        destinatarios = []
        
        # Criador do budget
        if budget.criado_por and budget.criado_por.email:
            destinatarios.append(budget.criado_por.email)
        
        # Responsável pelo projeto
        if budget.projeto and hasattr(budget.projeto, 'responsavel'):
            if budget.projeto.responsavel and budget.projeto.responsavel.email:
                destinatarios.append(budget.projeto.responsavel.email)
        
        # Gestores da empresa (usuários is_staff)
        gestores = User.objects.filter(
            is_staff=True,
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        for gestor in gestores:
            destinatarios.append(gestor.email)
        
        # Remover duplicatas
        return list(set(destinatarios))
    
    @staticmethod
    def _enviar_email(assunto, mensagem_html, destinatarios):
        """
        Envia e-mail HTML
        """
        try:
            mensagem_texto = strip_tags(mensagem_html)
            
            email = EmailMultiAlternatives(
                subject=assunto,
                body=mensagem_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=destinatarios
            )
            email.attach_alternative(mensagem_html, "text/html")
            email.send()
            
            logger.info(f"E-mail enviado: {assunto} para {len(destinatarios)} destinatário(s)")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {e}")
            return False
    
    # ========================================================================
    # NOTIFICAÇÕES DE BUDGET
    # ========================================================================
    
    @staticmethod
    def notificar_novo_budget(budget):
        """
        Notifica criação de novo budget
        """
        assunto = f"Novo Budget Criado: {budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0066cc;">🆕 Novo Budget Criado</h2>
            
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Código:</td>
                    <td style="padding: 8px;">{budget.codigo}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Descrição:</td>
                    <td style="padding: 8px;">{budget.descricao}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Valor de Venda:</td>
                    <td style="padding: 8px;">R$ {budget.valor_venda:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Custo Previsto:</td>
                    <td style="padding: 8px;">R$ {budget.custo_total_previsto:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Margem:</td>
                    <td style="padding: 8px; color: {'green' if budget.margem_prevista_percentual > 0 else 'red'};">
                        {budget.margem_prevista_percentual:.2f}%
                    </td>
                </tr>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="{settings.SITE_URL}/admin/financeiro/projectbudget/{budget.id}/" 
                   style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Ver Budget
                </a>
            </p>
        </body>
        </html>
        """
        
        destinatarios = NotificadorBudget._get_destinatarios_budget(budget)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    @staticmethod
    def notificar_inicio_execucao(budget):
        """
        Notifica início de execução do budget
        """
        assunto = f"Budget em Execução: {budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #28a745;">▶️ Budget Iniciou Execução</h2>
            
            <p>O budget <strong>{budget.codigo}</strong> entrou em execução.</p>
            
            <table style="border-collapse: collapse; width: 100%;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Projeto:</td>
                    <td style="padding: 8px;">{budget.projeto or budget.descricao}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Data Início:</td>
                    <td style="padding: 8px;">{budget.data_inicio_real or 'Hoje'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Término Previsto:</td>
                    <td style="padding: 8px;">{budget.data_termino_prevista or 'Não definido'}</td>
                </tr>
            </table>
            
            <p style="margin-top: 20px; padding: 10px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                ⚠️ Atenção: Todos os lançamentos de despesa serão monitorados automaticamente.
            </p>
        </body>
        </html>
        """
        
        destinatarios = NotificadorBudget._get_destinatarios_budget(budget)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    # ========================================================================
    # ALERTAS DE SEMÁFORO
    # ========================================================================
    
    @staticmethod
    def notificar_zona_amarela(budget, despesa):
        """
        Alerta quando budget atinge zona amarela (80-95%)
        """
        assunto = f"⚠️ ALERTA: Budget {budget.codigo} em Zona Amarela ({budget.percentual_uso_budget:.1f}%)"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #fff3cd; padding: 20px; border-left: 5px solid #ffc107;">
                <h2 style="color: #856404; margin-top: 0;">🟡 ATENÇÃO: Zona Amarela</h2>
                
                <p style="font-size: 16px;">
                    O budget <strong>{budget.codigo}</strong> atingiu <strong>{budget.percentual_uso_budget:.1f}%</strong> de uso.
                </p>
                
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Custo Previsto:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">R$ {budget.custo_total_previsto:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Gasto Até Agora:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; color: #dc3545;">
                            R$ {(budget.custo_total_previsto * budget.percentual_uso_budget / 100):,.2f}
                        </td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Margem Restante:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">
                            R$ {(budget.custo_total_previsto * (100 - budget.percentual_uso_budget) / 100):,.2f}
                        </td>
                    </tr>
                </table>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Última Despesa:</h3>
                    <p><strong>{despesa.get_tipo_despesa_display()}:</strong> {despesa.descricao}</p>
                    <p><strong>Valor:</strong> R$ {despesa.valor:,.2f}</p>
                </div>
                
                <p style="font-size: 14px; color: #856404; font-weight: bold;">
                    ⚠️ AÇÃO NECESSÁRIA: Acompanhe de perto os próximos lançamentos. 
                    Ao atingir 95%, o budget será bloqueado automaticamente.
                </p>
                
                <p style="margin-top: 20px;">
                    <a href="{settings.SITE_URL}/admin/financeiro/projectbudget/{budget.id}/" 
                       style="background-color: #ffc107; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Visualizar Budget
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        destinatarios = NotificadorBudget._get_destinatarios_budget(budget)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    @staticmethod
    def notificar_zona_vermelha(budget, despesa):
        """
        Alerta CRÍTICO quando budget atinge zona vermelha (>95%)
        """
        assunto = f"🚨 CRÍTICO: Budget {budget.codigo} BLOQUEADO ({budget.percentual_uso_budget:.1f}%)"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8d7da; padding: 20px; border-left: 5px solid #dc3545;">
                <h2 style="color: #721c24; margin-top: 0;">🔴 CRÍTICO: Budget Bloqueado</h2>
                
                <p style="font-size: 18px; font-weight: bold; color: #721c24;">
                    O budget <strong>{budget.codigo}</strong> atingiu <strong>{budget.percentual_uso_budget:.1f}%</strong> de uso e foi BLOQUEADO automaticamente.
                </p>
                
                <div style="background-color: #721c24; color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-size: 16px; font-weight: bold;">
                        🔒 Novos lançamentos de despesa estão BLOQUEADOS
                    </p>
                    <p style="margin: 10px 0 0 0;">
                        É necessária uma justificativa aprovada para desbloquear.
                    </p>
                </div>
                
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Custo Previsto:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6;">R$ {budget.custo_total_previsto:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Gasto Real:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">
                            R$ {(budget.custo_total_previsto * budget.percentual_uso_budget / 100):,.2f}
                        </td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Estouro:</td>
                        <td style="padding: 12px; border: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">
                            R$ {(budget.custo_total_previsto * (budget.percentual_uso_budget - 100) / 100):,.2f}
                        </td>
                    </tr>
                </table>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #dc3545;">Despesa que Causou Bloqueio:</h3>
                    <p><strong>{despesa.get_tipo_despesa_display()}:</strong> {despesa.descricao}</p>
                    <p><strong>Valor:</strong> R$ {despesa.valor:,.2f}</p>
                    <p><strong>Data:</strong> {despesa.data_despesa}</p>
                </div>
                
                <p style="font-size: 14px; color: #721c24; font-weight: bold;">
                    ⚠️ AÇÃO URGENTE NECESSÁRIA:<br>
                    1. Revisar os custos do projeto<br>
                    2. Criar justificativa detalhada<br>
                    3. Aguardar aprovação do gestor
                </p>
                
                <p style="margin-top: 20px;">
                    <a href="{settings.SITE_URL}/admin/financeiro/projectbudget/{budget.id}/" 
                       style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                        Criar Justificativa
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        destinatarios = NotificadorBudget._get_destinatarios_budget(budget)
        
        # Enviar também para TODOS os gestores (prioridade alta)
        gestores_emails = User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True)
        destinatarios.extend(gestores_emails)
        
        return NotificadorBudget._enviar_email(assunto, mensagem_html, list(set(destinatarios)))
    
    # ========================================================================
    # JUSTIFICATIVAS
    # ========================================================================
    
    @staticmethod
    def notificar_nova_justificativa(justificativa):
        """
        Notifica gestores sobre nova justificativa pendente
        """
        assunto = f"Nova Justificativa de Budget: {justificativa.budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #0066cc;">📝 Nova Justificativa Aguardando Aprovação</h2>
            
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Budget:</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{justificativa.budget.codigo}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Motivo:</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{justificativa.get_motivo_display()}</td>
                </tr>
                <tr style="background-color: #f8f9fa;">
                    <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Valor Adicional:</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">R$ {justificativa.valor_adicional_necessario:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: bold; border: 1px solid #dee2e6;">Solicitado Por:</td>
                    <td style="padding: 12px; border: 1px solid #dee2e6;">{justificativa.solicitado_por.get_full_name() or justificativa.solicitado_por.username}</td>
                </tr>
            </table>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Descrição:</h3>
                <p>{justificativa.descricao}</p>
            </div>
            
            <p style="margin-top: 20px;">
                <a href="{settings.SITE_URL}/admin/financeiro/justificativabudget/{justificativa.id}/" 
                   style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">
                    Aprovar
                </a>
                <a href="{settings.SITE_URL}/admin/financeiro/justificativabudget/{justificativa.id}/" 
                   style="background-color: #dc3545; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Rejeitar
                </a>
            </p>
        </body>
        </html>
        """
        
        # Enviar apenas para gestores
        gestores_emails = User.objects.filter(
            is_staff=True,
            is_active=True
        ).values_list('email', flat=True)
        
        return NotificadorBudget._enviar_email(assunto, mensagem_html, list(gestores_emails))
    
    @staticmethod
    def notificar_justificativa_aprovada(justificativa):
        """
        Notifica solicitante que justificativa foi aprovada
        """
        assunto = f"✅ Justificativa Aprovada: {justificativa.budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #d4edda; padding: 20px; border-left: 5px solid #28a745;">
                <h2 style="color: #155724; margin-top: 0;">✅ Justificativa Aprovada</h2>
                
                <p>Sua justificativa para o budget <strong>{justificativa.budget.codigo}</strong> foi aprovada.</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Parecer:</strong></p>
                    <p>{justificativa.parecer or 'Sem observações'}</p>
                    <p><strong>Aprovado por:</strong> {justificativa.aprovado_por.get_full_name() if justificativa.aprovado_por else 'N/A'}</p>
                </div>
                
                <p style="color: #155724; font-weight: bold;">
                    O budget foi desbloqueado e você pode continuar lançando despesas.
                </p>
            </div>
        </body>
        </html>
        """
        
        destinatarios = [justificativa.solicitado_por.email] if justificativa.solicitado_por.email else []
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    @staticmethod
    def notificar_justificativa_rejeitada(justificativa):
        """
        Notifica solicitante que justificativa foi rejeitada
        """
        assunto = f"❌ Justificativa Rejeitada: {justificativa.budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8d7da; padding: 20px; border-left: 5px solid #dc3545;">
                <h2 style="color: #721c24; margin-top: 0;">❌ Justificativa Rejeitada</h2>
                
                <p>Sua justificativa para o budget <strong>{justificativa.budget.codigo}</strong> foi rejeitada.</p>
                
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Motivo da Rejeição:</strong></p>
                    <p>{justificativa.parecer}</p>
                    <p><strong>Rejeitado por:</strong> {justificativa.aprovado_por.get_full_name() if justificativa.aprovado_por else 'N/A'}</p>
                </div>
                
                <p style="color: #721c24; font-weight: bold;">
                    O budget continua bloqueado. Entre em contato com a gestão para mais informações.
                </p>
            </div>
        </body>
        </html>
        """
        
        destinatarios = [justificativa.solicitado_por.email] if justificativa.solicitado_por.email else []
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    # ========================================================================
    # OUTROS ALERTAS
    # ========================================================================
    
    @staticmethod
    def alertar_venda_prejuizo(budget):
        """
        Alerta quando budget tem margem negativa (venda com prejuízo)
        """
        assunto = f"⚠️ ALERTA: Venda com Prejuízo - {budget.codigo}"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f8d7da; padding: 20px; border-left: 5px solid #dc3545;">
                <h2 style="color: #721c24; margin-top: 0;">⚠️ VENDA COM PREJUÍZO DETECTADA</h2>
                
                <p style="font-size: 16px; font-weight: bold;">
                    O budget <strong>{budget.codigo}</strong> tem margem NEGATIVA de {budget.margem_prevista_percentual:.2f}%
                </p>
                
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold;">Valor de Venda:</td>
                        <td style="padding: 12px;">R$ {budget.valor_venda:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold;">Custo Previsto:</td>
                        <td style="padding: 12px; color: #dc3545;">R$ {budget.custo_total_previsto:,.2f}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 12px; font-weight: bold;">Prejuízo:</td>
                        <td style="padding: 12px; color: #dc3545; font-weight: bold;">R$ {abs(budget.lucro_previsto):,.2f}</td>
                    </tr>
                </table>
                
                <p style="font-size: 14px; color: #721c24; font-weight: bold;">
                    AÇÃO NECESSÁRIA: Revisar orçamento ou renegociar com cliente.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Enviar para gestores e vendedor
        gestores_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, list(gestores_emails))
    
    @staticmethod
    def alertar_budget_atrasado(budget):
        """
        Alerta quando budget está atrasado
        """
        from datetime import date
        
        dias_atraso = (date.today() - budget.data_termino_prevista).days
        
        assunto = f"⏰ Budget Atrasado: {budget.codigo} ({dias_atraso} dias)"
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #ff9800;">⏰ Budget em Atraso</h2>
            
            <p>O budget <strong>{budget.codigo}</strong> está <strong>{dias_atraso} dia(s) atrasado</strong>.</p>
            
            <p><strong>Data prevista de término:</strong> {budget.data_termino_prevista}</p>
            <p><strong>Status atual:</strong> {budget.get_status_display()}</p>
            
            <p>Por favor, verifique o andamento do projeto.</p>
        </body>
        </html>
        """
        
        destinatarios = NotificadorBudget._get_destinatarios_budget(budget)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, destinatarios)
    
    @staticmethod
    def relatorio_budgets_criticos(budgets_criticos):
        """
        Envia relatório consolidado de budgets críticos (diário)
        """
        assunto = f"📊 Relatório Diário: {budgets_criticos.count()} Budget(s) em Situação Crítica"
        
        linhas_tabela = ""
        for budget in budgets_criticos:
            cor_semaforo = {
                'VERDE': '#28a745',
                'AMARELO': '#ffc107',
                'VERMELHO': '#dc3545'
            }.get(budget.semaforo, '#6c757d')
            
            linhas_tabela += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #dee2e6;">{budget.codigo}</td>
                <td style="padding: 8px; border: 1px solid #dee2e6;">{budget.descricao[:30]}</td>
                <td style="padding: 8px; border: 1px solid #dee2e6; background-color: {cor_semaforo}; color: white; text-align: center;">
                    {budget.get_semaforo_display()}
                </td>
                <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">
                    {budget.percentual_uso_budget:.1f}%
                </td>
                <td style="padding: 8px; border: 1px solid #dee2e6; text-align: center;">
                    {'🔒 SIM' if budget.bloqueado else 'Não'}
                </td>
            </tr>
            """
        
        mensagem_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>📊 Relatório de Budgets em Situação Crítica</h2>
            
            <p>Total de budgets em situação crítica: <strong>{budgets_criticos.count()}</strong></p>
            
            <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #343a40; color: white;">
                        <th style="padding: 12px; border: 1px solid #dee2e6;">Código</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6;">Descrição</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6;">Semáforo</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6;">Uso</th>
                        <th style="padding: 12px; border: 1px solid #dee2e6;">Bloqueado</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas_tabela}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        gestores_emails = User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True)
        return NotificadorBudget._enviar_email(assunto, mensagem_html, list(gestores_emails))
