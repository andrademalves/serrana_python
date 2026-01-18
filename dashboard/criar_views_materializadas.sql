-- ===========================================================================
-- VIEWS MATERIALIZADAS - DASHBOARD BI
-- ===========================================================================
-- Sistema de Business Intelligence para Fábrica de Esquadrias
-- Autor: Sistema BI Profissional
-- Data: Dezembro 2025
-- 
-- IMPORTANTE: Executar como superusuário PostgreSQL
-- Banco de dados: serrana_db (ou seu nome de banco)
-- ===========================================================================

-- Conectar no banco correto
-- \c serrana_db

-- ===========================================================================
-- VIEW 1: HISTÓRICO DE MOVIMENTAÇÃO DE ESTOQUE
-- ===========================================================================
-- Consolida movimentações por dia e produto
-- Usado em: Gráficos de tendência, análise de consumo
-- Atualização: Diariamente às 00:00 via Celery
-- ===========================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_estoque_historico CASCADE;

CREATE MATERIALIZED VIEW mv_estoque_historico AS
SELECT 
    DATE(me.data_operacao) AS data,
    me.produto_id,
    p.codigo AS produto_codigo,
    p.descricao AS produto_descricao,
    p.unidade AS produto_unidade,
    
    -- Entradas
    SUM(CASE 
        WHEN me.tipo_movimento = 'ENTRADA' THEN me.quantidade 
        ELSE 0 
    END) AS quantidade_entrada,
    
    SUM(CASE 
        WHEN me.tipo_movimento = 'ENTRADA' THEN (me.quantidade * me.custo_unitario_aplicado) 
        ELSE 0 
    END) AS valor_entrada,
    
    -- Saídas
    SUM(CASE 
        WHEN me.tipo_movimento = 'SAIDA' THEN me.quantidade 
        ELSE 0 
    END) AS quantidade_saida,
    
    SUM(CASE 
        WHEN me.tipo_movimento = 'SAIDA' THEN (me.quantidade * me.custo_unitario_aplicado) 
        ELSE 0 
    END) AS valor_saida,
    
    -- Totais
    SUM(me.quantidade * me.custo_unitario_aplicado) AS valor_total_movimentado,
    COUNT(me.id) AS quantidade_movimentos,
    
    -- Estatísticas
    AVG(me.custo_unitario_aplicado) AS custo_medio,
    MIN(me.custo_unitario_aplicado) AS custo_minimo,
    MAX(me.custo_unitario_aplicado) AS custo_maximo
    
FROM estoque_movimentoestoque me
INNER JOIN cadastros_produto p ON p.id = me.produto_id
WHERE me.estornado = FALSE
  AND p.ativo = TRUE
GROUP BY 
    DATE(me.data_operacao), 
    me.produto_id, 
    p.codigo, 
    p.descricao,
    p.unidade;

-- Índice único (obrigatório para REFRESH CONCURRENTLY)
CREATE UNIQUE INDEX idx_mv_estoque_historico_pk 
ON mv_estoque_historico (data, produto_id);

-- Índices adicionais para performance
CREATE INDEX idx_mv_estoque_historico_data 
ON mv_estoque_historico (data DESC);

CREATE INDEX idx_mv_estoque_historico_produto 
ON mv_estoque_historico (produto_id);

CREATE INDEX idx_mv_estoque_historico_valor_total 
ON mv_estoque_historico (valor_total_movimentado DESC);

-- Comentário
COMMENT ON MATERIALIZED VIEW mv_estoque_historico IS 
'Histórico consolidado de movimentações de estoque por dia e produto. Atualização diária via Celery.';

-- ===========================================================================
-- VIEW 2: SALDO DE ESTOQUE POR LOCAL (SNAPSHOT)
-- ===========================================================================
-- Saldo atual de cada produto em cada local
-- Usado em: Curva ABC, análise de valor imobilizado
-- Atualização: Horária via Celery
-- ===========================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_estoque_saldo_atual CASCADE;

CREATE MATERIALIZED VIEW mv_estoque_saldo_atual AS
SELECT 
    s.produto_id,
    p.codigo AS produto_codigo,
    p.descricao AS produto_descricao,
    p.unidade AS produto_unidade,
    p.estoque_minimo,
    p.estoque_maximo,
    
    s.local_id,
    l.codigo AS local_codigo,
    l.descricao AS local_descricao,
    
    s.saldo_quantidade,
    s.custo_medio,
    (s.saldo_quantidade * s.custo_medio) AS valor_imobilizado,
    s.data_ultima_entrada,
    s.data_ultima_saida,
    
    -- Classificação
    CASE 
        WHEN s.saldo_quantidade <= 0 THEN 'SEM_ESTOQUE'
        WHEN s.saldo_quantidade < p.estoque_minimo THEN 'ABAIXO_MINIMO'
        WHEN s.saldo_quantidade > p.estoque_maximo THEN 'ACIMA_MAXIMO'
        ELSE 'NORMAL'
    END AS classificacao_estoque,
    
    -- Dias sem movimentação
    CASE 
        WHEN s.data_ultima_saida IS NOT NULL 
        THEN EXTRACT(DAY FROM (CURRENT_DATE - s.data_ultima_saida))
        ELSE NULL
    END AS dias_sem_saida,
    
    NOW() AS data_snapshot
    
FROM estoque_saldoestoque s
INNER JOIN cadastros_produto p ON p.id = s.produto_id
INNER JOIN estoque_localestoque l ON l.id = s.local_id
WHERE p.ativo = TRUE
  AND l.ativo = TRUE;

-- Índice único
CREATE UNIQUE INDEX idx_mv_estoque_saldo_atual_pk 
ON mv_estoque_saldo_atual (produto_id, local_id);

-- Índices adicionais
CREATE INDEX idx_mv_estoque_saldo_atual_produto 
ON mv_estoque_saldo_atual (produto_id);

CREATE INDEX idx_mv_estoque_saldo_atual_local 
ON mv_estoque_saldo_atual (local_id);

CREATE INDEX idx_mv_estoque_saldo_atual_valor 
ON mv_estoque_saldo_atual (valor_imobilizado DESC);

CREATE INDEX idx_mv_estoque_saldo_atual_classificacao 
ON mv_estoque_saldo_atual (classificacao_estoque);

COMMENT ON MATERIALIZED VIEW mv_estoque_saldo_atual IS 
'Snapshot de saldo atual de estoque por produto e local. Atualização horária via Celery.';

-- ===========================================================================
-- VIEW 3: CONSUMO MÉDIO MENSAL (6 MESES)
-- ===========================================================================
-- Calcula consumo médio dos últimos 6 meses
-- Usado em: Previsão de ruptura, sugestão de compra
-- Atualização: Diária às 06:00 via Celery
-- ===========================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_estoque_consumo_medio CASCADE;

CREATE MATERIALIZED VIEW mv_estoque_consumo_medio AS
WITH meses_recentes AS (
    SELECT 
        DATE_TRUNC('month', me.data_operacao) AS mes,
        me.produto_id,
        SUM(me.quantidade) AS quantidade_mes
    FROM estoque_movimentoestoque me
    WHERE me.tipo_movimento = 'SAIDA'
      AND me.estornado = FALSE
      AND me.data_operacao >= CURRENT_DATE - INTERVAL '6 months'
    GROUP BY DATE_TRUNC('month', me.data_operacao), me.produto_id
)
SELECT 
    mr.produto_id,
    p.codigo AS produto_codigo,
    p.descricao AS produto_descricao,
    p.unidade AS produto_unidade,
    
    -- Estatísticas de consumo
    COUNT(mr.mes) AS meses_com_consumo,
    AVG(mr.quantidade_mes) AS consumo_medio_mensal,
    STDDEV(mr.quantidade_mes) AS desvio_padrao,
    MIN(mr.quantidade_mes) AS consumo_minimo,
    MAX(mr.quantidade_mes) AS consumo_maximo,
    SUM(mr.quantidade_mes) AS consumo_total_6_meses,
    
    -- Consumo diário aproximado
    AVG(mr.quantidade_mes) / 30 AS consumo_medio_diario,
    
    -- Tendência (simplificado - positivo se último mês > média)
    CASE 
        WHEN MAX(mr.mes) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') THEN
            CASE 
                WHEN (
                    SELECT quantidade_mes 
                    FROM meses_recentes mr2 
                    WHERE mr2.produto_id = mr.produto_id 
                      AND mr2.mes = MAX(mr.mes)
                ) > AVG(mr.quantidade_mes) THEN 'CRESCENTE'
                ELSE 'DECRESCENTE'
            END
        ELSE 'ESTÁVEL'
    END AS tendencia,
    
    NOW() AS data_calculo
    
FROM meses_recentes mr
INNER JOIN cadastros_produto p ON p.id = mr.produto_id
WHERE p.ativo = TRUE
GROUP BY mr.produto_id, p.codigo, p.descricao, p.unidade
HAVING COUNT(mr.mes) >= 3;  -- Mínimo 3 meses com consumo

-- Índice único
CREATE UNIQUE INDEX idx_mv_estoque_consumo_medio_pk 
ON mv_estoque_consumo_medio (produto_id);

-- Índices adicionais
CREATE INDEX idx_mv_estoque_consumo_medio_consumo 
ON mv_estoque_consumo_medio (consumo_medio_mensal DESC);

CREATE INDEX idx_mv_estoque_consumo_medio_tendencia 
ON mv_estoque_consumo_medio (tendencia);

COMMENT ON MATERIALIZED VIEW mv_estoque_consumo_medio IS 
'Consumo médio mensal dos últimos 6 meses. Usado para previsão de ruptura e sugestão de compra.';

-- ===========================================================================
-- PRIMEIRO REFRESH (POPULAR VIEWS)
-- ===========================================================================
REFRESH MATERIALIZED VIEW mv_estoque_historico;
REFRESH MATERIALIZED VIEW mv_estoque_saldo_atual;
REFRESH MATERIALIZED VIEW mv_estoque_consumo_medio;

-- ===========================================================================
-- PERMISSÕES (AJUSTAR CONFORME SEU USUÁRIO)
-- ===========================================================================
-- GRANT SELECT ON mv_estoque_historico TO seu_usuario_app;
-- GRANT SELECT ON mv_estoque_saldo_atual TO seu_usuario_app;
-- GRANT SELECT ON mv_estoque_consumo_medio TO seu_usuario_app;

-- ===========================================================================
-- VIEWS FUTURAS (QUANDO MÓDULOS ESTIVEREM PRONTOS)
-- ===========================================================================

-- ===========================================================================
-- VIEW 4: OBRAS - ANÁLISE FINANCEIRA (CRIAR QUANDO FINANCEIRO EXISTIR)
-- ===========================================================================
/*
DROP MATERIALIZED VIEW IF EXISTS mv_obras_financeiro CASCADE;

CREATE MATERIALIZED VIEW mv_obras_financeiro AS
WITH custos_obra AS (
    SELECT 
        obra_id,
        SUM(CASE WHEN origem = 'ESTOQUE' THEN valor ELSE 0 END) AS custo_material,
        SUM(CASE WHEN categoria = 'MAO_OBRA' THEN valor ELSE 0 END) AS custo_mao_obra,
        SUM(CASE WHEN categoria = 'TERCEIRO' THEN valor ELSE 0 END) AS custo_terceiro,
        SUM(valor) AS custo_total
    FROM estoque_custoobra
    WHERE ativo = TRUE
    GROUP BY obra_id
),
receitas_obra AS (
    SELECT 
        centro_custo_id AS obra_id,
        SUM(CASE WHEN situacao = 'PAGO' THEN valor_pago ELSE 0 END) AS receita_recebida,
        SUM(CASE WHEN situacao IN ('ABERTO', 'PARCIAL') THEN (valor - COALESCE(valor_pago, 0)) ELSE 0 END) AS receita_a_receber
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER' AND ativo = TRUE
    GROUP BY centro_custo_id
),
despesas_obra AS (
    SELECT 
        centro_custo_id AS obra_id,
        SUM(CASE WHEN situacao = 'PAGO' THEN valor_pago ELSE 0 END) AS despesa_paga,
        SUM(CASE WHEN situacao IN ('ABERTO', 'PARCIAL') THEN (valor - COALESCE(valor_pago, 0)) ELSE 0 END) AS despesa_a_pagar
    FROM financeiro_titulo
    WHERE tipo = 'PAGAR' AND ativo = TRUE
    GROUP BY centro_custo_id
)
SELECT 
    o.id AS obra_id,
    o.codigo AS obra_codigo,
    o.nome AS obra_nome,
    o.status,
    o.valor_contrato,
    o.valor_orcado,
    
    -- Custos
    COALESCE(c.custo_total, 0) AS custo_realizado,
    COALESCE(c.custo_material, 0) AS custo_material,
    COALESCE(c.custo_mao_obra, 0) AS custo_mao_obra,
    COALESCE(c.custo_terceiro, 0) AS custo_terceiro,
    
    -- Lucro por Competência
    o.valor_contrato - COALESCE(c.custo_total, 0) AS lucro_competencia,
    CASE 
        WHEN o.valor_contrato > 0 
        THEN ((o.valor_contrato - COALESCE(c.custo_total, 0)) / o.valor_contrato * 100)
        ELSE 0 
    END AS margem_competencia,
    
    -- Lucro por Caixa (Cash Flow)
    COALESCE(r.receita_recebida, 0) - COALESCE(d.despesa_paga, 0) AS lucro_caixa,
    CASE 
        WHEN COALESCE(r.receita_recebida, 0) > 0 
        THEN ((COALESCE(r.receita_recebida, 0) - COALESCE(d.despesa_paga, 0)) / r.receita_recebida * 100)
        ELSE 0 
    END AS margem_caixa,
    
    -- Receitas/Despesas futuras
    COALESCE(r.receita_a_receber, 0) AS receita_a_receber,
    COALESCE(d.despesa_a_pagar, 0) AS despesa_a_pagar,
    
    -- Budget
    CASE 
        WHEN o.valor_orcado > 0 
        THEN ((COALESCE(c.custo_total, 0) / o.valor_orcado) * 100)
        ELSE 0 
    END AS percentual_budget_utilizado,
    
    CASE 
        WHEN COALESCE(c.custo_total, 0) > o.valor_orcado THEN TRUE
        ELSE FALSE
    END AS estouro_budget,
    
    NOW() AS data_atualizacao
    
FROM projetos_obra o
LEFT JOIN custos_obra c ON c.obra_id = o.id
LEFT JOIN receitas_obra r ON r.obra_id = o.id
LEFT JOIN despesas_obra d ON d.obra_id = o.id
WHERE o.ativo = TRUE;

CREATE UNIQUE INDEX idx_mv_obras_financeiro_pk ON mv_obras_financeiro (obra_id);
CREATE INDEX idx_mv_obras_financeiro_status ON mv_obras_financeiro (status);
CREATE INDEX idx_mv_obras_financeiro_margem ON mv_obras_financeiro (margem_competencia DESC);

COMMENT ON MATERIALIZED VIEW mv_obras_financeiro IS 
'Análise financeira completa de obras: lucro competência, lucro caixa, budget.';
*/

-- ===========================================================================
-- VIEW 5: FLUXO DE CAIXA PROJETADO (CRIAR QUANDO FINANCEIRO EXISTIR)
-- ===========================================================================
/*
DROP MATERIALIZED VIEW IF EXISTS mv_fluxo_caixa_projetado CASCADE;

CREATE MATERIALIZED VIEW mv_fluxo_caixa_projetado AS
WITH dias_futuros AS (
    SELECT 
        CURRENT_DATE + INTERVAL '1 day' * generate_series(0, 90) AS data
),
entradas_dia AS (
    SELECT 
        vencimento AS data,
        SUM(valor - COALESCE(valor_pago, 0)) AS valor_entradas
    FROM financeiro_titulo
    WHERE tipo = 'RECEBER'
      AND situacao IN ('ABERTO', 'PARCIAL')
      AND vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
    GROUP BY vencimento
),
saidas_dia AS (
    SELECT 
        vencimento AS data,
        SUM(valor - COALESCE(valor_pago, 0)) AS valor_saidas
    FROM financeiro_titulo
    WHERE tipo = 'PAGAR'
      AND situacao IN ('ABERTO', 'PARCIAL')
      AND vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
    GROUP BY vencimento
)
SELECT 
    df.data,
    COALESCE(e.valor_entradas, 0) AS entradas,
    COALESCE(s.valor_saidas, 0) AS saidas,
    COALESCE(e.valor_entradas, 0) - COALESCE(s.valor_saidas, 0) AS saldo_dia,
    SUM(COALESCE(e.valor_entradas, 0) - COALESCE(s.valor_saidas, 0)) 
        OVER (ORDER BY df.data) AS saldo_acumulado
FROM dias_futuros df
LEFT JOIN entradas_dia e ON e.data = df.data
LEFT JOIN saidas_dia s ON s.data = df.data
ORDER BY df.data;

CREATE UNIQUE INDEX idx_mv_fluxo_caixa_projetado_pk ON mv_fluxo_caixa_projetado (data);

COMMENT ON MATERIALIZED VIEW mv_fluxo_caixa_projetado IS 
'Projeção de fluxo de caixa para os próximos 90 dias baseada em títulos abertos.';
*/

-- ===========================================================================
-- SCRIPTS DE MANUTENÇÃO
-- ===========================================================================

-- Refresh manual de todas as views
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estoque_historico;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estoque_saldo_atual;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estoque_consumo_medio;

-- Ver tamanho das views
-- SELECT 
--     schemaname,
--     matviewname,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size
-- FROM pg_matviews
-- WHERE schemaname = 'public'
-- ORDER BY pg_total_relation_size(schemaname||'.'||matviewname) DESC;

-- ===========================================================================
-- FIM DO SCRIPT
-- ===========================================================================
\echo '✅ Views materializadas criadas com sucesso!'
\echo 'Execute: SELECT COUNT(*) FROM mv_estoque_historico; para validar'
