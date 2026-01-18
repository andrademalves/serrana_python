# Generated manually - Desconto Global e Auditoria

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projetos', '0008_orcamentoparcela_descricao_and_more'),
    ]

    operations = [
        # Alterar campo codigo para editable=False e blank=True
        migrations.AlterField(
            model_name='orcamento',
            name='codigo',
            field=models.CharField(blank=True, editable=False, max_length=50, unique=True, verbose_name='Código'),
        ),
        
        # Adicionar campos de desconto global
        migrations.AddField(
            model_name='orcamento',
            name='tipo_desconto',
            field=models.CharField(
                choices=[('NENHUM', 'Nenhum'), ('PERCENTUAL', 'Percentual (%)'), ('VALOR_FIXO', 'Valor Fixo (R$)')],
                default='NENHUM',
                max_length=20,
                verbose_name='Tipo de Desconto'
            ),
        ),
        migrations.AddField(
            model_name='orcamento',
            name='desconto_valor',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                help_text='Percentual ou valor fixo',
                max_digits=12,
                verbose_name='Valor do Desconto'
            ),
        ),
        
        # Alterar campos valor_total e desconto
        migrations.AlterField(
            model_name='orcamento',
            name='valor_total',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                help_text='Soma dos itens',
                max_digits=12,
                verbose_name='Valor Total'
            ),
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='desconto',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                editable=False,
                max_digits=12,
                verbose_name='Desconto Aplicado (R$)'
            ),
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='valor_final',
            field=models.DecimalField(
                decimal_places=2,
                default=0.00,
                editable=False,
                max_digits=12,
                verbose_name='Valor Final'
            ),
        ),
        
        # Criar model OrcamentoHistorico
        migrations.CreateModel(
            name='OrcamentoHistorico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Data/Hora')),
                ('acao', models.CharField(
                    choices=[('CRIADO', 'Criado'), ('ALTERADO', 'Alterado'), ('DESCONTO', 'Desconto Aplicado'), ('PARCELA', 'Parcelas Alteradas')],
                    max_length=20,
                    verbose_name='Ação'
                )),
                ('diff', models.JSONField(default=dict, help_text='Alterações antes/depois', verbose_name='Diferenças')),
                ('orcamento', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historico',
                    to='projetos.orcamento',
                    verbose_name='Orçamento'
                )),
                ('usuario', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário'
                )),
            ],
            options={
                'verbose_name': 'Histórico do Orçamento',
                'verbose_name_plural': 'Históricos dos Orçamentos',
                'db_table': 'orcamento_historico',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Adicionar índice
        migrations.AddIndex(
            model_name='orcamentohistorico',
            index=models.Index(fields=['-timestamp', 'orcamento'], name='orcamento_h_timesta_idx'),
        ),
    ]
