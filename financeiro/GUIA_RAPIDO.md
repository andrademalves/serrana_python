# 🚀 MÓDULO FINANCEIRO - GUIA RÁPIDO DE USO

## ✅ INSTALAÇÃO

### 1. Criar Migrações
```bash
python manage.py makemigrations financeiro
python manage.py migrate financeiro
```

### 2. Popular Dados Iniciais
```bash
python manage.py popular_financeiro
```

Isso cria:
- 10 Bancos principais (BB, Itaú, Bradesco, Nubank, etc)
- 9 Formas de Pagamento (PIX, Boleto, Cartão, etc)
- 2 Contas Financeiras (Caixa + Conta Corrente)
- 4 Centros de Custo (Admin, Produção, Comercial, Loja)

---

## 📋 USO BÁSICO

### 1. Acessar Dashboard
```
http://localhost:8000/financeiro/
```

Mostra:
- Saldo de caixa
- Contas a pagar/receber
- Projeções 7/30/60/90 dias
- Indicadores de saúde (inadimplência, liquidez, PMR, PMP)
- Resultado do mês

### 2. Criar Conta a Pagar
1. Acesse: `/financeiro/titulos/criar/`
2. Preencha:
   - Tipo: **PAGAR**
   - Nº Documento: Ex: NF-1234
   - Descrição: Material de construção
   - Fornecedor: (selecione da lista)
   - Categoria: (plano de contas)
   - Centro de Custo: (opcional - obra/departamento)
   - Valor: 5000.00
   - Parcelas: 3
   - Intervalo: 30 dias
3. Sistema cria automaticamente 3 parcelas

### 3. Criar Conta a Receber
- Mesmo processo, mas Tipo: **RECEBER**
- Selecione Cliente no lugar de Fornecedor

### 4. Realizar Baixa (Pagamento/Recebimento)
1. Vá em `/financeiro/contas-pagar/` ou `/financeiro/contas-receber/`
2. Clique em "Baixar" na parcela
3. Preencha:
   - Data de Pagamento
   - Conta Financeira (onde o dinheiro saiu/entrou)
   - Forma de Pagamento (PIX, Boleto, etc)
   - Valor Principal: (pode ser parcial)
   - Juros, Multa, Desconto (opcional)
4. Sistema:
   - Atualiza saldo da parcela
   - Cria movimentação na conta financeira
   - Recalcula status (Aberto/Parcial/Quitado)

### 5. Estornar Baixa
- Acesse a baixa no detalhe do título
- Clique em "Estornar"
- Informe motivo
- Sistema:
  - Reabre saldo da parcela
  - Cria movimentação reversa
  - Mantém histórico completo

---

## 📊 RELATÓRIOS

### Calendário Financeiro
```
/financeiro/calendario/
```
- Visão mensal com todos os vencimentos
- Filtro por mês/ano
- Destaca vencidos em vermelho

### Contas a Pagar/Receber
```
/financeiro/relatorios/contas-pagar/
/financeiro/relatorios/contas-receber/
```
Filtros:
- Status (abertas/atrasadas/quitadas)
- Período
- Fornecedor/Cliente
- Categoria
- Centro de Custo

### Fluxo de Caixa
```
/financeiro/relatorios/fluxo-caixa/
```
- Previsto x Realizado por mês
- Navegação entre meses
- Identifica gaps (diferenças)

### DRE Simplificada
```
/financeiro/relatorios/dre/
```
- Receitas por categoria
- Despesas por categoria
- Resultado e margem

### Ponto de Equilíbrio
```
/financeiro/relatorios/ponto-equilibrio/
```
- Classifica custos fixos/variáveis
- Calcula margem de contribuição
- Determina break-even point
- Status: OK/Alerta/Crítico

### Resultado por Centro de Custo
```
/financeiro/relatorios/resultado-centro-custo/
```
- Receitas/Despesas por obra ou departamento
- Margem de cada centro

---

## 🔄 MIGRAÇÃO DO LEGADO

### Teste (não salva)
```bash
python manage.py migrar_financeiro_legado --dry-run
```

### Teste limitado (primeiros 100)
```bash
python manage.py migrar_financeiro_legado --dry-run --limite 100
```

### Execução real
```bash
python manage.py migrar_financeiro_legado
```

**O que faz:**
1. Lê tabela `financeiro` (legado)
2. Converte datas VARCHAR → DATE
3. Cria TituloFinanceiro
4. Cria ParcelaFinanceira
5. Se baixado, cria BaixaFinanceira
6. Mapeia:
   - IDCREDOR → Pessoa
   - CONTA/SUBCONTA → PlanoConta
   - IDPROJETO → CentroCusto
   - IDBANCO → ContaFinanceira

---

## 🏗️ ESTRUTURA BÁSICA

```
Título (Documento original - NF, Contrato)
  └── Parcela 1 (vencimento 30 dias)
       ├── Baixa 1 (R$ 500 em 15/01)
       └── Baixa 2 (R$ 300 em 20/01)
  └── Parcela 2 (vencimento 60 dias)
  └── Parcela 3 (vencimento 90 dias)
```

**Separação clara:**
- **Título** = Compromisso financeiro (o que você deve pagar/receber)
- **Parcela** = Vencimento individual
- **Baixa** = Pagamento/Recebimento efetivo (o que entrou/saiu do caixa)

---

## 📈 INDICADORES AUTOMÁTICOS

### Dashboard calcula automaticamente:

1. **Inadimplência**
   - (Recebíveis vencidos / Total a receber) × 100
   - Status: OK < 5% | Alerta 5-10% | Crítico > 10%

2. **Liquidez 30 dias**
   - Entradas previstas / Saídas previstas
   - Status: OK ≥ 1.2 | Alerta 1.0-1.2 | Crítico < 1.0

3. **PMR (Prazo Médio Recebimento)**
   - Média de dias entre emissão e recebimento
   - Últimos 90 dias
   - Status: OK ≤ 30d | Alerta 30-45d | Crítico > 45d

4. **PMP (Prazo Médio Pagamento)**
   - Média de dias entre emissão e pagamento
   - Últimos 90 dias

5. **Resultado Mensal**
   - Receitas - Despesas = Resultado
   - Margem %

---

## 💡 DICAS E BOAS PRÁTICAS

### ✅ Fazer

1. **Categorizar corretamente**
   - Use plano de contas adequado
   - Associe a centro de custo/obra quando aplicável

2. **Registrar baixas pontualmente**
   - Dá visão real do caixa
   - Permite projeções precisas

3. **Usar conta financeira correta**
   - Separe Caixa, Banco, Carteiras digitais
   - Facilita conciliação

4. **Classificar custos (fixos/variáveis)**
   - Necessário para ponto de equilíbrio
   - Acesse Admin → Categoria Custo Variabilidade

5. **Revisar indicadores semanalmente**
   - Inadimplência alta? Cobrar clientes
   - Liquidez baixa? Negociar prazos

### ❌ Evitar

1. **Deletar registros**
   - Use estorno ou cancele
   - Mantém auditoria

2. **Misturar contas pessoais com empresariais**
   - Crie contas separadas

3. **Baixar sem conta financeira**
   - Sempre indique onde o dinheiro entrou/saiu

4. **Ignorar centro de custo em obras**
   - Perde controle de rentabilidade por projeto

---

## 🔍 CONSULTAS RÁPIDAS (Django Shell)

```python
# Saldo de uma conta
from financeiro.services.calculadora import CalculadoraSaldos
CalculadoraSaldos.saldo_conta(1)  # ID da conta

# Total a receber
CalculadoraSaldos.total_a_receber_aberto()

# Dashboard completo
from financeiro.services.indicadores import IndicadoresSaudeFinanceira
dados = IndicadoresSaudeFinanceira.dashboard_resumo()

# Ponto de equilíbrio
from financeiro.services.ponto_equilibrio import AnalisePontoEquilibrio
break_even = AnalisePontoEquilibrio.calcular_break_even(periodo_meses=3)
```

---

## 🆘 PROBLEMAS COMUNS

### Erro: "Baixa excede saldo aberto"
**Causa:** Tentando baixar mais que o saldo da parcela  
**Solução:** Verifique baixas anteriores, pode estar duplicando

### Saldo da conta não bate
**Causa:** Movimentações estornadas ou saldo inicial incorreto  
**Solução:** 
```python
from financeiro.services.calculadora import CalculadoraSaldos
saldo = CalculadoraSaldos.saldo_conta(id_conta)
```

### Status não atualiza
**Causa:** Problema em transaction ou signal  
**Solução:**
```python
from financeiro.models import ParcelaFinanceira
parcela = ParcelaFinanceira.objects.get(pk=X)
parcela.atualizar_status()
```

---

## 📞 PRÓXIMOS PASSOS

1. ✅ Criar migrações e popular dados
2. ✅ Criar contas financeiras reais (suas contas bancárias)
3. ✅ Cadastrar plano de contas completo
4. ✅ Migrar dados do legado (se houver)
5. ✅ Cadastrar títulos novos
6. ✅ Realizar baixas conforme pagamentos
7. ✅ Revisar dashboard semanalmente
8. ✅ Classificar custos para ponto de equilíbrio

---

**Documentação completa:** `financeiro/DOCUMENTACAO.md`

**Versão:** 1.0  
**Sistema:** Serrana Empresarial
