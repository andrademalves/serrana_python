"""
Script de teste para validar o fluxo:
Orçamento → Aprovação → Projeto + Centro de Custo (automático)
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Empresa, User
from cadastros.models import Pessoa
from projetos.models import Orcamento, OrcamentoItem, OrcamentoParcela, Projeto
from estoque.models import Item
from financeiro.models import CentroCusto, TituloFinanceiro

print("=" * 80)
print("TESTE DO FLUXO: ORÇAMENTO → PROJETO + CENTRO DE CUSTO AUTOMÁTICO")
print("=" * 80)

# 1. Buscar dados necessários
print("\n1️⃣ Buscando dados necessários...")
empresa = Empresa.objects.first()
usuario = User.objects.filter(is_active=True).first()
cliente = Pessoa.objects.filter(cliente=True).first()
vendedor = Pessoa.objects.filter(vendedor=True).first()
item = Item.objects.first()

if not all([empresa, usuario, cliente, vendedor, item]):
    print("❌ Faltam dados no sistema:")
    print(f"   - Empresa: {'✅' if empresa else '❌'}")
    print(f"   - Usuário: {'✅' if usuario else '❌'}")
    print(f"   - Cliente: {'✅' if cliente else '❌'}")
    print(f"   - Vendedor: {'✅' if vendedor else '❌'}")
    print(f"   - Item: {'✅' if item else '❌'}")
    sys.exit(1)

print(f"✅ Empresa: {empresa.razao_social}")
print(f"✅ Usuário: {usuario.username}")
print(f"✅ Cliente: {cliente.nome}")
print(f"✅ Vendedor: {vendedor.nome}")
print(f"✅ Item: {item.descricao}")

# 2. Criar Orçamento
print("\n2️⃣ Criando novo orçamento...")
orcamento = Orcamento.objects.create(
    empresa=empresa,
    cliente=cliente,
    vendedor=vendedor,
    descricao="Teste de Orçamento - Automação",
    data_orcamento=date.today(),
    status='PENDENTE',
    criado_por=usuario
)
print(f"✅ Orçamento criado: {orcamento.codigo}")

# 3. Adicionar Itens
print("\n3️⃣ Adicionando itens ao orçamento...")
item_orc = OrcamentoItem.objects.create(
    orcamento=orcamento,
    item=item,
    quantidade=10,
    valor_unitario=Decimal('100.00'),
    descricao="Item de teste"
)
print(f"✅ Item adicionado: {item_orc.descricao} - Qtd: {item_orc.quantidade} - R$ {item_orc.valor_total}")

# Atualizar totais (o signal deve fazer isso automaticamente)
orcamento.refresh_from_db()
print(f"✅ Valor total do orçamento: R$ {orcamento.valor_final}")

# 4. Adicionar Parcelas
print("\n4️⃣ Adicionando parcelas ao orçamento...")
valor_parcela = orcamento.valor_final / 3

for i in range(1, 4):
    parcela = OrcamentoParcela.objects.create(
        orcamento=orcamento,
        numero_parcela=i,
        data_vencimento=date.today() + timedelta(days=30*i),
        valor=valor_parcela,
        forma_pagamento='BOLETO'
    )
    print(f"✅ Parcela {i}/3: R$ {parcela.valor} - Venc: {parcela.data_vencimento}")

# 5. Aprovar Orçamento (deve criar automaticamente Projeto + Centro de Custo)
print("\n5️⃣ APROVANDO ORÇAMENTO (deve criar Projeto + Centro de Custo automaticamente)...")
print("   ⏳ Aguarde...")

# Contar projetos e centros de custo antes
projetos_antes = Projeto.objects.count()
cc_antes = CentroCusto.objects.count()
titulos_antes = TituloFinanceiro.objects.count()

# APROVAR
orcamento.status = 'APROVADO'
orcamento.data_aprovacao = date.today()
orcamento.save()

print(f"   ✅ Status alterado para: {orcamento.get_status_display()}")

# Verificar se foi criado automaticamente
orcamento.refresh_from_db()
projetos_depois = Projeto.objects.count()
cc_depois = CentroCusto.objects.count()
titulos_depois = TituloFinanceiro.objects.count()

print(f"\n📊 RESULTADO DA AUTOMAÇÃO:")
print(f"   - Projetos: {projetos_antes} → {projetos_depois} (Δ = {projetos_depois - projetos_antes})")
print(f"   - Centros de Custo: {cc_antes} → {cc_depois} (Δ = {cc_depois - cc_antes})")
print(f"   - Títulos Financeiros: {titulos_antes} → {titulos_depois} (Δ = {titulos_depois - titulos_antes})")

# 6. Verificar se o projeto foi criado
print("\n6️⃣ Verificando projeto criado automaticamente...")
projeto = orcamento.projetos.first()

if projeto:
    print(f"   ✅ PROJETO CRIADO: {projeto.codigo}")
    print(f"      - Cliente: {projeto.cliente.nome}")
    print(f"      - Vendedor: {projeto.vendedor.username}")
    print(f"      - Valor Contratado: R$ {projeto.valor_contratado}")
    print(f"      - Status: {projeto.get_status_display()}")
    
    # Verificar Centro de Custo
    try:
        cc = projeto.centro_custo
        print(f"\n   ✅ CENTRO DE CUSTO VINCULADO:")
        print(f"      - Código: {cc.codigo}")
        print(f"      - Nome: {cc.nome}")
        print(f"      - Tipo: {cc.get_tipo_display()}")
        print(f"      - Responsável: {cc.responsavel.username if cc.responsavel else 'N/A'}")
        
        # Verificar Títulos Financeiros
        titulos = TituloFinanceiro.objects.filter(centro_custo=cc)
        if titulos.exists():
            print(f"\n   ✅ TÍTULOS FINANCEIROS CRIADOS: {titulos.count()}")
            for titulo in titulos:
                print(f"      - {titulo.descricao}")
                print(f"        Valor: R$ {titulo.valor_total} | Parcelas: {titulo.parcelas.count()}")
        else:
            print(f"\n   ⚠️ Nenhum título financeiro foi criado")
    except CentroCusto.DoesNotExist:
        print(f"\n   ⚠️ Centro de Custo não foi vinculado ao projeto")
        
else:
    print(f"   ❌ FALHA: Projeto NÃO foi criado automaticamente!")
    print(f"   Status do orçamento: {orcamento.get_status_display()}")

# 7. Verificar se o status mudou para CONVERTIDO
orcamento.refresh_from_db()
print(f"\n7️⃣ Status final do orçamento: {orcamento.get_status_display()}")
if orcamento.status == 'CONVERTIDO':
    print(f"   ✅ Orçamento marcado como CONVERTIDO corretamente!")
else:
    print(f"   ⚠️ Status esperado: CONVERTIDO, obtido: {orcamento.status}")

print("\n" + "=" * 80)
print("✅ TESTE CONCLUÍDO!")
print("=" * 80)
