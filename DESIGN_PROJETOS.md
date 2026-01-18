# ESTRUTURA DO MÓDULO ORÇAMENTOS E PROJETOS

## Visão Geral

O módulo gerencia:
1. **Vendas Diretas**: Venda simples de produtos
2. **Orçamentos**: Propostas que podem virar projetos
3. **Projetos**: Obras/serviços com controle completo de custos e alocações
4. **Conta Corrente por Projeto**: Registro de todas as movimentações financeiras

## Modelos de Dados

### 1. Orcamento
- Cliente
- Vendedor
- Data do orçamento
- Validade
- Itens do orçamento (produtos/serviços)
- Valor total
- Status (Pendente, Aprovado, Rejeitado, Convertido em Projeto)
- Desconto
- Observações

### 2. OrcamentoItem
- Orçamento (FK)
- Item/Produto (FK) ou Descrição livre
- Quantidade
- Valor unitário
- Valor total
- Desconto
- Tipo (Produto, Serviço, Mão de Obra)

### 3. Projeto
Campos do projeto original + novos:
- Código do projeto (único, auto-gerado)
- Cliente (FK para Pessoa)
- Vendedor (FK para User)
- Orçamento original (FK, nullable)
- Descrição do projeto
- **Datas**:
  - Data contratação
  - Data início prevista
  - Data início real
  - Data término prevista
  - Data término real
- **Endereço da Obra**:
  - Logradouro, complemento, bairro, cidade, UF, CEP
- **Valores**:
  - Valor contratado
  - Valor orçado (budget)
  - Valor total alocado (calculado)
  - Margem (calculado)
- **Visitas Técnicas**:
  - Número de visitas realizadas
  - Visitas cobradas
  - Valor por visita
  - Total de visitas já virou desconto? (boolean)
- **Status**:
  - Em orçamento
  - Aguardando início
  - Em andamento
  - Pausado
  - Concluído
  - Cancelado
- Observações
- Auditoria (criado por, atualizado por)

### 4. VisitaTecnica
- Projeto (FK)
- Data/Hora da visita
- Técnico responsável (FK User)
- Descrição/Objetivo
- Cobrada? (boolean)
- Valor cobrado
- Virou desconto? (boolean)
- Data que virou desconto
- Observações
- Criado por, criado em

### 5. AlocacaoProjeto
Controle de TUDO que foi alocado ao projeto:
- Projeto (FK)
- Data da alocação
- **Tipo de Alocação**:
  - Material/Produto (FK Item)
  - Mão de obra interna
  - Mão de obra terceirizada
  - Serviço terceirizado
  - Equipamento
  - Transporte
  - Outros
- **Se for Material/Produto**:
  - Item (FK)
  - Quantidade
  - Valor unitário (do custo médio no momento)
  - Movimentação estoque (FK, criada automaticamente)
- **Se for Mão de Obra Interna**:
  - Funcionário (FK Pessoa)
  - Horas trabalhadas
  - Valor hora
- **Se for Terceiro/Serviço**:
  - Fornecedor (FK Pessoa)
  - Descrição do serviço
  - Valor
- Documento (NF, recibo, etc)
- Valor total
- Observações
- Criado por, criado em

### 6. ContaCorrenteProjeto
Movimentações financeiras do projeto:
- Projeto (FK)
- Data movimento
- **Tipo**:
  - Recebimento (entrada de dinheiro)
  - Pagamento/Custo (saída de dinheiro)
  - Visita técnica (pode ser entrada ou saída)
- Descrição
- Valor
- Documento
- Alocação relacionada (FK AlocacaoProjeto, nullable)
- Visita relacionada (FK VisitaTecnica, nullable)
- Saldo anterior (calculado)
- Saldo após (calculado)
- Observações
- Criado por, criado em

### 7. VendaDireta
Venda simples de produtos (sem projeto):
- Código venda (único)
- Cliente (FK Pessoa)
- Vendedor (FK User)
- Data venda
- Valor total
- Desconto
- Valor final
- Forma de pagamento
- Status (Pendente, Pago, Cancelado)
- Observações
- Criado por, criado em

### 8. VendaDiretaItem
Itens da venda:
- Venda (FK)
- Item/Produto (FK)
- Quantidade
- Valor unitário
- Desconto
- Valor total
- Movimentação estoque (FK, criada automaticamente)

## Regras de Negócio

### Visitas Técnicas
1. Visitas podem ser cobradas ou não
2. Visitas cobradas geram entrada na conta corrente
3. Total de visitas cobradas pode virar desconto no projeto
4. Quando viram desconto:
   - Marca todas as visitas como "virou_desconto = True"
   - Cria lançamento de saída na conta corrente
   - Atualiza valor do projeto

### Alocações
1. Ao alocar MATERIAL:
   - Cria movimentação SAIDA no estoque automaticamente
   - Usa custo médio do momento da alocação
   - Gera lançamento na conta corrente do projeto

2. Ao alocar MÃO DE OBRA INTERNA:
   - Calcula valor (horas × valor_hora)
   - Gera lançamento na conta corrente

3. Ao alocar TERCEIROS:
   - Gera lançamento na conta corrente

### Conta Corrente
1. Saldo calculado automaticamente
2. Todo lançamento recalcula saldos posteriores
3. Saldo inicial = 0
4. Entradas: Recebimentos, visitas cobradas
5. Saídas: Alocações, pagamentos

### Vendas Diretas
1. Ao confirmar venda:
   - Cria movimentações SAIDA no estoque para cada item
   - Valida estoque disponível
2. Ao cancelar:
   - Estorna movimentações do estoque

## Integrações

### Com Estoque
- VendaDireta → cria EstoqueMovimentacao (SAIDA)
- AlocacaoProjeto (tipo Material) → cria EstoqueMovimentacao (SAIDA)

### Com Cadastros
- Cliente/Fornecedor/Funcionário → usa Pessoa
- Vendedor/Técnico → usa User

## Dashboards e Relatórios

### Dashboard Projetos
- Projetos ativos
- Projetos atrasados
- Margem média dos projetos
- Total alocado vs Total contratado
- Próximas visitas técnicas

### Relatórios
1. **Extrato de Projeto**:
   - Conta corrente completa
   - Todas as alocações
   - Visitas técnicas
   - Margem atual

2. **Análise de Custos**:
   - Custos por tipo (material, MO, terceiros)
   - Comparativo orçado × realizado

3. **Vendas Diretas**:
   - Vendas por período
   - Vendas por cliente
   - Vendas por vendedor
   - Produtos mais vendidos
