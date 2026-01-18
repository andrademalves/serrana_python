# 📊 DASHBOARD BI - FÁBRICA DE ESQUADRIAS

## 🎯 ARQUITETURA E DESIGN

### Visão Geral
Sistema de Business Intelligence integrado para apoio à decisão gerencial, operacional e financeira, com foco em KPIs acionáveis e rastreabilidade total.

---

## 🏗️ ARQUITETURA TÉCNICA

### Stack Recomendada

**Backend:**
- Django 4.x/5.x (views + services)
- PostgreSQL (views materializadas para performance)
- Celery (atualização assíncrona de KPIs)
- Redis (cache de indicadores)

**Frontend:**
- Django Templates + HTMX (simplicidade e performance)
- Bootstrap 5 (layout responsivo)
- **Chart.js** (gráficos - leve e profissional)
- DataTables (tabelas analíticas)

**Alternativa API:**
- Django REST Framework + Vue.js/React (se precisar SPA)

**Escolha:** Django Templates + HTMX + Chart.js
- ✅ Menos complexidade
- ✅ Melhor performance inicial
- ✅ Integração natural com Django
- ✅ Fácil manutenção

---

## 📐 LAYOUT DO DASHBOARD

### Estrutura de Páginas

```
/dashboard/
├── index/                    # Dashboard Principal (visão geral)
├── estoque/                  # Dashboard de Estoque
├── obras/                    # Dashboard de Obras
├── financeiro/              # Dashboard Financeiro
└── relatorios/              # Relatórios Exportáveis
```

### Dashboard Principal (index)

**Seção 1: FILTROS GLOBAIS** (fixo no topo)
```
┌─────────────────────────────────────────────────────────────────┐
│ Período: [Hoje | Semana | Mês | Trimestre | Ano | Personalizado]│
│ Obra: [Todas | Obra X]   Centro Custo: [Todos | CC X]           │
│ [Aplicar Filtros] [Exportar PDF/Excel] [Atualizar Dados]        │
└─────────────────────────────────────────────────────────────────┘
```

**Seção 2: CARDS DE KPIs** (linha superior)
```
┌───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ 💰 CAIXA  │ 📦 ESTOQUE│ 🏗️ OBRAS  │ 💵 A REC. │ 💳 A PAG. │ 📈 LUCRO  │
│ R$ 150K   │ R$ 320K   │ 12 ativas │ R$ 280K   │ R$ 185K   │ R$ 45K    │
│ ↑ 12%     │ ↓ -5%     │ 3 novas   │ 15 dias   │ 8 dias    │ 18% marg  │
└───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

**Seção 3: GRÁFICOS PRINCIPAIS** (2 colunas)
```
┌─────────────────────────────┬─────────────────────────────┐
│ Fluxo de Caixa (30 dias)    │ Obras: Custo x Receita      │
│ [Gráfico de Linha]          │ [Gráfico de Barras]         │
├─────────────────────────────┼─────────────────────────────┤
│ Estoque ABC (Pareto)        │ Resultado Mensal (DRE)      │
│ [Gráfico de Pareto]         │ [Gráfico de Linha]          │
└─────────────────────────────┴─────────────────────────────┘
```

**Seção 4: ALERTAS E AÇÕES** (linha inferior)
```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️ ALERTAS CRÍTICOS                                             │
├─────────────────────────────────────────────────────────────────┤
│ • 15 produtos abaixo do estoque mínimo                          │
│ • Obra "Residencial XYZ" com budget estourado em 18%           │
│ • R$ 35K em títulos vencidos a receber                         │
│ • Fluxo de caixa negativo em 15 dias                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 KPIs DETALHADOS

### 1. ESTOQUE

#### KPI 1.1: Valor Total do Estoque
**Fórmula:**
```sql
SUM(saldo_quantidade * custo_medio) AS valor_total_estoque
FROM saldos_estoque
WHERE saldo_quantidade > 0
```

**Indicador:**
- Valor atual: R$ XXX.XXX
- Variação vs mês anterior: +/- X%
- Composição: % MP, % PA, % Outros

#### KPI 1.2: Itens Abaixo do Estoque Mínimo
**Fórmula:**
```sql
COUNT(*) AS itens_criticos
FROM (
    SELECT p.id, p.codigo, p.descricao,
           COALESCE(SUM(s.saldo_quantidade), 0) AS saldo_total,
           p.estoque_minimo
    FROM cadastros_produto p
    LEFT JOIN saldos_estoque s ON s.produto_id = p.id
    WHERE p.ativo = TRUE
    GROUP BY p.id
    HAVING COALESCE(SUM(s.saldo_quantidade), 0) < p.estoque_minimo
) criticos
```

**Indicador:**
- Quantidade de produtos críticos
- % do total de produtos
- Lista Top 10 mais críticos

#### KPI 1.3: Giro de Estoque
**Fórmula:**
```sql
-- Consumo do período
SELECT SUM(quantidade) AS consumo_periodo
FROM movimentos_estoque
WHERE tipo_movimento = 'SAIDA'
  AND data_operacao >= DATE_TRUNC('month', CURRENT_DATE)
  AND data_operacao < DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'

-- Estoque médio
SELECT AVG(valor_total) AS estoque_medio
FROM (
    SELECT DATE(data_operacao) AS data,
           SUM(saldo_quantidade * custo_medio) AS valor_total
    FROM saldos_estoque_historico -- view materializada
    GROUP BY DATE(data_operacao)
) diario

-- Giro = Consumo / Estoque Médio
```

**Indicador:**
- Giro mensal: X.XX vezes
- Dias de cobertura: XX dias
- Meta: >= 2x/mês

#### KPI 1.4: Curva ABC (Pareto)
**Fórmula:**
```sql
WITH estoque_valorizado AS (
    SELECT 
        p.codigo,
        p.descricao,
        SUM(s.saldo_quantidade) AS quantidade,
        AVG(s.custo_medio) AS custo_medio,
        SUM(s.saldo_quantidade * s.custo_medio) AS valor_total
    FROM saldos_estoque s
    JOIN cadastros_produto p ON p.id = s.produto_id
    WHERE s.saldo_quantidade > 0
    GROUP BY p.id, p.codigo, p.descricao
),
ranked AS (
    SELECT *,
           SUM(valor_total) OVER (ORDER BY valor_total DESC) AS valor_acumulado,
           SUM(valor_total) OVER () AS valor_total_geral
    FROM estoque_valorizado
)
SELECT *,
       (valor_acumulado / valor_total_geral * 100) AS percentual_acumulado,
       CASE 
           WHEN (valor_acumulado / valor_total_geral * 100) <= 80 THEN 'A'
           WHEN (valor_acumulado / valor_total_geral * 100) <= 95 THEN 'B'
           ELSE 'C'
       END AS classe_abc
FROM ranked
ORDER BY valor_total DESC
```

**Indicador:**
- Top 20% produtos = 80% do valor (Classe A)
- Classe A: XX produtos (R$ XXX)
- Classe B: XX produtos (R$ XXX)
- Classe C: XX produtos (R$ XXX)

#### KPI 1.5: Consumo Médio Mensal
**Fórmula:**
```sql
SELECT 
    p.codigo,
    p.descricao,
    COUNT(DISTINCT DATE_TRUNC('month', m.data_operacao)) AS meses_com_consumo,
    SUM(m.quantidade) AS consumo_total,
    AVG(mensal.quantidade) AS consumo_medio_mensal,
    STDDEV(mensal.quantidade) AS desvio_padrao
FROM movimentos_estoque m
JOIN cadastros_produto p ON p.id = m.produto_id
LEFT JOIN LATERAL (
    SELECT DATE_TRUNC('month', data_operacao) AS mes,
           SUM(quantidade) AS quantidade
    FROM movimentos_estoque
    WHERE produto_id = p.id
      AND tipo_movimento = 'SAIDA'
      AND data_operacao >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', data_operacao)
) mensal ON TRUE
WHERE m.tipo_movimento = 'SAIDA'
  AND m.data_operacao >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY p.id, p.codigo, p.descricao
ORDER BY consumo_medio_mensal DESC
LIMIT 20
```

**Indicador:**
- Top 20 produtos por consumo
- Variação (desvio padrão)
- Tendência (crescente/estável/decrescente)

---

### 2. OBRAS

#### KPI 2.1: Status das Obras
**Fórmula:**
```sql
SELECT 
    status,
    COUNT(*) AS quantidade,
    SUM(valor_contrato) AS valor_total_contrato
FROM projetos_obra
WHERE ativo = TRUE
GROUP BY status
```

**Indicador:**
```
┌─────────────┬──────┬─────────────┐
│ Status      │ Qtd  │ Valor Total │
├─────────────┼──────┼─────────────┤
│ Orçamento   │  5   │ R$ 450K     │
│ Execução    │ 12   │ R$ 2.3M     │
│ Concluída   │  3   │ R$ 680K     │
└─────────────┴──────┴─────────────┘
```

#### KPI 2.2: Análise Financeira por Obra
**Fórmula:**
```sql
WITH custos_obra AS (
    SELECT 
        obra_id,
        SUM(CASE WHEN origem = 'ESTOQUE' THEN valor ELSE 0 END) AS custo_material,
        SUM(CASE WHEN categoria = 'MAO_OBRA' THEN valor ELSE 0 END) AS custo_mao_obra,
        SUM(CASE WHEN categoria = 'TERCEIRO' THEN valor ELSE 0 END) AS custo_terceiro,
        SUM(CASE WHEN categoria = 'IMPOSTO' THEN valor ELSE 0 END) AS custo_imposto,
        SUM(valor) AS custo_total
    FROM custos_obra
    GROUP BY obra_id
),
receitas_obra AS (
    SELECT 
        centro_custo_id AS obra_id,
        SUM(valor_pago) AS receita_recebida
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER'
      AND situacao = 'PAGO'
    GROUP BY centro_custo_id
),
despesas_obra AS (
    SELECT 
        centro_custo_id AS obra_id,
        SUM(valor_pago) AS despesa_paga
    FROM financeiro_titulo
    WHERE tipo = 'PAGAR'
      AND situacao = 'PAGO'
    GROUP BY centro_custo_id
)
SELECT 
    o.id,
    o.codigo,
    o.nome,
    o.cliente_id,
    o.valor_contrato,
    COALESCE(c.custo_total, 0) AS custo_realizado,
    COALESCE(r.receita_recebida, 0) AS receita_recebida,
    COALESCE(d.despesa_paga, 0) AS despesa_paga,
    
    -- LUCRO POR COMPETÊNCIA
    o.valor_contrato - COALESCE(c.custo_total, 0) AS lucro_competencia,
    
    -- LUCRO REAL (CAIXA)
    COALESCE(r.receita_recebida, 0) - COALESCE(d.despesa_paga, 0) AS lucro_caixa,
    
    -- MARGENS
    CASE 
        WHEN o.valor_contrato > 0 THEN 
            ((o.valor_contrato - COALESCE(c.custo_total, 0)) / o.valor_contrato * 100)
        ELSE 0 
    END AS margem_competencia,
    
    CASE 
        WHEN r.receita_recebida > 0 THEN 
            ((r.receita_recebida - d.despesa_paga) / r.receita_recebida * 100)
        ELSE 0 
    END AS margem_caixa,
    
    -- PERCENTUAIS DE EXECUÇÃO
    CASE 
        WHEN o.valor_contrato > 0 THEN 
            (COALESCE(c.custo_total, 0) / o.valor_contrato * 100)
        ELSE 0 
    END AS percentual_executado,
    
    CASE 
        WHEN o.valor_contrato > 0 THEN 
            (COALESCE(r.receita_recebida, 0) / o.valor_contrato * 100)
        ELSE 0 
    END AS percentual_recebido
    
FROM projetos_obra o
LEFT JOIN custos_obra c ON c.obra_id = o.id
LEFT JOIN receitas_obra r ON r.obra_id = o.id
LEFT JOIN despesas_obra d ON d.obra_id = o.id
WHERE o.ativo = TRUE
ORDER BY o.data_inicio DESC
```

**Indicadores:**
```
Obra: Residencial XYZ
├─ Contrato: R$ 150.000,00
├─ Custos Realizados: R$ 98.500,00 (65,7%)
│  ├─ Material: R$ 62.000,00
│  ├─ Mão de Obra: R$ 28.000,00
│  ├─ Terceiros: R$ 6.500,00
│  └─ Impostos: R$ 2.000,00
├─ Receita Recebida: R$ 120.000,00 (80%)
├─ Despesa Paga: R$ 95.000,00
├─ LUCRO COMPETÊNCIA: R$ 51.500,00 (34,3%)
└─ LUCRO CAIXA: R$ 25.000,00 (20,8%)
```

#### KPI 2.3: Budget x Realizado
**Fórmula:**
```sql
SELECT 
    o.codigo AS obra,
    o.valor_contrato AS budget,
    COALESCE(SUM(c.valor), 0) AS realizado,
    o.valor_contrato - COALESCE(SUM(c.valor), 0) AS saldo,
    CASE 
        WHEN o.valor_contrato > 0 THEN 
            (COALESCE(SUM(c.valor), 0) / o.valor_contrato * 100)
        ELSE 0 
    END AS percentual_executado,
    CASE 
        WHEN COALESCE(SUM(c.valor), 0) > o.valor_contrato THEN 'ESTOURO'
        WHEN (COALESCE(SUM(c.valor), 0) / o.valor_contrato * 100) > 90 THEN 'ATENÇÃO'
        ELSE 'OK'
    END AS status_budget
FROM projetos_obra o
LEFT JOIN custos_obra c ON c.obra_id = o.id
WHERE o.status = 'EM_EXECUCAO'
GROUP BY o.id, o.codigo, o.valor_contrato
ORDER BY percentual_executado DESC
```

**Indicador (Visual de Gauge):**
```
Obra: Casa Moderna
Budget: R$ 200.000
Realizado: R$ 218.000 (109%)
Status: ⚠️ ESTOURO (+R$ 18.000)

[████████████░] 109%
```

---

### 3. FINANCEIRO

#### KPI 3.1: Saldo de Caixa Atual
**Fórmula:**
```sql
SELECT 
    COALESCE(SUM(CASE WHEN tipo = 'RECEBER' AND situacao = 'PAGO' THEN valor_pago ELSE 0 END), 0) -
    COALESCE(SUM(CASE WHEN tipo = 'PAGAR' AND situacao = 'PAGO' THEN valor_pago ELSE 0 END), 0) AS saldo_caixa
FROM financeiro_titulo
WHERE data_pagamento <= CURRENT_DATE
```

**Indicador:**
- Saldo Atual: R$ XXX.XXX
- Variação D-1: +/- R$ X.XXX
- Variação Mês: +/- X%

#### KPI 3.2: Contas a Pagar e a Receber
**Fórmula:**
```sql
-- A RECEBER
SELECT 
    SUM(CASE WHEN vencimento < CURRENT_DATE THEN valor - valor_pago ELSE 0 END) AS vencido,
    SUM(CASE WHEN vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 THEN valor - valor_pago ELSE 0 END) AS proximos_7_dias,
    SUM(CASE WHEN vencimento BETWEEN CURRENT_DATE + 8 AND CURRENT_DATE + 30 THEN valor - valor_pago ELSE 0 END) AS proximos_30_dias,
    SUM(valor - valor_pago) AS total_aberto
FROM financeiro_titulo
WHERE tipo = 'RECEBER'
  AND situacao IN ('ABERTO', 'PARCIAL')

-- A PAGAR (mesma estrutura)
```

**Indicador:**
```
┌─────────────┬──────────────┬──────────────┐
│             │ A RECEBER    │ A PAGAR      │
├─────────────┼──────────────┼──────────────┤
│ Vencido     │ R$ 35.200    │ R$ 12.800    │
│ Próx 7 dias │ R$ 48.500    │ R$ 22.300    │
│ Próx 30 dias│ R$ 125.000   │ R$ 85.600    │
│ TOTAL       │ R$ 208.700   │ R$ 120.700   │
└─────────────┴──────────────┴──────────────┘
```

#### KPI 3.3: Fluxo de Caixa Projetado
**Fórmula:**
```sql
WITH fluxo_diario AS (
    SELECT 
        data_geracao AS data,
        'INICIAL' AS tipo,
        (
            SELECT 
                COALESCE(SUM(CASE WHEN tipo = 'RECEBER' THEN valor_pago ELSE -valor_pago END), 0)
            FROM financeiro_titulo
            WHERE data_pagamento < DATE_TRUNC('day', CURRENT_DATE)
              AND situacao = 'PAGO'
        ) AS valor
    
    UNION ALL
    
    SELECT 
        vencimento AS data,
        'RECEBER' AS tipo,
        SUM(valor - valor_pago) AS valor
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER'
      AND situacao IN ('ABERTO', 'PARCIAL')
      AND vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + 90
    GROUP BY vencimento
    
    UNION ALL
    
    SELECT 
        vencimento AS data,
        'PAGAR' AS tipo,
        -SUM(valor - valor_pago) AS valor
    FROM financeiro_titulo
    WHERE tipo = 'PAGAR'
      AND situacao IN ('ABERTO', 'PARCIAL')
      AND vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + 90
    GROUP BY vencimento
)
SELECT 
    data,
    SUM(CASE WHEN tipo = 'RECEBER' THEN valor ELSE 0 END) AS entrada,
    SUM(CASE WHEN tipo = 'PAGAR' THEN -valor ELSE 0 END) AS saida,
    SUM(valor) OVER (ORDER BY data) AS saldo_acumulado
FROM fluxo_diario
ORDER BY data
```

**Indicador (Gráfico de Linha):**
```
Fluxo de Caixa Projetado (90 dias)

R$ 200K ┤     ╭──────╮
        │    ╱        ╲
R$ 150K ┤   ╱          ╲     ╭───
        │  ╱            ╲   ╱
R$ 100K ┤ ╱              ╲ ╱
        │╱                ╰
R$ 50K  ┼──────────────────────────
        └─┬──┬──┬──┬──┬──┬──┬──┬─
          0  15 30 45 60 75 90 dias

⚠️ ALERTA: Saldo negativo em 15 dias
```

#### KPI 3.4: Resultado Mensal (DRE Simplificada)
**Fórmula:**
```sql
WITH receitas AS (
    SELECT 
        DATE_TRUNC('month', data_pagamento) AS mes,
        SUM(valor_pago) AS receita
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER'
      AND situacao = 'PAGO'
      AND data_pagamento >= DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY DATE_TRUNC('month', data_pagamento)
),
despesas AS (
    SELECT 
        DATE_TRUNC('month', data_pagamento) AS mes,
        SUM(valor_pago) AS despesa
    FROM financeiro_titulo
    WHERE tipo = 'PAGAR'
      AND situacao = 'PAGO'
      AND data_pagamento >= DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY DATE_TRUNC('month', data_pagamento)
)
SELECT 
    COALESCE(r.mes, d.mes) AS mes,
    COALESCE(r.receita, 0) AS receita,
    COALESCE(d.despesa, 0) AS despesa,
    COALESCE(r.receita, 0) - COALESCE(d.despesa, 0) AS resultado,
    CASE 
        WHEN COALESCE(r.receita, 0) > 0 THEN 
            ((COALESCE(r.receita, 0) - COALESCE(d.despesa, 0)) / COALESCE(r.receita, 0) * 100)
        ELSE 0 
    END AS margem
FROM receitas r
FULL OUTER JOIN despesas d ON r.mes = d.mes
ORDER BY mes
```

**Indicador:**
```
DRE Mensal (Ano 2025)

        JAN    FEV    MAR    ABR    MAI
Receita 150K   180K   165K   210K   195K
Despesa 108K   125K   118K   142K   135K
───────────────────────────────────────
LUCRO    42K    55K    47K    68K    60K
Margem   28%    31%    28%    32%    31%
```

#### KPI 3.5: Inadimplência
**Fórmula:**
```sql
WITH titulos_abertos AS (
    SELECT 
        COUNT(*) AS total_titulos,
        SUM(valor - valor_pago) AS total_valor,
        COUNT(CASE WHEN vencimento < CURRENT_DATE THEN 1 END) AS titulos_vencidos,
        SUM(CASE WHEN vencimento < CURRENT_DATE THEN valor - valor_pago ELSE 0 END) AS valor_vencido,
        AVG(CURRENT_DATE - vencimento) FILTER (WHERE vencimento < CURRENT_DATE) AS dias_atraso_medio
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER'
      AND situacao IN ('ABERTO', 'PARCIAL')
)
SELECT 
    *,
    (titulos_vencidos::FLOAT / total_titulos * 100) AS percentual_titulos_vencidos,
    (valor_vencido / total_valor * 100) AS percentual_valor_vencido
FROM titulos_abertos
```

**Indicador:**
```
📉 INADIMPLÊNCIA

Total em Aberto: R$ 208.700
Vencido: R$ 35.200 (16,9%)
Títulos Vencidos: 8 de 42 (19%)
Atraso Médio: 12 dias

Status: ⚠️ ATENÇÃO
```

---

## 📈 GRÁFICOS DETALHADOS

### Gráfico 1: Fluxo de Caixa (Linha + Área)
**Tipo:** Line Chart (Chart.js)
**Eixo X:** Datas (próximos 90 dias)
**Eixo Y:** Valores (R$)
**Séries:**
- Linha verde: Saldo acumulado
- Área azul: Entradas
- Área vermelha: Saídas

**Configuração Chart.js:**
```javascript
{
    type: 'line',
    data: {
        labels: ['01/01', '02/01', ...],
        datasets: [
            {
                label: 'Saldo Acumulado',
                data: [150000, 148000, 152000, ...],
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                tension: 0.4
            },
            {
                label: 'Entradas',
                data: [25000, 0, 48000, ...],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                fill: true
            },
            {
                label: 'Saídas',
                data: [-18000, -22000, -15000, ...],
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                fill: true
            }
        ]
    },
    options: {
        responsive: true,
        plugins: {
            title: { display: true, text: 'Fluxo de Caixa Projetado (90 dias)' },
            legend: { position: 'bottom' }
        },
        scales: {
            y: {
                ticks: {
                    callback: value => 'R$ ' + value.toLocaleString('pt-BR')
                }
            }
        }
    }
}
```

### Gráfico 2: Obras - Custo por Categoria (Barras Empilhadas)
**Tipo:** Stacked Bar Chart
**Eixo X:** Obras
**Eixo Y:** Valores (R$)
**Séries:**
- Material (azul)
- Mão de Obra (verde)
- Terceiros (amarelo)
- Impostos (vermelho)

### Gráfico 3: Estoque ABC - Pareto
**Tipo:** Bar + Line (combo)
**Eixo X:** Produtos (Top 20)
**Eixo Y1:** Valor (barras)
**Eixo Y2:** % Acumulado (linha)

### Gráfico 4: DRE Mensal (Barras Agrupadas)
**Tipo:** Grouped Bar Chart
**Eixo X:** Meses
**Eixo Y:** Valores (R$)
**Séries:**
- Receita (verde)
- Despesa (vermelho)
- Lucro (azul)

### Gráfico 5: Despesas por Plano de Contas (Pizza)
**Tipo:** Doughnut Chart
**Dados:** % por plano de contas
**Cores:** Paleta automática

---

## 🗂️ TABELAS ANALÍTICAS

### Tabela 1: Estoque Crítico
```
┌─────────┬──────────────┬────────┬──────────┬────────┬────────────┬──────────┐
│ Código  │ Descrição    │ Local  │ Saldo    │ Mín.   │ Falta      │ Situação │
├─────────┼──────────────┼────────┼──────────┼────────┼────────────┼──────────┤
│ MP-001  │ Alumínio 6m  │ ALMOX  │ 15 un    │ 50 un  │ -35 un     │ 🔴 CRIT  │
│ MP-023  │ Vidro Temp   │ ALMOX  │ 8 m²     │ 20 m²  │ -12 m²     │ 🔴 CRIT  │
│ PA-105  │ Janela 1x1   │ LOJA   │ 3 un     │ 5 un   │ -2 un      │ 🟡 ATEN  │
└─────────┴──────────────┴────────┴──────────┴────────┴────────────┴──────────┘

Ações: [Gerar Pedido de Compra] [Exportar Excel]
```

### Tabela 2: Análise de Obras
```
┌───────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┐
│ Obra      │ Cliente  │ Contrato │ Custo    │ Recebido │ Lucro    │ Margem │
├───────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┤
│ RES-001   │ João S.  │ 150.000  │ 98.500   │ 120.000  │ 25.000   │ 20,8%  │
│ COM-005   │ Loja X   │ 280.000  │ 215.000  │ 180.000  │ -35.000  │ -19,4% │
│ RES-012   │ Maria L. │ 95.000   │ 62.000   │ 95.000   │ 33.000   │ 34,7%  │
└───────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────┘

Status: 🔴 1 obra com prejuízo | 🟡 3 obras com margem < 20%
Ações: [Ver Detalhes] [Análise Completa] [Exportar PDF]
```

### Tabela 3: Títulos a Receber
```
┌────────────┬─────────┬──────────┬────────────┬──────────┬─────────┬──────────┐
│ Vencimento │ Cliente │ Valor    │ Pago       │ Saldo    │ Atraso  │ Situação │
├────────────┼─────────┼──────────┼────────────┼──────────┼─────────┼──────────┤
│ 15/12/2025 │ João S. │ 15.000   │ 0          │ 15.000   │ 14 dias │ 🔴 VENC  │
│ 20/12/2025 │ Maria L.│ 8.500    │ 3.000      │ 5.500    │ 9 dias  │ 🔴 VENC  │
│ 05/01/2026 │ Loja X  │ 45.000   │ 0          │ 45.000   │ -       │ 🟢 ABER  │
└────────────┴─────────┴──────────┴────────────┴──────────┴─────────┴──────────┘

Total Vencido: R$ 35.200 (8 títulos)
Ações: [Cobrar Selecionados] [Enviar Email] [Gerar Boleto]
```

---

## 🎨 PALETA DE CORES

**Cores Semânticas:**
```css
--success: #22c55e    /* Verde - positivo, OK */
--warning: #f59e0b    /* Amarelo - atenção */
--danger: #ef4444     /* Vermelho - crítico */
--info: #3b82f6       /* Azul - informação */
--primary: #6366f1    /* Roxo - ação principal */
--gray: #6b7280       /* Cinza - neutro */
```

**Categorias:**
- Material: #3b82f6 (azul)
- Mão de Obra: #22c55e (verde)
- Terceiros: #f59e0b (amarelo)
- Impostos: #ef4444 (vermelho)

---

## 📤 RELATÓRIOS EXPORTÁVEIS

### 1. Análise Completa da Obra (PDF)
**Conteúdo:**
- Identificação da obra
- Resumo financeiro (contrato, custos, receitas)
- Detalhamento de custos por categoria
- Movimentos de estoque vinculados
- Títulos financeiros (a pagar e a receber)
- Gráficos (custo acumulado, budget x realizado)
- Lucro competência vs caixa

**Biblioteca:** ReportLab ou WeasyPrint

### 2. Estoque Crítico (Excel)
**Conteúdo:**
- Lista completa de produtos abaixo do mínimo
- Saldo atual, mínimo, falta
- Fornecedor principal, prazo de entrega
- Sugestão de quantidade para compra

**Biblioteca:** openpyxl ou xlsxwriter

### 3. Fluxo de Caixa Projetado (Excel)
**Conteúdo:**
- Tabela dia a dia (90 dias)
- Entradas, saídas, saldo acumulado
- Títulos vinculados
- Gráfico embutido

### 4. DRE Mensal (PDF)
**Conteúdo:**
- Receitas por categoria
- Despesas por plano de contas
- Resultado mensal
- Comparativo ano anterior

---

## ⚡ PERFORMANCE E OTIMIZAÇÃO

### Views Materializadas (PostgreSQL)

**View 1: Saldos Históricos**
```sql
CREATE MATERIALIZED VIEW saldos_estoque_historico AS
SELECT 
    DATE_TRUNC('day', m.data_operacao) AS data,
    p.id AS produto_id,
    l.id AS local_id,
    SUM(
        CASE 
            WHEN m.tipo_movimento = 'ENTRADA' THEN m.quantidade
            WHEN m.tipo_movimento = 'SAIDA' THEN -m.quantidade
            WHEN m.tipo_movimento = 'TRANSFERENCIA' THEN 
                CASE WHEN m.local_destino_id = l.id THEN m.quantidade ELSE -m.quantidade END
            ELSE 0
        END
    ) OVER (PARTITION BY p.id, l.id ORDER BY DATE_TRUNC('day', m.data_operacao)) AS saldo_quantidade,
    AVG(m.custo_unitario_aplicado) AS custo_medio
FROM movimentos_estoque m
JOIN cadastros_produto p ON p.id = m.produto_id
CROSS JOIN locais_estoque l
GROUP BY DATE_TRUNC('day', m.data_operacao), p.id, l.id, m.quantidade, m.tipo_movimento, m.local_destino_id, m.custo_unitario_aplicado;

CREATE INDEX idx_saldos_hist_data ON saldos_estoque_historico(data);
CREATE INDEX idx_saldos_hist_produto ON saldos_estoque_historico(produto_id);
```

**Atualização:**
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY saldos_estoque_historico;
```

**View 2: KPIs Consolidados**
```sql
CREATE MATERIALIZED VIEW dashboard_kpis AS
SELECT 
    CURRENT_DATE AS data_atualizacao,
    
    -- ESTOQUE
    (SELECT SUM(saldo_quantidade * custo_medio) FROM saldos_estoque) AS valor_total_estoque,
    (SELECT COUNT(*) FROM produtos_abaixo_minimo_view) AS itens_criticos,
    
    -- OBRAS
    (SELECT COUNT(*) FROM projetos_obra WHERE status = 'EM_EXECUCAO') AS obras_ativas,
    (SELECT SUM(valor_contrato) FROM projetos_obra WHERE ativo = TRUE) AS valor_contratado,
    
    -- FINANCEIRO
    (SELECT saldo_caixa FROM caixa_atual_view) AS saldo_caixa,
    (SELECT total_aberto FROM titulos_receber_view) AS total_a_receber,
    (SELECT total_aberto FROM titulos_pagar_view) AS total_a_pagar
;
```

### Cache Redis

**Estratégia:**
```python
from django.core.cache import cache

def get_kpis_estoque():
    cache_key = 'dashboard:kpis:estoque'
    kpis = cache.get(cache_key)
    
    if kpis is None:
        kpis = calcular_kpis_estoque()
        cache.set(cache_key, kpis, timeout=3600)  # 1 hora
    
    return kpis
```

### Celery Tasks (Atualização Assíncrona)

```python
@shared_task
def atualizar_kpis_dashboard():
    """
    Task Celery para atualizar KPIs do dashboard.
    Executar a cada hora.
    """
    # Atualizar views materializadas
    refresh_materialized_views()
    
    # Limpar cache
    cache.delete_pattern('dashboard:*')
    
    # Recalcular indicadores pesados
    recalcular_curva_abc()
    recalcular_fluxo_caixa_projetado()
```

**Configuração Celery Beat:**
```python
CELERY_BEAT_SCHEDULE = {
    'atualizar-kpis-dashboard': {
        'task': 'dashboard.tasks.atualizar_kpis_dashboard',
        'schedule': crontab(minute=0),  # A cada hora
    },
}
```

---

## 🔮 EVOLUÇÃO FUTURA

### Fase 2: BI Avançado
- **Drill-down:** Clique em gráfico → detalha dados
- **Filtros dinâmicos:** HTMX com atualização parcial
- **Comparativos:** Ano anterior, budget vs realizado
- **Forecasting:** Previsão de vendas e custos (ML)

### Fase 3: Alertas Inteligentes
- **Machine Learning:** Prever rupturas de estoque
- **Anomalias:** Detectar gastos fora do padrão
- **Notificações:** Email/SMS em eventos críticos

### Fase 4: Mobile Dashboard
- **API REST:** Django REST Framework
- **App Mobile:** React Native ou PWA
- **Offline-first:** Sync quando online

---

**Próximo passo:** Implementação dos Services e Views Django
