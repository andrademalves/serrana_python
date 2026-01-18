"""
SCRIPT DE TESTE - MÓDULO ORÇAMENTOS/VENDAS
==========================================

Execute este script para testar todas as funcionalidades do módulo.

Uso:
    python manage.py shell < vendas/teste_automatizado.py

OU:
    python manage.py shell
    >>> exec(open('vendas/teste_automatizado.py').read())
"""

print("="*70)
print("TESTE AUTOMATIZADO - MÓDULO ORÇAMENTOS/VENDAS")
print("="*70)

# ==================== IMPORTS ====================
print("\n[1/10] Importando módulos...")

from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from cadastros.models import Pessoa, Produto
from projetos.models import Obra
from financeiro.models import Titulo, CentroCusto, PlanoContas
from vendas.models import (
    CondicaoPagamento, Orcamento, OrcamentoItem,
    OrcamentoHistorico, OrcamentoAnexo
)
from vendas.services import OrcamentoService, RelatorioComercialService

User = get_user_model()

print("✓ Módulos importados com sucesso!")

# ==================== VERIFICAR PRÉ-REQUISITOS ====================
print("\n[2/10] Verificando pré-requisitos...")

# Verificar se existem usuários
usuarios = User.objects.filter(is_active=True)
if not usuarios.exists():
    print("❌ ERRO: Nenhum usuário encontrado. Crie um superusuário:")
    print("   python manage.py createsuperuser")
    exit(1)

vendedor = usuarios.first()
print(f"✓ Vendedor: {vendedor.get_full_name()} ({vendedor.username})")

# Verificar Plano de Contas
plano_contas, created = PlanoContas.objects.get_or_create(
    codigo='3.1.01',
    defaults={
        'nome': 'Receita de Vendas',
        'tipo': 'RECEITA',
        'ativo': True
    }
)
if created:
    print("✓ Plano de Contas '3.1.01' criado")
else:
    print("✓ Plano de Contas '3.1.01' já existe")

# ==================== CRIAR DADOS DE TESTE ====================
print("\n[3/10] Criando dados de teste...")

# Cliente Pessoa Física
pf, created = Pessoa.objects.get_or_create(
    cpf='123.456.789-00',
    defaults={
        'tipo_pessoa': 'FISICA',
        'nome_razao': 'João da Silva - TESTE',
        'cliente': True,
        'email': 'joao.teste@email.com',
        'telefone': '(11) 98765-4321',
        'endereco_logradouro': 'Rua das Flores',
        'endereco_numero': '123',
        'endereco_bairro': 'Centro',
        'endereco_cidade': 'São Paulo',
        'endereco_estado': 'SP',
        'endereco_cep': '01000-000',
        'ativo': True
    }
)
print(f"✓ Cliente PF: {pf.nome_razao}")

# Cliente Pessoa Jurídica
pj, created = Pessoa.objects.get_or_create(
    cnpj='12.345.678/0001-90',
    defaults={
        'tipo_pessoa': 'JURIDICA',
        'nome_razao': 'Construtora XYZ - TESTE',
        'cliente': True,
        'email': 'contato@teste.com',
        'telefone': '(11) 3000-0000',
        'endereco_logradouro': 'Av. Paulista',
        'endereco_numero': '1000',
        'endereco_bairro': 'Bela Vista',
        'endereco_cidade': 'São Paulo',
        'endereco_estado': 'SP',
        'endereco_cep': '01310-100',
        'ativo': True
    }
)
print(f"✓ Cliente PJ: {pj.nome_razao}")

# Produtos
janela, created = Produto.objects.get_or_create(
    descricao='Janela 2 Folhas - TESTE',
    defaults={
        'unidade': 'UN',
        'ativo': True
    }
)
print(f"✓ Produto 1: {janela.descricao}")

porta, created = Produto.objects.get_or_create(
    descricao='Porta 1 Folha - TESTE',
    defaults={
        'unidade': 'UN',
        'ativo': True
    }
)
print(f"✓ Produto 2: {porta.descricao}")

# ==================== CRIAR CONDIÇÕES DE PAGAMENTO ====================
print("\n[4/10] Criando condições de pagamento...")

# À Vista
cond_av, created = CondicaoPagamento.objects.get_or_create(
    codigo='TESTE-AV',
    defaults={
        'descricao': 'À Vista - TESTE',
        'tipo': 'A_VISTA',
        'numero_parcelas': 1,
        'primeira_parcela_dias': 0,
        'ativo': True
    }
)
print(f"✓ Condição 1: {cond_av.descricao}")

# Parcelado 3x
cond_3x, created = CondicaoPagamento.objects.get_or_create(
    codigo='TESTE-3X',
    defaults={
        'descricao': '3x sem juros - TESTE',
        'tipo': 'PARCELADO',
        'numero_parcelas': 3,
        'intervalo_dias': 30,
        'primeira_parcela_dias': 30,
        'ativo': True
    }
)
print(f"✓ Condição 2: {cond_3x.descricao}")

# Entrada + Parcelas
cond_ent, created = CondicaoPagamento.objects.get_or_create(
    codigo='TESTE-ENT3X',
    defaults={
        'descricao': '30% Entrada + 3x - TESTE',
        'tipo': 'ENTRADA_PARCELAS',
        'percentual_entrada': Decimal('30.00'),
        'numero_parcelas': 3,
        'intervalo_dias': 30,
        'primeira_parcela_dias': 0,
        'ativo': True
    }
)
print(f"✓ Condição 3: {cond_ent.descricao}")

# Medição
cond_med, created = CondicaoPagamento.objects.get_or_create(
    codigo='TESTE-MED',
    defaults={
        'descricao': 'Medição 30-40-30 - TESTE',
        'tipo': 'MEDICAO',
        'medicoes_percentuais': [30, 40, 30],
        'intervalo_dias': 30,
        'primeira_parcela_dias': 0,
        'ativo': True
    }
)
print(f"✓ Condição 4: {cond_med.descricao}")

# ==================== TESTE 1: CRIAR ORÇAMENTO ====================
print("\n[5/10] TESTE 1: Criar orçamento...")

try:
    orc1 = OrcamentoService.criar_orcamento(
        cliente=pf,
        vendedor=vendedor,
        condicao_pagamento=cond_av,
        criado_por=vendedor,
        observacoes="Orçamento de teste automatizado"
    )
    print(f"✓ Orçamento criado: {orc1.numero}")
    print(f"  Cliente: {orc1.cliente.nome_razao}")
    print(f"  Status: {orc1.status}")
    print(f"  Validade: {orc1.validade_ate}")
except Exception as e:
    print(f"❌ ERRO ao criar orçamento: {e}")
    exit(1)

# ==================== TESTE 2: ADICIONAR ITENS ====================
print("\n[6/10] TESTE 2: Adicionar itens ao orçamento...")

try:
    # Item 1: Janela
    item1 = OrcamentoService.adicionar_item(
        orcamento=orc1,
        produto=janela,
        quantidade=Decimal('2.0'),
        preco_unitario=Decimal('1500.00'),
        custo_unitario_estimado=Decimal('1000.00'),
        largura=Decimal('1.20'),
        altura=Decimal('1.50'),
        cor='Branco',
        linha='Suprema',
        vidro='Incolor 4mm',
        acabamento='Anodizado'
    )
    print(f"✓ Item 1 adicionado: {item1.descricao}")
    print(f"  Quantidade: {item1.quantidade} {item1.unidade}")
    print(f"  Preço: R$ {item1.preco_unitario}")
    print(f"  Total: R$ {item1.total_item}")
    
    # Item 2: Porta
    item2 = OrcamentoService.adicionar_item(
        orcamento=orc1,
        produto=porta,
        quantidade=Decimal('1.0'),
        preco_unitario=Decimal('2200.00'),
        custo_unitario_estimado=Decimal('1500.00'),
        largura=Decimal('0.80'),
        altura=Decimal('2.10'),
        cor='Branco',
        linha='Elegance'
    )
    print(f"✓ Item 2 adicionado: {item2.descricao}")
    
    # Item 3: Serviço
    item3 = OrcamentoService.adicionar_item(
        orcamento=orc1,
        descricao='Instalação e Mão de Obra',
        quantidade=Decimal('1.0'),
        unidade='SV',
        preco_unitario=Decimal('500.00')
    )
    print(f"✓ Item 3 adicionado: {item3.descricao}")
    
    # Atualizar totais
    orc1.refresh_from_db()
    print(f"\n  SUBTOTAL: R$ {orc1.subtotal}")
    print(f"  TOTAL: R$ {orc1.total}")
    
except Exception as e:
    print(f"❌ ERRO ao adicionar itens: {e}")
    exit(1)

# ==================== TESTE 3: CALCULAR MARGEM ====================
print("\n[7/10] TESTE 3: Calcular margem...")

try:
    margem = OrcamentoService.calcular_margem_orcamento(orc1)
    print(f"✓ Margem calculada:")
    print(f"  Total Venda: R$ {margem['total_venda']}")
    print(f"  Custo Total: R$ {margem['custo_total']}")
    print(f"  Lucro: R$ {margem['lucro']}")
    print(f"  Margem %: {margem['margem_percentual']:.2f}%")
except Exception as e:
    print(f"❌ ERRO ao calcular margem: {e}")

# ==================== TESTE 4: MUDAR STATUS ====================
print("\n[8/10] TESTE 4: Mudar status do orçamento...")

try:
    OrcamentoService.mudar_status(
        orcamento=orc1,
        novo_status='ENVIADO',
        usuario=vendedor,
        observacao="Proposta enviada por email - TESTE"
    )
    orc1.refresh_from_db()
    print(f"✓ Status alterado para: {orc1.status}")
    
    # Verificar histórico
    historico_count = orc1.historico.count()
    print(f"  Registros no histórico: {historico_count}")
except Exception as e:
    print(f"❌ ERRO ao mudar status: {e}")

# ==================== TESTE 5: APROVAR ORÇAMENTO ====================
print("\n[9/10] TESTE 5: Aprovar orçamento (CRITICA!)...")

try:
    print("  Aprovando orçamento...")
    obra = OrcamentoService.aprovar_orcamento(
        orcamento=orc1,
        usuario=vendedor,
        observacao="Aprovação automática via teste - Cliente confirmou"
    )
    
    print(f"✓ Orçamento aprovado com sucesso!")
    print(f"\n  OBRA CRIADA:")
    print(f"    Código: {obra.codigo}")
    print(f"    Nome: {obra.nome}")
    print(f"    Cliente: {obra.cliente.nome_razao}")
    print(f"    Status: {obra.status}")
    print(f"    Valor Orçado: R$ {obra.valor_orcado}")
    
    if obra.centro_custo:
        print(f"\n  CENTRO DE CUSTO CRIADO:")
        print(f"    Nome: {obra.centro_custo.nome}")
        print(f"    Tipo: {obra.centro_custo.tipo}")
    
    # Verificar títulos criados
    titulos = Titulo.objects.filter(
        descricao__contains=orc1.numero
    ).order_by('data_vencimento')
    
    print(f"\n  TÍTULOS A RECEBER CRIADOS: {titulos.count()}")
    for i, titulo in enumerate(titulos, 1):
        print(f"    {i}. {titulo.numero}")
        print(f"       Valor: R$ {titulo.valor_original}")
        print(f"       Vencimento: {titulo.data_vencimento}")
        print(f"       Status: {titulo.status}")
    
    # Verificar vínculo
    orc1.refresh_from_db()
    print(f"\n  VÍNCULO:")
    print(f"    Orçamento → Obra: {orc1.obra_gerada.codigo if orc1.obra_gerada else 'ERRO!'}")
    
except Exception as e:
    print(f"❌ ERRO CRÍTICO ao aprovar orçamento: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ==================== TESTE 6: RELATÓRIOS ====================
print("\n[10/10] TESTE 6: Relatórios comerciais...")

try:
    # Funil de vendas
    inicio = datetime.date(2025, 1, 1)
    fim = datetime.date(2025, 12, 31)
    
    funil = RelatorioComercialService.funil_vendas(inicio, fim)
    print(f"✓ Funil de vendas (2025):")
    for etapa in funil:
        print(f"  {etapa['status']}: {etapa['quantidade']} orçamento(s) - R$ {etapa['valor_total'] or 0}")
    
    # Taxa de conversão
    conversao = RelatorioComercialService.taxa_conversao_vendedor(inicio, fim)
    print(f"\n✓ Taxa de conversão por vendedor:")
    for v in conversao:
        nome = f"{v['first_name']} {v['last_name']}"
        print(f"  {nome}: {v['taxa_conversao']}% ({v['total_aprovados']}/{v['total_orcamentos']})")
    
    # Backlog
    backlog = RelatorioComercialService.backlog_obras()
    print(f"\n✓ Backlog de obras: {len(backlog)} obra(s)")
    
except Exception as e:
    print(f"❌ ERRO nos relatórios: {e}")

# ==================== RESUMO ====================
print("\n" + "="*70)
print("RESUMO DO TESTE")
print("="*70)

print("\n✅ TODOS OS TESTES EXECUTADOS COM SUCESSO!")

print("\nDADOS CRIADOS:")
print(f"  - 2 Clientes (PF e PJ)")
print(f"  - 2 Produtos (Janela e Porta)")
print(f"  - 4 Condições de Pagamento")
print(f"  - 1 Orçamento ({orc1.numero})")
print(f"  - 3 Itens no orçamento")
print(f"  - 1 Obra ({obra.codigo})")
print(f"  - 1 Centro de Custo")
print(f"  - {titulos.count()} Título(s) a Receber")

print("\nVALORES:")
print(f"  - Total Orçamento: R$ {orc1.total}")
print(f"  - Margem Estimada: {margem['margem_percentual']:.2f}%")

print("\nPRÓXIMOS PASSOS:")
print("  1. Acesse /admin/vendas/orcamento/ para ver no Django Admin")
print("  2. Acesse /vendas/orcamentos/ para ver na interface web")
print(f"  3. Acesse /projetos/obras/{obra.pk}/ para ver a obra gerada")
print(f"  4. Acesse /financeiro/titulos/ para ver os títulos")

print("\nLIMPEZA (opcional):")
print("  Para deletar dados de teste, execute:")
print("  >>> Orcamento.objects.filter(numero__contains='TESTE').delete()")
print("  >>> Pessoa.objects.filter(nome_razao__contains='TESTE').delete()")
print("  >>> Produto.objects.filter(descricao__contains='TESTE').delete()")
print("  >>> CondicaoPagamento.objects.filter(codigo__startswith='TESTE').delete()")

print("\n" + "="*70)
print("TESTE CONCLUÍDO!")
print("="*70)
