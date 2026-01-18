"""
Management Command: Atualizar Consumo Médio e Estoque Mínimo
=============================================================

Recalcula consumo_medio_diario e estoque_minimo de todos os produtos.
Deve ser executado periodicamente (job noturno/semanal).

Uso:
    python manage.py atualizar_consumo_medio
    python manage.py atualizar_consumo_medio --dias=60
    python manage.py atualizar_consumo_medio --dry-run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from estoque.services_profissional import EstoqueMinimoService


class Command(BaseCommand):
    help = 'Atualiza consumo médio diário e estoque mínimo de todos os produtos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=90,
            help='Período de análise em dias (padrão: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula execução sem alterar dados'
        )
    
    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.WARNING(f'\n{"="*70}')
        )
        self.stdout.write(
            self.style.WARNING(f'ATUALIZAÇÃO DE CONSUMO MÉDIO E ESTOQUE MÍNIMO')
        )
        self.stdout.write(
            self.style.WARNING(f'{"="*70}\n')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.NOTICE('[DRY RUN] Simulação - nenhum dado será alterado\n')
            )
        
        self.stdout.write(f'Período de análise: {dias} dias')
        self.stdout.write(f'Iniciando em: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}\n')
        
        try:
            if dry_run:
                self.stdout.write(
                    self.style.NOTICE('Simulação concluída (nenhum dado foi alterado)')
                )
            else:
                # Executar atualização
                resultado = EstoqueMinimoService.atualizar_consumo_medio_produtos(
                    dias_analise=dias
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Atualização concluída com sucesso!')
                )
                self.stdout.write(f'  - Produtos atualizados: {resultado["produtos_atualizados"]}')
                self.stdout.write(f'  - Produtos sem consumo: {resultado["produtos_sem_consumo"]}')
                self.stdout.write(f'  - Data/hora: {resultado["data_atualizacao"].strftime("%d/%m/%Y %H:%M:%S")}')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Erro durante atualização: {str(e)}')
            )
            raise
        
        self.stdout.write(
            self.style.WARNING(f'\n{"="*70}\n')
        )
