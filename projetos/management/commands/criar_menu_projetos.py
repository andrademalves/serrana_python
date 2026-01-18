from django.core.management.base import BaseCommand
from usuarios.models import Modulo, Menu

class Command(BaseCommand):
    help = 'Cria o módulo e menus de Projetos e Vendas'

    def handle(self, *args, **kwargs):
        # Criar módulo Projetos
        modulo_projetos, created = Modulo.objects.get_or_create(
            nome='Orçamentos e Projetos',
            defaults={
                'icone': 'bi bi-briefcase',
                'descricao': 'Gestão de orçamentos, projetos e vendas diretas',
                'ordem': 4,
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Módulo "{modulo_projetos.nome}" criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING(f'Módulo "{modulo_projetos.nome}" já existe.'))
        
        # Criar menus do módulo Projetos
        menus_projetos = [
            {
                'nome': 'Dashboard',
                'url': 'projetos:dashboard',
                'icone': 'bi bi-speedometer2',
                'ordem': 1
            },
            {
                'nome': 'Orçamentos',
                'url': 'projetos:listar_orcamentos',
                'icone': 'bi bi-file-earmark-text',
                'ordem': 2
            },
            {
                'nome': 'Projetos',
                'url': 'projetos:listar_projetos',
                'icone': 'bi bi-folder',
                'ordem': 3
            },
            {
                'nome': 'Vendas Diretas',
                'url': 'projetos:listar_vendas',
                'icone': 'bi bi-cart',
                'ordem': 4
            },
        ]
        
        for menu_data in menus_projetos:
            menu, created = Menu.objects.get_or_create(
                nome=menu_data['nome'],
                modulo=modulo_projetos,
                defaults={
                    'url': menu_data['url'],
                    'icone': menu_data['icone'],
                    'ordem': menu_data['ordem'],
                    'ativo': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Menu "{menu.nome}" criado!'))
            else:
                self.stdout.write(self.style.WARNING(f'  Menu "{menu.nome}" já existe.'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Configuração do módulo Projetos concluída!'))
