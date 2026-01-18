from django.core.management.base import BaseCommand
from usuarios.models import Menu, Modulo


class Command(BaseCommand):
    help = 'Cria o módulo e menu para o sistema de Estoque'

    def handle(self, *args, **options):
        self.stdout.write('Criando módulo e menu de Estoque...')
        
        # Cria ou obtém o módulo Estoque
        modulo, created = Modulo.objects.get_or_create(
            nome='Estoque',
            defaults={
                'descricao': 'Módulo de Gestão de Estoque',
                'icone': 'bi-box-seam',
                'ordem': 3,
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Módulo criado: {modulo.nome}'))
        else:
            self.stdout.write(self.style.WARNING(f'Módulo já existe: {modulo.nome}'))
        
        # Cria os menus do estoque
        menus = [
            {
                'nome': 'Dashboard Estoque',
                'url': '/estoque/',
                'icone': 'bi-speedometer2',
                'ordem': 1,
                'menu_pai': None
            },
            {
                'nome': 'Itens',
                'url': '/estoque/itens/',
                'icone': 'bi-boxes',
                'ordem': 2,
                'menu_pai': None
            },
            {
                'nome': 'Movimentações',
                'url': '/estoque/movimentacoes/',
                'icone': 'bi-arrow-left-right',
                'ordem': 3,
                'menu_pai': None
            },
            {
                'nome': 'Relatórios',
                'url': '#',
                'icone': 'bi-file-earmark-text',
                'ordem': 4,
                'menu_pai': None
            },
            {
                'nome': 'Estoque Atual',
                'url': '/estoque/relatorios/estoque-atual/',
                'icone': 'bi-clipboard-data',
                'ordem': 1,
                'menu_pai': 'Relatórios'
            },
            {
                'nome': 'Histórico Movimentações',
                'url': '/estoque/relatorios/movimentacoes/',
                'icone': 'bi-clock-history',
                'ordem': 2,
                'menu_pai': 'Relatórios'
            },
        ]
        
        for menu_data in menus:
            menu_pai = None
            if menu_data['menu_pai']:
                try:
                    menu_pai = Menu.objects.get(
                        nome=menu_data['menu_pai'],
                        modulo=modulo
                    )
                except Menu.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Menu pai não encontrado: {menu_data["menu_pai"]}'))
                    continue
            
            menu, created = Menu.objects.get_or_create(
                nome=menu_data['nome'],
                modulo=modulo,
                defaults={
                    'url': menu_data['url'],
                    'icone': menu_data['icone'],
                    'ordem': menu_data['ordem'],
                    'menu_pai': menu_pai,
                    'ativo': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Menu criado: {menu.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'Menu já existe: {menu.nome}'))
        
        total_menus = Menu.objects.filter(modulo=modulo).count()
        self.stdout.write(self.style.SUCCESS(f'\nTotal de menus no módulo Estoque: {total_menus}'))
        self.stdout.write(self.style.SUCCESS('Módulo Estoque configurado com sucesso!'))
