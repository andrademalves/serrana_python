# Generated manually on 2025-12-30

from django.db import migrations, connection


def sync_movimentos_estoque(apps, schema_editor):
    """Sincroniza a estrutura da tabela movimentos_estoque com o modelo atual."""
    
    with connection.cursor() as cursor:
        # Verificar colunas existentes
        cursor.execute("SHOW COLUMNS FROM movimentos_estoque")
        colunas_existentes = {row[0] for row in cursor.fetchall()}
        
        print(f"Colunas existentes: {colunas_existentes}")
        
        # Renomear tipo_mov para tipo_movimento
        if 'tipo_mov' in colunas_existentes and 'tipo_movimento' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque CHANGE COLUMN tipo_mov tipo_movimento VARCHAR(20)")
            print("✓ Renomeado tipo_mov → tipo_movimento")
        
        # Renomear valor_unitario para custo_unitario
        if 'valor_unitario' in colunas_existentes and 'custo_unitario' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque CHANGE COLUMN valor_unitario custo_unitario DECIMAL(12,4) DEFAULT 0.0000")
            print("✓ Renomeado valor_unitario → custo_unitario")
        
        # Renomear valor_total para custo_total
        if 'valor_total' in colunas_existentes and 'custo_total' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque CHANGE COLUMN valor_total custo_total DECIMAL(12,2) DEFAULT 0.00")
            print("✓ Renomeado valor_total → custo_total")
        
        # Renomear data_mov para data_movimento
        if 'data_mov' in colunas_existentes and 'data_movimento' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque CHANGE COLUMN data_mov data_movimento DATETIME(6)")
            print("✓ Renomeado data_mov → data_movimento")
        
        # Adicionar documento_tipo se não existir
        if 'documento_tipo' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN documento_tipo VARCHAR(10) NULL")
            print("✓ Adicionado documento_tipo")
        
        # Adicionar local_origem_id se não existir
        if 'local_origem_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN local_origem_id BIGINT NULL")
            print("✓ Adicionado local_origem_id")
        
        # Adicionar local_destino_id se não existir
        if 'local_destino_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN local_destino_id BIGINT NULL")
            print("✓ Adicionado local_destino_id")
        
        # Adicionar destino_id se não existir
        if 'destino_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN destino_id BIGINT NULL")
            print("✓ Adicionado destino_id")
        
        # Adicionar projeto_id se não existir
        if 'projeto_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN projeto_id BIGINT NULL")
            print("✓ Adicionado projeto_id")
        
        # Adicionar fornecedor_id se não existir
        if 'fornecedor_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN fornecedor_id BIGINT NULL")
            print("✓ Adicionado fornecedor_id")
        
        # Adicionar solicitante_id se não existir
        if 'solicitante_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN solicitante_id INT NULL")
            print("✓ Adicionado solicitante_id")
        
        # Adicionar movimento_estornado_id se não existir
        if 'movimento_estornado_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN movimento_estornado_id BIGINT NULL")
            print("✓ Adicionado movimento_estornado_id")
        
        # Adicionar criado_em se não existir
        if 'criado_em' not in colunas_existentes:
            cursor.execute("ALTER TABLE movimentos_estoque ADD COLUMN criado_em DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)")
            print("✓ Adicionado criado_em")
        
        # Criar índices
        try:
            cursor.execute("CREATE INDEX movimentos_estoque_tipo_movimento_idx ON movimentos_estoque(tipo_movimento)")
            print("✓ Criado índice em tipo_movimento")
        except:
            print("- Índice tipo_movimento já existe")
        
        try:
            cursor.execute("CREATE INDEX movimentos_estoque_documento_idx ON movimentos_estoque(documento)")
            print("✓ Criado índice em documento")
        except:
            print("- Índice documento já existe")
        
        try:
            cursor.execute("CREATE INDEX movimentos_estoque_data_movimento_idx ON movimentos_estoque(data_movimento)")
            print("✓ Criado índice em data_movimento")
        except:
            print("- Índice data_movimento já existe")


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0004_rename_table_movimentos'),
    ]

    operations = [
        migrations.RunPython(sync_movimentos_estoque, reverse_code=migrations.RunPython.noop),
    ]
