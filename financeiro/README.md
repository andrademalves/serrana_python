# 💰 MÓDULO FINANCEIRO - Sistema Serrana

## 📝 Resumo Executivo

Módulo completo de **gestão financeira** para Django 6.0, com arquitetura profissional de contas a pagar e receber, controle bancário, projeções de fluxo de caixa, indicadores de saúde financeira e análise de ponto de equilíbrio.

### 🎯 Características Principais

✅ **Contas a Pagar e Receber**  
✅ **Controle de Bancos e Caixas**  
✅ **Formas de Pagamento** (PIX, Boleto, Cartões, etc)  
✅ **Baixas Parciais e Múltiplas**  
✅ **Estorno com Auditoria**  
✅ **Projeções de Fluxo** (7, 30, 60, 90 dias)  
✅ **Dashboard com KPIs**  
✅ **Calendário Financeiro**  
✅ **Indicadores de Saúde** (Inadimplência, Liquidez, PMR, PMP)  
✅ **Ponto de Equilíbrio** (Break-even Analysis)  
✅ **Relatórios Gerenciais** (Fluxo de Caixa, DRE, Resultado por Centro de Custo)  
✅ **Migração de Legado**  

---

## 📦 Instalação Rápida

```bash
# 1. Módulo já está no projeto (financeiro/)

# 2. Criar migrações
python manage.py makemigrations financeiro
python manage.py migrate financeiro

# 3. Popular dados iniciais
python manage.py popular_financeiro

# 4. Acessar dashboard
http://localhost:8000/financeiro/
```

---

## 🏗️ Arquitetura

### Separação Clara de Responsabilidades

```
TituloFinanceiro (Documento - NF, Contrato)
    ↓
ParcelaFinanceira (Vencimentos)
    ↓
BaixaFinanceira (Pagamentos efetivos)
    ↓
MovimentacaoConta (Extrato bancário)
```

**Princípios:**
- Título ≠ Parcela ≠ Baixa
- Baixas parciais permitidas
- Estorno sem delete (auditável)
- Status automático (Aberto/Parcial/Quitado)

---

## 📊 Models

### Cadastros
- `Banco` - Instituições financeiras
- `ContaFinanceira` - Contas correntes, caixas, carteiras
- `FormaPagamento` - PIX, Boleto, Cartões, etc
- `CentroCusto` - Obras, departamentos
- `CategoriaCustoVariabilidade` - Classificação fixo/variável

### Operação
- `TituloFinanceiro` - Compromisso financeiro (a pagar/receber)
- `ParcelaFinanceira` - Vencimento individual
- `BaixaFinanceira` - Pagamento/recebimento efetivo
- `MovimentacaoConta` - Extrato interno
- `TransferenciaEntreContas` - Movimentações entre contas

---

## 🧮 Services (Lógica de Negócio)

### **CalculadoraSaldos**
```python
from financeiro.services.calculadora import CalculadoraSaldos

# Saldo de uma conta
saldo = CalculadoraSaldos.saldo_conta(conta_id)

# Total a receber em aberto
total = CalculadoraSaldos.total_a_receber_aberto()
```

### **ProjecaoFluxoCaixa**
```python
from financeiro.services.calculadora import ProjecaoFluxoCaixa

# Projeções múltiplas (7, 30, 60, 90 dias)
projecoes = ProjecaoFluxoCaixa.projecoes_multiplas()

# Fluxo mensal (previsto x realizado)
fluxo = ProjecaoFluxoCaixa.fluxo_mensal(2025, 12)
```

### **IndicadoresSaudeFinanceira**
```python
from financeiro.services.indicadores import IndicadoresSaudeFinanceira

# Dashboard completo
dados = IndicadoresSaudeFinanceira.dashboard_resumo()

# Inadimplência
inadimp = IndicadoresSaudeFinanceira.inadimplencia()

# Liquidez
liquidez = IndicadoresSaudeFinanceira.liquidez_curto_prazo(30)
```

### **AnalisePontoEquilibrio**
```python
from financeiro.services.ponto_equilibrio import AnalisePontoEquilibrio

# Break-even analysis
break_even = AnalisePontoEquilibrio.calcular_break_even(periodo_meses=3)

# Projeção futura
projecao = AnalisePontoEquilibrio.projecao_break_even_futuro(receita=50000)
```

---

## 🌐 URLs Principais

```
/financeiro/                                    # Dashboard
/financeiro/titulos/                            # Lista títulos
/financeiro/titulos/criar/                      # Novo título
/financeiro/contas-pagar/                       # Contas a pagar
/financeiro/contas-receber/                     # Contas a receber
/financeiro/calendario/                         # Calendário financeiro

/financeiro/relatorios/fluxo-caixa/            # Fluxo de caixa
/financeiro/relatorios/dre/                    # DRE
/financeiro/relatorios/ponto-equilibrio/       # Break-even
/financeiro/relatorios/resultado-centro-custo/ # Por obra/depto
```

---

## 📈 Dashboard - Indicadores

### Cards Resumo
- 💰 **Caixa Atual** - Soma de todas as contas
- 📥 **A Receber** - Total aberto + vencido
- 📤 **A Pagar** - Total aberto + vencido
- 📊 **Projeção 30 Dias** - Saldo previsto

### Indicadores de Saúde
- **Inadimplência** - % de recebíveis vencidos
- **Liquidez 30d** - Entradas/Saídas previstas
- **PMR** - Prazo médio de recebimento
- **PMP** - Prazo médio de pagamento

### Projeções
- Tabela com 7, 30, 60, 90 dias
- Entradas previstas / Saídas previstas / Saldo

### Resultado Mensal
- Receitas vs Despesas vs Margem %

---

## 🔄 Migração do Legado

```bash
# Teste (dry-run)
python manage.py migrar_financeiro_legado --dry-run

# Teste limitado
python manage.py migrar_financeiro_legado --dry-run --limite 100

# Execução real
python manage.py migrar_financeiro_legado
```

**Converte:**
- Tabela `financeiro` (legado) → Títulos + Parcelas + Baixas
- Datas VARCHAR → DATE
- TIPOCONTA → tipo (PAGAR/RECEBER)
- IDCREDOR → Pessoa
- CONTA/SUBCONTA → PlanoConta
- IDPROJETO → CentroCusto
- IDBANCO → ContaFinanceira

---

## 📋 Workflow Típico

### 1. Criar Conta a Pagar
```
Fornecedor enviou NF de R$ 5.000,00 para pagar em 3x
```
1. Acesse `/financeiro/titulos/criar/`
2. Tipo: **PAGAR**
3. Preencha dados (NF, fornecedor, categoria, valor)
4. Parcelas: 3, Intervalo: 30 dias
5. Sistema cria automaticamente 3 parcelas

### 2. Realizar Baixa
```
Pagou primeira parcela de R$ 1.666,67
```
1. `/financeiro/contas-pagar/`
2. Clique "Baixar" na parcela
3. Selecione conta financeira e forma (PIX)
4. Sistema:
   - Atualiza saldo parcela
   - Cria movimentação no banco
   - Recalcula status

### 3. Estornar
```
Pagamento foi estornado pelo banco
```
1. Detalhe do título
2. Clique "Estornar" na baixa
3. Informe motivo
4. Sistema reabre parcela e cria movimentação reversa

---

## 🎓 Regras de Negócio

### ✅ Validações Automáticas
- Baixa não pode exceder saldo aberto da parcela
- Transferência: contas origem ≠ destino
- Ajuste: requer pelo menos um local
- Estorno mantém histórico completo

### ✅ Status Automáticos
- **ABERTO** - Nada pago
- **PARCIAL** - Pago parcialmente
- **QUITADO** - Totalmente pago
- **CANCELADO** - Todas parcelas canceladas

### ✅ Movimentações Automáticas
- Toda baixa gera MovimentacaoConta
- RECEBER → ENTRADA na conta
- PAGAR → SAIDA da conta
- Estorno cria movimentação reversa

---

## 📚 Documentação

- **DOCUMENTACAO.md** - Documentação completa e técnica
- **GUIA_RAPIDO.md** - Guia de uso passo a passo
- **README.md** - Este arquivo

---

## 🔧 Tecnologias

- **Django 6.0** - Framework
- **MySQL** - Banco de dados
- **Bootstrap 5** - Interface
- **Bootstrap Icons** - Ícones
- **Decimal** - Precisão monetária

---

## 📊 Performance

### Índices Criados
- Parcelas: (titulo, numero_parcela), (data_vencimento, status)
- Baixas: (parcela), (data_pagamento)
- Movimentações: (conta_financeira, data)

### Otimizações
- `select_related()` para FKs
- `prefetch_related()` para reverse FKs
- Agregações no banco (Sum, Count)
- Cálculos isolados em Services

---

## 🚀 Próximas Melhorias (Roadmap)

### Fase 2
- [ ] Integração CNAB (remessa/retorno boletos)
- [ ] Conciliação bancária automatizada
- [ ] Recorrência de títulos (mensalidades)
- [ ] Renegociação de parcelas
- [ ] Cobrança automática (emails, WhatsApp)

### Fase 3
- [ ] API REST (DRF)
- [ ] Mobile app
- [ ] Dashboards interativos (Chart.js)
- [ ] Exportação Excel/PDF
- [ ] BI integrado

---

## 📞 Suporte

**Documentação:** Consulte `DOCUMENTACAO.md` e `GUIA_RAPIDO.md`  
**Testes:** `python manage.py test financeiro`  
**Shell:** `python manage.py shell`  

---

## 📄 Licença

Proprietário - Sistema Serrana Empresarial

---

**Versão:** 1.0.0  
**Data:** Dezembro/2025  
**Desenvolvido por:** Arquiteto de Software Sênior
