"""
Serviços para o módulo de usuários
Contém lógica de negócio isolada das views
"""
import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .models import BackupBancoDados, Empresa

logger = logging.getLogger(__name__)


class BackupService:
    """
    Serviço responsável por gerar e gerenciar backups do banco de dados MySQL
    """
    
    def __init__(self):
        # Diretório onde os backups serão salvos
        self.backup_dir = getattr(settings, 'BACKUP_DIR', '/var/backups/serrana_app')
        
        # Garantir que o diretório existe
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Configurações do banco de dados
        db_config = settings.DATABASES['default']
        self.db_name = db_config['NAME']
        self.db_user = db_config['USER']
        self.db_password = db_config['PASSWORD']
        self.db_host = db_config.get('HOST', 'localhost')
        self.db_port = db_config.get('PORT', '3306')
        
        # Dias de retenção de backups
        self.retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
    
    def gerar_backup(self, empresa, usuario, tipo_backup='manual'):
        """
        Gera um backup do banco de dados MySQL
        
        Args:
            empresa: Instância do modelo Empresa
            usuario: Instância do modelo User que está gerando o backup (pode ser None para agendados)
            tipo_backup: 'manual' ou 'agendado'
            
        Returns:
            BackupBancoDados: Instância do backup criado
        """
        # Criar registro de backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefixo = 'manual' if tipo_backup == 'manual' else 'auto'
        nome_arquivo = f"backup_{prefixo}_{self.db_name}_{timestamp}.sql"
        caminho_completo = os.path.join(self.backup_dir, nome_arquivo)
        
        backup = BackupBancoDados.objects.create(
            empresa=empresa,
            usuario=usuario,
            nome_arquivo=nome_arquivo,
            caminho_arquivo=caminho_completo,
            database_name=self.db_name,
            status='processando',
            tipo_backup=tipo_backup,
            protegido=False,  # Por padrão não é protegido
            data_expiracao=timezone.now() + timedelta(days=self.retention_days)
        )
        
        inicio = timezone.now()
        
        try:
            # Executar mysqldump
            self._executar_mysqldump(caminho_completo)
            
            # Calcular tamanho do arquivo
            tamanho = os.path.getsize(caminho_completo)
            
            # Calcular tempo de execução
            fim = timezone.now()
            tempo_execucao = (fim - inicio).total_seconds()
            
            # Atualizar registro
            backup.status = 'concluido'
            backup.tamanho_bytes = tamanho
            backup.tempo_execucao_segundos = tempo_execucao
            backup.concluido_em = fim
            backup.save()
            
            logger.info(f"Backup gerado com sucesso: {nome_arquivo} ({backup.tamanho_formatado})")
            
            return backup
            
        except Exception as e:
            # Registrar erro
            backup.status = 'erro'
            backup.mensagem_erro = str(e)
            backup.concluido_em = timezone.now()
            backup.save()
            
            logger.error(f"Erro ao gerar backup: {str(e)}")
            
            # Remover arquivo parcial se existir
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except:
                    pass
            
            raise
    
    def _executar_mysqldump(self, caminho_arquivo):
        """
        Executa o comando mysqldump para gerar o backup
        
        Args:
            caminho_arquivo: Caminho completo onde o backup será salvo
        """
        # Construir comando mysqldump
        # IMPORTANTE: Usar variável de ambiente para senha evita exposição na linha de comando
        cmd = [
            'mysqldump',
            f'--host={self.db_host}',
            f'--port={self.db_port}',
            f'--user={self.db_user}',
            '--single-transaction',  # Para InnoDB, evita lock
            '--quick',  # Para tabelas grandes
            '--lock-tables=false',  # Não bloquear tabelas
            '--add-drop-table',  # Adicionar DROP TABLE antes de CREATE TABLE
            '--routines',  # Incluir stored procedures e functions
            '--triggers',  # Incluir triggers
            '--events',  # Incluir events
            self.db_name
        ]
        
        # Configurar ambiente com a senha
        env = os.environ.copy()
        env['MYSQL_PWD'] = self.db_password
        
        try:
            # Executar comando e salvar saída em arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                result = subprocess.run(
                    cmd,
                    env=env,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    timeout=3600  # Timeout de 1 hora
                )
            
            # Verificar se houve warnings no stderr
            if result.stderr:
                logger.warning(f"Warnings do mysqldump: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Erro ao executar mysqldump: {e.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        except subprocess.TimeoutExpired:
            error_msg = "Timeout ao executar mysqldump (>1 hora)"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def limpar_backups_antigos(self):
        """
        Remove backups expirados do disco e do banco de dados
        
        Returns:
            tuple: (quantidade_removida, espaço_liberado_bytes)
        """
        backups_expirados = BackupBancoDados.objects.filter(
            data_expiracao__lt=timezone.now(),
            status='concluido'
        )
        
        quantidade = 0
        espaco_liberado = 0
        
        for backup in backups_expirados:
            try:
                # Remover arquivo do disco
                if os.path.exists(backup.caminho_arquivo):
                    espaco_liberado += backup.tamanho_bytes
                    os.remove(backup.caminho_arquivo)
                    logger.info(f"Arquivo removido: {backup.caminho_arquivo}")
                
                # Remover registro do banco
                backup.delete()
                quantidade += 1
                
            except Exception as e:
                logger.error(f"Erro ao limpar backup {backup.nome_arquivo}: {str(e)}")
        
        if quantidade > 0:
            logger.info(f"Limpeza concluída: {quantidade} backup(s) removido(s), "
                       f"{espaco_liberado / (1024*1024):.2f} MB liberados")
        
        return quantidade, espaco_liberado
    
    def aplicar_politica_retencao(self, config):
        """
        Aplica a política de retenção definida na configuração
        Remove backups antigos conforme as regras:
        - Manter apenas os últimos N backups (se configurado)
        - Manter apenas backups dos últimos X dias (se configurado)
        - NUNCA remove backups protegidos
        - Sempre mantém pelo menos 1 backup
        
        Args:
            config: Instância de BackupConfig
            
        Returns:
            int: Quantidade de backups removidos
        """
        from usuarios.models import BackupBancoDados
        
        quantidade_removida = 0
        
        try:
            # Buscar todos os backups agendados não protegidos
            backups = BackupBancoDados.objects.filter(
                tipo_backup='agendado',
                protegido=False,
                status='concluido'
            ).order_by('-criado_em')
            
            total_backups = backups.count()
            
            # Garantir que sempre mantém pelo menos 1 backup
            if total_backups <= 1:
                logger.info("Apenas 1 backup existe. Não aplicando política de retenção.")
                return 0
            
            backups_para_remover = []
            
            # Aplicar regra de "manter últimos N"
            if config.manter_ultimos_n > 0:
                # Pega backups além dos N mais recentes
                backups_excedentes = backups[config.manter_ultimos_n:]
                backups_para_remover.extend(list(backups_excedentes))
            
            # Aplicar regra de "manter por X dias"
            if config.manter_dias > 0:
                data_limite = timezone.now() - timedelta(days=config.manter_dias)
                backups_antigos = backups.filter(criado_em__lt=data_limite)
                
                for backup in backups_antigos:
                    if backup not in backups_para_remover:
                        backups_para_remover.append(backup)
            
            # Remover duplicatas
            backups_para_remover = list(set(backups_para_remover))
            
            # Garantir que mantém pelo menos 1 backup
            if len(backups_para_remover) >= total_backups:
                # Não remover o mais recente
                backups_ordenados = sorted(backups_para_remover, key=lambda x: x.criado_em, reverse=True)
                backups_para_remover = backups_ordenados[1:]  # Mantém o primeiro (mais recente)
            
            # Remover os backups
            for backup in backups_para_remover:
                try:
                    # Remover arquivo do disco
                    if os.path.exists(backup.caminho_arquivo):
                        os.remove(backup.caminho_arquivo)
                        logger.info(f"Arquivo removido pela política: {backup.caminho_arquivo}")
                    
                    # Remover registro do banco
                    backup.delete()
                    quantidade_removida += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao remover backup {backup.nome_arquivo}: {str(e)}")
            
            if quantidade_removida > 0:
                logger.info(f"Política de retenção aplicada: {quantidade_removida} backup(s) removido(s)")
            
        except Exception as e:
            logger.error(f"Erro ao aplicar política de retenção: {str(e)}")
        
        return quantidade_removida
    
    def verificar_arquivo_existe(self, backup):
        """
        Verifica se o arquivo de backup existe no disco
        
        Args:
            backup: Instância de BackupBancoDados
            
        Returns:
            bool: True se o arquivo existe
        """
        return os.path.exists(backup.caminho_arquivo)
    
    def obter_tamanho_arquivo(self, backup):
        """
        Obtém o tamanho real do arquivo no disco
        
        Args:
            backup: Instância de BackupBancoDados
            
        Returns:
            int: Tamanho em bytes ou 0 se o arquivo não existir
        """
        if os.path.exists(backup.caminho_arquivo):
            return os.path.getsize(backup.caminho_arquivo)
        return 0
