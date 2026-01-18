"""
Popula dados iniciais do módulo financeiro
Bancos, formas de pagamento, contas, centros de custo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal

from financeiro.models import (
    Banco, ContaFinanceira, FormaPagamento, CentroCusto
)


class Command(BaseCommand):
    help = 'Popula dados iniciais do financeiro'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Populando dados iniciais do financeiro...'))
        
        # Usuário padrão
        try:
            usuario = User.objects.get(username='admin')
        except User.DoesNotExist:
            usuario = User.objects.first()
        
        # ===== BANCOS =====
        self.stdout.write('Criando bancos...')
        bancos_data = [
            {'codigo_compe': '001', 'nome': 'Banco do Brasil'},
            {'codigo_compe': '104', 'nome': 'Caixa Econômica Federal'},
            {'codigo_compe': '237', 'nome': 'Bradesco'},
            {'codigo_compe': '341', 'nome': 'Itaú Unibanco'},
            {'codigo_compe': '033', 'nome': 'Santander'},
            {'codigo_compe': '748', 'nome': 'Sicredi'},
            {'codigo_compe': '756', 'nome': 'Sicoob'},
            {'codigo_compe': '077', 'nome': 'Banco Inter'},
            {'codigo_compe': '212', 'nome': 'Banco Original'},
            {'codigo_compe': '260', 'nome': 'Nu Pagamentos (Nubank)'},
        ]
        
        for banco_info in bancos_data:
            Banco.objects.get_or_create(
                codigo_compe=banco_info['codigo_compe'],
                defaults={
                    'nome': banco_info['nome'],
                    'ativo': True,
                    'criado_por': usuario
                }
            )
        
        # ===== FORMAS DE PAGAMENTO =====
        self.stdout.write('Criando formas de pagamento...')
        formas_data = [
            {
                'codigo': 'PIX',
                'descricao': 'PIX',
                'tipo': 'PIX',
                'prazo_compensacao': 0,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'DINHEIRO',
                'descricao': 'Dinheiro',
                'tipo': 'DINHEIRO',
                'prazo_compensacao': 0,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'BOLETO',
                'descricao': 'Boleto Bancário',
                'tipo': 'BOLETO',
                'prazo_compensacao': 1,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('2.50')
            },
            {
                'codigo': 'TED',
                'descricao': 'Transferência TED',
                'tipo': 'TRANSFERENCIA',
                'prazo_compensacao': 0,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'DOC',
                'descricao': 'Transferência DOC',
                'tipo': 'TRANSFERENCIA',
                'prazo_compensacao': 1,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'CREDITO',
                'descricao': 'Cartão de Crédito',
                'tipo': 'CARTAO_CREDITO',
                'prazo_compensacao': 30,
                'taxa_percentual': Decimal('2.99'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'DEBITO',
                'descricao': 'Cartão de Débito',
                'tipo': 'CARTAO_DEBITO',
                'prazo_compensacao': 1,
                'taxa_percentual': Decimal('1.99'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'CHEQUE',
                'descricao': 'Cheque',
                'tipo': 'CHEQUE',
                'prazo_compensacao': 2,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
            {
                'codigo': 'DEPOSITO',
                'descricao': 'Depósito Bancário',
                'tipo': 'DEPOSITO',
                'prazo_compensacao': 0,
                'taxa_percentual': Decimal('0.00'),
                'taxa_fixa': Decimal('0.00')
            },
        ]
        
        for forma_info in formas_data:
            FormaPagamento.objects.get_or_create(
                codigo=forma_info['codigo'],
                defaults={
                    **forma_info,
                    'ativo': True,
                    'criado_por': usuario
                }
            )
        
        # ===== CONTAS FINANCEIRAS =====
        self.stdout.write('Criando contas financeiras...')
        
        # Caixa
        ContaFinanceira.objects.get_or_create(
            nome='Caixa Geral',
            defaults={
                'tipo': 'CAIXA',
                'saldo_inicial': Decimal('0.00'),
                'limite_credito': Decimal('0.00'),
                'ativo': True,
                'criado_por': usuario
            }
        )
        
        # Conta Corrente exemplo
        try:
            bb = Banco.objects.get(codigo_compe='001')
            ContaFinanceira.objects.get_or_create(
                nome='Conta Corrente - Banco do Brasil',
                defaults={
                    'tipo': 'CONTA_CORRENTE',
                    'banco': bb,
                    'agencia': '0001',
                    'conta': '00001-0',
                    'saldo_inicial': Decimal('0.00'),
                    'limite_credito': Decimal('5000.00'),
                    'ativo': True,
                    'criado_por': usuario
                }
            )
        except Banco.DoesNotExist:
            pass
        
        # ===== CENTROS DE CUSTO =====
        self.stdout.write('Criando centros de custo...')
        centros_data = [
            {'codigo': 'ADM', 'nome': 'Administrativo', 'tipo': 'ADMINISTRATIVO'},
            {'codigo': 'PROD', 'nome': 'Produção', 'tipo': 'PRODUCAO'},
            {'codigo': 'COM', 'nome': 'Comercial', 'tipo': 'COMERCIAL'},
            {'codigo': 'LOJA', 'nome': 'Loja/Showroom', 'tipo': 'LOJA'},
        ]
        
        for centro_info in centros_data:
            CentroCusto.objects.get_or_create(
                codigo=centro_info['codigo'],
                defaults={
                    **centro_info,
                    'ativo': True,
                    'criado_por': usuario
                }
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Dados iniciais criados com sucesso!'))
        self.stdout.write(self.style.SUCCESS(f'  - Bancos: {Banco.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - Formas de Pagamento: {FormaPagamento.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - Contas Financeiras: {ContaFinanceira.objects.count()}'))
        self.stdout.write(self.style.SUCCESS(f'  - Centros de Custo: {CentroCusto.objects.count()}'))
