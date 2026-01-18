"""
Serviço de Envio de E-mails
Envia e-mails via SMTP com retry e logging
Suporta SMTP personalizado por empresa
"""
from django.core.mail import send_mail, EmailMessage, get_connection
from django.conf import settings
from django.utils import timezone
from financeiro.models import LogCobranca
from financeiro.services.template_service import TemplateService
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Serviço para envio de e-mails"""
    
    @staticmethod
    def _get_connection(empresa):
        """
        Retorna conexão SMTP baseada nas configurações da empresa
        Se empresa não tem SMTP próprio, usa configurações padrão do Django
        """
        if not empresa:
            return None
        
        smtp_config = empresa.get_smtp_config()
        
        if smtp_config:
            # Usar SMTP da empresa
            logger.info(f"Usando SMTP da empresa: {empresa.nome_fantasia}")
            
            # TLS e SSL são mutuamente exclusivos
            use_tls = smtp_config['use_tls'] and not smtp_config['use_ssl']
            use_ssl = smtp_config['use_ssl'] and not smtp_config['use_tls']
            
            # Se ambos estão True, priorizar TLS
            if smtp_config['use_tls'] and smtp_config['use_ssl']:
                use_tls = True
                use_ssl = False
            
            return get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_config['host'],
                port=smtp_config['port'],
                username=smtp_config['username'],
                password=smtp_config['password'],
                use_tls=use_tls,
                use_ssl=use_ssl,
                fail_silently=False,
            )
        else:
            # Usar SMTP padrão do settings
            logger.info("Usando SMTP padrão do sistema")
            return None
    
    @staticmethod
    def _get_from_email(empresa):
        """Retorna e-mail remetente da empresa ou padrão"""
        if empresa and empresa.smtp_ativo and empresa.smtp_from_email:
            from_name = empresa.smtp_from_name or empresa.nome_fantasia
            return f'{from_name} <{empresa.smtp_from_email}>'
        return settings.DEFAULT_FROM_EMAIL
    
    @staticmethod
    def enviar_cobranca(log_id):
        """
        Envia e-mail de cobrança baseado no log
        """
        try:
            log = LogCobranca.objects.select_related(
                'parcela__titulo__empresa',
                'etapa'
            ).get(id=log_id)
            
            # Atualiza status
            log.status = 'PROCESSANDO'
            log.tentativas += 1
            log.data_tentativa = timezone.now()
            log.save()
            
            # Renderiza template
            parcela = log.parcela
            etapa = log.etapa
            empresa = parcela.titulo.empresa
            
            assunto = TemplateService.renderizar(etapa.assunto_email, parcela)
            mensagem = TemplateService.renderizar(etapa.template_email, parcela)
            
            # Armazena no log
            log.assunto = assunto
            log.mensagem = mensagem
            log.save()
            
            # Conexão SMTP da empresa
            connection = EmailService._get_connection(empresa)
            from_email = EmailService._get_from_email(empresa)
            
            # Envia e-mail
            email = EmailMessage(
                subject=assunto,
                body=mensagem,
                from_email=from_email,
                to=[log.destinatario],
                connection=connection,
            )
            
            email.send(fail_silently=False)
            
            # Sucesso
            log.status = 'ENVIADO'
            log.data_envio = timezone.now()
            log.erro = None
            log.save()
            
            logger.info(f"E-mail enviado com sucesso: Log {log.id} para {log.destinatario}")
            
            return True
            
        except LogCobranca.DoesNotExist:
            logger.error(f"Log {log_id} não encontrado")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail (Log {log_id}): {str(e)}")
            
            # Atualiza log com erro
            log.status = 'FALHA'
            log.erro = str(e)
            log.save()
            
            # Retry se ainda tem tentativas
            if log.pode_reprocessar():
                # Aqui poderia enfileirar novamente com delay
                pass
            
            return False
    
    @staticmethod
    def testar_configuracao(empresa=None):
        """
        Testa se configuração de SMTP está funcionando
        Se empresa fornecida, testa SMTP da empresa
        Senão, testa SMTP padrão do sistema
        """
        try:
            connection = EmailService._get_connection(empresa) if empresa else None
            from_email = EmailService._get_from_email(empresa) if empresa else settings.DEFAULT_FROM_EMAIL
            
            # E-mail de teste para o próprio remetente
            to_email = empresa.smtp_from_email if (empresa and empresa.smtp_from_email) else settings.DEFAULT_FROM_EMAIL
            
            send_mail(
                'Teste de Configuração SMTP',
                f'Teste realizado em {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}\n\n'
                f'Se você recebeu este e-mail, o SMTP está configurado corretamente.\n\n'
                f'Empresa: {empresa.nome_fantasia if empresa else "Sistema"}\n'
                f'Host: {empresa.smtp_host if empresa else settings.EMAIL_HOST}',
                from_email,
                [to_email],
                fail_silently=False,
                connection=connection,
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao testar SMTP: {str(e)}")
            return False
