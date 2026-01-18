"""
Comando para recalcular todos os saldos de estoque a partir dos movimentos.

Útil para:
- Corrigir inconsistências
- Após importação de dados
- Manutenção periódica

Uso:
    python manage.py recalcular_saldos_estoque
    python manage.py recalcular_saldos_estoque --item ITEM000001
    python manage.py recalcular_saldos_estoque --local ALMOX01
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from estoque.models import Item, LocalEstoque, MovimentoEstoque, SaldoEstoque


class Command(BaseCommand):
    help = 'Recalcula saldos de estoque a partir dos movimentos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--item',
            type=str,
            help='Código do item para recalcular (opcional - se omitido, recalcula todos)',
        )
        parser.add_argument(
            '--local',
            type=str,
            help='Código do local para recalcular (opcional - se omitido, recalcula todos)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o recálculo sem salvar',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        codigo_item = options.get('item')
        codigo_local = options.get('local')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODO DRY-RUN ==='))
        
        self.stdout.write(self.style.SUCCESS('Iniciando recálculo de saldos...'))
        
        try:
            with transaction.atomic():
                # Filtrar itens e locais se especificado
                itens = Item.objects.filter(ativo=True)
                if codigo_item:
                    itens = itens.filter(codigo=codigo_item)
                    if not itens.exists():
                        self.stdout.write(self.style.ERROR(f'Item {codigo_item} não encontrado'))
                        return
                
                locais = LocalEstoque.objects.filter(ativo=True)
                if codigo_local:
                    locais = locais.filter(codigo=codigo_local)
                    if not locais.exists():
                        self.stdout.write(self.style.ERROR(f'Local {codigo_local} não encontrado'))
                        return
                
                # Limpar saldos afetados
                saldos_query = SaldoEstoque.objects.all()
                if codigo_item:
                    saldos_query = saldos_query.filter(item__codigo=codigo_item)
                if codigo_local:
                    saldos_query = saldos_query.filter(local__codigo=codigo_local)
                
                saldos_deletados = saldos_query.count()
                saldos_query.delete()
                self.stdout.write(f'Saldos antigos removidos: {saldos_deletados}')
                
                # Processar movimentos
                movimentos = MovimentoEstoque.objects.all().order_by('data_movimento', 'criado_em')
                if codigo_item:
                    movimentos = movimentos.filter(item__codigo=codigo_item)
                if codigo_local:
                    movimentos = movimentos.filter(
                        local_origem__codigo=codigo_local
                    ) | movimentos.filter(
                        local_destino__codigo=codigo_local
                    )
                
                total_movimentos = movimentos.count()
                self.stdout.write(f'Movimentos a processar: {total_movimentos}')
                
                # Processar cada movimento
                processados = 0
                erros = 0
                
                for movimento in movimentos:
                    try:
                        self._processar_movimento(movimento)
                        processados += 1
                        
                        if processados % 100 == 0:
                            self.stdout.write(f'  Processados: {processados}/{total_movimentos}')
                    
                    except Exception as e:
                        erros += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  Erro no movimento {movimento.id}: {str(e)}'
                            )
                        )
                
                # Estatísticas finais
                novos_saldos = SaldoEstoque.objects.all()
                if codigo_item:
                    novos_saldos = novos_saldos.filter(item__codigo=codigo_item)
                if codigo_local:
                    novos_saldos = novos_saldos.filter(local__codigo=codigo_local)
                
                total_saldos = novos_saldos.count()
                
                self.stdout.write(self.style.SUCCESS(f'\n=== RESULTADO ==='))
                self.stdout.write(f'Movimentos processados: {processados}')
                self.stdout.write(f'Erros: {erros}')
                self.stdout.write(f'Saldos criados: {total_saldos}')
                
                # Mostrar alguns saldos
                self.stdout.write('\nAmostras de saldos:')
                for saldo in novos_saldos[:10]:
                    self.stdout.write(
                        f'  {saldo.item.codigo} @ {saldo.local.codigo}: '
                        f'{saldo.quantidade} {saldo.item.unidade_medida} '
                        f'(Custo médio: R$ {saldo.custo_medio})'
                    )
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\nRollback (dry-run)'))
                    raise Exception('Dry-run')
                
            self.stdout.write(self.style.SUCCESS('\n✓ Recálculo concluído com sucesso!'))
        
        except Exception as e:
            if not dry_run:
                self.stdout.write(self.style.ERROR(f'\nErro no recálculo: {str(e)}'))
            else:
                self.stdout.write(self.style.SUCCESS('\n✓ Dry-run concluído'))
    
    def _processar_movimento(self, movimento):
        """Processa um movimento e atualiza saldos"""
        
        if movimento.tipo_movimento == 'ENTRADA':
            self._processar_entrada(movimento)
        
        elif movimento.tipo_movimento == 'SAIDA':
            self._processar_saida(movimento)
        
        elif movimento.tipo_movimento == 'TRANSFERENCIA':
            self._processar_transferencia(movimento)
        
        elif movimento.tipo_movimento == 'AJUSTE':
            self._processar_ajuste(movimento)
    
    def _processar_entrada(self, mov):
        """Processa entrada"""
        saldo, created = SaldoEstoque.objects.get_or_create(
            item=mov.item,
            local=mov.local_destino,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        # WAC - Weighted Average Cost
        if mov.custo_unitario > 0:
            quantidade_anterior = saldo.quantidade
            valor_anterior = quantidade_anterior * saldo.custo_medio
            valor_entrada = mov.quantidade * mov.custo_unitario
            quantidade_nova = quantidade_anterior + mov.quantidade
            
            if quantidade_nova > 0:
                saldo.custo_medio = (
                    (valor_anterior + valor_entrada) / quantidade_nova
                ).quantize(Decimal('0.0001'))
        
        saldo.quantidade += mov.quantidade
        saldo.save()
    
    def _processar_saida(self, mov):
        """Processa saída"""
        saldo, created = SaldoEstoque.objects.get_or_create(
            item=mov.item,
            local=mov.local_origem,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        saldo.quantidade -= mov.quantidade
        saldo.save()
    
    def _processar_transferencia(self, mov):
        """Processa transferência"""
        # Saída do origem
        saldo_origem, created = SaldoEstoque.objects.get_or_create(
            item=mov.item,
            local=mov.local_origem,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        custo_transferencia = saldo_origem.custo_medio
        saldo_origem.quantidade -= mov.quantidade
        saldo_origem.save()
        
        # Entrada no destino
        saldo_destino, created = SaldoEstoque.objects.get_or_create(
            item=mov.item,
            local=mov.local_destino,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        # WAC no destino
        quantidade_anterior = saldo_destino.quantidade
        valor_anterior = quantidade_anterior * saldo_destino.custo_medio
        valor_transferido = mov.quantidade * custo_transferencia
        quantidade_nova = quantidade_anterior + mov.quantidade
        
        if quantidade_nova > 0:
            saldo_destino.custo_medio = (
                (valor_anterior + valor_transferido) / quantidade_nova
            ).quantize(Decimal('0.0001'))
        
        saldo_destino.quantidade += mov.quantidade
        saldo_destino.save()
    
    def _processar_ajuste(self, mov):
        """Processa ajuste"""
        local = mov.local_destino or mov.local_origem
        
        saldo, created = SaldoEstoque.objects.get_or_create(
            item=mov.item,
            local=local,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        if mov.quantidade > 0:  # Ajuste positivo
            if mov.custo_unitario > 0:
                quantidade_anterior = saldo.quantidade
                valor_anterior = quantidade_anterior * saldo.custo_medio
                valor_ajuste = mov.quantidade * mov.custo_unitario
                quantidade_nova = quantidade_anterior + mov.quantidade
                
                if quantidade_nova > 0:
                    saldo.custo_medio = (
                        (valor_anterior + valor_ajuste) / quantidade_nova
                    ).quantize(Decimal('0.0001'))
            
            saldo.quantidade += mov.quantidade
        else:  # Ajuste negativo
            saldo.quantidade += mov.quantidade
        
        saldo.save()
