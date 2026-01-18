from django.core.management.base import BaseCommand
from cadastros.models import Pessoa
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Popula alguns vendedores de exemplo no sistema'

    def handle(self, *args, **options):
        # Pegar ou criar usuário admin para auditoria
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@serrana.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Usuário admin criado'))

        # Lista de vendedores para criar
        vendedores_data = [
            {
                'tipo': 'F',
                'nome': 'João Silva',
                'cpf_cnpj': '111.111.111-11',
                'email': 'joao.silva@serrana.com',
                'celular1': '(11) 98765-4321',
                'funcionario': True,
                'vendedor': True,
                'cargo': 'Vendedor',
            },
            {
                'tipo': 'F',
                'nome': 'Maria Santos',
                'cpf_cnpj': '222.222.222-22',
                'email': 'maria.santos@serrana.com',
                'celular1': '(11) 98765-4322',
                'funcionario': True,
                'vendedor': True,
                'cargo': 'Vendedora',
            },
            {
                'tipo': 'F',
                'nome': 'Carlos Oliveira',
                'cpf_cnpj': '333.333.333-33',
                'email': 'carlos.oliveira@serrana.com',
                'celular1': '(11) 98765-4323',
                'funcionario': True,
                'vendedor': True,
                'cargo': 'Vendedor Sênior',
            },
        ]

        vendedores_criados = 0
        vendedores_atualizados = 0

        for vendedor_data in vendedores_data:
            cpf = vendedor_data['cpf_cnpj']
            
            # Verificar se já existe
            vendedor, created = Pessoa.objects.get_or_create(
                cpf_cnpj=cpf,
                defaults={
                    **vendedor_data,
                    'criado_por': admin_user,
                    'ativo': True,
                }
            )
            
            if created:
                vendedores_criados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Vendedor criado: {vendedor.nome}')
                )
            else:
                # Atualizar flags se necessário
                if not vendedor.vendedor:
                    vendedor.vendedor = True
                    vendedor.ativo = True
                    vendedor.atualizado_por = admin_user
                    vendedor.save()
                    vendedores_atualizados += 1
                    self.stdout.write(
                        self.style.WARNING(f'Vendedor atualizado: {vendedor.nome}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Vendedor já existe: {vendedor.nome}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nResumo:\n'
                f'- Vendedores criados: {vendedores_criados}\n'
                f'- Vendedores atualizados: {vendedores_atualizados}'
            )
        )
