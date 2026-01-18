# GUIA DE IMPLEMENTAÇÃO - MÓDULO ORÇAMENTOS E VENDAS

## 📋 ÍNDICE
1. [Pré-Requisitos](#pré-requisitos)
2. [Instalação Passo a Passo](#instalação-passo-a-passo)
3. [Configuração](#configuração)
4. [Migrações](#migrações)
5. [Dados Iniciais](#dados-iniciais)
6. [Testes](#testes)
7. [Workflow de Uso](#workflow-de-uso)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 PRÉ-REQUISITOS

### Módulos Necessários
O módulo **Vendas/Orçamentos** depende dos seguintes módulos já implementados:

```python
# MÓDULOS OBRIGATÓRIOS:
✅ cadastros (Pessoa, Produto)
✅ projetos (Obra)
✅ financeiro (Titulo, CentroCusto, PlanoContas)
```

### Verificar Dependências
Execute para verificar:

```bash
python manage.py shell
```

```python
from cadastros.models import Pessoa, Produto
from projetos.models import Obra
from financeiro.models import Titulo, CentroCusto, PlanoContas

print("Módulos OK!")
```

---

## 📦 INSTALAÇÃO PASSO A PASSO

### PASSO 1: Adicionar App ao INSTALLED_APPS

Edite `serrana/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps do projeto
    'usuarios',
    'cadastros',
    'estoque',
    'projetos',
    'financeiro',
    'vendas',  # ← ADICIONAR AQUI
]
```

### PASSO 2: Adicionar URLs

Edite `serrana/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('cadastros.urls')),
    path('estoque/', include('estoque.urls')),
    path('projetos/', include('projetos.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('vendas/', include('vendas.urls')),  # ← ADICIONAR AQUI
    path('usuarios/', include('usuarios.urls')),
]
```

### PASSO 3: Criar Migrações

```bash
python manage.py makemigrations vendas
```

**Saída esperada:**
```
Migrations for 'vendas':
  vendas\migrations\0001_initial.py
    - Create model CondicaoPagamento
    - Create model Orcamento
    - Create model OrcamentoItem
    - Create model OrcamentoAnexo
    - Create model OrcamentoHistorico
```

### PASSO 4: Aplicar Migrações

```bash
python manage.py migrate vendas
```

**Saída esperada:**
```
Running migrations:
  Applying vendas.0001_initial... OK
```

### PASSO 5: Criar Superusuário (se ainda não existir)

```bash
python manage.py createsuperuser
```

---

## ⚙️ CONFIGURAÇÃO

### PASSO 6: Configurar Plano de Contas (IMPORTANTE!)

O módulo cria automaticamente títulos a receber. Certifique-se de ter o plano de contas configurado:

**Opção A: Via Admin** (`/admin/financeiro/planocontas/`)

Criar plano com:
- **Código:** `3.1.01`
- **Nome:** `Receita de Vendas`
- **Tipo:** `RECEITA`

**Opção B: Via Shell**

```bash
python manage.py shell
```

```python
from financeiro.models import PlanoContas

PlanoContas.objects.create(
    codigo='3.1.01',
    nome='Receita de Vendas',
    tipo='RECEITA',
    ativo=True
)
```

### PASSO 7: Criar Condições de Pagamento

Acesse `/admin/vendas/condicaopagamento/` e crie:

#### 1. À Vista
```
Código: AV
Descrição: À Vista
Tipo: A_VISTA
Primeira Parcela Dias: 0
Número Parcelas: 1
Padrao: True (marcar como padrão)
```

#### 2. Parcelado 3x
```
Código: 3X
Descrição: Parcelado em 3 vezes
Tipo: PARCELADO
Número Parcelas: 3
Intervalo Dias: 30
Primeira Parcela Dias: 30
```

#### 3. Entrada + 3 Parcelas
```
Código: ENT3X
Descrição: 30% Entrada + 3 Parcelas
Tipo: ENTRADA_PARCELAS
Percentual Entrada: 30.00
Número Parcelas: 3
Intervalo Dias: 30
Primeira Parcela Dias: 0
```

#### 4. Medição (Obra)
```
Código: MED3
Descrição: Medição 30-40-30
Tipo: MEDICAO
Medições Percentuais: [30, 40, 30]  (JSON)
Intervalo Dias: 30
Primeira Parcela Dias: 0
```

---

## 🎯 DADOS INICIAIS (TESTES)

### PASSO 8: Criar Clientes de Teste

```bash
python manage.py shell
```

```python
from cadastros.models import Pessoa

# Cliente 1: Pessoa Física
pf = Pessoa.objects.create(
    tipo_pessoa='FISICA',
    nome_razao='João da Silva',
    cpf='123.456.789-00',
    cliente=True,
    email='joao@email.com',
    telefone='(11) 98765-4321',
    endereco_logradouro='Rua das Flores',
    endereco_numero='123',
    endereco_bairro='Centro',
    endereco_cidade='São Paulo',
    endereco_estado='SP',
    endereco_cep='01000-000',
    ativo=True
)

# Cliente 2: Pessoa Jurídica
pj = Pessoa.objects.create(
    tipo_pessoa='JURIDICA',
    nome_razao='Construtora XYZ Ltda',
    cnpj='12.345.678/0001-90',
    cliente=True,
    email='contato@construtoraxyz.com',
    telefone='(11) 3000-0000',
    endereco_logradouro='Av. Paulista',
    endereco_numero='1000',
    endereco_bairro='Bela Vista',
    endereco_cidade='São Paulo',
    endereco_estado='SP',
    endereco_cep='01310-100',
    ativo=True
)

print("Clientes criados!")
```

### PASSO 9: Criar Produtos de Teste

```python
from cadastros.models import Produto

# Produto 1: Janela
janela = Produto.objects.create(
    descricao='Janela de Correr 2 Folhas - Linha Suprema',
    unidade='UN',
    preco_venda=1500.00,
    ativo=True
)

# Produto 2: Porta
porta = Produto.objects.create(
    descricao='Porta de Abrir 1 Folha - Linha Elegance',
    unidade='UN',
    preco_venda=2200.00,
    ativo=True
)

print("Produtos criados!")
```

---

## 🧪 TESTES

### TESTE 1: Criar Orçamento Completo

```python
from vendas.services import OrcamentoService
from vendas.models import CondicaoPagamento
from django.contrib.auth import get_user_model
from cadastros.models import Pessoa, Produto
from decimal import Decimal

User = get_user_model()

# Buscar dados
cliente = Pessoa.objects.get(nome_razao__icontains='João')
vendedor = User.objects.first()
condicao = CondicaoPagamento.objects.get(codigo='AV')

# Criar orçamento
orcamento = OrcamentoService.criar_orcamento(
    cliente=cliente,
    vendedor=vendedor,
    condicao_pagamento=condicao,
    criado_por=vendedor,
    observacoes="Orçamento teste"
)

print(f"Orçamento {orcamento.numero} criado!")

# Adicionar itens
produto1 = Produto.objects.first()
item1 = OrcamentoService.adicionar_item(
    orcamento=orcamento,
    produto=produto1,
    quantidade=Decimal('2.0'),
    preco_unitario=Decimal('1500.00'),
    largura=Decimal('1.20'),
    altura=Decimal('1.50'),
    cor='Branco',
    linha='Suprema'
)

item2 = OrcamentoService.adicionar_item(
    orcamento=orcamento,
    descricao='Mão de obra instalação',
    quantidade=Decimal('1.0'),
    unidade='SV',
    preco_unitario=Decimal('500.00')
)

print(f"Total orçamento: R$ {orcamento.total}")
```

### TESTE 2: Aprovar Orçamento (Criar Obra + Títulos)

```python
# Mudar status para ENVIADO
OrcamentoService.mudar_status(
    orcamento=orcamento,
    novo_status='ENVIADO',
    usuario=vendedor
)

# Aprovar
obra = OrcamentoService.aprovar_orcamento(
    orcamento=orcamento,
    usuario=vendedor,
    observacao="Aprovado via teste"
)

print(f"Obra criada: {obra.codigo}")

# Verificar títulos
from financeiro.models import Titulo
titulos = Titulo.objects.filter(
    descricao__contains=orcamento.numero
)
print(f"Títulos criados: {titulos.count()}")

for titulo in titulos:
    print(f" - {titulo.numero}: R$ {titulo.valor_original} (Vencto: {titulo.data_vencimento})")
```

**Resultado esperado:**
```
Obra criada: OBR-2025-0001
Títulos criados: 1
 - ORC-2025-0001-1/1: R$ 3500.00 (Vencto: 2025-01-15)
```

### TESTE 3: Calcular Margem

```python
margem = OrcamentoService.calcular_margem_orcamento(orcamento)
print(f"Total Venda: R$ {margem['total_venda']}")
print(f"Custo Total: R$ {margem['custo_total']}")
print(f"Lucro: R$ {margem['lucro']}")
print(f"Margem: {margem['margem_percentual']}%")
```

---

## 🌐 WORKFLOW DE USO

### Fluxo Comercial Completo

```
1. CADASTRAR CLIENTE
   ↓
   cadastros/pessoas/novo/ (marcar "Cliente")

2. CRIAR ORÇAMENTO
   ↓
   vendas/orcamentos/novo/

3. ADICIONAR ITENS
   ↓
   vendas/orcamentos/<id>/editar/

4. ENVIAR AO CLIENTE
   ↓
   Mudar status: RASCUNHO → ENVIADO
   Gerar PDF da proposta

5. NEGOCIAÇÃO (opcional)
   ↓
   Status: ENVIADO → NEGOCIACAO
   Ajustar preços, condições

6. APROVAÇÃO (CRÍTICO!)
   ↓
   Botão "Aprovar Orçamento"
   ⚡ Cria automaticamente:
      - Obra (módulo projetos)
      - Centro de Custo
      - Títulos a Receber (conforme condição pagamento)

7. EXECUÇÃO DA OBRA
   ↓
   projetos/obras/<id>/

8. RECEBIMENTOS
   ↓
   financeiro/titulos/ (baixar títulos)
```

---

## 🔥 TROUBLESHOOTING

### Problema 1: Erro ao Aprovar Orçamento

**Erro:**
```
PlanoContas matching query does not exist
```

**Solução:**
Criar plano de contas `3.1.01`:

```python
from financeiro.models import PlanoContas

PlanoContas.objects.create(
    codigo='3.1.01',
    nome='Receita de Vendas',
    tipo='RECEITA'
)
```

### Problema 2: Obra Não Sendo Criada

**Erro:**
```
ValidationError: Cliente sem endereço
```

**Solução:**
Validar se cliente tem todos os dados:

```python
from vendas.services import OrcamentoService
from cadastros.models import Pessoa

cliente = Pessoa.objects.get(id=1)
is_valid, erros = OrcamentoService.validar_cliente_orcamento(cliente)

if not is_valid:
    print("Erros:", erros)
```

### Problema 3: Títulos com Valores Errados

**Verificação:**
```python
from vendas.models import Orcamento

orc = Orcamento.objects.get(numero='ORC-2025-0001')
print(f"Condição: {orc.condicao_pagamento.tipo}")
print(f"Percentual Entrada: {orc.condicao_pagamento.percentual_entrada}%")
print(f"Nº Parcelas: {orc.condicao_pagamento.numero_parcelas}")

# Verificar títulos
for titulo in orc.obra_gerada.titulos_receber.all():
    print(f"{titulo.numero}: R$ {titulo.valor_original}")
```

### Problema 4: Migração Falha

**Erro:**
```
django.db.utils.IntegrityError: foreign key constraint fails
```

**Solução:**
Rodar migrações em ordem:

```bash
python manage.py migrate cadastros
python manage.py migrate projetos
python manage.py migrate financeiro
python manage.py migrate vendas
```

---

## 📊 QUERIES ÚTEIS

### Relatório: Orçamentos do Mês

```python
from vendas.models import Orcamento
import datetime

mes_atual = datetime.date.today().replace(day=1)
orcamentos = Orcamento.objects.filter(
    data_orcamento__gte=mes_atual
).values('status').annotate(
    total=Count('id'),
    valor=Sum('total')
)

for item in orcamentos:
    print(f"{item['status']}: {item['total']} orçamentos (R$ {item['valor']})")
```

### Relatório: Taxa de Conversão

```python
from vendas.services import RelatorioComercialService
import datetime

inicio = datetime.date(2025, 1, 1)
fim = datetime.date(2025, 12, 31)

conversao = RelatorioComercialService.taxa_conversao_vendedor(inicio, fim)

for vendedor in conversao:
    print(f"{vendedor['first_name']} {vendedor['last_name']}: " +
          f"{vendedor['taxa_conversao']}% " +
          f"({vendedor['total_aprovados']}/{vendedor['total_orcamentos']})")
```

---

## ✅ CHECKLIST FINAL

- [ ] App `vendas` adicionado ao `INSTALLED_APPS`
- [ ] URLs configuradas em `urls.py`
- [ ] Migrações criadas e aplicadas
- [ ] Plano de Contas `3.1.01` criado
- [ ] Condições de Pagamento cadastradas
- [ ] Clientes e Produtos de teste criados
- [ ] Teste de criação de orçamento OK
- [ ] Teste de aprovação e geração de obra OK
- [ ] Teste de geração de títulos OK
- [ ] Admin funcionando (`/admin/vendas/`)
- [ ] Interface web acessível (`/vendas/orcamentos/`)

---

## 🎓 PRÓXIMOS PASSOS

### FASE 2: Gerador de PDF
- Implementar gerador de propostas com ReportLab
- Template profissional com logo
- Assinatura digital

### FASE 3: CRM
- Etapas do funil
- Tarefas e follow-ups
- Histórico de contatos

### FASE 4: Comissões
- Cálculo automático de comissões
- Relatório de vendedores
- Metas e projeções

---

## 📞 SUPORTE

Documentação completa em:
- `DESIGN_ORCAMENTOS_VENDAS.md` - Arquitetura técnica
- `vendas/README.md` - Visão geral do módulo

---

**Versão:** 1.0  
**Data:** Dezembro 2025  
**Autor:** Sistema Comercial Profissional
