from django.core.management.base import BaseCommand
from cadastros.models import Estado, Cidade

class Command(BaseCommand):
    help = 'Popula estados e cidades brasileiros'

    def handle(self, *args, **options):
        self.stdout.write('Criando estados e cidades...')

        # Estados principais
        estados_data = [
            {'sigla': 'AC', 'nome': 'Acre'},
            {'sigla': 'AL', 'nome': 'Alagoas'},
            {'sigla': 'AP', 'nome': 'Amapá'},
            {'sigla': 'AM', 'nome': 'Amazonas'},
            {'sigla': 'BA', 'nome': 'Bahia'},
            {'sigla': 'CE', 'nome': 'Ceará'},
            {'sigla': 'DF', 'nome': 'Distrito Federal'},
            {'sigla': 'ES', 'nome': 'Espírito Santo'},
            {'sigla': 'GO', 'nome': 'Goiás'},
            {'sigla': 'MA', 'nome': 'Maranhão'},
            {'sigla': 'MT', 'nome': 'Mato Grosso'},
            {'sigla': 'MS', 'nome': 'Mato Grosso do Sul'},
            {'sigla': 'MG', 'nome': 'Minas Gerais'},
            {'sigla': 'PA', 'nome': 'Pará'},
            {'sigla': 'PB', 'nome': 'Paraíba'},
            {'sigla': 'PR', 'nome': 'Paraná'},
            {'sigla': 'PE', 'nome': 'Pernambuco'},
            {'sigla': 'PI', 'nome': 'Piauí'},
            {'sigla': 'RJ', 'nome': 'Rio de Janeiro'},
            {'sigla': 'RN', 'nome': 'Rio Grande do Norte'},
            {'sigla': 'RS', 'nome': 'Rio Grande do Sul'},
            {'sigla': 'RO', 'nome': 'Rondônia'},
            {'sigla': 'RR', 'nome': 'Roraima'},
            {'sigla': 'SC', 'nome': 'Santa Catarina'},
            {'sigla': 'SP', 'nome': 'São Paulo'},
            {'sigla': 'SE', 'nome': 'Sergipe'},
            {'sigla': 'TO', 'nome': 'Tocantins'},
        ]

        for estado_data in estados_data:
            estado, created = Estado.objects.get_or_create(
                sigla=estado_data['sigla'],
                defaults={'nome': estado_data['nome']}
            )
            if created:
                self.stdout.write(f'Estado criado: {estado.nome}')

        # Algumas cidades exemplo (adicione mais conforme necessário)
        sp = Estado.objects.get(sigla='SP')
        cidades_sp = [
            'São Paulo',
            'Campinas',
            'Santos',
            'Ribeirão Preto',
            'Sorocaba',
            'São José dos Campos',
        ]
        
        for cidade_nome in cidades_sp:
            cidade, created = Cidade.objects.get_or_create(
                estado=sp,
                nome=cidade_nome
            )
            if created:
                self.stdout.write(f'Cidade criada: {cidade.nome}')

        self.stdout.write(self.style.SUCCESS('Estados e cidades criados com sucesso!'))
