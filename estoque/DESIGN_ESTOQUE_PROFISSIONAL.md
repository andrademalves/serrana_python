# 🏭 SISTEMA DE ESTOQUE PROFISSIONAL - FÁBRICA DE ESQUADRIAS

## 📐 ARQUITETURA E DESIGN

### Visão Geral
Sistema de controle de estoque profissional integrado com Obras e Financeiro, utilizando custeio WAC (Weighted Average Cost), com rastreabilidade completa de movimentações e controle de estoque mínimo baseado em consumo real.

---

## 🗃️ MODELO DE DADOS

### 1. APROVEITAMENTO DA BASE EXISTENTE

**Pessoa** (JÁ EXISTE - sem alterações)
```python
class Pessoa:
    # Campos existentes
    nome_razao_social
    cpf_cnpj
    # Flags
    fornecedor = BooleanField()
    cliente = BooleanField()
    funcionario = BooleanField()
    terceiro = BooleanField()
    # Contatos, endereços, etc
```

**Produto** (JÁ EXISTE - ajustes graduais)
```python
class Produto:
    # Campos existentes
    tipo  # produto/servico
    codigo
    descricao
    unidade
    
    # CAMPOS MANTIDOS NO MVP (compatibilidade)
    estoque_atual  # será gradualmente substituído por saldo calculado
    custo  # será substituído por custo_medio do SaldoEstoque
    
    # Fornecedor
    fornecedor = FK(Pessoa)  # fornecedor principal/padrão
    
    # NOVOS CAMPOS PARA ESTOQUE MÍNIMO
    consumo_medio_diario = DecimalField(null=True, blank=True)  # calculado ou manual
    lead_time_dias = IntegerField(default=0)  # prazo de entrega do fornecedor
    estoque_seguranca = DecimalField(default=0)  # estoque de segurança
    estoque_minimo = DecimalField(default=0)  # ponto de ressuprimento
    
    # Auditoria
    ativo
    criado_em, criado_por
    atualizado_em, atualizado_por
```

**Obra/Projeto** (JÁ EXISTE - assumindo)
```python
class Obra:  # ou Projeto
    codigo
    nome
    cliente = FK(Pessoa)
    # ... outros campos
    ativo
```

---

### 2. NOVOS MODELS - ESTOQUE

#### 2.1. LocalEstoque (Locais Físicos)

```python
class LocalEstoque(models.Model):
    """
    Locais físicos de armazenamento.
    Ex: Almoxarifado MP, Produção, Almoxarifado PA, Loja, Obra X, Terceiro Y
    """
    TIPO_CHOICES = [
        ('MP', 'Almoxarifado de Matéria-Prima'),
        ('PRODUCAO', 'Produção/Fabricação'),
        ('PA', 'Almoxarifado de Produto Acabado'),
        ('LOJA', 'Loja/Showroom'),
        ('TERCEIRO', 'Em Terceiros'),
        ('OBRA', 'Em Obra'),
        ('OUTROS', 'Outros'),
    ]
    
    codigo = CharField(max_length=20, unique=True)
    nome = CharField(max_length=100)
    tipo = CharField(max_length=20, choices=TIPO_CHOICES)
    endereco = CharField(max_length=255, blank=True, null=True)
    
    # Configurações
    permite_saldo_negativo = BooleanField(default=False)
    ativo = BooleanField(default=True)
    
    # Responsável (opcional)
    responsavel = FK(Pessoa, null=True, blank=True, limit_choices_to={'funcionario': True})
    
    # Auditoria
    criado_em = DateTimeField(auto_now_add=True)
    criado_por = FK(User, related_name='locais_criados')
    
    class Meta:
        db_table = 'locais_estoque'
        verbose_name = 'Local de Estoque'
        verbose_name_plural = 'Locais de Estoque'
        ordering = ['codigo']
```

#### 2.2. DestinoEstoque (Finalidades)

```python
class DestinoEstoque(models.Model):
    """
    Finalidade/Motivo da saída de estoque.
    Ex: Obra, Loja, Perda/Sucata, Amostra, Manutenção
    """
    codigo = CharField(max_length=20, unique=True)
    nome = CharField(max_length=100)
    
    # Configurações
    exige_obra = BooleanField(default=False)  # se True, saída precisa ter obra informada
    gera_custo_obra = BooleanField(default=True)  # se gera lançamento em CustoObra
    ativo = BooleanField(default=True)
    
    # Auditoria
    criado_em = DateTimeField(auto_now_add=True)
    criado_por = FK(User)
    
    class Meta:
        db_table = 'destinos_estoque'
        verbose_name = 'Destino de Estoque'
        verbose_name_plural = 'Destinos de Estoque'
        ordering = ['codigo']
```

**Destinos Padrão Iniciais:**
- OBRA (exige_obra=True, gera_custo_obra=True)
- LOJA (exige_obra=False, gera_custo_obra=False)
- PERDA_SUCATA (exige_obra=False, gera_custo_obra=False)
- AMOSTRA (exige_obra=False, gera_custo_obra=False)
- MANUTENCAO (exige_obra=False, gera_custo_obra=False)
- CONSUMO_INTERNO (exige_obra=False, gera_custo_obra=False)

#### 2.3. MovimentoEstoque (Tabela Central)

```python
class MovimentoEstoque(models.Model):
    """
    Registro de TODAS as movimentações de estoque.
    Tabela central/histórico imutável (não permite edição após criação).
    """
    TIPO_MOVIMENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('TRANSFERENCIA', 'Transferência'),
        ('AJUSTE', 'Ajuste/Inventário'),
        ('ESTORNO', 'Estorno'),
    ]
    
    DOCUMENTO_TIPO_CHOICES = [
        ('NF_ENTRADA', 'Nota Fiscal de Entrada'),
        ('REQ_SAIDA', 'Requisição de Saída'),
        ('TRANS', 'Transferência'),
        ('INV', 'Inventário/Ajuste'),
        ('OP', 'Ordem de Produção'),
        ('DEV', 'Devolução'),
        ('EST', 'Estorno'),
        ('OUTROS', 'Outros'),
    ]
    
    # Identificação do Movimento
    tipo_movimento = CharField(max_length=20, choices=TIPO_MOVIMENTO_CHOICES, db_index=True)
    documento = CharField(max_length=50, db_index=True)  # Nº NF, Nº Requisição, etc
    documento_tipo = CharField(max_length=20, choices=DOCUMENTO_TIPO_CHOICES)
    data_operacao = DateTimeField(db_index=True)  # quando ocorreu
    
    # Produto
    produto = FK(Produto, on_delete=PROTECT, related_name='movimentos')
    
    # Locais (origem/destino físico)
    local_origem = FK(LocalEstoque, null=True, blank=True, related_name='movimentos_origem')
    local_destino = FK(LocalEstoque, null=True, blank=True, related_name='movimentos_destino')
    
    # Destino (finalidade) - obrigatório em SAIDA
    destino = FK(DestinoEstoque, null=True, blank=True, related_name='movimentos')
    
    # Obra (se destino exigir ou se for saída para obra)
    obra = FK(Obra, null=True, blank=True, related_name='movimentos_estoque')
    
    # Quantidade e Custos
    quantidade = DecimalField(max_digits=12, decimal_places=3)
    custo_unitario_aplicado = DecimalField(max_digits=12, decimal_places=4)  # custo na entrada ou custo médio na saída
    custo_total = DecimalField(max_digits=12, decimal_places=2)  # quantidade * custo_unitario
    
    # Fornecedor (em ENTRADA)
    fornecedor = FK(Pessoa, null=True, blank=True, related_name='entradas_estoque', 
                    limit_choices_to={'fornecedor': True})
    
    # CONTROLE DE PESSOAS (quem solicitou, quem entregou)
    solicitante = FK(Pessoa, null=True, blank=True, related_name='requisicoes_solicitadas',
                     limit_choices_to={'funcionario': True}, 
                     verbose_name='Funcionário Solicitante')
    entregador = FK(Pessoa, null=True, blank=True, related_name='entregas_realizadas',
                    limit_choices_to={'funcionario': True}, 
                    verbose_name='Funcionário Entregador/Almoxarife')
    
    # Observações
    observacao = TextField(blank=True, null=True)
    
    # Estorno
    movimento_origem = FK('self', null=True, blank=True, related_name='estornos',
                          verbose_name='Movimento Original (para estorno)')
    
    # Auditoria
    criado_em = DateTimeField(auto_now_add=True)
    criado_por = FK(User, related_name='movimentos_criados', verbose_name='Usuário que Registrou')
    
    class Meta:
        db_table = 'movimentos_estoque'
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'
        ordering = ['-data_operacao', '-criado_em']
        indexes = [
            Index(fields=['tipo_movimento', 'data_operacao']),
            Index(fields=['produto', 'data_operacao']),
            Index(fields=['obra']),
            Index(fields=['solicitante']),
            Index(fields=['entregador']),
        ]
    
    def clean(self):
        """Validações de negócio"""
        # ENTRADA: deve ter local_destino, não deve ter local_origem
        if self.tipo_movimento == 'ENTRADA':
            if not self.local_destino:
                raise ValidationError('Entrada deve ter local de destino.')
            if self.local_origem:
                raise ValidationError('Entrada não deve ter local de origem.')
        
        # SAIDA: deve ter local_origem, destino; não deve ter local_destino
        elif self.tipo_movimento == 'SAIDA':
            if not self.local_origem:
                raise ValidationError('Saída deve ter local de origem.')
            if not self.destino:
                raise ValidationError('Saída deve ter um destino/finalidade.')
            if self.local_destino:
                raise ValidationError('Saída não deve ter local de destino (use destino).')
            
            # Se destino exige obra, obra deve estar preenchida
            if self.destino.exige_obra and not self.obra:
                raise ValidationError(f'Destino "{self.destino.nome}" exige que uma obra seja informada.')
        
        # TRANSFERENCIA: deve ter origem e destino, e não podem ser iguais
        elif self.tipo_movimento == 'TRANSFERENCIA':
            if not self.local_origem or not self.local_destino:
                raise ValidationError('Transferência deve ter local de origem e destino.')
            if self.local_origem == self.local_destino:
                raise ValidationError('Local de origem e destino não podem ser iguais.')
    
    def save(self, *args, **kwargs):
        # Calcular custo total
        self.custo_total = self.quantidade * self.custo_unitario_aplicado
        
        # Validar
        self.full_clean()
        
        # Se é novo movimento, atualizar saldos
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._atualizar_saldos()
            
            # Se saída para obra que gera custo, criar CustoObra
            if (self.tipo_movimento == 'SAIDA' and 
                self.obra and 
                self.destino and 
                self.destino.gera_custo_obra):
                self._gerar_custo_obra()
```

#### 2.4. SaldoEstoque (Cache/Performance)

```python
class SaldoEstoque(models.Model):
    """
    Saldo de estoque por (produto, local).
    Atualizado automaticamente pelos movimentos.
    """
    produto = FK(Produto, on_delete=CASCADE, related_name='saldos')
    local = FK(LocalEstoque, on_delete=CASCADE, related_name='saldos')
    
    saldo_quantidade = DecimalField(max_digits=12, decimal_places=3, default=0)
    custo_medio = DecimalField(max_digits=12, decimal_places=4, default=0)  # WAC
    
    atualizado_em = DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'saldos_estoque'
        verbose_name = 'Saldo de Estoque'
        verbose_name_plural = 'Saldos de Estoque'
        unique_together = [['produto', 'local']]
        indexes = [
            Index(fields=['produto', 'local']),
            Index(fields=['saldo_quantidade']),
        ]
    
    @property
    def valor_total(self):
        return self.saldo_quantidade * self.custo_medio
```

---

### 3. INTEGRAÇÃO COM OBRAS - CUSTOS

#### 3.1. CustoObra

```python
class CustoObra(models.Model):
    """
    Registro de custos de uma obra.
    Origem: estoque, terceiros, manual, impostos, etc.
    """
    CATEGORIA_CHOICES = [
        ('MATERIAL', 'Material'),
        ('MAO_OBRA', 'Mão de Obra'),
        ('TERCEIRO', 'Terceirizado'),
        ('IMPOSTO', 'Imposto/Taxa'),
        ('TRANSPORTE', 'Transporte'),
        ('EQUIPAMENTO', 'Equipamento/Aluguel'),
        ('OUTROS', 'Outros'),
    ]
    
    ORIGEM_CHOICES = [
        ('ESTOQUE', 'Estoque (Automático)'),
        ('TERCEIRO', 'Fornecedor Terceiro'),
        ('MANUAL', 'Lançamento Manual'),
        ('IMPOSTO', 'Imposto/Taxa'),
        ('RATEIO', 'Rateio'),
    ]
    
    obra = FK(Obra, on_delete=PROTECT, related_name='custos')
    data = DateField(db_index=True)
    
    # Classificação
    categoria = CharField(max_length=20, choices=CATEGORIA_CHOICES)
    origem = CharField(max_length=20, choices=ORIGEM_CHOICES)
    
    # Descrição
    descricao = CharField(max_length=255)
    
    # Valor
    valor = DecimalField(max_digits=12, decimal_places=2)
    
    # Vínculos
    movimento_estoque = FK(MovimentoEstoque, null=True, blank=True, 
                           related_name='custos_obra',
                           verbose_name='Movimento de Estoque Origem')
    fornecedor = FK(Pessoa, null=True, blank=True, related_name='custos_obras',
                    limit_choices_to={'fornecedor': True})
    documento = CharField(max_length=50, blank=True, null=True)  # NF, Recibo, etc
    
    # Observações
    observacao = TextField(blank=True, null=True)
    
    # Auditoria
    criado_em = DateTimeField(auto_now_add=True)
    criado_por = FK(User, related_name='custos_obra_criados')
    
    class Meta:
        db_table = 'custos_obra'
        verbose_name = 'Custo de Obra'
        verbose_name_plural = 'Custos de Obras'
        ordering = ['-data', '-criado_em']
        indexes = [
            Index(fields=['obra', 'data']),
            Index(fields=['categoria']),
            Index(fields=['origem']),
        ]
```

---

### 4. FORNECEDORES (FASE 2 - Preparação)

#### 4.1. ProdutoFornecedor (Múltiplos Fornecedores)

```python
class ProdutoFornecedor(models.Model):
    """
    Relacionamento produto x fornecedor (múltiplos).
    Permite manter histórico de fornecedores e condições.
    FASE 2 - por enquanto usa Produto.fornecedor
    """
    produto = FK(Produto, on_delete=CASCADE, related_name='fornecedores_adicionais')
    fornecedor = FK(Pessoa, on_delete=PROTECT, limit_choices_to={'fornecedor': True})
    
    codigo_no_fornecedor = CharField(max_length=50, blank=True, null=True)
    prazo_entrega_dias = IntegerField(default=0)
    custo_ultima_compra = DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    data_ultima_compra = DateField(null=True, blank=True)
    
    preferencial = BooleanField(default=False)  # se é fornecedor preferencial
    ativo = BooleanField(default=True)
    
    # Auditoria
    criado_em = DateTimeField(auto_now_add=True)
    criado_por = FK(User)
    
    class Meta:
        db_table = 'produto_fornecedor'
        verbose_name = 'Produto x Fornecedor'
        verbose_name_plural = 'Produtos x Fornecedores'
        unique_together = [['produto', 'fornecedor']]
```

---

## 📊 REGRAS DE NEGÓCIO

### 1. CUSTEIO WAC (Weighted Average Cost)

**Entrada:**
```python
# Custo Médio Novo = (Valor Estoque Anterior + Valor Entrada) / Quantidade Total

saldo_anterior = SaldoEstoque.get(produto, local)
qtd_anterior = saldo_anterior.saldo_quantidade
custo_anterior = saldo_anterior.custo_medio

qtd_entrada = movimento.quantidade
custo_entrada = movimento.custo_unitario_aplicado

qtd_nova = qtd_anterior + qtd_entrada
valor_anterior = qtd_anterior * custo_anterior
valor_entrada = qtd_entrada * custo_entrada
valor_total = valor_anterior + valor_entrada

custo_medio_novo = valor_total / qtd_nova if qtd_nova > 0 else 0

saldo_anterior.saldo_quantidade = qtd_nova
saldo_anterior.custo_medio = custo_medio_novo
saldo_anterior.save()
```

**Saída:**
```python
# Usa custo médio vigente, não recalcula

saldo = SaldoEstoque.get(produto, local)
movimento.custo_unitario_aplicado = saldo.custo_medio
movimento.custo_total = movimento.quantidade * saldo.custo_medio

saldo.saldo_quantidade -= movimento.quantidade
saldo.save()  # custo_medio permanece o mesmo
```

### 2. ESTOQUE MÍNIMO E PONTO DE RESSUPRIMENTO

**Cálculo Automático:**
```python
# Consumo médio diário (últimos 90 dias)
consumo_medio_diario = calcular_consumo_medio(produto, dias=90)

# Ponto de Ressuprimento
ponto_ressuprimento = (consumo_medio_diario * lead_time_dias) + estoque_seguranca

# Quantidade Sugerida para Compra
saldo_atual = sum(saldos por local)
if saldo_atual < ponto_ressuprimento:
    quantidade_sugerida = ponto_ressuprimento - saldo_atual
```

**Atualização Automática:**
- Job noturno ou semanal que recalcula consumo_medio_diario
- Atualiza estoque_minimo automaticamente
- Gera alertas para produtos abaixo do mínimo

---

## 🖥️ TELAS E FLUXOS (MVP)

### CADASTROS

1. **Locais de Estoque**
   - CRUD completo
   - Lista: código, nome, tipo, responsável, ativo
   - Form: todos os campos + validações

2. **Destinos de Estoque**
   - CRUD completo
   - Lista: código, nome, exige_obra, gera_custo_obra, ativo
   - Form: todos os campos

3. **Produtos** (ajustar existente)
   - Adicionar campos: consumo_medio_diario, lead_time_dias, estoque_seguranca
   - Mostrar saldo total calculado (soma de saldos por local)

### OPERAÇÕES

4. **Entrada de Estoque (NF)**
   - Form:
     - Documento (NF), Data
     - Fornecedor (select de Pessoa.fornecedor=True)
     - Local Destino
     - Produtos (grid): produto, quantidade, custo unitário, total
   - Ao salvar: cria MovimentoEstoque para cada produto, atualiza saldos com WAC

5. **Requisição/Retirada de Material**
   - Form:
     - Documento (REQ), Data
     - Local Origem
     - Destino (select de DestinoEstoque)
     - Obra (se destino exigir)
     - **Solicitante** (select de Pessoa.funcionario=True)
     - **Entregador/Almoxarife** (select de Pessoa.funcionario=True)
     - Produtos (grid): produto, quantidade disponível, quantidade retirada
   - Validações:
     - Verificar saldo disponível
     - Obra obrigatória se destino exigir
   - Ao salvar:
     - Cria MovimentoEstoque
     - Atualiza saldos
     - Se destino gera custo obra: cria CustoObra automaticamente

6. **Transferência entre Locais**
   - Form:
     - Documento, Data
     - Local Origem
     - Local Destino
     - Produtos (grid): produto, quantidade
   - Ao salvar: cria MovimentoEstoque, move saldo (mantém custo médio)

7. **Ajuste/Inventário**
   - Form:
     - Documento, Data, Motivo
     - Local
     - Produtos (grid): produto, saldo sistema, saldo físico, diferença
   - Ao salvar: cria MovimentoEstoque tipo AJUSTE

8. **Estorno**
   - Buscar movimento original
   - Confirmar estorno
   - Cria movimento inverso vinculado ao original

### RELATÓRIOS

9. **Posição de Estoque**
   - Filtros: produto, local, tipo produto
   - Colunas: código, descrição, local, saldo, custo médio, valor total
   - Total geral

10. **Extrato de Movimentos**
    - Filtros: período, produto, local, obra, tipo movimento, solicitante, entregador
    - Colunas: data, tipo, documento, produto, qtd, custo unit, total, origem, destino, obra, solicitante, entregador
    - Exportar Excel

11. **Produtos Abaixo do Mínimo**
    - Colunas: código, descrição, saldo atual, estoque mínimo, diferença, fornecedor principal, sugestão compra
    - Ordenar por criticidade

12. **Consumo Médio por Produto**
    - Período (ex: 90 dias)
    - Colunas: produto, consumo total, consumo médio diário, lead time, ponto ressuprimento, saldo atual, status

13. **Custos por Obra**
    - Filtro: obra, período, categoria
    - Colunas: data, categoria, origem, descrição, valor
    - Separar: custos do estoque vs outros
    - Total por categoria e geral

---

## 🔄 MIGRAÇÃO DO MODELO ANTIGO

### Estratégia de Transição

**Fase 1 - MVP (Compatibilidade)**
- Manter Produto.estoque_atual como campo
- Criar property/método: `get_saldo_total()` que soma SaldoEstoque
- Nas telas, mostrar saldo calculado
- Job de sincronização: atualiza Produto.estoque_atual a partir dos saldos

**Fase 2 - Deprecação**
- Remover Produto.estoque_atual do model
- Criar view/property `estoque_atual` que retorna saldo calculado

**Comando de Migração Inicial:**
```python
# management/command/migrar_estoque_inicial.py
# Para cada produto com estoque_atual > 0:
#   - Criar LocalEstoque padrão (ex: "ALMOX_GERAL")
#   - Criar MovimentoEstoque tipo AJUSTE com quantidade = estoque_atual
#   - Criar SaldoEstoque correspondente
```

---

## 🔐 PERMISSÕES E SEGURANÇA

### Grupos de Usuários

1. **Almoxarife**
   - Pode: entrada, saída, transferência, ajuste
   - Não pode: estorno sem aprovação

2. **Gestor Estoque**
   - Pode: tudo do almoxarife + estorno + relatórios gerenciais

3. **Operador Produção**
   - Pode: requisição (saída) limitada

4. **Visualizador**
   - Apenas relatórios

### Auditoria

- Todos os movimentos registram: criado_por, criado_em
- MovimentoEstoque é imutável (não permite edição)
- Estornos criam novo movimento, não deletam o original
- Log de alterações em cadastros críticos

---

## 📈 INDICADORES E KPIs

### Dashboard Gerencial

1. **Valor Total do Estoque**
   - Por local
   - Por tipo de produto

2. **Giro de Estoque**
   - Saídas últimos 30/90 dias vs estoque médio

3. **Produtos Críticos**
   - Abaixo do mínimo
   - Zerados com demanda

4. **Custos por Obra**
   - Top 5 obras por custo de material
   - % material vs total da obra

5. **Fornecedores**
   - Top fornecedores por volume
   - Prazo médio de entrega

---

**PRÓXIMO PASSO:** Implementação dos Models Django
