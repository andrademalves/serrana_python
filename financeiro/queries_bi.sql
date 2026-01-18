-- ============================================================================
-- QUERIES SQL PARA BUSINESS INTELLIGENCE - ETAPA 3
-- Sistema de Budget e Controle de Lucratividade
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PERFORMANCE DE VENDEDORES
-- KPI: Assertividade (Lucro Orçado vs Lucro Real)
-- ----------------------------------------------------------------------------

-- Ranking de vendedores por assertividade
CREATE OR REPLACE VIEW vw_performance_vendedores AS
SELECT 
    p.id AS vendedor_id,
    p.nome AS vendedor_nome,
    COUNT(DISTINCT pb.id) AS total_projetos,
    
    -- Valores orçados
    SUM(pb.valor_venda) AS total_vendas,
    SUM(pb.custo_total_previsto) AS total_custo_previsto,
    SUM(pb.lucro_previsto) AS total_lucro_previsto,
    AVG(pb.margem_prevista_percentual) AS margem_prevista_media,
    
    -- Valores reais
    COALESCE(SUM(despesas.total_gasto), 0) AS total_custo_real,
    SUM(pb.valor_venda) - COALESCE(SUM(despesas.total_gasto), 0) AS total_lucro_real,
    
    -- Assertividade: (Lucro Real / Lucro Previsto) * 100
    CASE 
        WHEN SUM(pb.lucro_previsto) > 0 THEN
            ((SUM(pb.valor_venda) - COALESCE(SUM(despesas.total_gasto), 0)) / SUM(pb.lucro_previsto)) * 100
        ELSE 0
    END AS assertividade_percentual,
    
    -- Vendas com prejuízo
    SUM(CASE WHEN pb.margem_prevista_percentual < 0 THEN 1 ELSE 0 END) AS vendas_com_prejuizo,
    
    -- Desvio médio (Real - Previsto)
    AVG(COALESCE(despesas.total_gasto, 0) - pb.custo_total_previsto) AS desvio_medio_custos
    
FROM cadastros_pessoa p
INNER JOIN vendas_orcamento vo ON vo.vendedor_id = p.id
INNER JOIN projetos_projeto proj ON proj.orcamento_id = vo.id
INNER JOIN project_budgets pb ON pb.projeto_id = proj.id
LEFT JOIN (
    SELECT 
        budget_id,
        SUM(valor) AS total_gasto
    FROM project_expenses
    WHERE status IN ('APROVADO', 'PAGO')
    GROUP BY budget_id
) despesas ON despesas.budget_id = pb.id

WHERE p.vendedor = TRUE
  AND pb.status IN ('EM_EXECUCAO', 'FINALIZADO')
  AND pb.criado_em >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)

GROUP BY p.id, p.nome
HAVING total_projetos > 0
ORDER BY assertividade_percentual DESC;


-- Detalhamento por projeto (vendedor específico)
CREATE OR REPLACE VIEW vw_projetos_vendedor_detalhe AS
SELECT 
    p.nome AS vendedor_nome,
    pb.codigo AS budget_codigo,
    pb.descricao AS projeto_descricao,
    pb.valor_venda,
    pb.custo_total_previsto AS custo_previsto,
    COALESCE(despesas.total_gasto, 0) AS custo_real,
    pb.lucro_previsto,
    pb.valor_venda - COALESCE(despesas.total_gasto, 0) AS lucro_real,
    pb.margem_prevista_percentual AS margem_prevista,
    
    -- Margem real
    CASE 
        WHEN pb.valor_venda > 0 THEN
            ((pb.valor_venda - COALESCE(despesas.total_gasto, 0)) / pb.valor_venda) * 100
        ELSE 0
    END AS margem_real,
    
    -- Assertividade do projeto
    CASE 
        WHEN pb.lucro_previsto > 0 THEN
            ((pb.valor_venda - COALESCE(despesas.total_gasto, 0)) / pb.lucro_previsto) * 100
        ELSE 0
    END AS assertividade_projeto,
    
    CASE 
        WHEN pb.valor_venda - COALESCE(despesas.total_gasto, 0) < 0 THEN 'PREJUÍZO'
        WHEN pb.margem_prevista_percentual < 0 THEN 'VENDA ERRADA'
        ELSE 'OK'
    END AS status_lucratividade,
    
    pb.semaforo,
    pb.percentual_uso_budget,
    pb.criado_em AS data_budget

FROM cadastros_pessoa p
INNER JOIN vendas_orcamento vo ON vo.vendedor_id = p.id
INNER JOIN projetos_projeto proj ON proj.orcamento_id = vo.id
INNER JOIN project_budgets pb ON pb.projeto_id = proj.id
LEFT JOIN (
    SELECT budget_id, SUM(valor) AS total_gasto
    FROM project_expenses
    WHERE status IN ('APROVADO', 'PAGO')
    GROUP BY budget_id
) despesas ON despesas.budget_id = pb.id

WHERE p.vendedor = TRUE
ORDER BY pb.criado_em DESC;


-- ----------------------------------------------------------------------------
-- 2. PERFORMANCE DE INSTALADORES
-- KPI: Índice de Retrabalho e Desperdício
-- ----------------------------------------------------------------------------

-- Ranking de instaladores
CREATE OR REPLACE VIEW vw_performance_instaladores AS
SELECT 
    p.id AS instalador_id,
    p.nome AS instalador_nome,
    COUNT(DISTINCT pe.budget_id) AS total_projetos_trabalhados,
    
    -- Horas trabalhadas
    SUM(CASE WHEN pe.tipo_despesa = 'MAO_OBRA' THEN pe.horas_trabalhadas ELSE 0 END) AS total_horas_trabalhadas,
    
    -- Custos
    SUM(CASE WHEN pe.tipo_despesa = 'MAO_OBRA' THEN pe.valor ELSE 0 END) AS total_custo_mao_obra,
    
    -- Retrabalho
    COUNT(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN 1 END) AS total_retrabalhos,
    SUM(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.valor ELSE 0 END) AS custo_retrabalho,
    
    -- Desperdício
    COUNT(CASE WHEN pe.tipo_despesa = 'DESPERDICIO' THEN 1 END) AS total_desperdicios,
    SUM(CASE WHEN pe.tipo_despesa = 'DESPERDICIO' THEN pe.valor ELSE 0 END) AS custo_desperdicio,
    
    -- Índice de retrabalho: % de projetos com retrabalho
    (COUNT(DISTINCT CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.budget_id END) / 
     COUNT(DISTINCT pe.budget_id)) * 100 AS indice_retrabalho_percentual,
    
    -- Visitas extras (contar quantas vezes foi ao mesmo projeto)
    AVG(visitas.total_visitas) AS media_visitas_por_projeto,
    
    -- Custo extra (retrabalho + desperdício)
    SUM(CASE WHEN pe.tipo_despesa IN ('RETRABALHO', 'DESPERDICIO') THEN pe.valor ELSE 0 END) AS custo_extra_total,
    
    -- Classificação
    CASE 
        WHEN (COUNT(DISTINCT CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.budget_id END) / 
              COUNT(DISTINCT pe.budget_id)) * 100 > 30 THEN 'CRÍTICO'
        WHEN (COUNT(DISTINCT CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.budget_id END) / 
              COUNT(DISTINCT pe.budget_id)) * 100 > 15 THEN 'ATENÇÃO'
        WHEN (COUNT(DISTINCT CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.budget_id END) / 
              COUNT(DISTINCT pe.budget_id)) * 100 > 5 THEN 'ACEITÁVEL'
        ELSE 'EXCELENTE'
    END AS classificacao

FROM cadastros_pessoa p
INNER JOIN project_expenses pe ON pe.funcionario_id = p.id
LEFT JOIN (
    SELECT 
        funcionario_id,
        budget_id,
        COUNT(*) AS total_visitas
    FROM project_expenses
    WHERE tipo_despesa = 'MAO_OBRA'
    GROUP BY funcionario_id, budget_id
) visitas ON visitas.funcionario_id = p.id AND visitas.budget_id = pe.budget_id

WHERE p.funcionario = TRUE
  AND pe.status IN ('APROVADO', 'PAGO')
  AND pe.data_despesa >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)

GROUP BY p.id, p.nome
HAVING total_projetos_trabalhados > 0
ORDER BY indice_retrabalho_percentual ASC, custo_extra_total ASC;


-- Detalhamento de retrabalhos por instalador e projeto
CREATE OR REPLACE VIEW vw_retrabalhos_instalador_detalhe AS
SELECT 
    p.nome AS instalador_nome,
    pb.codigo AS budget_codigo,
    pb.descricao AS projeto_descricao,
    
    -- Contagem de visitas
    COUNT(CASE WHEN pe.tipo_despesa = 'MAO_OBRA' THEN 1 END) AS total_visitas,
    COUNT(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN 1 END) AS total_retrabalhos,
    
    -- Horas
    SUM(CASE WHEN pe.tipo_despesa = 'MAO_OBRA' THEN pe.horas_trabalhadas ELSE 0 END) AS horas_normais,
    SUM(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.horas_trabalhadas ELSE 0 END) AS horas_retrabalho,
    
    -- Custos
    SUM(CASE WHEN pe.tipo_despesa = 'MAO_OBRA' THEN pe.valor ELSE 0 END) AS custo_normal,
    SUM(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN pe.valor ELSE 0 END) AS custo_retrabalho,
    SUM(CASE WHEN pe.tipo_despesa = 'DESPERDICIO' THEN pe.valor ELSE 0 END) AS custo_desperdicio,
    
    -- Classificação do projeto
    CASE 
        WHEN COUNT(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN 1 END) > 2 THEN 'CRÍTICO'
        WHEN COUNT(CASE WHEN pe.tipo_despesa = 'RETRABALHO' THEN 1 END) > 0 THEN 'ATENÇÃO'
        ELSE 'OK'
    END AS status_projeto,
    
    pb.semaforo,
    pb.percentual_uso_budget

FROM cadastros_pessoa p
INNER JOIN project_expenses pe ON pe.funcionario_id = p.id
INNER JOIN project_budgets pb ON pb.id = pe.budget_id

WHERE p.funcionario = TRUE
  AND pe.status IN ('APROVADO', 'PAGO')
  AND pe.data_despesa >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)

GROUP BY p.nome, pb.codigo, pb.descricao, pb.semaforo, pb.percentual_uso_budget
HAVING total_visitas > 0
ORDER BY total_retrabalhos DESC, custo_retrabalho DESC;


-- ----------------------------------------------------------------------------
-- 3. ANÁLISE DE LUCRATIVIDADE GERAL
-- Visão consolidada da empresa
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_lucratividade_consolidada AS
SELECT 
    DATE_FORMAT(pb.criado_em, '%Y-%m') AS periodo_mes,
    COUNT(pb.id) AS total_budgets,
    
    -- Valores de venda
    SUM(pb.valor_venda) AS faturamento_total,
    AVG(pb.valor_venda) AS ticket_medio,
    
    -- Custos previstos
    SUM(pb.custo_total_previsto) AS custo_previsto_total,
    SUM(pb.lucro_previsto) AS lucro_previsto_total,
    AVG(pb.margem_prevista_percentual) AS margem_prevista_media,
    
    -- Custos reais
    COALESCE(SUM(despesas.total_gasto), 0) AS custo_real_total,
    SUM(pb.valor_venda) - COALESCE(SUM(despesas.total_gasto), 0) AS lucro_real_total,
    
    -- Margem real
    CASE 
        WHEN SUM(pb.valor_venda) > 0 THEN
            ((SUM(pb.valor_venda) - COALESCE(SUM(despesas.total_gasto), 0)) / SUM(pb.valor_venda)) * 100
        ELSE 0
    END AS margem_real_media,
    
    -- Desvios
    COALESCE(SUM(despesas.total_gasto), 0) - SUM(pb.custo_total_previsto) AS desvio_custo_total,
    (SUM(pb.valor_venda) - COALESCE(SUM(despesas.total_gasto), 0)) - SUM(pb.lucro_previsto) AS desvio_lucro_total,
    
    -- Percentuais de desvio
    CASE 
        WHEN SUM(pb.custo_total_previsto) > 0 THEN
            ((COALESCE(SUM(despesas.total_gasto), 0) - SUM(pb.custo_total_previsto)) / SUM(pb.custo_total_previsto)) * 100
        ELSE 0
    END AS desvio_custo_percentual,
    
    -- Contadores de status
    SUM(CASE WHEN pb.semaforo = 'VERDE' THEN 1 ELSE 0 END) AS budgets_verdes,
    SUM(CASE WHEN pb.semaforo = 'AMARELO' THEN 1 ELSE 0 END) AS budgets_amarelos,
    SUM(CASE WHEN pb.semaforo = 'VERMELHO' THEN 1 ELSE 0 END) AS budgets_vermelhos,
    SUM(CASE WHEN pb.bloqueado = TRUE THEN 1 ELSE 0 END) AS budgets_bloqueados,
    SUM(CASE WHEN pb.margem_prevista_percentual < 0 THEN 1 ELSE 0 END) AS vendas_prejuizo

FROM project_budgets pb
LEFT JOIN (
    SELECT budget_id, SUM(valor) AS total_gasto
    FROM project_expenses
    WHERE status IN ('APROVADO', 'PAGO')
    GROUP BY budget_id
) despesas ON despesas.budget_id = pb.id

WHERE pb.status IN ('EM_EXECUCAO', 'FINALIZADO')
  AND pb.criado_em >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)

GROUP BY DATE_FORMAT(pb.criado_em, '%Y-%m')
ORDER BY periodo_mes DESC;


-- ----------------------------------------------------------------------------
-- 4. ANÁLISE DE DESPESAS POR TIPO
-- Onde está indo o dinheiro?
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_analise_despesas_tipo AS
SELECT 
    pe.tipo_despesa,
    COUNT(*) AS quantidade_lancamentos,
    SUM(pe.valor) AS valor_total,
    AVG(pe.valor) AS valor_medio,
    MIN(pe.valor) AS valor_minimo,
    MAX(pe.valor) AS valor_maximo,
    
    -- Percentual sobre total
    (SUM(pe.valor) / (SELECT SUM(valor) FROM project_expenses WHERE status IN ('APROVADO', 'PAGO'))) * 100 AS percentual_total,
    
    -- Por status
    SUM(CASE WHEN pe.status = 'PENDENTE' THEN pe.valor ELSE 0 END) AS valor_pendente,
    SUM(CASE WHEN pe.status = 'APROVADO' THEN pe.valor ELSE 0 END) AS valor_aprovado,
    SUM(CASE WHEN pe.status = 'REJEITADO' THEN pe.valor ELSE 0 END) AS valor_rejeitado,
    SUM(CASE WHEN pe.status = 'PAGO' THEN pe.valor ELSE 0 END) AS valor_pago

FROM project_expenses pe
WHERE pe.data_despesa >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)
GROUP BY pe.tipo_despesa
ORDER BY valor_total DESC;


-- ----------------------------------------------------------------------------
-- 5. BUDGETS EM SITUAÇÃO CRÍTICA
-- Monitoramento em tempo real
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_budgets_situacao_critica AS
SELECT 
    pb.codigo,
    pb.descricao,
    e.nome_fantasia AS empresa,
    pb.status,
    pb.semaforo,
    pb.percentual_uso_budget,
    pb.bloqueado,
    
    pb.custo_total_previsto AS custo_previsto,
    COALESCE(despesas.total_gasto, 0) AS custo_real,
    pb.custo_total_previsto - COALESCE(despesas.total_gasto, 0) AS margem_restante,
    
    pb.valor_venda,
    pb.margem_prevista_percentual AS margem_prevista,
    
    -- Margem real atual
    CASE 
        WHEN pb.valor_venda > 0 THEN
            ((pb.valor_venda - COALESCE(despesas.total_gasto, 0)) / pb.valor_venda) * 100
        ELSE 0
    END AS margem_real_atual,
    
    -- Justificativas pendentes
    COALESCE(just.total_pendentes, 0) AS justificativas_pendentes,
    
    -- Datas
    pb.data_inicio_real,
    pb.data_termino_prevista,
    CASE 
        WHEN pb.data_termino_prevista < CURRENT_DATE THEN 'ATRASADO'
        WHEN DATEDIFF(pb.data_termino_prevista, CURRENT_DATE) <= 7 THEN 'VENCE EM 7 DIAS'
        ELSE 'NO PRAZO'
    END AS status_prazo,
    
    pb.criado_em,
    u.username AS criado_por

FROM project_budgets pb
INNER JOIN empresas e ON e.id = pb.empresa_id
LEFT JOIN usuarios_user u ON u.id = pb.criado_por_id
LEFT JOIN (
    SELECT budget_id, SUM(valor) AS total_gasto
    FROM project_expenses
    WHERE status IN ('APROVADO', 'PAGO')
    GROUP BY budget_id
) despesas ON despesas.budget_id = pb.id
LEFT JOIN (
    SELECT budget_id, COUNT(*) AS total_pendentes
    FROM justificativas_budget
    WHERE status = 'PENDENTE'
    GROUP BY budget_id
) just ON just.budget_id = pb.id

WHERE pb.status = 'EM_EXECUCAO'
  AND (pb.semaforo IN ('AMARELO', 'VERMELHO') OR pb.bloqueado = TRUE)

ORDER BY 
    CASE pb.semaforo 
        WHEN 'VERMELHO' THEN 1
        WHEN 'AMARELO' THEN 2
        ELSE 3
    END,
    pb.percentual_uso_budget DESC;


-- ----------------------------------------------------------------------------
-- 6. ÍNDICES PARA OTIMIZAÇÃO
-- ----------------------------------------------------------------------------

-- Índices para melhorar performance das queries
CREATE INDEX idx_project_expenses_budget_status ON project_expenses(budget_id, status);
CREATE INDEX idx_project_expenses_funcionario_tipo ON project_expenses(funcionario_id, tipo_despesa);
CREATE INDEX idx_project_expenses_data ON project_expenses(data_despesa);
CREATE INDEX idx_project_budgets_semaforo_status ON project_budgets(semaforo, status);
CREATE INDEX idx_project_budgets_criado_em ON project_budgets(criado_em);
CREATE INDEX idx_justificativas_budget_status ON justificativas_budget(budget_id, status);
