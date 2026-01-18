# Generated manually on 2025-12-30

from django.db import migrations, connection


def create_locais_and_destinos_tables(apps, schema_editor):
    """Cria tabelas locais_estoque e destinos_estoque."""
    
    with connection.cursor() as cursor:
        # Verifica se tabela locais_estoque existe
        cursor.execute("SHOW TABLES LIKE 'locais_estoque'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE locais_estoque (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    codigo VARCHAR(20) UNIQUE NOT NULL,
                    descricao VARCHAR(100) NOT NULL,
                    endereco VARCHAR(255) NULL,
                    responsavel_id INT NULL,
                    permite_saldo_negativo TINYINT(1) DEFAULT 0,
                    ativo TINYINT(1) DEFAULT 1,
                    criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                    criado_por_id INT NULL,
                    KEY locais_estoque_codigo_idx (codigo),
                    KEY locais_estoque_responsavel_id_fk (responsavel_id),
                    KEY locais_estoque_criado_por_id_fk (criado_por_id),
                    CONSTRAINT locais_estoque_responsavel_id_fk FOREIGN KEY (responsavel_id) REFERENCES auth_user(id) ON DELETE SET NULL,
                    CONSTRAINT locais_estoque_criado_por_id_fk FOREIGN KEY (criado_por_id) REFERENCES auth_user(id) ON DELETE SET NULL
                )
            """)
            print("✓ Tabela locais_estoque criada")
        else:
            print("- Tabela locais_estoque já existe")
        
        # Verifica se tabela destinos_estoque existe
        cursor.execute("SHOW TABLES LIKE 'destinos_estoque'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE destinos_estoque (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    codigo VARCHAR(20) UNIQUE NOT NULL,
                    descricao VARCHAR(100) NOT NULL,
                    tipo VARCHAR(20) NOT NULL,
                    controla_custo TINYINT(1) DEFAULT 1,
                    ativo TINYINT(1) DEFAULT 1,
                    criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                    criado_por_id INT NULL,
                    KEY destinos_estoque_codigo_idx (codigo),
                    KEY destinos_estoque_tipo_idx (tipo),
                    KEY destinos_estoque_criado_por_id_fk (criado_por_id),
                    CONSTRAINT destinos_estoque_criado_por_id_fk FOREIGN KEY (criado_por_id) REFERENCES auth_user(id) ON DELETE SET NULL
                )
            """)
            print("✓ Tabela destinos_estoque criada")
        else:
            print("- Tabela destinos_estoque já existe")


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0008_remove_old_item_fields'),
    ]

    operations = [
        migrations.RunPython(create_locais_and_destinos_tables, reverse_code=migrations.RunPython.noop),
    ]
