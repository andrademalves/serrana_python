"""
Management command para executar backups agendados do banco de dados
Deve ser chamado via cron a cada 5 minutos:
*/5 * * * * /path/to/venv/bin/python /path/to/manage.py run_scheduled_backups >> /var/log/backup_cron.log 2>&1
"""
import os
import fcntl
import sys
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from usuarios.models import BackupConfig, Empresa
from usuarios.services import BackupService


class Command(BaseCommand):
    help = 'Executa backups agendados do banco de dados MySQL'
    
    LOCK_FILE = os.path.join(settings.BASE_DIR, 'backups', '.backup_lock')
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a execução mesmo que não esteja no horário agendado',
        )
    
    def handle(self, *args, **options):
        """Executa o comando"""
        force = options.get('force', False)
        
        # Garantir que o diretório de backups existe
        os.makedirs(os.path.dirname(self.LOCK_FILE), exist_ok=True)
        
        # Tenta adquirir lock para evitar execuções concorrentes
        lock_file = None
        try:
            lock_file = open(self.LOCK_FILE, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            self.stdout.write(f"[{datetime.now()}] Lock adquirido. Iniciando verificação...")
            
            # Busca a configuração
            config = BackupConfig.get_config()
            
            if not config.habilitado and not force:
                self.stdout.write(self.style.WARNING("Backups agendados estão desabilitados."))
                return
            
            # Verifica se deve executar
            if not force and not config.deve_executar_hoje():
                self.stdout.write(f"Não é hora de executar. Próxima execução: {config.hora_execucao}")
                return
            
            self.stdout.write(self.style.SUCCESS(f"Iniciando backup agendado..."))
            
            # Executa o backup
            sucesso = self._executar_backup(config)
            
            if sucesso:
                self.stdout.write(self.style.SUCCESS("✓ Backup agendado concluído com sucesso"))
                
                # Aplica política de retenção
                self._aplicar_politica_retencao(config)
            else:
                self.stdout.write(self.style.ERROR("✗ Backup agendado falhou"))
        
        except IOError:
            self.stdout.write(self.style.WARNING(
                "Outro processo de backup já está em execução. Pulando..."
            ))
            sys.exit(0)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro inesperado: {str(e)}"))
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        finally:
            if lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    os.remove(self.LOCK_FILE)
                except:
                    pass
    
    def _executar_backup(self, config):
        """
        Executa o backup para todas as empresas
        Retorna True se bem-sucedido, False caso contrário
        """
        try:
            # Busca a primeira empresa ativa (backup é do banco inteiro)
            empresa = Empresa.objects.filter(ativa=True).first()
            
            if not empresa:
                mensagem = "Nenhuma empresa ativa encontrada"
                self._atualizar_status_execucao(config, 'erro', mensagem)
                self.stdout.write(self.style.ERROR(mensagem))
                return False
            
            self.stdout.write(f"Gerando backup para empresa: {empresa.razao_social}")
            
            # Instancia o serviço e gera o backup
            service = BackupService()
            backup = service.gerar_backup(
                empresa=empresa,
                usuario=None,  # NULL para backups agendados
                tipo_backup='agendado'
            )
            
            if backup.status == 'concluido':
                mensagem = f"Backup gerado: {backup.nome_arquivo} ({backup.tamanho_formatado})"
                self._atualizar_status_execucao(config, 'concluido', mensagem)
                self.stdout.write(self.style.SUCCESS(f"  ✓ {mensagem}"))
                return True
            else:
                mensagem = f"Backup falhou: {backup.mensagem_erro or 'Erro desconhecido'}"
                self._atualizar_status_execucao(config, 'erro', mensagem)
                self.stdout.write(self.style.ERROR(f"  ✗ {mensagem}"))
                return False
        
        except Exception as e:
            mensagem = f"Erro ao gerar backup: {str(e)}"
            self._atualizar_status_execucao(config, 'erro', mensagem)
            self.stdout.write(self.style.ERROR(f"  ✗ {mensagem}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            return False
    
    def _atualizar_status_execucao(self, config, status, mensagem):
        """Atualiza o status da última execução na configuração"""
        config.ultima_execucao = datetime.now()
        config.status_ultima_execucao = status
        config.mensagem_ultima_execucao = mensagem
        config.save()
    
    def _aplicar_politica_retencao(self, config):
        """Aplica a política de retenção, removendo backups antigos"""
        try:
            self.stdout.write("Aplicando política de retenção...")
            
            service = BackupService()
            removidos = service.aplicar_politica_retencao(config)
            
            if removidos > 0:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ {removidos} backup(s) antigo(s) removido(s)"
                ))
            else:
                self.stdout.write("  • Nenhum backup a remover")
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"  ⚠ Erro ao aplicar política de retenção: {str(e)}"
            ))
