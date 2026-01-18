# DESIGN - MÓDULO ORÇAMENTOS E VENDAS

**Sistema Comercial para Fábrica de Esquadrias**  
**Data:** Dezembro 2025  
**Versão:** 1.0

---

## 📋 ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura e Modelagem](#2-arquitetura-e-modelagem)
3. [Regras de Negócio](#3-regras-de-negócio)
4. [Fluxo de Processos](#4-fluxo-de-processos)
5. [Integrações](#5-integrações)
6. [Relatórios e Análises](#6-relatórios-e-análises)
7. [Roadmap Futuro](#7-roadmap-futuro)

---

## 1. VISÃO GERAL

### 1.1 Objetivo

Criar um **módulo comercial completo** que permita:
- ✅ Criar e gerenciar orçamentos
- ✅ Gerar propostas comerciais profissionais (PDF)
- ✅ Controlar funil de vendas (pipeline)
- ✅ Aprovar orçamento → gerar OBRA automaticamente
- ✅ Gerar contas a receber no Financeiro
- ✅ Análise comercial (conversão, ticket médio, backlog)

### 1.2 Escopo MVP

**Incluído:**
- Orçamentos com itens (produtos/serviços)
- Múltiplas condições de pagamento
- Geração automática de obras
- Geração automática de títulos financeiros
- Propostas comerciais em PDF
- Relatórios comerciais básicos
- Histórico de status (audit trail)

**Não Incluído (Roadmap):**
- CRM completo (follow-up, tarefas)
- Integração WhatsApp/Email automático
- Assinatura digital de contratos
- Metas de vendedores
- Comissões automáticas

### 1.3 Premissas

1. **Cliente sempre no cadastro Pessoa**
   - Obrigatório: telefone/WhatsApp, endereço, e-mail
   - Campo `cliente=True` ativa validações adicionais

2. **Orçamento ≠ Contrato**
   - Orçamento pode existir sem contrato formal
   - Contrato é opcional (documento assinado)

3. **Aprovação gera tudo automaticamente**
   - Obra no módulo Projetos
   - Centro de Custo
   - Títulos a Receber
   - Histórico auditável

4. **Lucro calculado na Obra, não no Orçamento**
   - Orçamento tem custo estimado (opcional)
   - Lucro real vem da execução da obra

---

## 2. ARQUITETURA E MODELAGEM

### 2.1 Diagrama ER Simplificado

```
┌─────────────────┐
│    Pessoa       │ (EXISTENTE - Cliente/Vendedor)
│  (Cliente)      │
└────────┬────────┘
         │ 1
         │
         │ N
┌────────▼────────┐
│   Orcamento     │────┐
│                 │    │
│ - numero        │    │ 1
│ - status        │    │
│ - total         │    │
│ - validade_ate  │    │ N
└────────┬────────┘    │
         │             │
         │ 1           │
         │             │
         │ N           │
┌────────▼────────┐    │
│ OrcamentoItem   │    │
│                 │    │
│ - produto       │    │
│ - quantidade    │    │
│ - preco_unit    │    │
│ - custo_estim   │    │
└─────────────────┘    │
                       │
                       │
                  ┌────▼──────────────┐
                  │ CondicaoPagamento │
                  │                   │
                  │ - tipo            │
                  │ - entrada         │
                  │ - parcelas        │
                  └───────────────────┘

┌─────────────────┐
│ OrcamentoAnexo  │ (Versões PDF, Arquivos)
│                 │
│ - versao        │
│ - arquivo       │
│ - data_envio    │
└─────────────────┘

APROVAÇÃO DO ORÇAMENTO GERA:

┌─────────────────┐
│      Obra       │ (módulo projetos)
│                 │
│ - cliente       │◄─── dados do orçamento
│ - valor_contrato│
│ - budget        │
└────────┬────────┘
         │
         │ 1
         │
         │ N
┌────────▼────────┐
│ Titulo Receber  │ (módulo financeiro)
│                 │
│ - valor         │
│ - vencimento    │
│ - centro_custo  │◄─── obra
└─────────────────┘
```

### 2.2 Models Django Detalhados

#### 2.2.1 CondicaoPagamento

```python
class CondicaoPagamento(models.Model):
    """
    Condições de pagamento predefinidas.
    Ex: À vista, Entrada + 3x, 30/40/30 (medições)
    """
    
    TIPO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('PARCELADO', 'Parcelado'),
        ('ENTRADA_PARCELAS', 'Entrada + Parcelas'),
        ('MEDICAO', 'Medição de Obra'),
        ('PERSONALIZADO', 'Personalizado'),
    ]
    
    # Identificação
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Configuração
    percentual_entrada = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="% de entrada (0-100)"
    )
    numero_parcelas = models.PositiveIntegerField(
        default=1,
        help_text="Número de parcelas (incluindo entrada se houver)"
    )
    intervalo_dias = models.PositiveIntegerField(
        default=30,
        help_text="Intervalo em dias entre parcelas"
    )
    primeira_parcela_dias = models.PositiveIntegerField(
        default=0,
        help_text="Dias até primeira parcela (0=à vista)"
    )
    
    # Medições (JSON)
    medicoes_percentuais = models.JSONField(
        null=True, blank=True,
        help_text="Array de percentuais para medições: [30, 40, 30]"
    )
    
    # Controle
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendas_condicao_pagamento'
        verbose_name = 'Condição de Pagamento'
        verbose_name_plural = 'Condições de Pagamento'
        ordering = ['descricao']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    def validar_medicoes(self):
        """Valida que soma de medições = 100%"""
        if self.tipo == 'MEDICAO' and self.medicoes_percentuais:
            soma = sum(self.medicoes_percentuais)
            if soma != 100:
                raise ValueError(f"Soma de medições deve ser 100%. Atual: {soma}%")
```

#### 2.2.2 Orcamento

```python
from django.contrib.auth import get_user_model
from cadastros.models import Pessoa
from decimal import Decimal

User = get_user_model()

class Orcamento(models.Model):
    """
    Orçamento comercial para clientes.
    Pode gerar Obra automaticamente ao ser aprovado.
    """
    
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('ENVIADO', 'Enviado ao Cliente'),
        ('NEGOCIACAO', 'Em Negociação'),
        ('APROVADO', 'Aprovado'),
        ('REPROVADO', 'Reprovado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Identificação
    numero = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text="Gerado automaticamente: ORC-2025-0001"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='RASCUNHO'
    )
    
    # Cliente e Vendedor
    cliente = models.ForeignKey(
        Pessoa, on_delete=models.PROTECT, 
        related_name='orcamentos',
        limit_choices_to={'cliente': True}
    )
    vendedor = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='orcamentos_vendidos'
    )
    
    # Datas
    data_orcamento = models.DateField(auto_now_add=True)
    validade_ate = models.DateField(
        help_text="Até quando este orçamento é válido"
    )
    prazo_execucao_dias = models.PositiveIntegerField(
        default=30,
        help_text="Prazo previsto de execução em dias"
    )
    
    # Endereço de Execução (copiado do cliente, editável)
    endereco_execucao_logradouro = models.CharField(max_length=200)
    endereco_execucao_numero = models.CharField(max_length=20)
    endereco_execucao_complemento = models.CharField(max_length=100, blank=True)
    endereco_execucao_bairro = models.CharField(max_length=100)
    endereco_execucao_cidade = models.CharField(max_length=100)
    endereco_execucao_estado = models.CharField(max_length=2)
    endereco_execucao_cep = models.CharField(max_length=9)
    
    # Condição de Pagamento
    condicao_pagamento = models.ForeignKey(
        CondicaoPagamento, on_delete=models.PROTECT,
        related_name='orcamentos'
    )
    
    # Valores
    subtotal = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Soma dos itens"
    )
    desconto = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    frete = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    outras_despesas = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    total = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    # Custos e Margem (opcional - para análise)
    custo_total_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Soma dos custos estimados dos itens"
    )
    
    # Observações
    observacoes = models.TextField(blank=True)
    observacoes_internas = models.TextField(
        blank=True,
        help_text="Não aparecem na proposta ao cliente"
    )
    
    # Integração com Obra
    obra_gerada = models.OneToOneField(
        'projetos.Obra', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orcamento_origem'
    )
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    aprovado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orcamentos_aprovados'
    )
    
    # Auditoria
    criado_por = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='orcamentos_criados'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendas_orcamento'
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_orcamento', '-numero']
        indexes = [
            models.Index(fields=['status', 'data_orcamento']),
            models.Index(fields=['cliente', 'status']),
            models.Index(fields=['vendedor', 'data_orcamento']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.cliente.nome_razao}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        
        # Copiar endereço do cliente se vazio
        if not self.endereco_execucao_logradouro and self.cliente:
            self._copiar_endereco_cliente()
        
        # Recalcular total
        self.calcular_totais()
        
        super().save(*args, **kwargs)
    
    def _gerar_numero(self):
        """Gera número sequencial: ORC-2025-0001"""
        from django.db.models import Max
        import datetime
        
        ano = datetime.datetime.now().year
        prefixo = f"ORC-{ano}-"
        
        ultimo = Orcamento.objects.filter(
            numero__startswith=prefixo
        ).aggregate(Max('numero'))['numero__max']
        
        if ultimo:
            ultimo_num = int(ultimo.split('-')[-1])
            proximo = ultimo_num + 1
        else:
            proximo = 1
        
        return f"{prefixo}{proximo:04d}"
    
    def _copiar_endereco_cliente(self):
        """Copia endereço do cliente para endereço de execução"""
        if self.cliente:
            self.endereco_execucao_logradouro = self.cliente.endereco_logradouro or ''
            self.endereco_execucao_numero = self.cliente.endereco_numero or ''
            self.endereco_execucao_complemento = self.cliente.endereco_complemento or ''
            self.endereco_execucao_bairro = self.cliente.endereco_bairro or ''
            self.endereco_execucao_cidade = self.cliente.endereco_cidade or ''
            self.endereco_execucao_estado = self.cliente.endereco_estado or ''
            self.endereco_execucao_cep = self.cliente.endereco_cep or ''
    
    def calcular_totais(self):
        """Recalcula subtotal e total com base nos itens"""
        itens = self.itens.all()
        
        self.subtotal = sum(item.total_item for item in itens)
        self.custo_total_estimado = sum(
            item.custo_unitario_estimado * item.quantidade 
            for item in itens 
            if item.custo_unitario_estimado
        )
        
        self.total = self.subtotal - self.desconto + self.frete + self.outras_despesas
    
    @property
    def margem_estimada(self):
        """Margem estimada em %"""
        if self.total > 0 and self.custo_total_estimado > 0:
            lucro = self.total - self.custo_total_estimado
            return (lucro / self.total) * 100
        return Decimal('0.00')
    
    @property
    def esta_vencido(self):
        """Verifica se orçamento está vencido"""
        from datetime import date
        return date.today() > self.validade_ate
    
    @property
    def pode_aprovar(self):
        """Verifica se pode ser aprovado"""
        return (
            self.status in ['ENVIADO', 'NEGOCIACAO'] and
            not self.esta_vencido and
            self.itens.exists() and
            self.total > 0
        )
```

#### 2.2.3 OrcamentoItem

```python
from cadastros.models import Produto

class OrcamentoItem(models.Model):
    """
    Itens do orçamento (produtos ou serviços).
    Específico para esquadrias: pode ter largura, altura, cor, linha.
    """
    
    # Relacionamento
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.CASCADE,
        related_name='itens'
    )
    ordem = models.PositiveIntegerField(default=0)
    
    # Produto ou Descrição Livre
    produto = models.ForeignKey(
        Produto, on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Produto do cadastro (ou deixe vazio para descrição livre)"
    )
    descricao = models.CharField(
        max_length=500,
        help_text="Descrição exibida na proposta"
    )
    
    # Quantidade e Unidade
    quantidade = models.DecimalField(max_digits=15, decimal_places=3)
    unidade = models.CharField(
        max_length=10, default='UN',
        help_text="UN, M2, ML, KG, etc"
    )
    
    # Preços
    preco_unitario = models.DecimalField(
        max_digits=15, decimal_places=2,
        help_text="Preço de venda unitário"
    )
    custo_unitario_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Custo estimado (opcional, para margem)"
    )
    
    # Desconto no Item
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    desconto_valor = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    # Total do Item (calculado)
    total_item = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    
    # Campos Técnicos (Esquadrias)
    largura = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Largura em metros"
    )
    altura = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Altura em metros"
    )
    m2_calculado = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Área calculada (largura x altura)"
    )
    cor = models.CharField(max_length=100, blank=True)
    linha = models.CharField(max_length=100, blank=True)
    vidro = models.CharField(max_length=100, blank=True)
    acabamento = models.CharField(max_length=100, blank=True)
    
    # Observações Técnicas
    observacao_tecnica = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vendas_orcamento_item'
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'
        ordering = ['orcamento', 'ordem']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.descricao[:50]}"
    
    def save(self, *args, **kwargs):
        # Se produto selecionado, copiar dados
        if self.produto and not self.descricao:
            self.descricao = self.produto.descricao
            self.unidade = self.produto.unidade
            if not self.preco_unitario:
                self.preco_unitario = self.produto.preco_venda or Decimal('0.00')
        
        # Calcular m2 se largura e altura informadas
        if self.largura and self.altura:
            self.m2_calculado = self.largura * self.altura
        
        # Calcular total do item
        self.calcular_total()
        
        super().save(*args, **kwargs)
        
        # Recalcular totais do orçamento
        self.orcamento.calcular_totais()
        self.orcamento.save()
    
    def calcular_total(self):
        """Calcula total do item com desconto"""
        subtotal = self.quantidade * self.preco_unitario
        
        # Desconto percentual ou valor
        desconto = Decimal('0.00')
        if self.desconto_percentual > 0:
            desconto = subtotal * (self.desconto_percentual / 100)
        elif self.desconto_valor > 0:
            desconto = self.desconto_valor
        
        self.total_item = subtotal - desconto
```

#### 2.2.4 OrcamentoAnexo

```python
class OrcamentoAnexo(models.Model):
    """
    Anexos do orçamento: propostas enviadas (PDF), plantas, fotos, etc.
    """
    
    TIPO_CHOICES = [
        ('PROPOSTA', 'Proposta Comercial'),
        ('PLANTA', 'Planta/Projeto'),
        ('FOTO', 'Foto'),
        ('DOCUMENTO', 'Documento'),
        ('OUTRO', 'Outro'),
    ]
    
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.CASCADE,
        related_name='anexos'
    )
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='orcamentos/anexos/%Y/%m/')
    
    # Versionamento (para propostas)
    versao = models.PositiveIntegerField(default=1)
    data_envio = models.DateTimeField(null=True, blank=True)
    enviado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='anexos_criados'
    )
    
    class Meta:
        db_table = 'vendas_orcamento_anexo'
        verbose_name = 'Anexo de Orçamento'
        verbose_name_plural = 'Anexos de Orçamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.descricao}"
```

#### 2.2.5 OrcamentoHistorico

```python
class OrcamentoHistorico(models.Model):
    """
    Histórico de mudanças de status do orçamento.
    Audit trail completo.
    """
    
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.CASCADE,
        related_name='historico'
    )
    
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20)
    
    observacao = models.TextField(blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.PROTECT
    )
    
    class Meta:
        db_table = 'vendas_orcamento_historico'
        verbose_name = 'Histórico de Orçamento'
        verbose_name_plural = 'Históricos de Orçamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.status_anterior} → {self.status_novo}"
```

---

## 3. REGRAS DE NEGÓCIO

### 3.1 Criação de Orçamento

**Regras:**
1. ✅ Cliente deve ter telefone/WhatsApp e endereço cadastrados
2. ✅ Número gerado automaticamente: `ORC-YYYY-NNNN`
3. ✅ Status inicial: `RASCUNHO`
4. ✅ Validade padrão: 15 dias (configurável)
5. ✅ Endereço de execução copiado do cliente (editável)

**Validações:**
```python
def validar_cliente_orcamento(cliente):
    erros = []
    
    if not cliente.telefone and not cliente.celular:
        erros.append("Cliente deve ter telefone ou celular cadastrado")
    
    if not cliente.endereco_logradouro:
        erros.append("Cliente deve ter endereço completo")
    
    if not cliente.email:
        erros.append("Cliente deve ter e-mail cadastrado")
    
    if erros:
        raise ValidationError(erros)
```

### 3.2 Aprovação de Orçamento

**Regras:**
1. ✅ Pode aprovar se status = `ENVIADO` ou `NEGOCIACAO`
2. ✅ Não pode aprovar orçamento vencido
3. ✅ Deve ter pelo menos 1 item
4. ✅ Total deve ser > 0

**Ao aprovar, executar:**

```python
@transaction.atomic
def aprovar_orcamento(orcamento, usuario_aprovador):
    """
    Aprovação completa do orçamento.
    Gera obra e títulos financeiros automaticamente.
    """
    
    # 1. Validações
    if not orcamento.pode_aprovar:
        raise BusinessError("Orçamento não pode ser aprovado")
    
    # 2. Atualizar status
    orcamento.status = 'APROVADO'
    orcamento.data_aprovacao = timezone.now()
    orcamento.aprovado_por = usuario_aprovador
    orcamento.save()
    
    # 3. Criar OBRA
    obra = criar_obra_de_orcamento(orcamento)
    orcamento.obra_gerada = obra
    orcamento.save()
    
    # 4. Criar Centro de Custo
    centro_custo = criar_centro_custo_obra(obra)
    
    # 5. Gerar Títulos a Receber
    titulos = gerar_titulos_receber(orcamento, obra, centro_custo)
    
    # 6. Registrar histórico
    OrcamentoHistorico.objects.create(
        orcamento=orcamento,
        status_anterior='NEGOCIACAO',
        status_novo='APROVADO',
        observacao=f"Aprovado por {usuario_aprovador.get_full_name()}. Obra gerada: {obra.codigo}",
        criado_por=usuario_aprovador
    )
    
    return {
        'obra': obra,
        'centro_custo': centro_custo,
        'titulos': titulos
    }
```

### 3.3 Criação de Obra (ao aprovar)

```python
def criar_obra_de_orcamento(orcamento):
    """
    Cria obra automaticamente com dados do orçamento.
    """
    from projetos.models import Obra
    
    obra = Obra.objects.create(
        # Identificação
        codigo=gerar_codigo_obra(),  # OBRA-2025-0001
        nome=f"Obra - {orcamento.cliente.nome_razao[:100]}",
        
        # Cliente e Responsável
        cliente=orcamento.cliente,
        vendedor=orcamento.vendedor,
        
        # Endereço (copiado do orçamento)
        endereco_logradouro=orcamento.endereco_execucao_logradouro,
        endereco_numero=orcamento.endereco_execucao_numero,
        endereco_complemento=orcamento.endereco_execucao_complemento,
        endereco_bairro=orcamento.endereco_execucao_bairro,
        endereco_cidade=orcamento.endereco_execucao_cidade,
        endereco_estado=orcamento.endereco_execucao_estado,
        endereco_cep=orcamento.endereco_execucao_cep,
        
        # Valores
        valor_contrato=orcamento.total,
        valor_orcado=orcamento.custo_total_estimado,
        
        # Datas
        data_inicio_prevista=calcular_data_inicio(orcamento),
        data_fim_prevista=calcular_data_fim(orcamento),
        
        # Status
        status='ORCAMENTO',  # Aguardando início
        
        # Origem
        orcamento_origem_id=orcamento.id,
        
        # Auditoria
        criado_por=orcamento.aprovado_por
    )
    
    return obra
```

### 3.4 Geração de Títulos Financeiros

```python
def gerar_titulos_receber(orcamento, obra, centro_custo):
    """
    Gera títulos a receber conforme condição de pagamento.
    """
    from financeiro.models import Titulo, PlanoContas
    from datetime import timedelta
    
    condicao = orcamento.condicao_pagamento
    titulos = []
    
    # Plano de contas padrão
    plano_receita = PlanoContas.objects.get(codigo='3.01.01')  # Receita de Obras
    
    if condicao.tipo == 'A_VISTA':
        # 1 título à vista
        titulo = Titulo.objects.create(
            tipo='RECEBER',
            cliente=orcamento.cliente,
            descricao=f"Orçamento {orcamento.numero} - À Vista",
            valor=orcamento.total,
            vencimento=orcamento.data_aprovacao.date() + timedelta(days=condicao.primeira_parcela_dias),
            centro_custo=centro_custo,
            plano_contas=plano_receita,
            orcamento_origem=orcamento,
            obra=obra,
            criado_por=orcamento.aprovado_por
        )
        titulos.append(titulo)
    
    elif condicao.tipo == 'PARCELADO':
        # N parcelas iguais
        valor_parcela = orcamento.total / condicao.numero_parcelas
        
        for i in range(condicao.numero_parcelas):
            dias = condicao.primeira_parcela_dias + (i * condicao.intervalo_dias)
            
            titulo = Titulo.objects.create(
                tipo='RECEBER',
                cliente=orcamento.cliente,
                descricao=f"Orçamento {orcamento.numero} - Parcela {i+1}/{condicao.numero_parcelas}",
                valor=valor_parcela,
                vencimento=orcamento.data_aprovacao.date() + timedelta(days=dias),
                centro_custo=centro_custo,
                plano_contas=plano_receita,
                numero_parcela=i+1,
                total_parcelas=condicao.numero_parcelas,
                orcamento_origem=orcamento,
                obra=obra,
                criado_por=orcamento.aprovado_por
            )
            titulos.append(titulo)
    
    elif condicao.tipo == 'ENTRADA_PARCELAS':
        # Entrada + parcelas
        valor_entrada = orcamento.total * (condicao.percentual_entrada / 100)
        valor_restante = orcamento.total - valor_entrada
        valor_parcela = valor_restante / (condicao.numero_parcelas - 1) if condicao.numero_parcelas > 1 else valor_restante
        
        # Entrada
        titulo_entrada = Titulo.objects.create(
            tipo='RECEBER',
            cliente=orcamento.cliente,
            descricao=f"Orçamento {orcamento.numero} - Entrada ({condicao.percentual_entrada}%)",
            valor=valor_entrada,
            vencimento=orcamento.data_aprovacao.date(),
            centro_custo=centro_custo,
            plano_contas=plano_receita,
            numero_parcela=1,
            total_parcelas=condicao.numero_parcelas,
            orcamento_origem=orcamento,
            obra=obra,
            criado_por=orcamento.aprovado_por
        )
        titulos.append(titulo_entrada)
        
        # Demais parcelas
        for i in range(condicao.numero_parcelas - 1):
            dias = condicao.primeira_parcela_dias + ((i+1) * condicao.intervalo_dias)
            
            titulo = Titulo.objects.create(
                tipo='RECEBER',
                cliente=orcamento.cliente,
                descricao=f"Orçamento {orcamento.numero} - Parcela {i+2}/{condicao.numero_parcelas}",
                valor=valor_parcela,
                vencimento=orcamento.data_aprovacao.date() + timedelta(days=dias),
                centro_custo=centro_custo,
                plano_contas=plano_receita,
                numero_parcela=i+2,
                total_parcelas=condicao.numero_parcelas,
                orcamento_origem=orcamento,
                obra=obra,
                criado_por=orcamento.aprovado_por
            )
            titulos.append(titulo)
    
    elif condicao.tipo == 'MEDICAO':
        # Medições personalizadas
        percentuais = condicao.medicoes_percentuais or []
        
        for i, percentual in enumerate(percentuais):
            valor_medicao = orcamento.total * (percentual / 100)
            dias = condicao.primeira_parcela_dias + (i * condicao.intervalo_dias)
            
            titulo = Titulo.objects.create(
                tipo='RECEBER',
                cliente=orcamento.cliente,
                descricao=f"Orçamento {orcamento.numero} - Medição {i+1} ({percentual}%)",
                valor=valor_medicao,
                vencimento=orcamento.data_aprovacao.date() + timedelta(days=dias),
                centro_custo=centro_custo,
                plano_contas=plano_receita,
                numero_parcela=i+1,
                total_parcelas=len(percentuais),
                orcamento_origem=orcamento,
                obra=obra,
                criado_por=orcamento.aprovado_por
            )
            titulos.append(titulo)
    
    return titulos
```

---

## 4. FLUXO DE PROCESSOS

### 4.1 Fluxo Completo de Vendas

```
┌──────────────────────────────────────────────────────────────┐
│                    PROCESSO COMERCIAL                        │
└──────────────────────────────────────────────────────────────┘

1. CADASTRO CLIENTE
   │
   ├─► Validar: telefone, endereço, e-mail
   │
   └─► Cliente ativo = True

2. CRIAR ORÇAMENTO
   │
   ├─► Status = RASCUNHO
   ├─► Adicionar itens
   ├─► Calcular totais
   └─► Definir condição pagamento

3. ENVIAR PROPOSTA
   │
   ├─► Gerar PDF
   ├─► Status = ENVIADO
   ├─► Registrar histórico
   └─► (Opcional) Enviar email/WhatsApp

4. NEGOCIAÇÃO
   │
   ├─► Status = NEGOCIACAO
   ├─► Editar itens/valores
   ├─► Gerar novas versões
   └─► Follow-up comercial

5. APROVAÇÃO / REPROVAÇÃO
   │
   ├─── APROVADO ─────┐
   │                  │
   │                  ├─► Criar OBRA
   │                  ├─► Criar Centro Custo
   │                  ├─► Gerar Títulos RECEBER
   │                  └─► Registrar histórico
   │
   └─── REPROVADO ────┐
                      └─► Registrar motivo
                      └─► Arquivar

6. EXECUÇÃO DA OBRA
   │
   ├─► Módulo Projetos
   ├─► Controle de custos
   └─► Análise de lucro real

7. FATURAMENTO
   │
   ├─► Baixa dos títulos
   └─► Fluxo de caixa
```

### 4.2 Estados do Orçamento

```
RASCUNHO ───► ENVIADO ───► NEGOCIACAO ───┬───► APROVADO
                                          │
                                          ├───► REPROVADO
                                          │
                                          └───► CANCELADO

Transições permitidas:
- RASCUNHO → ENVIADO
- RASCUNHO → CANCELADO
- ENVIADO → NEGOCIACAO
- ENVIADO → APROVADO
- ENVIADO → REPROVADO
- NEGOCIACAO → ENVIADO (reenvio)
- NEGOCIACAO → APROVADO
- NEGOCIACAO → REPROVADO
- NEGOCIACAO → CANCELADO

Irreversíveis:
- APROVADO (não pode voltar)
- REPROVADO (não pode voltar)
- CANCELADO (não pode voltar)
```

---

## 5. INTEGRAÇÕES

### 5.1 Com Módulo Cadastros

**Validações ao criar orçamento:**
```python
# Em Pessoa, adicionar validação:
class Pessoa(models.Model):
    # ... campos existentes ...
    
    def validar_como_cliente(self):
        """Valida se pessoa pode ser cliente de orçamento"""
        if not self.cliente:
            raise ValidationError("Pessoa deve ser marcada como cliente")
        
        erros = []
        
        if not (self.telefone or self.celular):
            erros.append("Cliente deve ter telefone ou celular")
        
        if not self.endereco_logradouro:
            erros.append("Cliente deve ter endereço completo")
        
        if not self.email:
            erros.append("Cliente deve ter e-mail")
        
        if erros:
            raise ValidationError(erros)
```

### 5.2 Com Módulo Projetos (Obras)

**Adicionar em Obra:**
```python
class Obra(models.Model):
    # ... campos existentes ...
    
    orcamento_origem = models.OneToOneField(
        'vendas.Orcamento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='obra_gerada'
    )
```

### 5.3 Com Módulo Financeiro

**Adicionar em Titulo:**
```python
class Titulo(models.Model):
    # ... campos existentes ...
    
    orcamento_origem = models.ForeignKey(
        'vendas.Orcamento',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='titulos_gerados'
    )
```

---

## 6. RELATÓRIOS E ANÁLISES

### 6.1 Funil de Vendas

```sql
-- Quantidade e valor por status
SELECT 
    status,
    COUNT(*) AS quantidade,
    SUM(total) AS valor_total,
    ROUND(AVG(total), 2) AS ticket_medio
FROM vendas_orcamento
WHERE data_orcamento >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status
ORDER BY 
    CASE status
        WHEN 'RASCUNHO' THEN 1
        WHEN 'ENVIADO' THEN 2
        WHEN 'NEGOCIACAO' THEN 3
        WHEN 'APROVADO' THEN 4
        WHEN 'REPROVADO' THEN 5
        WHEN 'CANCELADO' THEN 6
    END;
```

### 6.2 Taxa de Conversão

```sql
-- Conversão por vendedor
WITH orcamentos_enviados AS (
    SELECT 
        vendedor_id,
        COUNT(*) AS total_enviados
    FROM vendas_orcamento
    WHERE status IN ('ENVIADO', 'NEGOCIACAO', 'APROVADO', 'REPROVADO')
      AND data_orcamento >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY vendedor_id
),
orcamentos_aprovados AS (
    SELECT 
        vendedor_id,
        COUNT(*) AS total_aprovados,
        SUM(total) AS valor_aprovado
    FROM vendas_orcamento
    WHERE status = 'APROVADO'
      AND data_orcamento >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY vendedor_id
)
SELECT 
    u.first_name || ' ' || u.last_name AS vendedor,
    COALESCE(e.total_enviados, 0) AS enviados,
    COALESCE(a.total_aprovados, 0) AS aprovados,
    CASE 
        WHEN COALESCE(e.total_enviados, 0) > 0 
        THEN ROUND((COALESCE(a.total_aprovados, 0)::NUMERIC / e.total_enviados * 100), 2)
        ELSE 0 
    END AS taxa_conversao_pct,
    COALESCE(a.valor_aprovado, 0) AS valor_vendido
FROM auth_user u
LEFT JOIN orcamentos_enviados e ON e.vendedor_id = u.id
LEFT JOIN orcamentos_aprovados a ON a.vendedor_id = u.id
WHERE EXISTS (
    SELECT 1 FROM vendas_orcamento 
    WHERE vendedor_id = u.id
)
ORDER BY taxa_conversao_pct DESC;
```

### 6.3 Backlog de Obras

```sql
-- Obras aprovadas mas ainda não faturadas
SELECT 
    o.numero,
    o.cliente_id,
    p.nome_razao AS cliente,
    o.total AS valor_orcamento,
    o.data_aprovacao,
    COALESCE(SUM(t.valor_pago), 0) AS valor_recebido,
    o.total - COALESCE(SUM(t.valor_pago), 0) AS saldo_a_receber,
    ob.status AS status_obra
FROM vendas_orcamento o
INNER JOIN cadastros_pessoa p ON p.id = o.cliente_id
LEFT JOIN projetos_obra ob ON ob.id = o.obra_gerada_id
LEFT JOIN financeiro_titulo t ON t.orcamento_origem_id = o.id AND t.situacao = 'PAGO'
WHERE o.status = 'APROVADO'
GROUP BY o.id, p.nome_razao, ob.status
ORDER BY o.data_aprovacao DESC;
```

---

## 7. ROADMAP FUTURO

### Fase 2: CRM Completo

- [ ] Tarefas e follow-up
- [ ] Funil visual (drag & drop)
- [ ] Integração WhatsApp Business
- [ ] E-mail marketing automático
- [ ] Lembretes de follow-up

### Fase 3: Assinatura Digital

- [ ] Integração Clicksign/Docusign
- [ ] Contratos digitais
- [ ] Anexo automático à obra

### Fase 4: Comissões

- [ ] Configuração de comissões por vendedor
- [ ] Cálculo automático
- [ ] Relatório de comissões
- [ ] Integração com folha de pagamento

### Fase 5: Metas e Gamificação

- [ ] Metas mensais por vendedor
- [ ] Ranking de vendedores
- [ ] Dashboard comercial
- [ ] Notificações de metas

---

**🎯 Design Completo - Módulo Orçamentos/Vendas v1.0**  
**Fábrica de Esquadrias Serrana - Dezembro 2025**
