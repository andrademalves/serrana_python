"""
Comando para migrar dados do sistema antigo de estoque para o novo modelo.

Migra:
1. Produtos antigos -> Itens novos
2. Movimentações antigas -> MovimentoEstoque
3. Recalcula saldos

Uso:
    python manage.py migrar_estoque_antigo
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime
from estoque.models import (
    Item, GrupoItem, LocalEstoque, DestinoEstoque,
    MovimentoEstoque, SaldoEstoque
)


class Command(BaseCommand):
    help = 'Migra dados do sistema antigo de estoque para o novo modelo'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a migração sem salvar dados',
        )
        parser.add_argument(
            '--skip-produtos',
            action='store_true',
            help='Pula a migração de produtos',
        )
        parser.add_argument(
            '--skip-movimentos',
            action='store_true',
            help='Pula a migração de movimentos',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODO DRY-RUN (não salvará dados) ==='))
        
        self.stdout.write(self.style.SUCCESS('Iniciando migração de estoque...'))
        
        try:
            with transaction.atomic():
                # 1. Criar dados iniciais (locais e destinos)
                self.criar_dados_iniciais()
                
                # 2. Migrar produtos -> itens (se não pular)
                if not options['skip_produtos']:
                    self.migrar_produtos()
                else:
                    self.stdout.write(self.style.WARNING('Pulando migração de produtos'))
                
                # 3. Migrar movimentações antigas (se não pular)
                if not options['skip_movimentos']:
                    self.migrar_movimentacoes()
                else:
                    self.stdout.write(self.style.WARNING('Pulando migração de movimentações'))
                
                # 4. Recalcular saldos
                self.recalcular_saldos()
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('Rollback (dry-run)'))
                    raise Exception('Dry-run - rollback intencional')
                
            self.stdout.write(self.style.SUCCESS('Migração concluída com sucesso!'))
        
        except Exception as e:
            if not dry_run:
                self.stdout.write(self.style.ERROR(f'Erro na migração: {str(e)}'))
            else:
                self.stdout.write(self.style.SUCCESS('Dry-run concluído'))
    
    def criar_dados_iniciais(self):
        """Cria locais e destinos padrão se não existirem"""
        self.stdout.write('Criando dados iniciais...')
        
        # Local padrão
        local, created = LocalEstoque.objects.get_or_create(
            codigo='ALMOX01',
            defaults={
                'descricao': 'Almoxarifado Geral',
                'permite_saldo_negativo': False,
                'ativo': True,
            }
        )
        if created:
            self.stdout.write(f'  ✓ Local criado: {local.codigo}')
        else:
            self.stdout.write(f'  - Local já existe: {local.codigo}')
        
        # Destinos padrão
        destinos_padrao = [
            ('PROJ', 'Projeto/Obra', 'PROJETO', True),
            ('LOJA', 'Loja Pronta Entrega', 'LOJA', True),
            ('PROD', 'Produção', 'PRODUCAO', True),
            ('MANUT', 'Manutenção', 'MANUTENCAO', False),
            ('AMOSTRA', 'Amostra', 'AMOSTRA', False),
            ('PERDA', 'Perda/Sucata', 'PERDA', False),
            ('OUTROS', 'Outros', 'OUTROS', False),
        ]
        
        for codigo, descricao, tipo, controla_custo in destinos_padrao:
            destino, created = DestinoEstoque.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'descricao': descricao,
                    'tipo': tipo,
                    'controla_custo': controla_custo,
                    'ativo': True,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Destino criado: {destino.codigo}')
    
    def migrar_produtos(self):
        """Migra tabela produtos antiga para itens"""
        self.stdout.write('Migrando produtos para itens...')
        
        # Importar modelo antigo (assumindo que ainda existe)
        try:
            from django.db import connection
            
            with connection.cursor() as cursor:
                # Verificar se tabela produtos existe
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'produtos'
                """)
                
                if cursor.fetchone()[0] == 0:
                    self.stdout.write(self.style.WARNING('  Tabela "produtos" não encontrada. Pulando...'))
                    return
                
                # Buscar produtos
                cursor.execute("""
                    SELECT 
                        id_produto,
                        descricao_produto,
                        material,
                        usuario,
                        data_criacao
                    FROM produtos
                    WHERE descricao_produto IS NOT NULL AND descricao_produto != ''
                """)
                
                produtos = cursor.fetchall()
                total = len(produtos)
                self.stdout.write(f'  Encontrados {total} produtos')
                
                for i, (id_prod, descricao, material, usuario, data_criacao) in enumerate(produtos, 1):
                    # Gerar código único
                    codigo = f'ITEM{str(id_prod).zfill(6)}'
                    
                    # Verificar se já existe
                    if Item.objects.filter(codigo=codigo).exists():
                        self.stdout.write(f'  - [{i}/{total}] Item {codigo} já existe')
                        continue
                    
                    # Criar item
                    item = Item.objects.create(
                        codigo=codigo,
                        descricao=descricao or 'Sem descrição',
                        tipo_item='MP',  # Padrão: Matéria-Prima
                        unidade_medida='UN',  # Padrão: Unidade
                        ativo=True,
                        observacoes=f'Migrado de produtos (ID original: {id_prod}). Material: {material or "N/A"}',
                    )
                    
                    self.stdout.write(f'  ✓ [{i}/{total}] Item criado: {item.codigo}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erro ao migrar produtos: {str(e)}'))
            raise
    
    def migrar_movimentacoes(self):
        """Migra tabela estoque antiga para movimentos"""
        self.stdout.write('Migrando movimentações...')
        
        try:
            from django.db import connection
            
            local_padrao = LocalEstoque.objects.get(codigo='ALMOX01')
            destino_padrao = DestinoEstoque.objects.get(codigo='OUTROS')
            destino_projeto = DestinoEstoque.objects.get(codigo='PROJ')
            
            with connection.cursor() as cursor:
                # Verificar se tabela estoque existe
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'estoque'
                """)
                
                if cursor.fetchone()[0] == 0:
                    self.stdout.write(self.style.WARNING('  Tabela "estoque" não encontrada. Pulando...'))
                    return
                
                # 1. Migrar ENTRADAS
                cursor.execute("""
                    SELECT 
                        IDESTOQUE,
                        DOCUMENTO,
                        DOCUMENTO_TIPO,
                        IDMATERIAL,
                        QUANTIDADE_ENTRADA,
                        CUSTO_ENTRADA,
                        DATA_ENTRADA,
                        DATA_OPERACAO,
                        IDFORNECEDOR,
                        DESCRICAO,
                        IDUSUARIO
                    FROM estoque
                    WHERE QUANTIDADE_ENTRADA > 0
                    ORDER BY COALESCE(DATA_ENTRADA, DATA_OPERACAO)
                """)
                
                entradas = cursor.fetchall()
                self.stdout.write(f'  Migrando {len(entradas)} entradas...')
                
                for i, row in enumerate(entradas, 1):
                    (id_estoque, doc, doc_tipo, id_material, qtd, custo_entrada,
                     data_entrada, data_operacao, id_fornecedor, descricao, id_usuario) = row
                    
                    # Buscar item correspondente
                    codigo_item = f'ITEM{str(id_material).zfill(6)}'
                    try:
                        item = Item.objects.get(codigo=codigo_item)
                    except Item.DoesNotExist:
                        self.stdout.write(f'  ! Item {codigo_item} não encontrado. Pulando...')
                        continue
                    
                    # Calcular custo unitário
                    custo_unitario = (custo_entrada / qtd) if qtd > 0 and custo_entrada else Decimal('0.0000')
                    
                    # Data do movimento
                    data_mov = data_entrada or data_operacao or datetime.now()
                    
                    # Buscar fornecedor
                    fornecedor = None
                    if id_fornecedor:
                        try:
                            from cadastros.models import Pessoa
                            fornecedor = Pessoa.objects.get(id=id_fornecedor)
                        except:
                            pass
                    
                    # Buscar usuário
                    usuario = None
                    if id_usuario:
                        try:
                            usuario = User.objects.get(id=id_usuario)
                        except:
                            pass
                    
                    # Criar movimento
                    MovimentoEstoque.objects.create(
                        tipo_movimento='ENTRADA',
                        documento=doc or f'MIG-ENT-{id_estoque}',
                        documento_tipo=doc_tipo or 'OUT',
                        data_movimento=data_mov,
                        item=item,
                        local_destino=local_padrao,
                        fornecedor=fornecedor,
                        quantidade=Decimal(str(qtd)),
                        custo_unitario=custo_unitario,
                        custo_total=Decimal(str(custo_entrada or 0)),
                        observacao=f'Migrado do sistema antigo. {descricao or ""}',
                        criado_por=usuario,
                    )
                    
                    if i % 50 == 0:
                        self.stdout.write(f'  ✓ {i}/{len(entradas)} entradas processadas')
                
                self.stdout.write(f'  ✓ Total de entradas migradas: {len(entradas)}')
                
                # 2. Migrar SAÍDAS
                cursor.execute("""
                    SELECT 
                        IDESTOQUE,
                        DOCUMENTO,
                        DOCUMENTO_TIPO,
                        IDMATERIAL,
                        QUANTIDADE_SAIDA,
                        CUSTO_TOTAL,
                        DATA_SAIDA,
                        DATA_OPERACAO,
                        IDPROJETO,
                        IDSOLICITANTE,
                        DESCRICAO,
                        IDUSUARIO
                    FROM estoque
                    WHERE QUANTIDADE_SAIDA > 0
                    ORDER BY COALESCE(DATA_SAIDA, DATA_OPERACAO)
                """)
                
                saidas = cursor.fetchall()
                self.stdout.write(f'  Migrando {len(saidas)} saídas...')
                
                for i, row in enumerate(saidas, 1):
                    (id_estoque, doc, doc_tipo, id_material, qtd, custo_total,
                     data_saida, data_operacao, id_projeto, id_solicitante, descricao, id_usuario) = row
                    
                    # Buscar item
                    codigo_item = f'ITEM{str(id_material).zfill(6)}'
                    try:
                        item = Item.objects.get(codigo=codigo_item)
                    except Item.DoesNotExist:
                        continue
                    
                    # Calcular custo unitário
                    custo_unitario = (custo_total / qtd) if qtd > 0 and custo_total else Decimal('0.0000')
                    
                    # Data do movimento
                    data_mov = data_saida or data_operacao or datetime.now()
                    
                    # Destino e projeto
                    destino = destino_projeto if id_projeto else destino_padrao
                    projeto = None
                    if id_projeto:
                        try:
                            from projetos.models import Projeto
                            projeto = Projeto.objects.get(id=id_projeto)
                        except:
                            pass
                    
                    # Solicitante
                    solicitante = None
                    if id_solicitante:
                        try:
                            solicitante = User.objects.get(id=id_solicitante)
                        except:
                            pass
                    
                    # Usuário
                    usuario = None
                    if id_usuario:
                        try:
                            usuario = User.objects.get(id=id_usuario)
                        except:
                            pass
                    
                    # Criar movimento
                    MovimentoEstoque.objects.create(
                        tipo_movimento='SAIDA',
                        documento=doc or f'MIG-SAI-{id_estoque}',
                        documento_tipo=doc_tipo or 'OUT',
                        data_movimento=data_mov,
                        item=item,
                        local_origem=local_padrao,
                        destino=destino,
                        projeto=projeto,
                        quantidade=Decimal(str(qtd)),
                        custo_unitario=custo_unitario,
                        custo_total=Decimal(str(custo_total or 0)),
                        solicitante=solicitante,
                        observacao=f'Migrado do sistema antigo. {descricao or ""}',
                        criado_por=usuario,
                    )
                    
                    if i % 50 == 0:
                        self.stdout.write(f'  ✓ {i}/{len(saidas)} saídas processadas')
                
                self.stdout.write(f'  ✓ Total de saídas migradas: {len(saidas)}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erro ao migrar movimentações: {str(e)}'))
            raise
    
    def recalcular_saldos(self):
        """Recalcula todos os saldos a partir dos movimentos"""
        self.stdout.write('Recalculando saldos...')
        
        # Limpar saldos existentes
        SaldoEstoque.objects.all().delete()
        
        # Processar todos os movimentos em ordem cronológica
        movimentos = MovimentoEstoque.objects.all().order_by('data_movimento', 'criado_em')
        total = movimentos.count()
        
        self.stdout.write(f'  Processando {total} movimentos...')
        
        for i, movimento in enumerate(movimentos, 1):
            try:
                # O método _atualizar_saldos() será chamado automaticamente no save
                # mas como já foi salvo, precisamos chamar manualmente
                movimento._atualizar_saldos()
                
                if i % 100 == 0:
                    self.stdout.write(f'  ✓ {i}/{total} movimentos processados')
            
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Erro no movimento {movimento.id}: {str(e)}'))
        
        # Estatísticas finais
        total_saldos = SaldoEstoque.objects.count()
        total_itens = SaldoEstoque.objects.values('item').distinct().count()
        
        self.stdout.write(f'  ✓ Saldos recalculados: {total_saldos} registros')
        self.stdout.write(f'  ✓ Itens com saldo: {total_itens}')
