# Generated manually on 2025-12-30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0003_sync_modelo_item'),
    ]

    operations = [
        migrations.RunSQL(
            sql="RENAME TABLE estoque_movimentacoes TO movimentos_estoque",
            reverse_sql="RENAME TABLE movimentos_estoque TO estoque_movimentacoes",
        ),
    ]
