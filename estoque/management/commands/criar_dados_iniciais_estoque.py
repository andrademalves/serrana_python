"""
Management Command: Criar Dados Iniciais de Estoque
===================================================

Cria locais e destinos padrão para início do sistema.

Uso:
    python manage.py criar_dados_iniciais_estoque
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from estoque.models_profissional import LocalEstoque, DestinoEstoque


class Command(BaseCommand):
    help = 'Cria dados iniciais (locais e destinos padrão) do sistema de estoque'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(f'\n{"="*70}')
        )
        self.stdout.write(
            self.style.WARNING('CRIAÇÃO DE DADOS INICIAIS DO ESTOQUE')
        )
        self.stdout.write(
            self.style.WARNING(f'{"="*70}\n')
        )
        
        try:
            # Obter usuário admin
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('Nenhum superusuário encontrado. Crie um admin primeiro.')
                )
                return
            
            with transaction.atomic():
                # Criar locais padrão
                self.stdout.write('\n1. Criando Locais de Estoque...')
                locais_criados = 0
                
                locais_padrao = [
                    {
                        'codigo': 'ALMOX_MP',
                        'nome': 'Almoxarifado de Matéria-Prima',
                        'tipo': 'MP',
                        'permite_saldo_negativo': False,
                    },
                    {
                        'codigo': 'PRODUCAO',
                        'nome': 'Área de Produção/Fabricação',
                        'tipo': 'PRODUCAO',
                        'permite_saldo_negativo': True,
                    },
                    {
                        'codigo': 'ALMOX_PA',
                        'nome': 'Almoxarifado de Produto Acabado',
                        'tipo': 'PA',
                        'permite_saldo_negativo': False,
                    },
                    {
                        'codigo': 'LOJA',
                        'nome': 'Loja/Showroom',
                        'tipo': 'LOJA',
                        'permite_saldo_negativo': False,
                    },
                ]
                
                for dados in locais_padrao:
                    local, created = LocalEstoque.objects.get_or_create(
                        codigo=dados['codigo'],
                        defaults={
                            'nome': dados['nome'],
                            'tipo': dados['tipo'],
                            'permite_saldo_negativo': dados['permite_saldo_negativo'],
                            'ativo': True,
                            'criado_por': user
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Criado: {local.codigo} - {local.nome}')
                        )
                        locais_criados += 1
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f'  - Já existe: {local.codigo}')
                        )
                
                # Criar destinos padrão
                self.stdout.write('\n2. Criando Destinos de Estoque...')
                destinos_criados = 0
                
                destinos_padrao = [
                    {
                        'codigo': 'OBRA',
                        'nome': 'Obra/Projeto',
                        'descricao': 'Saída de material para obra/projeto de cliente',
                        'exige_obra': True,
                        'gera_custo_obra': True,
                    },
                    {
                        'codigo': 'LOJA',
                        'nome': 'Loja/Venda Balcão',
                        'descricao': 'Venda direta na loja',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                    {
                        'codigo': 'PRODUCAO',
                        'nome': 'Produção/Fabricação',
                        'descricao': 'Consumo em produção',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                    {
                        'codigo': 'PERDA',
                        'nome': 'Perda/Sucata',
                        'descricao': 'Material perdido, quebrado ou sucateado',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                    {
                        'codigo': 'AMOSTRA',
                        'nome': 'Amostra/Brinde',
                        'descricao': 'Amostras grátis ou brindes',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                    {
                        'codigo': 'MANUTENCAO',
                        'nome': 'Manutenção',
                        'descricao': 'Uso em manutenção de equipamentos ou instalações',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                    {
                        'codigo': 'CONSUMO',
                        'nome': 'Consumo Interno',
                        'descricao': 'Consumo interno geral',
                        'exige_obra': False,
                        'gera_custo_obra': False,
                    },
                ]
                
                for dados in destinos_padrao:
                    destino, created = DestinoEstoque.objects.get_or_create(
                        codigo=dados['codigo'],
                        defaults={
                            'nome': dados['nome'],
                            'descricao': dados['descricao'],
                            'exige_obra': dados['exige_obra'],
                            'gera_custo_obra': dados['gera_custo_obra'],
                            'ativo': True,
                            'criado_por': user
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Criado: {destino.codigo} - {destino.nome}')
                        )
                        destinos_criados += 1
                    else:
                        self.stdout.write(
                            self.style.NOTICE(f'  - Já existe: {destino.codigo}')
                        )
                
                # Resumo
                self.stdout.write(
                    self.style.SUCCESS(f'\n{"="*70}')
                )
                self.stdout.write(
                    self.style.SUCCESS('✓ DADOS INICIAIS CRIADOS COM SUCESSO!')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'{"="*70}')
                )
                self.stdout.write(f'  - Locais criados: {locais_criados}')
                self.stdout.write(f'  - Destinos criados: {destinos_criados}')
                self.stdout.write('')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Erro ao criar dados iniciais: {str(e)}')
            )
            raise
