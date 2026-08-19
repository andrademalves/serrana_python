from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction


# ===================================
# MODELOS DE CADASTROS AUXILIARES
# ===================================

class GrupoItem(models.Model):
    """Grupos/Categorias de itens (ex: Perfis de Alumínio, Vidros, Acessórios)"""
    codigo = models.CharField('Código', max_length=20, unique=True)
    descricao = models.CharField('Descrição', max_length=100)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='grupos_item_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'grupos_item'
        verbose_name = 'Grupo de Item'
        verbose_name_plural = 'Grupos de Itens'
        ordering = ['descricao']
        indexes = [
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class LocalEstoque(models.Model):
    """Locais físicos onde o estoque é armazenado (Depósitos/Almoxarifados)"""
    codigo = models.CharField('Código', max_length=20, unique=True)
    descricao = models.CharField('Descrição', max_length=100)
    endereco = models.CharField('Endereço', max_length=255, blank=True, null=True)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='locais_responsavel', verbose_name='Responsável')
    permite_saldo_negativo = models.BooleanField('Permite Saldo Negativo', default=False, help_text='Se marcado, permite saídas mesmo sem saldo suficiente')
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='locais_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'locais_estoque'
        verbose_name = 'Local de Estoque'
        verbose_name_plural = 'Locais de Estoque'
        ordering = ['descricao']
        indexes = [
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class DestinoEstoque(models.Model):
    """Destinos/Finalidades das saídas de estoque"""
    TIPO_CHOICES = [
        ('PRODUCAO', 'Produção'),
        ('PROJETO', 'Projeto/Obra'),
        ('LOJA', 'Loja/Pronta Entrega'),
        ('MANUTENCAO', 'Manutenção'),
        ('AMOSTRA', 'Amostra'),
        ('PERDA', 'Perda/Sucata'),
        ('DEVOLUCAO', 'Devolução'),
        ('OUTROS', 'Outros'),
    ]
    
    codigo = models.CharField('Código', max_length=20, unique=True)
    descricao = models.CharField('Descrição', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    controla_custo = models.BooleanField('Controla Custo', default=True, help_text='Se marcado, o custo será lançado no destino (projeto, etc)')
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='destinos_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'destinos_estoque'
        verbose_name = 'Destino de Estoque'
        verbose_name_plural = 'Destinos de Estoque'
        ordering = ['descricao']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['tipo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# ===================================
# MODELO DE ITENS
# ===================================

class Item(models.Model):
    """
    Cadastro de Itens de Estoque (Matéria-Prima, Produto Acabado, Semi-Acabado, Consumível)
    """
    TIPO_CHOICES = [
        ('MP', 'Matéria-Prima'),
        ('PA', 'Produto Acabado'),
        ('SEMI', 'Semi-Acabado'),
        ('CONSUMIVEL', 'Consumível'),
    ]
    
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('KG', 'Quilograma'),
        ('MT', 'Metro'),
        ('M2', 'Metro Quadrado'),
        ('M3', 'Metro Cúbico'),
        ('LT', 'Litro'),
        ('CX', 'Caixa'),
        ('PCT', 'Pacote'),
        ('PC', 'Peça'),
        ('BAR', 'Barra'),
        ('CHAPA', 'Chapa'),
    ]
    
    MATERIAL_CHOICES = [
        ('ALUMINIO', 'Alumínio'),
        ('FERRO', 'Ferro'),
        ('ACO', 'Aço'),
        ('VIDRO', 'Vidro'),
        ('MADEIRA', 'Madeira'),
        ('PLASTICO', 'Plástico'),
        ('BORRACHA', 'Borracha'),
        ('OUTROS', 'Outros'),
    ]
    
    # Identificação
    codigo = models.CharField('Código', max_length=50, unique=True, db_index=True, default='AUTO')
    descricao = models.CharField('Descrição', max_length=255, db_index=True)
    tipo_item = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES, default='MP', db_index=True)
    grupo = models.ForeignKey(GrupoItem, on_delete=models.PROTECT, related_name='itens', verbose_name='Grupo', null=True, blank=True)
    
    # Especificações
    material = models.CharField('Material', max_length=20, choices=MATERIAL_CHOICES, blank=True, null=True)
    marca = models.CharField('Marca', max_length=100, blank=True, null=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True, null=True)
    cor = models.CharField('Cor', max_length=50, blank=True, null=True)
    unidade_medida = models.CharField('Unidade de Medida', max_length=10, choices=UNIDADE_CHOICES, default='UN')
    
    # Controle de Estoque
    estoque_minimo = models.DecimalField('Estoque Mínimo', max_digits=12, decimal_places=3, default=0.000)
    estoque_maximo = models.DecimalField('Estoque Máximo', max_digits=12, decimal_places=3, default=0.000, blank=True, null=True)
    
    # Outros
    ncm = models.CharField('NCM', max_length=20, blank=True, null=True, help_text='Nomenclatura Comum do Mercosul')
    codigo_barras = models.CharField('Código de Barras', max_length=50, blank=True, null=True)
    foto = models.ImageField('Foto', upload_to='estoque/itens/', blank=True, null=True, help_text='Imagem do item')
    url_foto = models.CharField('URL Foto', max_length=500, blank=True, null=True, help_text='Alternativa: URL externa da foto')
    ativo = models.BooleanField('Ativo', default=True)
    status_ativo = models.BooleanField('Status Ativo', default=True)  # Compatibilidade com banco legado
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='itens_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='itens_atualizados', verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'itens'
        verbose_name = 'Item'
        verbose_name_plural = 'Itens'
        ordering = ['descricao']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['descricao']),
            models.Index(fields=['tipo_item']),
            models.Index(fields=['ativo']),
        ]
    
    def save(self, *args, **kwargs):
        """Gera código único automaticamente se for AUTO"""
        # Se for um novo registro e o código é AUTO, gera temporariamente um código único
        is_new = self.pk is None
        if is_new and self.codigo == 'AUTO':
            # Gera um código temporário único com timestamp para evitar duplicata
            import time
            self.codigo = f'TEMP-{int(time.time() * 1000000)}'
        
        # Salva o registro
        super().save(*args, **kwargs)
        
        # Se era AUTO, agora atualiza com o código definitivo baseado no ID
        if is_new and self.codigo.startswith('TEMP-'):
            self.codigo = f'ITEM-{self.id:05d}'
            super().save(update_fields=['codigo'])

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    def get_saldo_total(self):
        """Retorna saldo total do item em todos os locais"""
        return self.saldos.aggregate(total=models.Sum('quantidade'))['total'] or Decimal('0.000')
    
    def get_custo_medio_ponderado(self):
        """Retorna custo médio ponderado considerando todos os locais"""
        saldos = self.saldos.filter(quantidade__gt=0)
        if not saldos.exists():
            return Decimal('0.0000')
        
        total_valor = sum(s.quantidade * s.custo_medio for s in saldos)
        total_quantidade = sum(s.quantidade for s in saldos)
        
        if total_quantidade > 0:
            return (total_valor / total_quantidade).quantize(Decimal('0.0001'))
        return Decimal('0.0000')


# ===================================
# MODELO DE SALDOS POR LOCAL
# ===================================

class SaldoEstoque(models.Model):
    """
    Saldo de estoque por item e local (tabela de performance/consulta)
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='saldos', verbose_name='Item')
    local = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE, related_name='saldos', verbose_name='Local')
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=0.000)
    custo_medio = models.DecimalField('Custo Médio (WAC)', max_digits=12, decimal_places=4, default=0.0000, help_text='Weighted Average Cost')
    
    # Auditoria
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'saldos_estoque'
        verbose_name = 'Saldo de Estoque'
        verbose_name_plural = 'Saldos de Estoque'
        unique_together = [['item', 'local']]
        indexes = [
            models.Index(fields=['item', 'local']),
            models.Index(fields=['item']),
            models.Index(fields=['local']),
            models.Index(fields=['quantidade']),
        ]
    
    def __str__(self):
        return f"{self.item.codigo} @ {self.local.codigo}: {self.quantidade} {self.item.unidade_medida}"
    
    @property
    def valor_total(self):
        """Valor total do saldo (quantidade * custo médio)"""
        return self.quantidade * self.custo_medio


# ===================================
# MODELO DE MOVIMENTAÇÕES
# ===================================

class MovimentoEstoque(models.Model):
    """
    Registro de todas as movimentações de estoque (tabela central/histórico)
    """
    TIPO_MOVIMENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('TRANSFERENCIA', 'Transferência'),
        ('AJUSTE', 'Ajuste/Inventário'),
        ('ESTORNO', 'Estorno'),
    ]
    
    DOCUMENTO_TIPO_CHOICES = [
        ('NF', 'Nota Fiscal'),
        ('REQ', 'Requisição'),
        ('OP', 'Ordem de Produção'),
        ('INV', 'Inventário'),
        ('DEV', 'Devolução'),
        ('TRF', 'Transferência'),
        ('OUT', 'Outros'),
    ]
    
    # Identificação do Movimento
    tipo_movimento = models.CharField('Tipo de Movimento', max_length=20, choices=TIPO_MOVIMENTO_CHOICES, db_index=True)
    documento = models.CharField('Nº Documento', max_length=50, blank=True, null=True, db_index=True)
    documento_tipo = models.CharField('Tipo Documento', max_length=10, choices=DOCUMENTO_TIPO_CHOICES, blank=True, null=True)
    data_movimento = models.DateTimeField('Data/Hora do Movimento', db_index=True)
    
    # Item
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='movimentos', verbose_name='Item')
    
    # Locais (Origem e Destino)
    local_origem = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT, related_name='movimentos_origem', verbose_name='Local Origem', null=True, blank=True)
    local_destino = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT, related_name='movimentos_destino', verbose_name='Local Destino', null=True, blank=True)
    
    # Destino/Finalidade da Saída
    destino = models.ForeignKey(DestinoEstoque, on_delete=models.PROTECT, related_name='movimentos', verbose_name='Destino', null=True, blank=True, help_text='Finalidade da saída')
    
    # Projeto (se for saída para projeto)
    projeto = models.ForeignKey('projetos.Projeto', on_delete=models.PROTECT, related_name='movimentos_estoque', verbose_name='Projeto', null=True, blank=True)
    
    # Fornecedor (se for entrada)
    fornecedor = models.ForeignKey('cadastros.Pessoa', on_delete=models.PROTECT, related_name='movimentos_estoque', verbose_name='Fornecedor', null=True, blank=True, limit_choices_to={'tipo_pessoa__fornecedor': True})
    
    # Quantidade e Valores
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3)
    custo_unitario = models.DecimalField('Custo Unitário', max_digits=12, decimal_places=4, default=0.0000, help_text='Custo na entrada ou custo médio na saída')
    custo_total = models.DecimalField('Custo Total', max_digits=12, decimal_places=2, default=0.00)
    
    # Referências
    solicitante = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentos_solicitados', verbose_name='Solicitante')
    solicitante_material = models.ForeignKey('cadastros.Pessoa', on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais_solicitados', verbose_name='Quem Solicitou o Material')
    liberado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimentos_liberados', verbose_name='Liberado Por')
    movimento_estornado = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='estornos', verbose_name='Movimento Estornado', help_text='Referência ao movimento que está sendo estornado')
    
    # Observações
    observacao = models.TextField('Observação', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='movimentos_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'movimentos_estoque'
        verbose_name = 'Movimento de Estoque'
        verbose_name_plural = 'Movimentos de Estoque'
        ordering = ['-data_movimento', '-criado_em']
        indexes = [
            models.Index(fields=['tipo_movimento']),
            models.Index(fields=['data_movimento']),
            models.Index(fields=['documento']),
            models.Index(fields=['item']),
            models.Index(fields=['local_origem']),
            models.Index(fields=['local_destino']),
            models.Index(fields=['projeto']),
            models.Index(fields=['-data_movimento']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_movimento_display()} - {self.item.codigo} - {self.quantidade}"
    
    def clean(self):
        """Validações do modelo"""
        # Validação de locais conforme tipo de movimento
        if self.tipo_movimento == 'ENTRADA':
            if not self.local_destino:
                raise ValidationError('Entrada deve ter Local Destino.')
            if self.local_origem:
                raise ValidationError('Entrada não deve ter Local Origem.')
        
        elif self.tipo_movimento == 'SAIDA':
            if not self.local_origem:
                raise ValidationError('Saída deve ter Local Origem.')
            if self.local_destino:
                raise ValidationError('Saída não deve ter Local Destino.')
            if not self.destino:
                raise ValidationError('Saída deve ter um Destino/Finalidade.')
        
        elif self.tipo_movimento == 'TRANSFERENCIA':
            if not self.local_origem or not self.local_destino:
                raise ValidationError('Transferência deve ter Local Origem e Local Destino.')
            if self.local_origem == self.local_destino:
                raise ValidationError('Local Origem e Destino não podem ser iguais em Transferência.')
        
        elif self.tipo_movimento == 'AJUSTE':
            if not self.local_destino and not self.local_origem:
                raise ValidationError('Ajuste deve ter um Local.')
        
        elif self.tipo_movimento == 'ESTORNO':
            if not self.movimento_estornado:
                raise ValidationError('Estorno deve referenciar o movimento original.')
    
    def save(self, *args, **kwargs):
        # Calcular custo total
        self.custo_total = self.quantidade * self.custo_unitario
        
        # Validar antes de salvar
        self.full_clean()
        
        # Se é novo movimento, atualizar saldos
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._atualizar_saldos()
    
    @transaction.atomic
    def _atualizar_saldos(self):
        """Atualiza saldos de estoque conforme tipo de movimento"""
        
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
        """Processa entrada de estoque (atualiza saldo e custo médio - WAC)"""
        saldo, created = SaldoEstoque.objects.get_or_create(
            item=self.item,
            local=self.local_destino,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        # Calcular novo custo médio ponderado (WAC - Weighted Average Cost)
        if self.custo_unitario > 0:
            quantidade_anterior = saldo.quantidade
            valor_anterior = quantidade_anterior * saldo.custo_medio
            valor_entrada = self.quantidade * self.custo_unitario
            quantidade_nova = quantidade_anterior + self.quantidade
            
            if quantidade_nova > 0:
                saldo.custo_medio = ((valor_anterior + valor_entrada) / quantidade_nova).quantize(Decimal('0.0001'))
        
        # Atualizar quantidade
        saldo.quantidade += self.quantidade
        saldo.save()
    
    def _processar_saida(self):
        """Processa saída de estoque (usa custo médio vigente)"""
        try:
            saldo = SaldoEstoque.objects.get(item=self.item, local=self.local_origem)
        except SaldoEstoque.DoesNotExist:
            raise ValidationError(f'Item {self.item.codigo} não possui saldo no local {self.local_origem.codigo}.')
        
        # Verificar se há saldo suficiente
        if not self.local_origem.permite_saldo_negativo:
            if saldo.quantidade < self.quantidade:
                raise ValidationError(
                    f'Saldo insuficiente. Disponível: {saldo.quantidade} {self.item.unidade_medida}. '
                    f'Solicitado: {self.quantidade} {self.item.unidade_medida}.'
                )
        
        # Aplicar custo médio vigente se não foi informado
        if self.custo_unitario == 0:
            self.custo_unitario = saldo.custo_medio
            self.custo_total = self.quantidade * self.custo_unitario
            self.save(update_fields=['custo_unitario', 'custo_total'])
        
        # Reduzir saldo
        saldo.quantidade -= self.quantidade
        saldo.save()
        
        # Se for saída para projeto, registrar custo no projeto
        if self.projeto and self.destino and self.destino.controla_custo:
            self._lancar_custo_projeto()
    
    def _processar_transferencia(self):
        """Processa transferência entre locais"""
        # Sair do local origem
        try:
            saldo_origem = SaldoEstoque.objects.get(item=self.item, local=self.local_origem)
        except SaldoEstoque.DoesNotExist:
            raise ValidationError(f'Item {self.item.codigo} não possui saldo no local origem {self.local_origem.codigo}.')
        
        # Verificar saldo
        if not self.local_origem.permite_saldo_negativo:
            if saldo_origem.quantidade < self.quantidade:
                raise ValidationError(f'Saldo insuficiente no local origem.')
        
        # Usar custo médio da origem
        custo_transferencia = saldo_origem.custo_medio
        saldo_origem.quantidade -= self.quantidade
        saldo_origem.save()
        
        # Entrar no local destino
        saldo_destino, created = SaldoEstoque.objects.get_or_create(
            item=self.item,
            local=self.local_destino,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        # Calcular novo custo médio no destino
        quantidade_anterior = saldo_destino.quantidade
        valor_anterior = quantidade_anterior * saldo_destino.custo_medio
        valor_transferido = self.quantidade * custo_transferencia
        quantidade_nova = quantidade_anterior + self.quantidade
        
        if quantidade_nova > 0:
            saldo_destino.custo_medio = ((valor_anterior + valor_transferido) / quantidade_nova).quantize(Decimal('0.0001'))
        
        saldo_destino.quantidade += self.quantidade
        saldo_destino.save()
        
        # Atualizar custo unitário do movimento
        if self.custo_unitario == 0:
            self.custo_unitario = custo_transferencia
            self.custo_total = self.quantidade * self.custo_unitario
            self.save(update_fields=['custo_unitario', 'custo_total'])
    
    def _processar_ajuste(self):
        """Processa ajuste/inventário de estoque"""
        # Ajuste pode ser positivo ou negativo
        local = self.local_destino or self.local_origem
        
        saldo, created = SaldoEstoque.objects.get_or_create(
            item=self.item,
            local=local,
            defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
        )
        
        # No ajuste, a quantidade pode ser positiva (aumento) ou negativa (redução)
        if self.quantidade > 0:  # Ajuste positivo (semelhante a entrada)
            if self.custo_unitario > 0:
                quantidade_anterior = saldo.quantidade
                valor_anterior = quantidade_anterior * saldo.custo_medio
                valor_ajuste = self.quantidade * self.custo_unitario
                quantidade_nova = quantidade_anterior + self.quantidade
                
                if quantidade_nova > 0:
                    saldo.custo_medio = ((valor_anterior + valor_ajuste) / quantidade_nova).quantize(Decimal('0.0001'))
            
            saldo.quantidade += self.quantidade
        else:  # Ajuste negativo
            saldo.quantidade += self.quantidade  # Já é negativo
        
        saldo.save()
    
    def _processar_estorno(self):
        """Processa estorno de um movimento anterior"""
        if not self.movimento_estornado:
            raise ValidationError('Estorno deve referenciar um movimento original.')
        
        movimento_original = self.movimento_estornado
        
        # Criar movimento inverso ao original
        if movimento_original.tipo_movimento == 'ENTRADA':
            # Estornar entrada = fazer saída
            saldo = SaldoEstoque.objects.get(item=self.item, local=movimento_original.local_destino)
            saldo.quantidade -= movimento_original.quantidade
            
            # Recalcular custo médio após estorno é complexo, mantém o mesmo por simplificação
            saldo.save()
        
        elif movimento_original.tipo_movimento == 'SAIDA':
            # Estornar saída = fazer entrada
            saldo, created = SaldoEstoque.objects.get_or_create(
                item=self.item,
                local=movimento_original.local_origem,
                defaults={'quantidade': Decimal('0.000'), 'custo_medio': Decimal('0.0000')}
            )
            saldo.quantidade += movimento_original.quantidade
            saldo.save()
    
    def _lancar_custo_projeto(self):
        """Lança custo do material no projeto (se houver integração)"""
        # Este método pode ser expandido para integrar com o módulo de projetos
        # Por enquanto, apenas registra o movimento com projeto_id
        pass


# ===================================
# MODELOS PARA BOM E PRODUÇÃO (FUTURO)
# ===================================

class BOM(models.Model):
    """
    Bill of Materials (Lista de Materiais) - Estrutura de Produto
    Define quais itens (MP) são necessários para produzir um item (PA/SEMI)
    """
    produto = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='bom_produto', verbose_name='Produto', limit_choices_to={'tipo_item__in': ['PA', 'SEMI']})
    versao = models.CharField('Versão', max_length=20, default='1.0')
    descricao = models.CharField('Descrição', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)
    data_vigencia = models.DateField('Data Vigência')
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='boms_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'bom'
        verbose_name = 'BOM (Lista de Materiais)'
        verbose_name_plural = 'BOMs (Listas de Materiais)'
        unique_together = [['produto', 'versao']]
        ordering = ['produto', '-versao']
    
    def __str__(self):
        return f"BOM {self.produto.codigo} v{self.versao}"


class BOMItem(models.Model):
    """Itens que compõem uma BOM"""
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='itens', verbose_name='BOM')
    item_componente = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='bom_componente', verbose_name='Item Componente')
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, help_text='Quantidade necessária para produzir 1 unidade do produto')
    sequencia = models.IntegerField('Sequência', default=0)
    
    # Perdas/Refugo
    percentual_perda = models.DecimalField('% Perda', max_digits=5, decimal_places=2, default=0.00, help_text='Percentual de perda no processo')
    
    class Meta:
        db_table = 'bom_itens'
        verbose_name = 'Item da BOM'
        verbose_name_plural = 'Itens da BOM'
        ordering = ['bom', 'sequencia']
        unique_together = [['bom', 'item_componente']]
    
    def __str__(self):
        return f"{self.bom.produto.codigo} - {self.item_componente.codigo}: {self.quantidade}"
    
    def get_quantidade_com_perda(self):
        """Retorna quantidade incluindo perda"""
        return self.quantidade * (1 + self.percentual_perda / 100)


class OrdemProducao(models.Model):
    """Ordens de Produção (para futuro)"""
    STATUS_CHOICES = [
        ('PLANEJADA', 'Planejada'),
        ('LIBERADA', 'Liberada'),
        ('EM_PRODUCAO', 'Em Produção'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    numero_op = models.CharField('Nº OP', max_length=50, unique=True, db_index=True)
    produto = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='ordens_producao', verbose_name='Produto', limit_choices_to={'tipo_item__in': ['PA', 'SEMI']})
    bom = models.ForeignKey(BOM, on_delete=models.PROTECT, related_name='ordens_producao', verbose_name='BOM')
    quantidade_planejada = models.DecimalField('Quantidade Planejada', max_digits=12, decimal_places=3)
    quantidade_produzida = models.DecimalField('Quantidade Produzida', max_digits=12, decimal_places=3, default=0.000)
    
    local_producao = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT, related_name='ordens_producao_origem', verbose_name='Local Produção')
    local_destino = models.ForeignKey(LocalEstoque, on_delete=models.PROTECT, related_name='ordens_producao_destino', verbose_name='Local Destino Produto')
    
    data_planejada = models.DateField('Data Planejada')
    data_inicio = models.DateTimeField('Data Início', null=True, blank=True)
    data_fim = models.DateTimeField('Data Fim', null=True, blank=True)
    
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PLANEJADA', db_index=True)
    projeto = models.ForeignKey('projetos.Projeto', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_producao', verbose_name='Projeto')
    
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ops_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'ordens_producao'
        verbose_name = 'Ordem de Produção'
        verbose_name_plural = 'Ordens de Produção'
        ordering = ['-numero_op']
        indexes = [
            models.Index(fields=['numero_op']),
            models.Index(fields=['status']),
            models.Index(fields=['data_planejada']),
        ]
    
    def __str__(self):
        return f"OP {self.numero_op} - {self.produto.codigo}"
