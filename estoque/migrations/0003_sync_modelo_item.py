# Sincronizar modelo Item com banco de dados

from django.conf import settings
from django.db import migrations, models, connection
import django.db.models.deletion


def adicionar_campos_faltantes(apps, schema_editor):
    """Adiciona campos que podem estar faltando"""
    with connection.cursor() as cursor:
        # Verificar quais colunas existem
        cursor.execute("SHOW COLUMNS FROM itens")
        colunas_existentes = {row[0] for row in cursor.fetchall()}
        
        # Adicionar campos que não existem
        if 'codigo' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN codigo VARCHAR(50) DEFAULT 'TEMP'")
        
        if 'codigo_barras' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN codigo_barras VARCHAR(50) NULL")
        
        if 'ncm' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN ncm VARCHAR(20) NULL")
        
        if 'url_foto' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN url_foto VARCHAR(500) NULL")
        
        if 'observacoes' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN observacoes TEXT NULL")
        
        if 'atualizado_em' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN atualizado_em DATETIME(6) NULL")
        
        if 'atualizado_por_id' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN atualizado_por_id INT NULL")
        
        if 'estoque_maximo' not in colunas_existentes:
            cursor.execute("ALTER TABLE itens ADD COLUMN estoque_maximo DECIMAL(12,3) NULL")
        
        # Gerar códigos únicos diretamente com SQL
        cursor.execute("SELECT id FROM itens WHERE codigo = 'TEMP' OR codigo IS NULL OR codigo = ''")
        ids_sem_codigo = [row[0] for row in cursor.fetchall()]
        
        for index, item_id in enumerate(ids_sem_codigo, start=1):
            codigo = f'ITEM-{index:05d}'
            cursor.execute("UPDATE itens SET codigo = %s WHERE id = %s", [codigo, item_id])
        
        # Adicionar índice e unique ao codigo
        try:
            cursor.execute("CREATE UNIQUE INDEX itens_codigo_unique ON itens(codigo)")
        except:
            pass  # Índice já existe


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('estoque', '0002_item_cor_item_marca_item_modelo'),
    ]

    operations = [
        migrations.RunPython(adicionar_campos_faltantes, migrations.RunPython.noop),
    ]
