from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from estoque.models import Item, MovimentoEstoque, GrupoItem, LocalEstoque, DestinoEstoque
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com itens de esquadrias'

    def handle(self, *args, **options):
        self.stdout.write('Populando estoque para empresa de esquadrias...')
        user, _ = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        # Remove dados usando raw SQL para evitar problemas com FKs para tabelas não existentes
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM movimentos_estoque")
            cursor.execute("DELETE FROM itens")
            cursor.execute("DELETE FROM grupos_item")
            cursor.execute("DELETE FROM locais_estoque WHERE 1=1")
            cursor.execute("DELETE FROM destinos_estoque WHERE 1=1")
        
        # Criar Locais de Estoque
        local_matriz = LocalEstoque.objects.create(
            codigo='MATRIZ',
            descricao='Estoque Matriz',
            responsavel=user,
            permite_saldo_negativo=False,
            ativo=True,
            criado_por=user
        )
        
        local_producao = LocalEstoque.objects.create(
            codigo='PRODUCAO',
            descricao='Produção/Fábrica',
            responsavel=user,
            permite_saldo_negativo=False,
            ativo=True,
            criado_por=user
        )
        
        local_loja = LocalEstoque.objects.create(
            codigo='LOJA',
            descricao='Loja/Showroom',
            responsavel=user,
            permite_saldo_negativo=False,
            ativo=True,
            criado_por=user
        )
        
        self.stdout.write(self.style.SUCCESS('Locais de estoque criados'))
        
        # Criar Destinos de Estoque
        destino_projeto = DestinoEstoque.objects.create(
            codigo='PROJETO',
            descricao='Projeto/Obra',
            tipo='PROJETO',
            controla_custo=True,
            ativo=True,
            criado_por=user
        )
        
        destino_producao = DestinoEstoque.objects.create(
            codigo='PRODUCAO',
            descricao='Produção',
            tipo='PRODUCAO',
            controla_custo=True,
            ativo=True,
            criado_por=user
        )
        
        destino_perda = DestinoEstoque.objects.create(
            codigo='PERDA',
            descricao='Perda/Sucata',
            tipo='PERDA',
            controla_custo=False,
            ativo=True,
            criado_por=user
        )
        
        self.stdout.write(self.style.SUCCESS('Destinos de estoque criados'))
        
        grupo_perfis = GrupoItem.objects.create(codigo='PERFIS', descricao='Perfis de Alumínio', ativo=True, criado_por=user)
        grupo_vidros = GrupoItem.objects.create(codigo='VIDROS', descricao='Vidros e Espelhos', ativo=True, criado_por=user)
        grupo_ferragens = GrupoItem.objects.create(codigo='FERR', descricao='Ferragens e Acessórios', ativo=True, criado_por=user)
        grupo_vedacao = GrupoItem.objects.create(codigo='VEDACAO', descricao='Vedações e Borrachas', ativo=True, criado_por=user)
        grupo_fixacao = GrupoItem.objects.create(codigo='FIX', descricao='Elementos de Fixação', ativo=True, criado_por=user)
        codigo_counter = 1
        perfis = [('Perfil de Alumínio Linha 25 - Requadro', 'Aluflex', 'REQ-25', '20.000'), ('Perfil de Alumínio Linha 25 - Marco', 'Aluflex', 'MAR-25', '15.000')]
        for desc, marca, modelo, estoque_min in perfis:
            Item.objects.create(tipo_item='MP', codigo=f'ITEM-{codigo_counter:05d}', descricao=desc, marca=marca, modelo=modelo, unidade_medida='BAR', estoque_minimo=Decimal(estoque_min), grupo=grupo_perfis, ativo=True, criado_por=user, atualizado_por=user)
            codigo_counter += 1
        self.stdout.write(self.style.SUCCESS(f'Criados {Item.objects.count()} itens'))
