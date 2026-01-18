# 🚀 INSTALAÇÃO RÁPIDA - MÓDULO ORÇAMENTOS/VENDAS

**Tempo estimado:** 5-10 minutos

---

## ✅ PRÉ-REQUISITOS

- ✓ Python 3.8+
- ✓ Django 4.2+
- ✓ PostgreSQL (ou outro banco)
- ✓ Módulos já instalados: `cadastros`, `projetos`, `financeiro`

---

## 📦 INSTALAÇÃO EM 5 PASSOS

### PASSO 1: Adicionar ao INSTALLED_APPS

Edite `serrana/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'cadastros',
    'estoque',
    'projetos',
    'financeiro',
    'vendas',  # ← ADICIONAR ESTA LINHA
    # ...
]
```

### PASSO 2: Adicionar URLs

Edite `serrana/urls.py`:

```python
urlpatterns = [
    # ...
    path('vendas/', include('vendas.urls')),  # ← ADICIONAR ESTA LINHA
    # ...
]
```

### PASSO 3: Migrar Banco de Dados

```bash
python manage.py makemigrations vendas
python manage.py migrate vendas
```

### PASSO 4: Criar Dados Iniciais

```bash
python manage.py shell
```

```python
from financeiro.models import PlanoContas
from vendas.models import CondicaoPagamento
from decimal import Decimal

# 1. Plano de Contas (OBRIGATÓRIO)
PlanoContas.objects.get_or_create(
    codigo='3.1.01',
    defaults={
        'nome': 'Receita de Vendas',
        'tipo': 'RECEITA',
        'ativo': True
    }
)

# 2. Condição de Pagamento Padrão
CondicaoPagamento.objects.get_or_create(
    codigo='AV',
    defaults={
        'descricao': 'À Vista',
        'tipo': 'A_VISTA',
        'numero_parcelas': 1,
        'primeira_parcela_dias': 0,
        'padrao': True,
        'ativo': True
    }
)

print("✓ Configuração inicial concluída!")
exit()
```

### PASSO 5: Executar Teste Automatizado (Opcional)

```bash
python manage.py shell < vendas/teste_automatizado.py
```

---

## 🎉 PRONTO!

Acesse:
- **Interface Web:** http://localhost:8000/vendas/orcamentos/
- **Django Admin:** http://localhost:8000/admin/vendas/

---

## 🔧 CONFIGURAÇÕES ADICIONAIS (Recomendado)

### Criar Mais Condições de Pagamento

```python
from vendas.models import CondicaoPagamento
from decimal import Decimal

# Parcelado 3x
CondicaoPagamento.objects.create(
    codigo='3X',
    descricao='3x sem juros',
    tipo='PARCELADO',
    numero_parcelas=3,
    intervalo_dias=30,
    primeira_parcela_dias=30,
    ativo=True
)

# Entrada + Parcelas
CondicaoPagamento.objects.create(
    codigo='ENT3X',
    descricao='30% Entrada + 3 Parcelas',
    tipo='ENTRADA_PARCELAS',
    percentual_entrada=Decimal('30.00'),
    numero_parcelas=3,
    intervalo_dias=30,
    primeira_parcela_dias=0,
    ativo=True
)

# Medição
CondicaoPagamento.objects.create(
    codigo='MED3',
    descricao='Medição 30-40-30',
    tipo='MEDICAO',
    medicoes_percentuais=[30, 40, 30],
    intervalo_dias=30,
    primeira_parcela_dias=0,
    ativo=True
)
```

---

## 📚 DOCUMENTAÇÃO

- **Início:** [INDICE_ORCAMENTOS_VENDAS.md](INDICE_ORCAMENTOS_VENDAS.md)
- **Implementação Completa:** [GUIA_IMPLEMENTACAO_ORCAMENTOS.md](GUIA_IMPLEMENTACAO_ORCAMENTOS.md)
- **Arquitetura:** [DESIGN_ORCAMENTOS_VENDAS.md](DESIGN_ORCAMENTOS_VENDAS.md)
- **API:** [vendas/README.md](vendas/README.md)

---

## ⚡ TESTE RÁPIDO

```bash
python manage.py shell
```

```python
from vendas.services import OrcamentoService
from cadastros.models import Pessoa
from vendas.models import CondicaoPagamento
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

# Criar cliente de teste
cliente, _ = Pessoa.objects.get_or_create(
    cpf='000.000.000-00',
    defaults={
        'tipo_pessoa': 'FISICA',
        'nome_razao': 'Cliente Teste',
        'cliente': True,
        'email': 'teste@teste.com',
        'telefone': '(00) 00000-0000',
        'endereco_logradouro': 'Rua Teste',
        'endereco_numero': '1',
        'endereco_bairro': 'Teste',
        'endereco_cidade': 'São Paulo',
        'endereco_estado': 'SP',
        'endereco_cep': '00000-000',
        'ativo': True
    }
)

# Criar orçamento
vendedor = User.objects.first()
condicao = CondicaoPagamento.objects.get(codigo='AV')

orcamento = OrcamentoService.criar_orcamento(
    cliente=cliente,
    vendedor=vendedor,
    condicao_pagamento=condicao,
    criado_por=vendedor
)

print(f"✓ Orçamento {orcamento.numero} criado!")
print(f"  Total: R$ {orcamento.total}")
```

---

## 🔍 VERIFICAÇÃO

### Checklist Pós-Instalação

- [ ] `vendas` aparece em INSTALLED_APPS
- [ ] Migrations aplicadas sem erros
- [ ] Plano de Contas `3.1.01` criado
- [ ] Condição de pagamento padrão criada
- [ ] Acesso a `/vendas/orcamentos/` funciona
- [ ] Django Admin `/admin/vendas/` funciona

### Se algo der errado:

1. Veja [GUIA_IMPLEMENTACAO_ORCAMENTOS.md](GUIA_IMPLEMENTACAO_ORCAMENTOS.md) - Seção Troubleshooting
2. Execute `python manage.py check`
3. Verifique logs de erro

---

## 🎯 PRÓXIMOS PASSOS

1. ✅ **Criar Clientes** em `/admin/cadastros/pessoa/` (marcar "Cliente")
2. ✅ **Criar Produtos** em `/admin/cadastros/produto/`
3. ✅ **Criar Orçamento** em `/vendas/orcamentos/novo/`
4. ✅ **Adicionar Itens** ao orçamento
5. ✅ **Aprovar** e ver obra + títulos criados automaticamente

---

**Versão:** 1.0  
**Suporte:** Consulte a documentação completa  
**Status:** ✅ Pronto para Produção
