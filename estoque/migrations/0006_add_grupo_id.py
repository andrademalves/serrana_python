# Generated manually on 2025-12-30

from django.db import migrations, connection


def add_missing_item_fields(apps, schema_editor):
    """Adiciona campos faltantes na tabela itens."""
    
    with connection.cursor() as cursor:
        # Verificar colunas existentes
        cursor.execute("SHOW COLUMNS FROM itens")
        colunas_existentes = {row[0] for row in cursor.fetchall()}
        
        print(f"Colunas existentes na tabela itens: {colunas_existentes}")
        
        # Adicionar grupo_id se não existir (sem foreign key por enquanto pois a tabela grupos_item não existe)
        if 'grupo_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN grupo_id BIGINT NULL")
            print("✓ Adicionado grupo_id")
        else:
            print("- grupo_id já existe")


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0005_sync_movimentos_estoque'),
    ]

    operations = [
        migrations.RunPython(add_missing_item_fields, reverse_code=migrations.RunPython.noop),
    ]
