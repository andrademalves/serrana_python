"""
Comando para popular bancos brasileiros
"""
from django.core.management.base import BaseCommand
from financeiro.models import Banco


class Command(BaseCommand):
    help = 'Popula bancos brasileiros comuns'

    def handle(self, *args, **options):
        bancos_data = [
            {'codigo_compe': '001', 'nome': 'Banco do Brasil S.A.'},
            {'codigo_compe': '033', 'nome': 'Banco Santander (Brasil) S.A.'},
            {'codigo_compe': '104', 'nome': 'Caixa Econômica Federal'},
            {'codigo_compe': '237', 'nome': 'Banco Bradesco S.A.'},
            {'codigo_compe': '341', 'nome': 'Itaú Unibanco S.A.'},
            {'codigo_compe': '077', 'nome': 'Banco Inter S.A.'},
            {'codigo_compe': '212', 'nome': 'Banco Original S.A.'},
            {'codigo_compe': '260', 'nome': 'Nu Pagamentos S.A. (Nubank)'},
            {'codigo_compe': '290', 'nome': 'Pagseguro Internet S.A.'},
            {'codigo_compe': '323', 'nome': 'Mercado Pago'},
            {'codigo_compe': '336', 'nome': 'Banco C6 S.A.'},
            {'codigo_compe': '380', 'nome': 'PicPay Servicos S.A.'},
            {'codigo_compe': '422', 'nome': 'Banco Safra S.A.'},
            {'codigo_compe': '748', 'nome': 'Banco Cooperativo Sicredi S.A.'},
            {'codigo_compe': '756', 'nome': 'Banco Cooperativo do Brasil S.A. (Sicoob)'},
        ]

        criados = 0
        atualizados = 0

        for banco_info in bancos_data:
            banco, created = Banco.objects.update_or_create(
                codigo_compe=banco_info['codigo_compe'],
                defaults={
                    'nome': banco_info['nome'],
                    'ativo': True
                }
            )
            
            if created:
                criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Criado: {banco.codigo_compe} - {banco.nome}')
                )
            else:
                atualizados += 1
                self.stdout.write(
                    self.style.WARNING(f'• Atualizado: {banco.codigo_compe} - {banco.nome}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Processo concluído: {criados} bancos criados, {atualizados} atualizados'
            )
        )
