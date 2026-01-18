# Implementação Multiempresa no Módulo Financeiro

## Models que precisam do campo empresa:

1. **Banco** - Não precisa (global)
2. **ContaFinanceira** - PRECISA
3. **FormaPagamento** - PRECISA
4. **CentroCusto** - PRECISA
5. **PlanoConta** - PRECISA
6. **TituloFinanceiro** - PRECISA
7. **ParcelaFinanceira** - Herda do título
8. **BaixaFinanceira** - Herda da parcela

## Migration necessária:

```python
# financeiro/migrations/000X_add_empresa_multiempresa.py

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', 'XXXX_ultima_migration'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        # Adicionar empresa (nullable temporariamente)
        migrations.AddField(
            model_name='contafinanceira',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='contas_financeiras',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        migrations.AddField(
            model_name='formapagamento',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='formas_pagamento',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        migrations.AddField(
            model_name='centrocusto',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='centros_custo',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        migrations.AddField(
            model_name='planoconta',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='planos_conta',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        migrations.AddField(
            model_name='titulofinanceiro',
            name='empresa',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='titulos_financeiros',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
    ]
```

## Views que precisam ser corrigidas:

### dashboard (views.py)
```python
@login_required
def dashboard(request):
    dados = IndicadoresSaudeFinanceira.dashboard_resumo(empresa=request.empresa)
    ...
```

### listar_titulos (views.py)
```python
titulos = TituloFinanceiro.objects.filter(empresa=request.empresa)
```

### listar_parcelas (views.py)
```python
parcelas = ParcelaFinanceira.objects.filter(
    titulo__empresa=request.empresa
)
```

### Relatórios (views_relatorios.py)
```python
parcelas = ParcelaFinanceira.objects.filter(
    titulo__empresa=request.empresa,
    tipo='PAGAR'
)
```

## Services que precisam ser atualizados:

### IndicadoresSaudeFinanceira
```python
@staticmethod
def dashboard_resumo(empresa):
    titulos_abertos = TituloFinanceiro.objects.filter(
        empresa=empresa,
        status__in=['ABERTO', 'PARCIAL']
    )
```

### CalculadoraSaldos
```python
@staticmethod
def saldo_conta(conta_id, empresa):
    conta = ContaFinanceira.objects.get(id=conta_id, empresa=empresa)
```

## Checklist de Implementação:

- [ ] Criar migration para adicionar campo empresa (nullable)
- [ ] Popular empresa_id com empresa padrão
- [ ] Criar migration para tornar empresa obrigatória
- [ ] Atualizar models.py
- [ ] Atualizar views.py (todas as views)
- [ ] Atualizar views_relatorios.py
- [ ] Atualizar services/indicadores.py
- [ ] Atualizar services/calculadora.py
- [ ] Atualizar services/ponto_equilibrio.py
- [ ] Atualizar forms.py para vincular à empresa
- [ ] Testar todos os relatórios
- [ ] Testar dashboard
- [ ] Testar criação de títulos
- [ ] Testar baixas
