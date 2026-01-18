from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cadastros.models import Pessoa

User = get_user_model()


class Command(BaseCommand):
    help = 'Popula o banco com pessoas de teste'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populando pessoas...')
        
        # Pegar ou criar usuário admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('Nenhum superusuário encontrado!'))
            return
        
        # Pessoas Físicas
        pessoas_fisicas = [
            {
                'tipo': 'F',
                'nome': 'João Silva Santos',
                'cpf_cnpj': '12345678901',
                'rg': '123456789',
                'data_emissao_rg': '2010-01-15',
                'orgao_emissor': 'SSP-SP',
                'sexo': 'M',
                'cep': '01310100',
                'logradouro': 'Avenida Paulista',
                'numero': '1000',
                'bairro': 'Bela Vista',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'telefone': '1133334444',
                'celular1': '11987654321',
                'email': 'joao.silva@email.com',
                'cliente': True,
                'funcionario': False,
                'fornecedor': False,
                'terceiro': False,
            },
            {
                'tipo': 'F',
                'nome': 'Maria Oliveira Costa',
                'cpf_cnpj': '98765432109',
                'rg': '987654321',
                'data_emissao_rg': '2015-05-20',
                'orgao_emissor': 'SSP-RJ',
                'sexo': 'F',
                'cep': '22250040',
                'logradouro': 'Rua Barata Ribeiro',
                'numero': '500',
                'bairro': 'Copacabana',
                'cidade': 'Rio de Janeiro',
                'uf': 'RJ',
                'telefone': '2122223333',
                'celular1': '21976543210',
                'email': 'maria.oliveira@email.com',
                'cliente': True,
                'funcionario': True,
                'fornecedor': False,
                'terceiro': False,
                'cargo': 'Vendedora',
                'data_admissao': '2020-01-10',
                'escolaridade': 'medio_completo',
                'ctps': '123456',
                'serie': '001',
                'uf_ctps': 'RJ',
            },
            {
                'tipo': 'F',
                'nome': 'Carlos Eduardo Mendes',
                'cpf_cnpj': '45678912345',
                'rg': '456789123',
                'data_emissao_rg': '2012-08-10',
                'orgao_emissor': 'SSP-MG',
                'sexo': 'M',
                'cep': '30130100',
                'logradouro': 'Avenida Afonso Pena',
                'numero': '1500',
                'bairro': 'Centro',
                'cidade': 'Belo Horizonte',
                'uf': 'MG',
                'celular1': '31988887777',
                'email': 'carlos.mendes@email.com',
                'cliente': False,
                'funcionario': True,
                'fornecedor': False,
                'terceiro': False,
                'cargo': 'Gerente',
                'data_admissao': '2018-03-15',
                'escolaridade': 'superior_completo',
                'ctps': '789012',
                'serie': '002',
                'uf_ctps': 'MG',
                'cnh': '12345678901',
                'cnh_categoria': 'B',
            },
        ]
        
        # Pessoas Jurídicas
        pessoas_juridicas = [
            {
                'tipo': 'J',
                'nome': 'Tech Solutions Ltda',
                'nome_fantasia': 'Tech Solutions',
                'cpf_cnpj': '12345678000190',
                'ie': '123456789',
                'cep': '04551000',
                'logradouro': 'Avenida Brigadeiro Faria Lima',
                'numero': '3000',
                'bairro': 'Itaim Bibi',
                'cidade': 'São Paulo',
                'uf': 'SP',
                'telefone': '1132221111',
                'celular1': '11999998888',
                'email': 'contato@techsolutions.com',
                'cliente': False,
                'funcionario': False,
                'fornecedor': True,
                'terceiro': False,
                'ramo_atividade': 'Tecnologia',
                'descricao_ramo': 'Desenvolvimento de Software',
            },
            {
                'tipo': 'J',
                'nome': 'Comercial Alimentos S/A',
                'nome_fantasia': 'Alimentos Bom Sabor',
                'cpf_cnpj': '98765432000123',
                'ie': '987654321',
                'cep': '90010000',
                'logradouro': 'Rua dos Andradas',
                'numero': '1000',
                'bairro': 'Centro',
                'cidade': 'Porto Alegre',
                'uf': 'RS',
                'telefone': '5133334444',
                'celular1': '51988776655',
                'email': 'vendas@bomsabor.com.br',
                'cliente': True,
                'funcionario': False,
                'fornecedor': True,
                'terceiro': False,
                'ramo_atividade': 'Alimentos',
                'descricao_ramo': 'Distribuição de alimentos',
            },
            {
                'tipo': 'J',
                'nome': 'Transportadora Rápida Eireli',
                'nome_fantasia': 'Rápida Transportes',
                'cpf_cnpj': '11223344000156',
                'ie': '112233445',
                'cep': '80010000',
                'logradouro': 'Rua XV de Novembro',
                'numero': '800',
                'bairro': 'Centro',
                'cidade': 'Curitiba',
                'uf': 'PR',
                'telefone': '4133445566',
                'celular1': '41987654321',
                'email': 'contato@rapidatransportes.com.br',
                'cliente': False,
                'funcionario': False,
                'fornecedor': False,
                'terceiro': True,
                'ramo_atividade': 'Logística',
                'descricao_ramo': 'Transporte de cargas',
            },
        ]
        
        # Criar pessoas físicas
        for data in pessoas_fisicas:
            pessoa, created = Pessoa.objects.get_or_create(
                cpf_cnpj=data['cpf_cnpj'],
                defaults={
                    **data,
                    'criado_por': admin_user,
                    'atualizado_por': admin_user,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Pessoa Física criada: {pessoa.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Pessoa Física já existe: {pessoa.nome}'))
        
        # Criar pessoas jurídicas
        for data in pessoas_juridicas:
            pessoa, created = Pessoa.objects.get_or_create(
                cpf_cnpj=data['cpf_cnpj'],
                defaults={
                    **data,
                    'criado_por': admin_user,
                    'atualizado_por': admin_user,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Pessoa Jurídica criada: {pessoa.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Pessoa Jurídica já existe: {pessoa.nome}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Pessoas populadas com sucesso!'))
