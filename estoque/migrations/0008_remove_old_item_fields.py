# Generated manually on 2025-12-30

from django.db import migrations, connection


def remove_old_item_fields(apps, schema_editor):
    """Remove campos antigos da tabela itens."""
    
    with connection.cursor() as cursor:
        # Verificar colunas existentes
        cursor.execute("SHOW COLUMNS FROM itens")
        colunas_existentes = {row[0] for row in cursor.fetchall()}
        
        # Remover preco_custo_medio se existir
        if 'preco_custo_medio' in colunas_existentes:
            cursor.execute("ALTER TABLE itens DROP COLUMN preco_custo_medio")
            print("✓ Removido preco_custo_medio")
        
        # Remover estoque_atual se existir
        if 'estoque_atual' in colunas_existentes:
            cursor.execute("ALTER TABLE itens DROP COLUMN estoque_atual")
            print("✓ Removido estoque_atual")


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0007_create_grupos_item'),
    ]

    operations = [
        migrations.RunPython(remove_old_item_fields, reverse_code=migrations.RunPython.noop),
    ]
