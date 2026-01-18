# Novo Modelo de Estoque - Sistema Serrana

## 📋 Visão Geral

Sistema profissional de controle de estoque para fábrica de esquadrias com:
- Controle de múltiplos locais de armazenamento
- Rastreabilidade completa de movimentações
- Custeio por Custo Médio Móvel (WAC - Weighted Average Cost)
- Integração com projetos para controle de custos
- Estrutura preparada para BOM e Ordem de Produção

---

## 🗄️ Modelo de Dados

### 1. Cadastros Auxiliares

#### **GrupoItem**
Categorização de itens (ex: Perfis de Alumínio, Vidros, Acessórios)

```sql
CREATE TABLE grupos_item (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descricao VARCHAR(100) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    INDEX idx_codigo (codigo),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **LocalEstoque**
Locais físicos de armazenamento (Depósitos/Almoxarifados)

```sql
CREATE TABLE locais_estoque (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descricao VARCHAR(100) NOT NULL,
    endereco VARCHAR(255),
    responsavel_id BIGINT,
    permite_saldo_negativo BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    INDEX idx_codigo (codigo),
    FOREIGN KEY (responsavel_id) REFERENCES auth_user(id),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **DestinoEstoque**
Destinos/Finalidades das saídas

```sql
CREATE TABLE destinos_estoque (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    descricao VARCHAR(100) NOT NULL,
    tipo VARCHAR(20) NOT NULL, -- PRODUCAO, PROJETO, LOJA, MANUTENCAO, etc
    controla_custo BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    INDEX idx_codigo (codigo),
    INDEX idx_tipo (tipo),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. Cadastro de Itens

#### **Item**
Cadastro completo de itens de estoque

```sql
CREATE TABLE itens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    tipo_item VARCHAR(15) NOT NULL, -- MP, PA, SEMI, CONSUMIVEL
    grupo_id BIGINT,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    cor VARCHAR(50),
    unidade_medida VARCHAR(10) NOT NULL,
    estoque_minimo DECIMAL(12,3) DEFAULT 0.000,
    estoque_maximo DECIMAL(12,3),
    ncm VARCHAR(20),
    codigo_barras VARCHAR(50),
    url_foto VARCHAR(500),
    ativo BOOLEAN DEFAULT TRUE,
    observacoes TEXT,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    atualizado_em DATETIME NOT NULL,
    atualizado_por_id BIGINT,
    INDEX idx_codigo (codigo),
    INDEX idx_descricao (descricao),
    INDEX idx_tipo_item (tipo_item),
    INDEX idx_ativo (ativo),
    FOREIGN KEY (grupo_id) REFERENCES grupos_item(id),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id),
    FOREIGN KEY (atualizado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3. Saldos de Estoque (Performance)

#### **SaldoEstoque**
Tabela de consulta rápida de saldos por item/local

```sql
CREATE TABLE saldos_estoque (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    item_id BIGINT NOT NULL,
    local_id BIGINT NOT NULL,
    quantidade DECIMAL(12,3) DEFAULT 0.000,
    custo_medio DECIMAL(12,4) DEFAULT 0.0000,
    atualizado_em DATETIME NOT NULL,
    UNIQUE KEY uk_item_local (item_id, local_id),
    INDEX idx_item_local (item_id, local_id),
    INDEX idx_item (item_id),
    INDEX idx_local (local_id),
    INDEX idx_quantidade (quantidade),
    FOREIGN KEY (item_id) REFERENCES itens(id) ON DELETE CASCADE,
    FOREIGN KEY (local_id) REFERENCES locais_estoque(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 4. Movimentações de Estoque (Histórico)

#### **MovimentoEstoque**
Registro de todas as movimentações

```sql
CREATE TABLE movimentos_estoque (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tipo_movimento VARCHAR(20) NOT NULL, -- ENTRADA, SAIDA, TRANSFERENCIA, AJUSTE, ESTORNO
    documento VARCHAR(50),
    documento_tipo VARCHAR(10),
    data_movimento DATETIME NOT NULL,
    item_id BIGINT NOT NULL,
    local_origem_id BIGINT,
    local_destino_id BIGINT,
    destino_id BIGINT,
    projeto_id BIGINT,
    fornecedor_id BIGINT,
    quantidade DECIMAL(12,3) NOT NULL,
    custo_unitario DECIMAL(12,4) DEFAULT 0.0000,
    custo_total DECIMAL(12,2) DEFAULT 0.00,
    solicitante_id BIGINT,
    movimento_estornado_id BIGINT,
    observacao TEXT,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    INDEX idx_tipo_movimento (tipo_movimento),
    INDEX idx_data_movimento (data_movimento),
    INDEX idx_data_movimento_desc (data_movimento DESC),
    INDEX idx_documento (documento),
    INDEX idx_item (item_id),
    INDEX idx_local_origem (local_origem_id),
    INDEX idx_local_destino (local_destino_id),
    INDEX idx_projeto (projeto_id),
    FOREIGN KEY (item_id) REFERENCES itens(id) ON DELETE PROTECT,
    FOREIGN KEY (local_origem_id) REFERENCES locais_estoque(id) ON DELETE PROTECT,
    FOREIGN KEY (local_destino_id) REFERENCES locais_estoque(id) ON DELETE PROTECT,
    FOREIGN KEY (destino_id) REFERENCES destinos_estoque(id) ON DELETE PROTECT,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE PROTECT,
    FOREIGN KEY (fornecedor_id) REFERENCES pessoas(id) ON DELETE PROTECT,
    FOREIGN KEY (solicitante_id) REFERENCES auth_user(id),
    FOREIGN KEY (movimento_estornado_id) REFERENCES movimentos_estoque(id),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 5. BOM e Produção (Preparado para Futuro)

#### **BOM (Bill of Materials)**
```sql
CREATE TABLE bom (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    produto_id BIGINT NOT NULL,
    versao VARCHAR(20) DEFAULT '1.0',
    descricao VARCHAR(255) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_vigencia DATE NOT NULL,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    UNIQUE KEY uk_produto_versao (produto_id, versao),
    FOREIGN KEY (produto_id) REFERENCES itens(id) ON DELETE CASCADE,
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **BOMItem**
```sql
CREATE TABLE bom_itens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bom_id BIGINT NOT NULL,
    item_componente_id BIGINT NOT NULL,
    quantidade DECIMAL(12,3) NOT NULL,
    sequencia INT DEFAULT 0,
    percentual_perda DECIMAL(5,2) DEFAULT 0.00,
    UNIQUE KEY uk_bom_item (bom_id, item_componente_id),
    FOREIGN KEY (bom_id) REFERENCES bom(id) ON DELETE CASCADE,
    FOREIGN KEY (item_componente_id) REFERENCES itens(id) ON DELETE PROTECT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### **OrdemProducao**
```sql
CREATE TABLE ordens_producao (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    numero_op VARCHAR(50) UNIQUE NOT NULL,
    produto_id BIGINT NOT NULL,
    bom_id BIGINT NOT NULL,
    quantidade_planejada DECIMAL(12,3) NOT NULL,
    quantidade_produzida DECIMAL(12,3) DEFAULT 0.000,
    local_producao_id BIGINT NOT NULL,
    local_destino_id BIGINT NOT NULL,
    data_planejada DATE NOT NULL,
    data_inicio DATETIME,
    data_fim DATETIME,
    status VARCHAR(20) DEFAULT 'PLANEJADA',
    projeto_id BIGINT,
    observacoes TEXT,
    criado_em DATETIME NOT NULL,
    criado_por_id BIGINT,
    INDEX idx_numero_op (numero_op),
    INDEX idx_status (status),
    INDEX idx_data_planejada (data_planejada),
    FOREIGN KEY (produto_id) REFERENCES itens(id) ON DELETE PROTECT,
    FOREIGN KEY (bom_id) REFERENCES bom(id) ON DELETE PROTECT,
    FOREIGN KEY (local_producao_id) REFERENCES locais_estoque(id) ON DELETE PROTECT,
    FOREIGN KEY (local_destino_id) REFERENCES locais_estoque(id) ON DELETE PROTECT,
    FOREIGN KEY (projeto_id) REFERENCES projetos(id),
    FOREIGN KEY (criado_por_id) REFERENCES auth_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 📐 Regras de Negócio

### 1. Movimentações de Estoque

#### **ENTRADA**
- Deve ter `local_destino`
- Não deve ter `local_origem`
- Atualiza saldo no local destino
- Recalcula custo médio (WAC) usando fórmula:
  ```
  Novo Custo Médio = (Valor Estoque Anterior + Valor Entrada) / Quantidade Total
  ```

#### **SAÍDA**
- Deve ter `local_origem`
- Deve ter `destino` (finalidade)
- Não deve ter `local_destino`
- Usa custo médio vigente do local
- Verifica saldo disponível (exceto se local permite negativo)
- Se destino controla custo e há projeto, registra custo no projeto

#### **TRANSFERÊNCIA**
- Deve ter `local_origem` e `local_destino`
- Locais não podem ser iguais
- Sai do origem com custo médio origem
- Entra no destino recalculando custo médio

#### **AJUSTE/INVENTÁRIO**
- Para correções de estoque
- Quantidade positiva = aumento
- Quantidade negativa = redução
- Pode atualizar custo médio se informado

#### **ESTORNO**
- Referencia movimento original
- Cria movimento inverso
- Reverte saldo (recalculo de custo simplificado)

### 2. Custeio - WAC (Weighted Average Cost)

**Fórmula na Entrada:**
```python
quantidade_nova = quantidade_anterior + quantidade_entrada
valor_anterior = quantidade_anterior * custo_medio_anterior
valor_entrada = quantidade_entrada * custo_unitario_entrada
custo_medio_novo = (valor_anterior + valor_entrada) / quantidade_nova
```

**Na Saída:**
- Usa o custo médio vigente do saldo no momento da saída
- Não recalcula custo médio (apenas reduz quantidade)

### 3. Controle de Projetos

Quando uma saída tem:
- `destino.controla_custo = True`
- `projeto_id` preenchido

O sistema pode integrar com módulo de projetos para:
- Acumular custo de materiais por projeto
- Gerar relatórios de consumo
- Análise de rentabilidade

---

## 📊 Views e Queries Importantes

### View: Posição Atual de Estoque
```sql
CREATE OR REPLACE VIEW v_posicao_estoque AS
SELECT 
    i.codigo AS codigo_item,
    i.descricao AS descricao_item,
    i.tipo_item,
    i.unidade_medida,
    l.codigo AS codigo_local,
    l.descricao AS descricao_local,
    s.quantidade,
    s.custo_medio,
    (s.quantidade * s.custo_medio) AS valor_total,
    i.estoque_minimo,
    CASE 
        WHEN s.quantidade <= i.estoque_minimo THEN 'ABAIXO_MINIMO'
        WHEN i.estoque_maximo IS NOT NULL AND s.quantidade >= i.estoque_maximo THEN 'ACIMA_MAXIMO'
        ELSE 'NORMAL'
    END AS status_estoque
FROM saldos_estoque s
INNER JOIN itens i ON s.item_id = i.id
INNER JOIN locais_estoque l ON s.local_id = l.id
WHERE i.ativo = TRUE AND l.ativo = TRUE;
```

### Query: Itens Abaixo do Mínimo
```sql
SELECT 
    i.codigo,
    i.descricao,
    l.descricao AS local,
    SUM(s.quantidade) AS saldo_atual,
    i.estoque_minimo,
    (i.estoque_minimo - SUM(s.quantidade)) AS quantidade_repor
FROM itens i
INNER JOIN saldos_estoque s ON i.id = s.item_id
INNER JOIN locais_estoque l ON s.local_id = l.id
WHERE i.ativo = TRUE
GROUP BY i.id, l.id
HAVING SUM(s.quantidade) <= i.estoque_minimo
ORDER BY (i.estoque_minimo - SUM(s.quantidade)) DESC;
```

### Query: Extrato de Movimentações
```sql
SELECT 
    m.data_movimento,
    m.tipo_movimento,
    m.documento,
    i.codigo AS item,
    i.descricao,
    lo.descricao AS local_origem,
    ld.descricao AS local_destino,
    d.descricao AS destino,
    p.codigo AS projeto,
    m.quantidade,
    m.custo_unitario,
    m.custo_total,
    u.username AS usuario
FROM movimentos_estoque m
INNER JOIN itens i ON m.item_id = i.id
LEFT JOIN locais_estoque lo ON m.local_origem_id = lo.id
LEFT JOIN locais_estoque ld ON m.local_destino_id = ld.id
LEFT JOIN destinos_estoque d ON m.destino_id = d.id
LEFT JOIN projetos p ON m.projeto_id = p.id
LEFT JOIN auth_user u ON m.criado_por_id = u.id
WHERE m.data_movimento BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY m.data_movimento DESC, m.criado_em DESC;
```

### Query: Consumo por Projeto
```sql
SELECT 
    p.codigo AS projeto,
    p.nome AS nome_projeto,
    i.codigo AS item,
    i.descricao,
    SUM(m.quantidade) AS quantidade_consumida,
    AVG(m.custo_unitario) AS custo_medio,
    SUM(m.custo_total) AS custo_total
FROM movimentos_estoque m
INNER JOIN projetos p ON m.projeto_id = p.id
INNER JOIN itens i ON m.item_id = i.id
INNER JOIN destinos_estoque d ON m.destino_id = d.id
WHERE m.tipo_movimento = 'SAIDA'
  AND d.controla_custo = TRUE
  AND p.id = ?
GROUP BY p.id, i.id
ORDER BY custo_total DESC;
```

### Query: Valorização do Estoque
```sql
SELECT 
    l.codigo AS local,
    l.descricao AS descricao_local,
    i.tipo_item,
    COUNT(DISTINCT i.id) AS qtd_itens,
    SUM(s.quantidade) AS quantidade_total,
    SUM(s.quantidade * s.custo_medio) AS valor_total
FROM saldos_estoque s
INNER JOIN itens i ON s.item_id = i.id
INNER JOIN locais_estoque l ON s.local_id = l.id
WHERE i.ativo = TRUE AND l.ativo = TRUE
GROUP BY l.id, i.tipo_item
WITH ROLLUP;
```

---

## 🔄 Migração de Dados

### Estratégia de Migração

#### 1. Preparação
```sql
-- Criar local padrão
INSERT INTO locais_estoque (codigo, descricao, permite_saldo_negativo, ativo, criado_em)
VALUES ('ALMOX01', 'Almoxarifado Geral', FALSE, TRUE, NOW());

-- Criar destinos padrão
INSERT INTO destinos_estoque (codigo, descricao, tipo, controla_custo, ativo, criado_em)
VALUES 
    ('PROJ', 'Projeto/Obra', 'PROJETO', TRUE, TRUE, NOW()),
    ('LOJA', 'Loja Pronta Entrega', 'LOJA', TRUE, TRUE, NOW()),
    ('PROD', 'Produção', 'PRODUCAO', TRUE, TRUE, NOW()),
    ('PERDA', 'Perda/Sucata', 'PERDA', FALSE, TRUE, NOW());
```

#### 2. Migrar Produtos -> Itens
```sql
-- Gerar código único se não existir
INSERT INTO itens (
    codigo,
    descricao,
    tipo_item,
    unidade_medida,
    ativo,
    criado_em,
    criado_por_id,
    atualizado_em
)
SELECT 
    CONCAT('ITEM', LPAD(id_produto, 6, '0')) AS codigo,
    descricao_produto AS descricao,
    'MP' AS tipo_item, -- Ajustar conforme necessário
    'UN' AS unidade_medida, -- Ajustar conforme necessário
    TRUE AS ativo,
    NOW() AS criado_em,
    NULL AS criado_por_id,
    NOW() AS atualizado_em
FROM produtos
WHERE descricao_produto IS NOT NULL;
```

#### 3. Migrar Estoque -> Movimentos
```sql
-- Entradas (QUANTIDADE_ENTRADA > 0)
INSERT INTO movimentos_estoque (
    tipo_movimento,
    documento,
    documento_tipo,
    data_movimento,
    item_id,
    local_destino_id,
    quantidade,
    custo_unitario,
    custo_total,
    fornecedor_id,
    observacao,
    criado_em,
    criado_por_id
)
SELECT 
    'ENTRADA' AS tipo_movimento,
    DOCUMENTO AS documento,
    DOCUMENTO_TIPO AS documento_tipo,
    COALESCE(DATA_ENTRADA, DATA_OPERACAO, NOW()) AS data_movimento,
    (SELECT id FROM itens WHERE codigo = CONCAT('ITEM', LPAD(e.IDMATERIAL, 6, '0'))) AS item_id,
    (SELECT id FROM locais_estoque WHERE codigo = 'ALMOX01') AS local_destino_id,
    QUANTIDADE_ENTRADA AS quantidade,
    CASE WHEN QUANTIDADE_ENTRADA > 0 THEN CUSTO_ENTRADA / QUANTIDADE_ENTRADA ELSE 0 END AS custo_unitario,
    CUSTO_ENTRADA AS custo_total,
    IDFORNECEDOR AS fornecedor_id,
    CONCAT('Migrado: ', COALESCE(DESCRICAO, '')) AS observacao,
    COALESCE(DATA_ENTRADA, DATA_OPERACAO, NOW()) AS criado_em,
    IDUSUARIO AS criado_por_id
FROM estoque e
WHERE QUANTIDADE_ENTRADA > 0;

-- Saídas (QUANTIDADE_SAIDA > 0)
INSERT INTO movimentos_estoque (
    tipo_movimento,
    documento,
    documento_tipo,
    data_movimento,
    item_id,
    local_origem_id,
    destino_id,
    projeto_id,
    quantidade,
    custo_unitario,
    custo_total,
    solicitante_id,
    observacao,
    criado_em,
    criado_por_id
)
SELECT 
    'SAIDA' AS tipo_movimento,
    DOCUMENTO AS documento,
    DOCUMENTO_TIPO AS documento_tipo,
    COALESCE(DATA_SAIDA, DATA_OPERACAO, NOW()) AS data_movimento,
    (SELECT id FROM itens WHERE codigo = CONCAT('ITEM', LPAD(e.IDMATERIAL, 6, '0'))) AS item_id,
    (SELECT id FROM locais_estoque WHERE codigo = 'ALMOX01') AS local_origem_id,
    (SELECT id FROM destinos_estoque WHERE codigo = CASE WHEN e.IDPROJETO IS NOT NULL THEN 'PROJ' ELSE 'LOJA' END) AS destino_id,
    IDPROJETO AS projeto_id,
    QUANTIDADE_SAIDA AS quantidade,
    CASE WHEN QUANTIDADE_SAIDA > 0 THEN CUSTO_TOTAL / QUANTIDADE_SAIDA ELSE 0 END AS custo_unitario,
    CUSTO_TOTAL AS custo_total,
    IDSOLICITANTE AS solicitante_id,
    CONCAT('Migrado: ', COALESCE(DESCRICAO, '')) AS observacao,
    COALESCE(DATA_SAIDA, DATA_OPERACAO, NOW()) AS criado_em,
    IDUSUARIO AS criado_por_id
FROM estoque e
WHERE QUANTIDADE_SAIDA > 0;
```

#### 4. Recalcular Saldos
```python
# Executar comando Django para recalcular todos os saldos
# python manage.py recalcular_saldos_estoque
```

---

## 🎯 Fluxos de Tela (MVP)

### Cadastros
1. **Itens**: CRUD completo com busca, filtros por tipo, grupo
2. **Locais de Estoque**: CRUD com responsável
3. **Destinos**: CRUD com tipos pré-definidos
4. **Grupos de Itens**: CRUD básico

### Operações
1. **Entrada de Estoque** (NF):
   - Fornecedor, Documento, Data
   - Itens com quantidade e custo
   - Local destino
   
2. **Saída de Estoque** (Requisição):
   - Local origem
   - Destino (finalidade)
   - Projeto (se aplicável)
   - Itens com quantidade
   - Solicitante
   
3. **Transferência entre Locais**:
   - Local origem e destino
   - Itens com quantidade
   
4. **Ajuste/Inventário**:
   - Local
   - Itens com diferença (+ ou -)
   - Motivo do ajuste

### Relatórios
1. **Posição de Estoque**: Saldo atual por item/local
2. **Itens Abaixo do Mínimo**: Alertas de reposição
3. **Extrato de Movimentações**: Filtros por período, item, local, tipo
4. **Consumo por Projeto**: Materiais e custos por projeto
5. **Valorização do Estoque**: Valor total por local e tipo de item

---

## ✅ Vantagens do Novo Modelo

1. **Separação Clara**:
   - Cadastros vs Movimentos vs Saldos
   - Local (onde está) vs Destino (para onde vai)

2. **Rastreabilidade Total**:
   - Histórico completo de movimentações
   - Auditoria em todas as tabelas

3. **Performance**:
   - Tabela `saldos_estoque` otimizada para consultas
   - Índices estratégicos

4. **Custeio Preciso**:
   - WAC calculado automaticamente
   - Custo por projeto rastreável

5. **Escalabilidade**:
   - Preparado para BOM e OP
   - Suporte a múltiplos locais e destinos
   - Flexível para novos tipos de movimento

6. **Consistência**:
   - Validações no modelo
   - Transações atômicas
   - Prevenção de saldo negativo (configurável)

---

## 📌 Próximos Passos

1. Criar migrations Django
2. Implementar views e forms
3. Criar templates
4. Implementar comando de migração de dados
5. Testes de validação
6. Documentação de usuário
7. Treinamento da equipe
