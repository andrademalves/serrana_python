"""
MODELS - MÓDULO ORÇAMENTOS E VENDAS
====================================

Sistema comercial para fábrica de esquadrias.
Controla orçamentos, propostas, aprovações e geração automática de obras.

Autor: Sistema Comercial Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
import datetime

# Imports de outros módulos
from cadastros.models import Pessoa, Produto

User = get_user_model()


# ==============================================================================
# 1. CONDIÇÃO DE PAGAMENTO
# ==============================================================================

class CondicaoPagamento(models.Model):
    """
    Condições de pagamento predefinidas.
    Exemplos: À vista, Parcelado, Entrada + Parcelas, Medições.
    """
    
    TIPO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('PARCELADO', 'Parcelado'),
        ('ENTRADA_PARCELAS', 'Entrada + Parcelas'),
        ('MEDICAO', 'Medição de Obra'),
        ('PERSONALIZADO', 'Personalizado'),
    ]
    
    # Identificação
    codigo = models.CharField(
        max_length=20, unique=True,
        help_text="Código único da condição (ex: AV, 3X, ENT3X)"
    )
    descricao = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Configuração de Parcelamento
    percentual_entrada = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentual de entrada (0-100%)"
    )
    numero_parcelas = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Número total de parcelas (incluindo entrada)"
    )
    intervalo_dias = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        help_text="Intervalo em dias entre parcelas"
    )
    primeira_parcela_dias = models.PositiveIntegerField(
        default=0,
        help_text="Dias até a primeira parcela (0=à vista)"
    )
    
    # Medições Personalizadas (JSON)
    medicoes_percentuais = models.JSONField(
        null=True, blank=True,
        help_text="Lista de percentuais para medições: [30, 40, 30]"
    )
    
    # Controle
    ativo = models.BooleanField(default=True)
    padrao = models.BooleanField(
        default=False,
        help_text="Condição padrão ao criar orçamento"
    )
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
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Validar medições somam 100%
        if self.tipo == 'MEDICAO':
            if not self.medicoes_percentuais:
                raise ValidationError({
                    'medicoes_percentuais': 'Medições obrigatórias para tipo MEDICAO'
                })
            
            soma = sum(self.medicoes_percentuais)
            if soma != 100:
                raise ValidationError({
                    'medicoes_percentuais': f'Soma de medições deve ser 100%. Atual: {soma}%'
                })
    
    def save(self, *args, **kwargs):
        # Se marcado como padrão, desmarcar os outros
        if self.padrao:
            CondicaoPagamento.objects.filter(padrao=True).update(padrao=False)
        
        super().save(*args, **kwargs)


# ==============================================================================
# 2. ORÇAMENTO
# ==============================================================================

class Orcamento(models.Model):
    """
    Orçamento comercial para clientes.
    Ao ser aprovado, gera automaticamente:
    - Obra (módulo projetos)
    - Centro de Custo
    - Títulos a Receber (módulo financeiro)
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
        max_length=20, choices=STATUS_CHOICES, 
        default='RASCUNHO', db_index=True
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
    data_orcamento = models.DateField(
        default=datetime.date.today,
        help_text="Data de criação do orçamento"
    )
    validade_ate = models.DateField(
        help_text="Até quando este orçamento é válido"
    )
    prazo_execucao_dias = models.PositiveIntegerField(
        default=30,
        help_text="Prazo previsto de execução em dias corridos"
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
    
    # Valores (calculados automaticamente)
    subtotal = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Soma dos itens (sem desconto)"
    )
    desconto = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Desconto global no orçamento"
    )
    frete = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00')
    )
    outras_despesas = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Impostos, taxas, etc"
    )
    total = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Valor final do orçamento"
    )
    
    # Custos Estimados (opcional - para análise de margem)
    custo_total_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal('0.00'),
        help_text="Soma dos custos estimados (não aparece na proposta)"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        help_text="Observações que aparecem na proposta"
    )
    observacoes_internas = models.TextField(
        blank=True,
        help_text="Anotações internas (não aparecem na proposta)"
    )
    
    # Integração com Projeto (após aprovação)
    projeto_gerado = models.OneToOneField(
        'projetos.Projeto', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orcamento_vendas_origem'
    )
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    aprovado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orcamentos_aprovados'
    )
    motivo_reprovacao = models.TextField(blank=True)
    
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
            models.Index(fields=['data_orcamento']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.cliente.nome_razao}"
    
    def save(self, *args, **kwargs):
        """
        Override save para:
        - Gerar número automaticamente
        - Copiar endereço do cliente
        - Calcular totais
        """
        # Gerar número se novo
        if not self.numero:
            self.numero = self._gerar_numero()
        
        # Copiar endereço do cliente se vazio
        if not self.endereco_execucao_logradouro and self.cliente:
            self._copiar_endereco_cliente()
        
        # Definir validade padrão (15 dias)
        if not self.validade_ate:
            self.validade_ate = self.data_orcamento + datetime.timedelta(days=15)
        
        super().save(*args, **kwargs)
    
    def _gerar_numero(self):
        """Gera número sequencial: ORC-YYYY-NNNN"""
        ano = datetime.datetime.now().year
        prefixo = f"ORC-{ano}-"
        
        ultimo = Orcamento.objects.filter(
            numero__startswith=prefixo
        ).order_by('-numero').first()
        
        if ultimo:
            ultimo_num = int(ultimo.numero.split('-')[-1])
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
        """
        Recalcula todos os totais com base nos itens.
        Deve ser chamado após alteração de itens.
        """
        itens = self.itens.all()
        
        # Subtotal = soma dos totais dos itens
        self.subtotal = sum(
            item.total_item for item in itens
        ) or Decimal('0.00')
        
        # Custo total estimado
        self.custo_total_estimado = sum(
            item.custo_unitario_estimado * item.quantidade 
            for item in itens 
            if item.custo_unitario_estimado
        ) or Decimal('0.00')
        
        # Total final
        self.total = (
            self.subtotal 
            - self.desconto 
            + self.frete 
            + self.outras_despesas
        )
    
    @property
    def margem_estimada_percentual(self):
        """Margem estimada em %"""
        if self.total > 0 and self.custo_total_estimado > 0:
            lucro = self.total - self.custo_total_estimado
            return (lucro / self.total) * 100
        return Decimal('0.00')
    
    @property
    def lucro_estimado(self):
        """Lucro estimado em R$"""
        return self.total - self.custo_total_estimado
    
    @property
    def esta_vencido(self):
        """Verifica se orçamento está vencido"""
        return datetime.date.today() > self.validade_ate
    
    @property
    def dias_ate_vencimento(self):
        """Dias até vencimento (negativo se vencido)"""
        delta = self.validade_ate - datetime.date.today()
        return delta.days
    
    @property
    def pode_editar(self):
        """Verifica se pode ser editado"""
        return self.status in ['RASCUNHO', 'ENVIADO', 'NEGOCIACAO']
    
    @property
    def pode_aprovar(self):
        """Verifica se pode ser aprovado"""
        return (
            self.status in ['ENVIADO', 'NEGOCIACAO'] and
            not self.esta_vencido and
            self.itens.exists() and
            self.total > 0
        )
    
    @property
    def pode_reprovar(self):
        """Verifica se pode ser reprovado"""
        return self.status in ['ENVIADO', 'NEGOCIACAO']
    
    @property
    def pode_cancelar(self):
        """Verifica se pode ser cancelado"""
        return self.status not in ['APROVADO', 'REPROVADO', 'CANCELADO']
    
    @property
    def endereco_completo_execucao(self):
        """Retorna endereço de execução formatado"""
        partes = [
            self.endereco_execucao_logradouro,
            self.endereco_execucao_numero,
        ]
        if self.endereco_execucao_complemento:
            partes.append(self.endereco_execucao_complemento)
        
        partes.append(self.endereco_execucao_bairro)
        partes.append(f"{self.endereco_execucao_cidade}/{self.endereco_execucao_estado}")
        partes.append(f"CEP: {self.endereco_execucao_cep}")
        
        return ", ".join(partes)


# ==============================================================================
# 3. ITEM DO ORÇAMENTO
# ==============================================================================

class OrcamentoItem(models.Model):
    """
    Itens do orçamento (produtos ou serviços).
    Específico para esquadrias: largura, altura, cor, linha, etc.
    """
    
    # Relacionamento
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.CASCADE,
        related_name='itens'
    )
    ordem = models.PositiveIntegerField(
        default=0,
        help_text="Ordem de exibição na proposta"
    )
    
    # Produto ou Descrição Livre
    produto = models.ForeignKey(
        Produto, on_delete=models.PROTECT,
        null=True, blank=True,
        help_text="Produto do cadastro (ou deixe vazio para texto livre)"
    )
    descricao = models.CharField(
        max_length=500,
        help_text="Descrição que aparece na proposta"
    )
    
    # Quantidade e Unidade
    quantidade = models.DecimalField(
        max_digits=15, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))]
    )
    unidade = models.CharField(
        max_length=10, default='UN',
        help_text="UN, M2, ML, KG, CJ, etc"
    )
    
    # Preços
    preco_unitario = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Preço de venda unitário"
    )
    custo_unitario_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Custo estimado unitário (não aparece na proposta)"
    )
    
    # Desconto no Item
    desconto_percentual = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    desconto_valor = models.DecimalField(
        max_digits=15, decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Total do Item (calculado)
    total_item = models.DecimalField(
        max_digits=15, decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Campos Técnicos Específicos para Esquadrias
    largura = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Largura em metros"
    )
    altura = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Altura em metros"
    )
    m2_calculado = models.DecimalField(
        max_digits=10, decimal_places=2, 
        null=True, blank=True,
        help_text="Área calculada (largura x altura)"
    )
    cor = models.CharField(max_length=100, blank=True)
    linha = models.CharField(
        max_length=100, blank=True,
        help_text="Linha do produto (ex: Suprema, Elegance)"
    )
    vidro = models.CharField(
        max_length=100, blank=True,
        help_text="Tipo de vidro (ex: Incolor 4mm, Fumê 6mm)"
    )
    acabamento = models.CharField(
        max_length=100, blank=True,
        help_text="Acabamento (ex: Anodizado, Eletrostático)"
    )
    
    # Observações Técnicas
    observacao_tecnica = models.TextField(
        blank=True,
        help_text="Detalhes técnicos (aparecem na proposta)"
    )
    
    class Meta:
        db_table = 'vendas_orcamento_item'
        verbose_name = 'Item de Orçamento'
        verbose_name_plural = 'Itens de Orçamento'
        ordering = ['orcamento', 'ordem']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.descricao[:50]}"
    
    def save(self, *args, **kwargs):
        """
        Override save para:
        - Copiar dados do produto
        - Calcular m2
        - Calcular total do item
        - Atualizar totais do orçamento
        """
        # Copiar dados do produto se selecionado
        if self.produto:
            if not self.descricao:
                self.descricao = self.produto.descricao
            if not self.unidade:
                self.unidade = self.produto.unidade
            # Preço padrão do produto
            if not self.preco_unitario and hasattr(self.produto, 'preco_venda'):
                self.preco_unitario = self.produto.preco_venda or Decimal('0.00')
        
        # Calcular m2 se largura e altura informadas
        if self.largura and self.altura:
            self.m2_calculado = self.largura * self.altura
        
        # Calcular total do item
        self.calcular_total()
        
        super().save(*args, **kwargs)
        
        # Atualizar totais do orçamento
        self.orcamento.calcular_totais()
        self.orcamento.save()
    
    def delete(self, *args, **kwargs):
        """Override delete para atualizar totais do orçamento"""
        orcamento = self.orcamento
        super().delete(*args, **kwargs)
        
        # Atualizar totais do orçamento
        orcamento.calcular_totais()
        orcamento.save()
    
    def calcular_total(self):
        """Calcula total do item aplicando descontos"""
        subtotal = self.quantidade * self.preco_unitario
        
        # Aplicar desconto (percentual ou valor, nunca os dois)
        desconto = Decimal('0.00')
        if self.desconto_percentual > 0:
            desconto = subtotal * (self.desconto_percentual / 100)
        elif self.desconto_valor > 0:
            desconto = self.desconto_valor
        
        self.total_item = subtotal - desconto
    
    @property
    def margem_estimada_item(self):
        """Margem estimada do item em %"""
        if self.preco_unitario > 0 and self.custo_unitario_estimado > 0:
            lucro = self.preco_unitario - self.custo_unitario_estimado
            return (lucro / self.preco_unitario) * 100
        return Decimal('0.00')


# ==============================================================================
# 4. ANEXOS DO ORÇAMENTO
# ==============================================================================

class OrcamentoAnexo(models.Model):
    """
    Anexos do orçamento: propostas enviadas (PDF), plantas, fotos, etc.
    Versionamento de propostas.
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
    data_envio = models.DateTimeField(
        null=True, blank=True,
        help_text="Data de envio ao cliente"
    )
    enviado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='anexos_enviados'
    )
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='anexos_criados'
    )
    
    class Meta:
        db_table = 'vendas_orcamento_anexo'
        verbose_name = 'Anexo de Orçamento'
        verbose_name_plural = 'Anexos de Orçamentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.orcamento.numero} - {self.descricao}"


# ==============================================================================
# 5. HISTÓRICO DO ORÇAMENTO
# ==============================================================================

class OrcamentoHistorico(models.Model):
    """
    Histórico de mudanças de status e alterações do orçamento.
    Audit trail completo.
    """
    
    orcamento = models.ForeignKey(
        Orcamento, on_delete=models.CASCADE,
        related_name='historico'
    )
    
    status_anterior = models.CharField(max_length=20, blank=True)
    status_novo = models.CharField(max_length=20)
    
    observacao = models.TextField(
        blank=True,
        help_text="Descrição da alteração"
    )
    
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
        if self.status_anterior:
            return f"{self.orcamento.numero} - {self.status_anterior} → {self.status_novo}"
        return f"{self.orcamento.numero} - {self.status_novo}"
