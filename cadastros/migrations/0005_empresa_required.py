# Generated migration - Passo 3: Tornar empresa obrigatória

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0004_popular_empresa_padrao'),
    ]

    operations = [
        # Tornar empresa obrigatória em Pessoa
        migrations.AlterField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pessoas',
                to='usuarios.empresa',
                verbose_name='Empresa',
                help_text='Empresa à qual esta pessoa pertence'
            ),
        ),
        
        # Tornar empresa obrigatória em Produto
        migrations.AlterField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='produtos',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        
        # Remover constraint UNIQUE do cpf_cnpj antes de adicionar unique_together
        migrations.AlterField(
            model_name='pessoa',
            name='cpf_cnpj',
            field=models.CharField(max_length=18, verbose_name='CPF/CNPJ'),
        ),
        
        # Adicionar unique_together
        migrations.AlterUniqueTogether(
            name='pessoa',
            unique_together={('empresa', 'cpf_cnpj')},
        ),
        
        # Remover constraint UNIQUE do codigo antes de adicionar unique_together
        migrations.AlterField(
            model_name='produto',
            name='codigo',
            field=models.CharField(max_length=50, verbose_name='Código'),
        ),
        
        migrations.AlterUniqueTogether(
            name='produto',
            unique_together={('empresa', 'codigo')},
        ),
        
        # Adicionar índices
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['empresa', 'ativo'], name='pessoa_emp_ativo_idx'),
        ),
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['empresa', 'cliente'], name='pessoa_emp_cliente_idx'),
        ),
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['empresa', 'fornecedor'], name='pessoa_emp_fornec_idx'),
        ),
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['cpf_cnpj'], name='pessoa_cpf_cnpj_idx'),
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['empresa', 'ativo'], name='produto_emp_ativo_idx'),
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['empresa', 'tipo'], name='produto_emp_tipo_idx'),
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['codigo'], name='produto_codigo_idx'),
        ),
    ]
