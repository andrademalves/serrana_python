# Generated migration - Passo 1: Adicionar campo empresa (nullable)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0002_remove_pessoa_celular_remove_pessoa_rg_ie_and_more'),
        ('usuarios', '0002_empresa_usuarioempresa_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pessoas',
                to='usuarios.empresa',
                verbose_name='Empresa',
                help_text='Empresa à qual esta pessoa pertence'
            ),
        ),
        migrations.AddField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='produtos',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
    ]
