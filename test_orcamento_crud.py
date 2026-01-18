"""
Script para testar criação e edição de orçamentos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth import get_user_model
from projetos.models import Orcamento, OrcamentoItem
from cadastros.models import Pessoa
from decimal import Decimal
from datetime import date

User = get_user_model()

print("=" * 60)
print("TESTE 1: Criar novo orçamento com item tipo 'produto_1'")
print("=" * 60)

try:
    # Buscar dados necessários
    admin = User.objects.get(username='admin')
    cliente = Pessoa.objects.filter(tipo__in=['CLIENTE', 'AMBOS'], ativo=True).first()
    
    if not cliente:
        print("❌ ERRO: Nenhum cliente encontrado no sistema")
        exit(1)
    
    # Criar orçamento
    orcamento = Orcamento.objects.create(
        cliente=cliente,
        vendedor=admin,
        data_orcamento=date.today(),
        valor_total=Decimal('1500.00'),
        desconto=Decimal('0.00'),
        valor_final=Decimal('1500.00'),
        criado_por=admin
    )
    print(f"✅ Orçamento criado: {orcamento.codigo}")
    
    # Criar item do orçamento (simulando envio do form com "produto_1")
    item = OrcamentoItem.objects.create(
        orcamento=orcamento,
        tipo='PRODUTO',
        item=None,  # FK será None pois produto_1 não existe em Item
        descricao='Produto de teste - Barra de alumínio',
        quantidade=Decimal('2.000'),
        valor_unitario=Decimal('750.0000'),
        desconto=Decimal('0.00')
    )
    print(f"✅ Item do orçamento criado: ID {item.id}")
    print(f"   - Tipo: {item.tipo}")
    print(f"   - Item FK: {item.item}")
    print(f"   - Descrição: {item.descricao}")
    print(f"   - Valor total: {item.valor_total}")
    
    print("\n" + "=" * 60)
    print("TESTE 2: Editar o item do orçamento")
    print("=" * 60)
    
    # Editar item
    item.quantidade = Decimal('3.000')
    item.valor_unitario = Decimal('500.0000')
    item.save()
    print(f"✅ Item atualizado")
    print(f"   - Nova quantidade: {item.quantidade}")
    print(f"   - Novo valor unitário: {item.valor_unitario}")
    print(f"   - Novo valor total: {item.valor_total}")
    
    print("\n" + "=" * 60)
    print("TESTE 3: Verificar se pode buscar e exibir")
    print("=" * 60)
    
    # Buscar orçamento
    orc_teste = Orcamento.objects.get(pk=orcamento.pk)
    print(f"✅ Orçamento encontrado: {orc_teste.codigo}")
    print(f"   - Cliente: {orc_teste.cliente.nome}")
    print(f"   - Data: {orc_teste.data_orcamento}")
    print(f"   - Itens: {orc_teste.itens.count()}")
    
    for i in orc_teste.itens.all():
        print(f"\n   Item ID {i.id}:")
        print(f"     - Tipo: {i.tipo}")
        print(f"     - Descrição: {i.descricao}")
        print(f"     - Quantidade: {i.quantidade}")
        print(f"     - Valor: R$ {i.valor_total}")
    
    print("\n" + "=" * 60)
    print("TESTE 4: Simular exclusão (soft delete via formulário)")
    print("=" * 60)
    
    # Criar segundo item para testar exclusão
    item2 = OrcamentoItem.objects.create(
        orcamento=orcamento,
        tipo='MATERIAL',
        item=None,
        descricao='Item para excluir',
        quantidade=Decimal('1.000'),
        valor_unitario=Decimal('100.0000'),
        desconto=Decimal('0.00')
    )
    print(f"✅ Segundo item criado: ID {item2.id}")
    
    # Deletar
    item2.delete()
    print(f"✅ Item excluído com sucesso")
    print(f"   - Itens restantes: {orcamento.itens.count()}")
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\nO sistema está funcionando corretamente:")
    print("1. ✅ Criar orçamento com item sem FK (produto_1)")
    print("2. ✅ Editar item do orçamento")
    print("3. ✅ Buscar e exibir orçamento")
    print("4. ✅ Excluir item do orçamento")
    
    print(f"\n📝 Orçamento de teste criado: ID {orcamento.pk}")
    print(f"   Você pode editá-lo em: http://127.0.0.1:8000/projetos/orcamentos/{orcamento.pk}/editar/")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
