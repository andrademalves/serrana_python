"""
Comando para criar menu de gestão de empresas no sistema
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from usuarios.models import Modulo, Menu


class Command(BaseCommand):
    help = 'Cria menu de gestão de empresas no módulo Sistema'

    def handle(self, *args, **options):
        # Buscar ou criar módulo Sistema
        modulo_sistema, criado = Modulo.objects.get_or_create(
            nome='Sistema',
            defaults={
                'descricao': 'Configurações e gestão do sistema',
                'icone': 'bi bi-gear',
                'ordem': 999,
                'ativo': True,
            }
        )
        
        if criado:
            self.stdout.write(self.style.SUCCESS('✓ Módulo "Sistema" criado!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Módulo "Sistema" encontrado (ID: {modulo_sistema.id})'))
        
        # Criar menu de Empresas se não existir
        menu_empresas, criado = Menu.objects.get_or_create(
            modulo=modulo_sistema,
            nome='Empresas',
            defaults={
                'url': 'usuarios:listar_empresas',
                'icone': 'bi bi-building',
                'descricao': 'Gerenciar empresas do sistema',
                'ordem': 20,
                'ativo': True,
            }
        )
        
        if criado:
            self.stdout.write(self.style.SUCCESS(f'✓ Menu "Empresas" criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING(f'Menu "Empresas" já existe (ID: {menu_empresas.id})'))
        
        # Criar submenus
        try:
            submenu_listar = Menu.objects.get(modulo=modulo_sistema, menu_pai=menu_empresas, url='usuarios:listar_empresas')
            self.stdout.write(self.style.WARNING(f'  Submenu "Listar Empresas" já existe'))
        except Menu.DoesNotExist:
            try:
                submenu_listar = Menu.objects.create(
                    modulo=modulo_sistema,
                    menu_pai=menu_empresas,
                    nome='Listar Empresas',
                    url='usuarios:listar_empresas',
                    icone='bi bi-list-ul',
                    descricao='Listar todas as empresas',
                    ordem=1,
                    ativo=True,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ Submenu "Listar Empresas" criado'))
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f'  Submenu "Listar Empresas" já existe (IntegrityError)'))
        
        try:
            submenu_criar = Menu.objects.get(modulo=modulo_sistema, menu_pai=menu_empresas, url='usuarios:criar_empresa')
            self.stdout.write(self.style.WARNING(f'  Submenu "Nova Empresa" já existe'))
        except Menu.DoesNotExist:
            try:
                submenu_criar = Menu.objects.create(
                    modulo=modulo_sistema,
                    menu_pai=menu_empresas,
                    nome='Nova Empresa',
                    url='usuarios:criar_empresa',
                    icone='bi bi-plus-circle',
                    descricao='Cadastrar nova empresa',
                    ordem=2,
                    ativo=True,
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ Submenu "Nova Empresa" criado'))
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f'  Submenu "Nova Empresa" já existe (IntegrityError)'))
        if criado:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Submenu "Nova Empresa" criado'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Menu de Empresas configurado com sucesso!'))
        self.stdout.write(self.style.SUCCESS('Agora você pode acessar: Módulo Sistema > Empresas'))
        self.stdout.write(self.style.SUCCESS('\nOu acesse diretamente: http://127.0.0.1:8000/usuarios/empresas/'))
