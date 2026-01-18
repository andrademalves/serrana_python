# Generated migration - Passo 2: Popular empresa padrão

from django.db import migrations


def popular_empresa_padrao(apps, schema_editor):
    """Vincula todos os registros existentes à empresa padrão 'Serrana'"""
    Pessoa = apps.get_model('cadastros', 'Pessoa')
    Produto = apps.get_model('cadastros', 'Produto')
    Empresa = apps.get_model('usuarios', 'Empresa')
    
    # Buscar empresa padrão (CNPJ 00000000000000 ou primeira)
    empresa_padrao = Empresa.objects.filter(cnpj='00000000000000').first()
    if not empresa_padrao:
        empresa_padrao = Empresa.objects.first()
    
    if empresa_padrao:
        # Atualizar pessoas sem empresa
        total_pessoas = Pessoa.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)
        
        # Atualizar produtos sem empresa
        total_produtos = Produto.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)
        
        print(f"✅ {total_pessoas} pessoas vinculadas à empresa: {empresa_padrao.nome_fantasia}")
        print(f"✅ {total_produtos} produtos vinculados à empresa: {empresa_padrao.nome_fantasia}")
    else:
        print("⚠️  AVISO: Nenhuma empresa encontrada no sistema!")


def reverter_empresa_padrao(apps, schema_editor):
    """Reverter: limpar empresa dos registros"""
    Pessoa = apps.get_model('cadastros', 'Pessoa')
    Produto = apps.get_model('cadastros', 'Produto')
    
    Pessoa.objects.all().update(empresa=None)
    Produto.objects.all().update(empresa=None)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0003_adicionar_empresa_nullable'),
    ]

    operations = [
        migrations.RunPython(
            popular_empresa_padrao,
            reverter_empresa_padrao
        ),
    ]
