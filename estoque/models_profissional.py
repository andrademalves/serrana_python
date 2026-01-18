"""
MODELS PROFISSIONAIS - SISTEMA DE ESTOQUE FÁBRICA DE ESQUADRIAS
================================================================

Sistema completo de controle de estoque com:
- Custeio WAC (Weighted Average Cost)
- Rastreabilidade de solicitante/entregador
- Integração com Obras e Custos
- Estoque mínimo baseado em consumo real
- Auditoria completa

Autor: Sistema Profissional
Data: Dezembro 2025
"""

from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta

# Imports dos models existentes
from cadastros.models import Pessoa, Produto
# Assumindo que Obra/Projeto existe - ajuste o import conforme necessário
# from projetos.models import Obra
# OU
# from cadastros.models import Obra


# ==============================================================================
# 1. LOCAIS DE ESTOQUE (Físicos)
# ==============================================================================

class LocalEstoque(models.Model):
    """
    Locais físicos de armazenamento.
    Ex: Almoxarifado MP, Produção, PA, Loja, Terceiros, Obra
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
    
    codigo = models.CharField('Código', max_length=20, unique=True, db_index=True)
    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, db_index=True)
    endereco = models.CharField('Endereço', max_length=255, blank=True, null=True)
    
    # Configurações
    permite_saldo_negativo = models.BooleanField('Permite Saldo Negativo', default=False)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Responsável (funcionário)
    responsavel = models.ForeignKey(
        Pessoa, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        limit_choices_to={'funcionario': True},
        related_name='locais_responsavel',
        verbose_name='Responsável'
    )
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='locais_estoque_criados',
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locais_estoque_atualizados',
        verbose_name='Atualizado por'
    )
    
    class Meta:
        db_table = 'locais_estoque'
        verbose_name = 'Local de Estoque'
        verbose_name_plural = 'Locais de Estoque'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['tipo', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.upper().strip()


# ==============================================================================
# 2. DESTINOS DE ESTOQUE (Finalidades)
# ==============================================================================

class DestinoEstoque(models.Model):
    """
    Finalidade/Motivo da saída de estoque.
    Ex: Obra, Loja, Perda/Sucata, Amostra, Manutenção
    """
    codigo = models.CharField('Código', max_length=20, unique=True, db_index=True)
    nome = models.CharField('Nome', max_length=100)
    descricao = models.TextField('Descrição', blank=True, null=True)
    
    # Configurações de comportamento
    exige_obra = models.BooleanField(
        'Exige Obra', 
        default=False,
        help_text='Se marcado, saídas com este destino devem ter uma obra informada'
    )
    gera_custo_obra = models.BooleanField(
        'Gera Custo na Obra', 
        default=True,
        help_text='Se marcado, cria lançamento automático em CustoObra'
    )
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='destinos_estoque_criados',
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='destinos_estoque_atualizados',
        verbose_name='Atualizado por'
    )
    
    class Meta:
        db_table = 'destinos_estoque'
        verbose_name = 'Destino de Estoque'
        verbose_name_plural = 'Destinos de Estoque'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.upper().strip()


# ==============================================================================
# 3. MOVIMENTO DE ESTOQUE (Tabela Central)
# ==============================================================================

class MovimentoEstoque(models.Model):
    """
    Registro de TODAS as movimentações de estoque.
    Tabela central/histórico IMUTÁVEL (não permite edição após criação).
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
    tipo_movimento = models.CharField(
        'Tipo de Movimento',
        max_length=20,
        choices=TIPO_MOVIMENTO_CHOICES,
        db_index=True
    )
    documento = models.CharField(
        'Nº Documento',
        max_length=50,
        db_index=True,
        help_text='Nº NF, Nº Requisição, etc'
    )
    documento_tipo = models.CharField(
        'Tipo de Documento',
        max_length=20,
        choices=DOCUMENTO_TIPO_CHOICES
    )
    data_operacao = models.DateTimeField('Data da Operação', db_index=True)
    
    # Produto
    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='movimentos_estoque',
        verbose_name='Produto'
    )
    
    # Locais (origem/destino físico)
    local_origem = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentos_origem',
        verbose_name='Local de Origem'
    )
    local_destino = models.ForeignKey(
        LocalEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentos_destino',
        verbose_name='Local de Destino'
    )
    
    # Destino (finalidade) - obrigatório em SAIDA
    destino = models.ForeignKey(
        DestinoEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentos',
        verbose_name='Destino/Finalidade'
    )
    
    # Obra (se destino exigir ou se for saída para obra)
    # AJUSTE: descomente e ajuste o import conforme seu projeto
    # obra = models.ForeignKey(
    #     'projetos.Obra',  # ou 'cadastros.Obra'
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name='movimentos_estoque',
    #     verbose_name='Obra/Projeto'
    # )
    obra = models.CharField(
        'Obra/Projeto',
        max_length=100,
        blank=True,
        null=True,
        help_text='TEMPORÁRIO: substituir por FK quando model Obra estiver pronto'
    )
    
    # Quantidade e Custos
    quantidade = models.DecimalField(
        'Quantidade',
        max_digits=12,
        decimal_places=3
    )
    custo_unitario_aplicado = models.DecimalField(
        'Custo Unitário',
        max_digits=12,
        decimal_places=4,
        help_text='Custo na entrada ou custo médio na saída'
    )
    custo_total = models.DecimalField(
        'Custo Total',
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    # Fornecedor (em ENTRADA)
    fornecedor = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'fornecedor': True},
        related_name='entradas_estoque',
        verbose_name='Fornecedor'
    )
    
    # =========================================================================
    # CONTROLE DE PESSOAS: Solicitante e Entregador
    # =========================================================================
    solicitante = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'funcionario': True},
        related_name='requisicoes_solicitadas',
        verbose_name='Funcionário Solicitante',
        help_text='Quem solicitou a retirada/material'
    )
    entregador = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'funcionario': True},
        related_name='entregas_realizadas',
        verbose_name='Funcionário Entregador/Almoxarife',
        help_text='Quem entregou/liberou o material'
    )
    
    # Observações
    observacao = models.TextField('Observações', blank=True, null=True)
    
    # Estorno
    movimento_origem = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='estornos',
        verbose_name='Movimento Original (para estorno)'
    )
    estornado = models.BooleanField('Estornado', default=False, db_index=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimentos_estoque_criados',
        verbose_name='Usuário que Registrou'
    )
    
    class Meta:
        db_table = 'movimentos_estoque'
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'
        ordering = ['-data_operacao', '-criado_em']
        indexes = [
            models.Index(fields=['tipo_movimento', 'data_operacao']),
            models.Index(fields=['produto', 'data_operacao']),
            models.Index(fields=['documento']),
            models.Index(fields=['local_origem']),
            models.Index(fields=['local_destino']),
            models.Index(fields=['solicitante']),
            models.Index(fields=['entregador']),
            models.Index(fields=['estornado']),
        ]
    
    def __str__(self):
        return f"{self.tipo_movimento} - {self.documento} - {self.produto.descricao}"
    
    def clean(self):
        """Validações de negócio"""
        errors = {}
        
        # ENTRADA: deve ter local_destino, não deve ter local_origem
        if self.tipo_movimento == 'ENTRADA':
            if not self.local_destino:
                errors['local_destino'] = 'Entrada deve ter local de destino.'
            if self.local_origem:
                errors['local_origem'] = 'Entrada não deve ter local de origem.'
            if not self.fornecedor:
                errors['fornecedor'] = 'Entrada deve ter fornecedor informado.'
            if self.custo_unitario_aplicado <= 0:
                errors['custo_unitario_aplicado'] = 'Custo unitário deve ser maior que zero.'
        
        # SAIDA: deve ter local_origem, destino; não deve ter local_destino
        elif self.tipo_movimento == 'SAIDA':
            if not self.local_origem:
                errors['local_origem'] = 'Saída deve ter local de origem.'
            if not self.destino:
                errors['destino'] = 'Saída deve ter um destino/finalidade.'
            if self.local_destino:
                errors['local_destino'] = 'Saída não deve ter local de destino (use destino).'
            
            # Se destino exige obra, obra deve estar preenchida
            if self.destino and self.destino.exige_obra and not self.obra:
                errors['obra'] = f'Destino "{self.destino.nome}" exige que uma obra seja informada.'
        
        # TRANSFERENCIA: deve ter origem e destino, e não podem ser iguais
        elif self.tipo_movimento == 'TRANSFERENCIA':
            if not self.local_origem or not self.local_destino:
                errors['local_destino'] = 'Transferência deve ter local de origem e destino.'
            if self.local_origem and self.local_destino and self.local_origem == self.local_destino:
                errors['local_destino'] = 'Local de origem e destino não podem ser iguais.'
        
        # Quantidade deve ser positiva
        if self.quantidade <= 0:
            errors['quantidade'] = 'Quantidade deve ser maior que zero.'
        
        if errors:
            raise ValidationError(errors)
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Salvar movimento e atualizar saldos automaticamente.
        """
        # Calcular custo total
        self.custo_total = self.quantidade * self.custo_unitario_aplicado
        
        # Validar
        self.full_clean()
        
        # Verificar se é novo movimento
        is_new = self.pk is None
        
        # Salvar o movimento
        super().save(*args, **kwargs)
        
        # Se é novo movimento, atualizar saldos
        if is_new:
            self._atualizar_saldos()
            
            # Se saída para obra que gera custo, criar CustoObra
            if (self.tipo_movimento == 'SAIDA' and 
                self.obra and 
                self.destino and 
                self.destino.gera_custo_obra):
                self._gerar_custo_obra()
    
    def _atualizar_saldos(self):
        """
        Atualiza saldos de estoque com base no tipo de movimento.
        Implementa lógica WAC (Weighted Average Cost) para entradas.
        """
        if self.tipo_movimento == 'ENTRADA':
            self._processar_entrada()
        
        elif self.tipo_movimento == 'SAIDA':
            self._processar_saida()
        
        elif self.tipo_movimento == 'TRANSFERENCIA':
            self._processar_transferencia()
        
        elif self.tipo_movimento == 'AJUSTE':
            self._processar_ajuste()
        
        elif self.tipo_movimento == 'ESTORNO':
            self._processar_estorno()
    
    def _processar_entrada(self):
        """
        ENTRADA: Aumenta saldo e recalcula custo médio (WAC).
        
        Fórmula WAC:
        Custo Médio Novo = (Valor Estoque Anterior + Valor Entrada) / Qtd Total
        """
        saldo, created = SaldoEstoque.objects.get_or_create(
            produto=self.produto,
            local=self.local_destino,
            defaults={'saldo_quantidade': 0, 'custo_medio': 0}
        )
        
        # Calcular WAC
        qtd_anterior = saldo.saldo_quantidade
        custo_anterior = saldo.custo_medio
        valor_anterior = qtd_anterior * custo_anterior
        
        qtd_entrada = self.quantidade
        custo_entrada = self.custo_unitario_aplicado
        valor_entrada = qtd_entrada * custo_entrada
        
        qtd_nova = qtd_anterior + qtd_entrada
        valor_total = valor_anterior + valor_entrada
        
        # Atualizar saldo
        saldo.saldo_quantidade = qtd_nova
        if qtd_nova > 0:
            saldo.custo_medio = (valor_total / qtd_nova).quantize(Decimal('0.0001'))
        else:
            saldo.custo_medio = Decimal('0')
        
        saldo.save()
    
    def _processar_saida(self):
        """
        SAIDA: Reduz saldo usando custo médio vigente.
        Não recalcula custo médio.
        """
        try:
            saldo = SaldoEstoque.objects.get(
                produto=self.produto,
                local=self.local_origem
            )
        except SaldoEstoque.DoesNotExist:
            raise ValidationError(
                f'Produto {self.produto.descricao} não possui saldo no local {self.local_origem.nome}'
            )
        
        # Verificar saldo disponível
        if saldo.saldo_quantidade < self.quantidade:
            if not self.local_origem.permite_saldo_negativo:
                raise ValidationError(
                    f'Saldo insuficiente. Disponível: {saldo.saldo_quantidade} {self.produto.unidade}'
                )
        
        # Atualizar custo unitário aplicado com custo médio vigente
        self.custo_unitario_aplicado = saldo.custo_medio
        self.custo_total = self.quantidade * self.custo_unitario_aplicado
        
        # Reduzir saldo
        saldo.saldo_quantidade -= self.quantidade
        saldo.save()
    
    def _processar_transferencia(self):
        """
        TRANSFERENCIA: Move quantidade entre locais.
        Mantém custo médio (não recalcula).
        """
        # Reduzir saldo na origem
        try:
            saldo_origem = SaldoEstoque.objects.get(
                produto=self.produto,
                local=self.local_origem
            )
        except SaldoEstoque.DoesNotExist:
            raise ValidationError(
                f'Produto {self.produto.descricao} não possui saldo no local {self.local_origem.nome}'
            )
        
        # Verificar saldo disponível
        if saldo_origem.saldo_quantidade < self.quantidade:
            if not self.local_origem.permite_saldo_negativo:
                raise ValidationError(
                    f'Saldo insuficiente na origem. Disponível: {saldo_origem.saldo_quantidade} {self.produto.unidade}'
                )
        
        # Usar custo médio da origem
        custo_medio_origem = saldo_origem.custo_medio
        self.custo_unitario_aplicado = custo_medio_origem
        self.custo_total = self.quantidade * custo_medio_origem
        
        # Atualizar origem
        saldo_origem.saldo_quantidade -= self.quantidade
        saldo_origem.save()
        
        # Aumentar saldo no destino
        saldo_destino, created = SaldoEstoque.objects.get_or_create(
            produto=self.produto,
            local=self.local_destino,
            defaults={'saldo_quantidade': 0, 'custo_medio': 0}
        )
        
        # Recalcular custo médio no destino (como uma entrada)
        qtd_anterior = saldo_destino.saldo_quantidade
        custo_anterior = saldo_destino.custo_medio
        valor_anterior = qtd_anterior * custo_anterior
        
        qtd_entrada = self.quantidade
        valor_entrada = qtd_entrada * custo_medio_origem
        
        qtd_nova = qtd_anterior + qtd_entrada
        valor_total = valor_anterior + valor_entrada
        
        saldo_destino.saldo_quantidade = qtd_nova
        if qtd_nova > 0:
            saldo_destino.custo_medio = (valor_total / qtd_nova).quantize(Decimal('0.0001'))
        
        saldo_destino.save()
    
    def _processar_ajuste(self):
        """
        AJUSTE: Ajusta saldo para quantidade informada.
        Pode ser positivo (aumenta) ou negativo (reduz).
        """
        local = self.local_destino or self.local_origem
        if not local:
            raise ValidationError('Ajuste deve ter um local informado.')
        
        saldo, created = SaldoEstoque.objects.get_or_create(
            produto=self.produto,
            local=local,
            defaults={'saldo_quantidade': 0, 'custo_medio': 0}
        )
        
        # Diferença = quantidade no movimento (positiva = aumenta, negativa = reduz)
        diferenca = self.quantidade
        
        # Atualizar saldo
        saldo.saldo_quantidade += diferenca
        
        # Se há custo informado e quantidade aumentou, recalcular custo médio
        if diferenca > 0 and self.custo_unitario_aplicado > 0:
            qtd_anterior = saldo.saldo_quantidade - diferenca
            custo_anterior = saldo.custo_medio
            valor_anterior = qtd_anterior * custo_anterior
            
            valor_entrada = diferenca * self.custo_unitario_aplicado
            qtd_nova = saldo.saldo_quantidade
            valor_total = valor_anterior + valor_entrada
            
            if qtd_nova > 0:
                saldo.custo_medio = (valor_total / qtd_nova).quantize(Decimal('0.0001'))
        
        saldo.save()
    
    def _processar_estorno(self):
        """
        ESTORNO: Reverte movimento original.
        """
        if not self.movimento_origem:
            raise ValidationError('Estorno deve ter um movimento de origem.')
        
        # Marcar movimento original como estornado
        movimento_original = self.movimento_origem
        movimento_original.estornado = True
        movimento_original.save()
        
        # Reverter saldo conforme tipo do movimento original
        if movimento_original.tipo_movimento == 'ENTRADA':
            # Era entrada: agora é saída
            self._processar_saida()
        
        elif movimento_original.tipo_movimento == 'SAIDA':
            # Era saída: agora é entrada (devolução)
            self._processar_entrada()
        
        elif movimento_original.tipo_movimento == 'TRANSFERENCIA':
            # Reverter transferência
            # Origem vira destino e vice-versa
            self._processar_transferencia()
    
    def _gerar_custo_obra(self):
        """
        Gera lançamento automático em CustoObra quando saída para obra.
        """
        # TEMPORÁRIO: implementar quando model CustoObra estiver pronto
        # CustoObra.objects.create(
        #     obra=self.obra,
        #     data=self.data_operacao.date(),
        #     categoria='MATERIAL',
        #     origem='ESTOQUE',
        #     descricao=f'{self.produto.descricao} - {self.quantidade} {self.produto.unidade}',
        #     valor=self.custo_total,
        #     movimento_estoque=self,
        #     criado_por=self.criado_por
        # )
        pass


# ==============================================================================
# 4. SALDO DE ESTOQUE (Cache/Performance)
# ==============================================================================

class SaldoEstoque(models.Model):
    """
    Saldo de estoque por (produto, local).
    Atualizado automaticamente pelos movimentos.
    NÃO EDITAR MANUALMENTE - usar MovimentoEstoque tipo AJUSTE.
    """
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='saldos_estoque',
        verbose_name='Produto'
    )
    local = models.ForeignKey(
        LocalEstoque,
        on_delete=models.CASCADE,
        related_name='saldos',
        verbose_name='Local'
    )
    
    saldo_quantidade = models.DecimalField(
        'Saldo Quantidade',
        max_digits=12,
        decimal_places=3,
        default=0
    )
    custo_medio = models.DecimalField(
        'Custo Médio (WAC)',
        max_digits=12,
        decimal_places=4,
        default=0,
        help_text='Custo médio ponderado (Weighted Average Cost)'
    )
    
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'saldos_estoque'
        verbose_name = 'Saldo de Estoque'
        verbose_name_plural = 'Saldos de Estoque'
        unique_together = [['produto', 'local']]
        indexes = [
            models.Index(fields=['produto', 'local']),
            models.Index(fields=['saldo_quantidade']),
        ]
    
    def __str__(self):
        return f"{self.produto.descricao} - {self.local.nome}: {self.saldo_quantidade}"
    
    @property
    def valor_total(self):
        """Valor total do saldo (quantidade * custo médio)"""
        return self.saldo_quantidade * self.custo_medio


# ==============================================================================
# 5. CUSTOS DE OBRA (Integração)
# ==============================================================================

class CustoObra(models.Model):
    """
    Registro de custos de uma obra.
    Origem: estoque (automático), terceiros, manual, impostos, etc.
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
    
    # AJUSTE: descomente e ajuste o import quando Obra estiver pronto
    # obra = models.ForeignKey(
    #     'projetos.Obra',
    #     on_delete=models.PROTECT,
    #     related_name='custos',
    #     verbose_name='Obra/Projeto'
    # )
    obra = models.CharField(
        'Obra/Projeto',
        max_length=100,
        help_text='TEMPORÁRIO: substituir por FK quando model Obra estiver pronto'
    )
    
    data = models.DateField('Data', db_index=True)
    
    # Classificação
    categoria = models.CharField('Categoria', max_length=20, choices=CATEGORIA_CHOICES, db_index=True)
    origem = models.CharField('Origem', max_length=20, choices=ORIGEM_CHOICES, db_index=True)
    
    # Descrição
    descricao = models.CharField('Descrição', max_length=255)
    
    # Valor
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    
    # Vínculos
    movimento_estoque = models.ForeignKey(
        MovimentoEstoque,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='custos_obra',
        verbose_name='Movimento de Estoque Origem'
    )
    fornecedor = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'fornecedor': True},
        related_name='custos_obras',
        verbose_name='Fornecedor'
    )
    documento = models.CharField('Documento', max_length=50, blank=True, null=True)
    
    # Observações
    observacao = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='custos_obra_criados',
        verbose_name='Criado por'
    )
    
    class Meta:
        db_table = 'custos_obra'
        verbose_name = 'Custo de Obra'
        verbose_name_plural = 'Custos de Obras'
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data']),
            models.Index(fields=['categoria']),
            models.Index(fields=['origem']),
        ]
    
    def __str__(self):
        return f"{self.obra} - {self.descricao}: R$ {self.valor}"


# ==============================================================================
# 6. PRODUTO x FORNECEDOR (Múltiplos - FASE 2)
# ==============================================================================

class ProdutoFornecedor(models.Model):
    """
    Relacionamento produto x fornecedor (múltiplos).
    Permite manter histórico de fornecedores e condições.
    FASE 2 - por enquanto usa Produto.fornecedor como padrão.
    """
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='fornecedores_adicionais',
        verbose_name='Produto'
    )
    fornecedor = models.ForeignKey(
        Pessoa,
        on_delete=models.PROTECT,
        limit_choices_to={'fornecedor': True},
        related_name='produtos_fornecidos',
        verbose_name='Fornecedor'
    )
    
    codigo_no_fornecedor = models.CharField(
        'Código no Fornecedor',
        max_length=50,
        blank=True,
        null=True
    )
    prazo_entrega_dias = models.IntegerField('Prazo Entrega (dias)', default=0)
    
    # Histórico de compras
    custo_ultima_compra = models.DecimalField(
        'Custo Última Compra',
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True
    )
    data_ultima_compra = models.DateField('Data Última Compra', null=True, blank=True)
    
    # Configurações
    preferencial = models.BooleanField(
        'Preferencial',
        default=False,
        help_text='Fornecedor preferencial para este produto'
    )
    ativo = models.BooleanField('Ativo', default=True)
    
    # Observações
    observacao = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='produto_fornecedor_criados',
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'produto_fornecedor'
        verbose_name = 'Produto x Fornecedor'
        verbose_name_plural = 'Produtos x Fornecedores'
        unique_together = [['produto', 'fornecedor']]
        ordering = ['produto', '-preferencial', 'fornecedor']
        indexes = [
            models.Index(fields=['produto', 'preferencial', 'ativo']),
        ]
    
    def __str__(self):
        pref = " (PREFERENCIAL)" if self.preferencial else ""
        return f"{self.produto.codigo} - {self.fornecedor.nome_razao_social}{pref}"
