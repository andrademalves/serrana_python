# ETAPA 1 - BUDGET E CONTROLE DE LUCRATIVIDADE
## Estrutura de Models e Cálculos de Impostos

### ✅ MODELOS CRIADOS/MODIFICADOS

#### 1. **RegimeTributario** (`financeiro.models`)
Tabela com regimes tributários disponíveis:
- Simples Nacional
- Lucro Presumido  
- Lucro Real
- MEI

#### 2. **AliquotaImposto** (`financeiro.models`)
Configuração de alíquotas por regime e empresa:
- Tipo de imposto (ISS, ICMS, PIS, COFINS, IRPJ, CSLL, IPI, INSS, Outros)
- Alíquota percentual (0-100%)
- Base de cálculo (Faturamento, Lucro, Custo Material, Custo Serviço)
- Vínculo com empresa e regime tributário

#### 3. **Empresa** (`usuarios.models`) - MODIFICADO
Adicionado campo:
- `regime_tributario` (ForeignKey para RegimeTributario)

#### 4. **ProjectBudget** (`financeiro.models`)
Orçamento de execução vinculado ao projeto:

**Materiais** (puxados automaticamente via engenharia de corte):
- Custo alumínio previsto
- Custo vidro previsto
- Custo acessórios previsto
- Custo outros materiais previsto

**Operacional**:
- KM estimado
- Valor combustível/litro
- Consumo médio (km/L)
- Custo pedágios previsto
- Custo estacionamento previsto

**Mão de Obra**:
- Horas fabricação previstas + valor/hora
- Horas montagem previstas + valor/hora

**Controle**:
- Custo total previsto (calculado automaticamente)
- Valor de venda
- Lucro previsto
- Margem prevista (%)
- **Percentual uso budget** (gastos reais / previsto)
- **Semáforo** (Verde/Amarelo/Vermelho)
- **Bloqueado** (automático quando > 95%)

#### 5. **ProjectExpense** (`financeiro.models`)
Lançamentos reais de despesas:
- Tipo (Material, Mão de Obra, Combustível, Pedágio, Retrabalho, Desperdício, etc)
- Valor
- KM rodado (via GPS)
- Horas trabalhadas
- Funcionário responsável
- **Recibo (upload de imagem)**
- **Geolocalização** (check-in/check-out)
- Status (Pendente/Aprovado/Rejeitado/Pago)
- Aprovação com usuário e data

#### 6. **JustificativaBudget** (`financeiro.models`)
Justificativas para estouro de budget (>95%):
- Motivo (Aumento Escopo, Erro Orçamento, Variação Preço, Retrabalho, Imprevisto, etc)
- Descrição detalhada
- Valor adicional necessário
- Documento comprobatório (upload)
- Status (Pendente/Aprovado/Rejeitado)
- Aprovação/Rejeição com parecer

---

### 🔧 SERVICES CRIADOS (`financeiro/services_budget.py`)

#### **CalculadoraImpostos**
- `calcular_impostos_venda(empresa, valor_venda)` 
  - Retorna todos os impostos calculados baseado no regime tributário
  - Total de impostos
  - Valor líquido após impostos
  
- `provisionar_impostos_orcamento(orcamento)`
  - Cria provisionamento automático de impostos no fechamento da venda

#### **ValidadorBudget**
- `validar_lancamento_despesa(budget, valor_despesa)`
  - Valida se despesa pode ser lançada
  - Verifica bloqueios e limites
  - Retorna mensagens de alerta

- `validar_budget_minimo(budget)`
  - Valida se budget tem valores mínimos preenchidos
  - Detecta operações com prejuízo

#### **AnalisadorPerformance**
- `calcular_assertividade_vendedor(vendedor, periodo_inicio, periodo_fim)`
  - KPI: Lucro Orçado vs Lucro Real
  - Detecta vendas com prejuízo
  - Índice de assertividade do vendedor

- `calcular_indice_retrabalho_instalador(instalador, periodo_inicio, periodo_fim)`
  - Visitas extras ao mesmo projeto
  - Registro de desperdício de material
  - Índice de retrabalho (%)

#### **GeradorRelatorios**
- `relatorio_projetos_criticos()`
  - Lista projetos vermelhos (>95%) e amarelos (80-95%)

- `relatorio_lucratividade_geral(empresa, periodo_inicio, periodo_fim)`
  - Visão consolidada de lucratividade
  - Desvios entre previsto x real

---

### 📊 LÓGICA DO SEMÁFORO

O sistema calcula automaticamente:

```python
percentual_uso = (gastos_reais / custo_previsto) * 100

Se < 80%  → VERDE   (budget saudável)
Se 80-95% → AMARELO (atenção, notificação disparada)
Se > 95%  → VERMELHO (bloqueio automático, exige justificativa)
```

**Bloqueio Automático:**
- Quando `percentual_uso > 95%` e `status = 'EM_EXECUCAO'`
- O campo `bloqueado` é setado como `True`
- Novos lançamentos de despesa são rejeitados pela API/App
- Apenas uma `JustificativaBudget` aprovada desbloqueia

---

### 🚀 PRÓXIMOS PASSOS (ETAPA 2)

1. **Criar Signals Django** para monitoramento automático:
   - `post_save` em `ProjectExpense` → atualizar semáforo
   - Disparar notificações quando entrar em amarelo/vermelho
   
2. **Views de Validação**:
   - API endpoint para lançar despesa (com validação de bloqueio)
   - View para aprovação de justificativas
   - Dashboard de budgets em tempo real

3. **Sistema de Notificações**:
   - E-mail/SMS quando budget > 80%
   - Alerta crítico quando budget > 95%

---

### 📋 COMANDOS PARA APLICAR AS MUDANÇAS

```bash
# 1. Criar migrations
python manage.py makemigrations usuarios
python manage.py makemigrations financeiro

# 2. Visualizar SQL das migrations (opcional)
python manage.py sqlmigrate financeiro 000X

# 3. Aplicar migrations
python manage.py migrate

# 4. Criar regimes tributários padrão (via shell ou fixture)
python manage.py shell
```

```python
# No shell Django:
from financeiro.models import RegimeTributario

RegimeTributario.objects.create(
    nome='SIMPLES_NACIONAL',
    descricao='Regime Simples Nacional - Unificação de impostos'
)
RegimeTributario.objects.create(
    nome='LUCRO_PRESUMIDO',
    descricao='Lucro Presumido - Base de cálculo simplificada'
)
RegimeTributario.objects.create(
    nome='LUCRO_REAL',
    descricao='Lucro Real - Base no lucro efetivo'
)
RegimeTributario.objects.create(
    nome='MEI',
    descricao='Microempreendedor Individual'
)
```

---

### 🔍 EXEMPLO DE USO

```python
from financeiro.models import ProjectBudget, ProjectExpense, AliquotaImposto
from financeiro.services_budget import CalculadoraImpostos, ValidadorBudget

# 1. Criar budget para um projeto
budget = ProjectBudget.objects.create(
    empresa=empresa,
    projeto=projeto,
    descricao="Instalação Esquadrias Residencial",
    custo_aluminio_previsto=15000,
    custo_vidro_previsto=8000,
    custo_acessorios_previsto=2000,
    km_estimado=150,
    valor_combustivel_litro=5.50,
    horas_fabricacao_previstas=40,
    valor_hora_fabricacao=35,
    horas_montagem_previstas=24,
    valor_hora_montagem=45,
    valor_venda=45000
)

# 2. Lançar despesa
pode_lancar, msg = ValidadorBudget.validar_lancamento_despesa(budget, 5000)
if pode_lancar:
    despesa = ProjectExpense.objects.create(
        budget=budget,
        tipo_despesa='MATERIAL',
        descricao='Compra alumínio extra',
        valor=5000,
        # ... outros campos
    )

# 3. Calcular impostos sobre venda
impostos = CalculadoraImpostos.calcular_impostos_venda(
    empresa=empresa,
    valor_venda=45000
)
print(f"Total impostos: R$ {impostos['total_impostos']}")
print(f"Valor líquido: R$ {impostos['valor_liquido']}")
```

---

### ⚠️ OBSERVAÇÕES IMPORTANTES

1. **Compatibilidade**: Os modelos mantêm compatibilidade com o cadastro de produtos existente

2. **Campos Nullable**: Alguns campos possuem `null=True, blank=True` para flexibilidade na migração

3. **Foreign Keys**: 
   - `projeto` pode ser `null` (caso budget seja criado antes de converter orçamento)
   - `orcamento` pode ser `null` (caso projeto não venha de orçamento)

4. **Índices**: Criados índices para otimizar consultas frequentes (status, semáforo, datas)

5. **Auditoria**: Todos os modelos possuem campos de auditoria (criado_em, criado_por, etc)

---

### 📁 ARQUIVOS MODIFICADOS/CRIADOS

```
financeiro/
  ├── models.py                    # ✏️ MODIFICADO - Novos modelos adicionados
  └── services_budget.py           # ✨ NOVO - Lógica de negócio

usuarios/
  └── models.py                    # ✏️ MODIFICADO - Campo regime_tributario
```

---

**Status**: ✅ ETAPA 1 CONCLUÍDA

**Próximo**: 🔄 ETAPA 2 - Lógica de Alertas e Controle (Signals/Services)
