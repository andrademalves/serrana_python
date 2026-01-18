# Módulo de Estoque - Sistema Serrana

## Descrição

Módulo completo de gestão de estoque desenvolvido para o Sistema Serrana. Permite controlar itens (matérias-primas e produtos acabados), movimentações de entrada/saída/ajuste, cálculo automático de custo médio e geração de relatórios.

## Funcionalidades Implementadas

### 1. Dashboard
- **URL**: `/estoque/`
- **Funcionalidades**:
  - Total de itens ativos
  - Itens com estoque abaixo do mínimo
  - Valor total do inventário
  - Movimentações recentes (últimos 7 dias)
  - Separação por tipo (Matéria Prima / Produto Acabado)
  - Ações rápidas (criar item, registrar movimentação, ver estoque baixo)

### 2. Gerenciamento de Itens

#### Listar Itens (`/estoque/itens/`)
- Listagem completa de todos os itens
- Filtros por:
  - Tipo de item (MP/PA)
  - Status (Ativo/Inativo)
  - Estoque baixo
  - Busca por descrição
- Destaque visual para itens com estoque abaixo do mínimo
- Valor total do estoque por item
- Ações: Editar e Desativar

#### Criar Item (`/estoque/itens/criar/`)
- Campos:
  - Tipo de item (Matéria Prima/Produto Acabado)
  - Descrição
  - Unidade de medida (8 opções: UN, KG, MT, M², M³, LT, CX, PCT)
  - Estoque mínimo
  - URL da foto
  - Observações
  - Status ativo
- Validação client-side com SweetAlert2
- Estoque inicial é zero (movimentado via ENTRADA)

#### Editar Item (`/estoque/itens/editar/<id>/`)
- Mesmos campos da criação
- Campos somente leitura:
  - Estoque atual (alterado apenas por movimentações)
  - Custo médio (calculado automaticamente)
- Informações de auditoria (criado por, atualizado por)

#### Desativar Item (`/estoque/itens/excluir/<id>/`)
- Soft delete (não remove do banco, apenas marca como inativo)
- Confirmação com SweetAlert2

### 3. Movimentações de Estoque

#### Listar Movimentações (`/estoque/movimentacoes/`)
- Listagem de todas as movimentações
- Filtros por:
  - Tipo de movimentação (Entrada/Saída/Ajuste)
  - Item
  - Data início e fim
- Limitado a 100 registros (performance)
- Cores por tipo:
  - Verde: ENTRADA
  - Vermelho: SAÍDA
  - Amarelo: AJUSTE

#### Criar Movimentação (`/estoque/movimentacoes/criar/`)
- Campos:
  - Item (com informação de estoque atual)
  - Tipo de movimentação (ENTRADA/SAÍDA/AJUSTE)
  - Quantidade
  - Valor unitário
  - Valor total (calculado automaticamente)
  - Número do documento (NF, Ordem de Produção, etc)
  - Observação
- Validações:
  - Quantidade deve ser maior que zero
  - Valor unitário não pode ser negativo
  - Alerta de estoque insuficiente para SAÍDA
- Cálculo automático de valor total

### 4. Relatórios

#### Relatório de Estoque Atual (`/estoque/relatorios/estoque-atual/`)
- Posição atual de todos os itens
- Filtros:
  - Tipo de item (MP/PA)
  - Somente estoque baixo
- Totalizadores:
  - Total de itens
  - Valor total do estoque
- Status visual:
  - Normal (verde)
  - Estoque Baixo (amarelo)
  - Esgotado (vermelho)
- Função de impressão

#### Relatório de Movimentações (`/estoque/relatorios/movimentacoes/`)
- Histórico completo de movimentações
- Filtros:
  - Período (data início/fim)
  - Tipo de movimentação
  - Item específico
- Totalizadores:
  - Total de movimentações
  - Valor total movimentado
- Função de impressão

## Modelos de Dados

### Item
```python
- tipo_item: CharField (MP/PA)
- descricao: CharField (255)
- unidade_medida: CharField (UN/KG/MT/M2/M3/LT/CX/PCT)
- preco_custo_medio: DecimalField (calculado automaticamente)
- estoque_minimo: DecimalField
- estoque_atual: DecimalField (atualizado automaticamente)
- url_foto: CharField (opcional)
- status_ativo: BooleanField
- observacoes: TextField
- criado_em: DateTimeField
- criado_por: ForeignKey (User)
- atualizado_em: DateTimeField
- atualizado_por: ForeignKey (User)
```

### EstoqueMovimentacao
```python
- item: ForeignKey (Item, PROTECT)
- tipo_mov: CharField (ENTRADA/SAIDA/AJUSTE)
- quantidade: DecimalField
- valor_unitario: DecimalField
- valor_total: DecimalField (calculado)
- documento: CharField (50, opcional)
- observacao: TextField
- data_mov: DateTimeField (auto_now_add)
- criado_por: ForeignKey (User)
```

## Regras de Negócio

### 1. Atualização Automática de Estoque
Ao criar uma movimentação:
- **ENTRADA**: Adiciona a quantidade ao estoque atual
- **SAÍDA**: Subtrai a quantidade do estoque atual
- **AJUSTE**: Adiciona ou subtrai (se quantidade negativa)

### 2. Cálculo de Custo Médio
Para movimentações do tipo **ENTRADA**:
```
Novo Custo Médio = (Estoque Atual * Custo Atual + Quantidade Entrada * Valor Unitário) / (Estoque Atual + Quantidade Entrada)
```
- Movimentações de SAÍDA e AJUSTE não alteram o custo médio
- Previne divisão por zero

### 3. Proteção de Dados
- Items com movimentações não podem ser excluídos (PROTECT)
- Soft delete para itens (apenas desativa)
- Auditoria completa (quem criou, quando, quem atualizou)

## Tecnologias Utilizadas

- **Backend**: Django 6.0
- **Database**: MySQL
- **Frontend**: Bootstrap 5.3.0, Bootstrap Icons 1.10.0
- **JavaScript**: Vanilla JS (cálculos e validações)
- **Alerts**: SweetAlert2 11

## Comandos de Gerenciamento

### popular_estoque
Popula o banco de dados com dados de teste:
```bash
python manage.py popular_estoque
```

**Cria**:
- 5 Matérias Primas (Farinha, Açúcar, Leite, Ovos, Manteiga)
- 4 Produtos Acabados (Pão, Bolo, Torta, Biscoito)
- 13 Movimentações (Entradas, Saídas, Ajustes)

### criar_menu_estoque
Cria o módulo e menus no sistema:
```bash
python manage.py criar_menu_estoque
```

**Cria**:
- Módulo "Estoque"
- 6 Menus (Dashboard, Itens, Movimentações, Relatórios + submenus)

## Permissões

Atualmente utiliza `@login_required` em todas as views.

Para implementar permissões granulares no futuro:
- Visualizar estoque
- Criar itens
- Editar itens
- Excluir itens
- Criar movimentações
- Visualizar relatórios

## URLs Disponíveis

```
/estoque/                                    - Dashboard
/estoque/itens/                              - Listar itens
/estoque/itens/criar/                        - Criar item
/estoque/itens/editar/<id>/                  - Editar item
/estoque/itens/excluir/<id>/                 - Desativar item
/estoque/movimentacoes/                      - Listar movimentações
/estoque/movimentacoes/criar/                - Criar movimentação
/estoque/relatorios/estoque-atual/           - Relatório de estoque
/estoque/relatorios/movimentacoes/           - Relatório de movimentações
```

## Melhorias Futuras

1. **Paginação**: Adicionar paginação para listagens grandes
2. **Exportação**: Excel/PDF para relatórios
3. **Gráficos**: Dashboard com gráficos de evolução de estoque
4. **Código de Barras**: Integração com leitor de código de barras
5. **Alertas**: Notificações automáticas de estoque baixo
6. **Lote/Validade**: Controle de lotes e datas de validade
7. **Localização**: Controle de localização física no estoque
8. **Inventário**: Processo de inventário periódico
9. **API REST**: Endpoints para integração com outros sistemas
10. **Permissões**: Sistema de permissões granulares por ação

## Estrutura de Arquivos

```
estoque/
├── management/
│   └── commands/
│       ├── criar_menu_estoque.py
│       └── popular_estoque.py
├── migrations/
│   └── 0001_initial.py
├── templates/
│   └── estoque/
│       ├── dashboard.html
│       ├── listar_itens.html
│       ├── criar_item.html
│       ├── editar_item.html
│       ├── listar_movimentacoes.html
│       ├── criar_movimentacao.html
│       ├── relatorio_estoque_atual.html
│       └── relatorio_movimentacoes.html
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── urls.py
└── views.py
```

## Autor

Sistema desenvolvido para Serrana Empresarial
Data: 2024
