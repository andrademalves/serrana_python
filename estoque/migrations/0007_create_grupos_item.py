# Generated manually on 2025-12-30

from django.db import migrations, connection


def create_grupos_item_table(apps, schema_editor):
    """Cria tabela grupos_item."""
    
    with connection.cursor() as cursor:
        # Verifica se a tabela já existe
        cursor.execute("SHOW TABLES LIKE 'grupos_item'")
        if cursor.fetchone():
            print("Tabela grupos_item já existe")
            return
        
        # Cria a tabela
        cursor.execute("""
            CREATE TABLE grupos_item (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(20) UNIQUE NOT NULL,
                descricao VARCHAR(100) NOT NULL,
                ativo TINYINT(1) DEFAULT 1,
                criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                criado_por_id INT NULL,
                KEY grupos_item_codigo_idx (codigo),
                KEY grupos_item_criado_por_id_fk (criado_por_id),
                CONSTRAINT grupos_item_criado_por_id_fk FOREIGN KEY (criado_por_id) REFERENCES auth_user(id) ON DELETE SET NULL
            )
        """)
        print("✓ Tabela grupos_item criada")


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0006_add_grupo_id'),
    ]

    operations = [
        migrations.RunPython(create_grupos_item_table, reverse_code=migrations.RunPython.noop),
    ]
