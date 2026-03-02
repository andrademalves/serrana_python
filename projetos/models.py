from django.db import models
from django.contrib.auth.models import User
from cadastros.models import Pessoa
from estoque.models import Item, MovimentoEstoque
from financeiro.models import CentroCusto
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
import json


class Orcamento(models.Model):
    """Orçamento que pode virar projeto"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
        ('CONVERTIDO', 'Convertido em Projeto'),
    ]
    
    FORMA_PAGAMENTO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('BOLETO', 'Boleto'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
        ('PARCELADO', 'Parcelado'),
        ('CHEQUE', 'Cheque'),
    ]
    
    TIPO_DESCONTO_CHOICES = [
        ('NENHUM', 'Nenhum'),
        ('PERCENTUAL', 'Percentual (%)'),
        ('VALOR_FIXO', 'Valor Fixo (R$)'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Empresa',
        default=1
    )
    
    codigo = models.CharField('Código', max_length=50, unique=True, editable=False, blank=True)
    descricao = models.CharField('Descrição', max_length=200, help_text='Descrição resumida do orçamento', default='Orçamento')
    cliente = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='orcamentos_projeto', verbose_name='Cliente', limit_choices_to={'cliente': True})
    vendedor = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='orcamentos_vendedor', verbose_name='Vendedor', limit_choices_to={'vendedor': True})
    data_orcamento = models.DateField('Data do Orçamento')
    data_aprovacao = models.DateField('Data de Aprovação', null=True, blank=True)
    validade_dias = models.IntegerField('Validade (dias)', default=30)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='A_VISTA')
    
    # Parcelamento
    numero_parcelas = models.IntegerField('Número de Parcelas', default=1)
    valor_entrada = models.DecimalField('Valor de Entrada', max_digits=12, decimal_places=2, default=0.00, help_text='Valor pago como entrada (opcional)')
    
    # Valores e Desconto Global
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0.00, help_text='Soma dos itens')
    tipo_desconto = models.CharField('Tipo de Desconto', max_length=20, choices=TIPO_DESCONTO_CHOICES, default='NENHUM')
    desconto_valor = models.DecimalField('Valor do Desconto', max_digits=12, decimal_places=2, default=0.00, help_text='Percentual ou valor fixo')
    desconto = models.DecimalField('Desconto Aplicado (R$)', max_digits=12, decimal_places=2, default=0.00, editable=False)
    valor_final = models.DecimalField('Valor Final', max_digits=12, decimal_places=2, default=0.00, editable=False)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orcamentos_projeto_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orcamentos_atualizados', verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'orcamentos'
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_orcamento']
    
    def __str__(self):
        return f"{self.codigo} - {self.cliente.nome}"
    
    def _gerar_codigo_automatico(self):
        """Gera código automático no formato ORC-YYYY-0001"""
        ano = timezone.now().year
        ultimo_orcamento = Orcamento.objects.filter(
            codigo__startswith=f'ORC-{ano}-'
        ).order_by('-codigo').first()
        
        if ultimo_orcamento:
            # Extrair número sequencial do último código
            try:
                ultimo_numero = int(ultimo_orcamento.codigo.split('-')[-1])
                novo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        
        return f'ORC-{ano}-{novo_numero:04d}'
    
    def _calcular_desconto(self):
        """Calcula o desconto em reais baseado no tipo"""
        if self.tipo_desconto == 'PERCENTUAL':
            percentual = min(self.desconto_valor, Decimal('100.00'))  # Máximo 100%
            return (self.valor_total * percentual / Decimal('100.00')).quantize(Decimal('0.01'))
        elif self.tipo_desconto == 'VALOR_FIXO':
            # Desconto não pode ser maior que o total
            return min(self.desconto_valor, self.valor_total)
        return Decimal('0.00')
    
    def save(self, *args, **kwargs):
        # Gerar código automático se for novo orçamento
        if not self.pk and not self.codigo:
            self.codigo = self._gerar_codigo_automatico()
        
        # Garantir que os valores sejam Decimal
        self.valor_total = Decimal(str(self.valor_total)) if self.valor_total else Decimal('0.00')
        
        # Calcular desconto em reais
        self.desconto = self._calcular_desconto()
        
        # Calcular valor final (nunca negativo)
        self.valor_final = max(self.valor_total - self.desconto, Decimal('0.00'))
        
        # Guardar valores antigos para auditoria
        old_values = None
        if self.pk:
            old_obj = Orcamento.objects.filter(pk=self.pk).first()
            if old_obj:
                old_values = {
                    'valor_total': str(old_obj.valor_total),
                    'tipo_desconto': old_obj.tipo_desconto,
                    'desconto_valor': str(old_obj.desconto_valor),
                    'desconto': str(old_obj.desconto),
                    'valor_final': str(old_obj.valor_final),
                    'status': old_obj.status,
                }
        
        super().save(*args, **kwargs)
        
        # Registrar auditoria após salvar (com try/except para evitar erros)
        try:
            if old_values:
                self._registrar_auditoria('ALTERADO', old_values)
            else:
                self._registrar_auditoria('CRIADO')
        except Exception as e:
            print(f"Erro ao registrar auditoria: {e}")
            # Não bloqueia o save se auditoria falhar
    
    def _registrar_auditoria(self, acao, old_values=None):
        """Registra histórico de alterações"""
        new_values = {
            'valor_total': str(self.valor_total),
            'tipo_desconto': self.tipo_desconto,
            'desconto_valor': str(self.desconto_valor),
            'desconto': str(self.desconto),
            'valor_final': str(self.valor_final),
            'status': self.status,
        }
        
        diff = {}
        if old_values:
            for key in new_values:
                if old_values.get(key) != new_values[key]:
                    diff[key] = {
                        'antes': old_values[key],
                        'depois': new_values[key]
                    }
        
        if diff or acao == 'CRIADO':
            OrcamentoHistorico.objects.create(
                orcamento=self,
                usuario_id=self.atualizado_por_id or self.criado_por_id,
                acao=acao,
                diff=diff if diff else new_values
            )


class OrcamentoItem(models.Model):
    """Itens do orçamento"""
    TIPO_CHOICES = [
        ('PRODUTO', 'Produto'),
        ('MATERIAL', 'Material'),
        ('SERVICO', 'Serviço'),
        ('MAO_OBRA', 'Mão de Obra'),
    ]
    
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens', verbose_name='Orçamento')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='PRODUTO')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Item')
    
    # Campos para guardar referência do Select2 (produto_1, item_13, etc)
    item_ref = models.CharField('Referência do Item', max_length=50, null=True, blank=True, 
                                 help_text='Formato: tipo_id (ex: produto_1)')
    item_codigo = models.CharField('Código do Item', max_length=50, null=True, blank=True)
    
    descricao = models.CharField('Descrição', max_length=255)
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, default=1.000)
    valor_unitario = models.DecimalField('Valor Unitário', max_digits=12, decimal_places=4, default=0.0000)
    desconto = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0.00)
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0.00)
    
    class Meta:
        db_table = 'orcamento_itens'
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'
    
    def __str__(self):
        return f"{self.descricao} - {self.quantidade}"
    
    def save(self, *args, **kwargs):
        # Garantir que todos os valores numéricos sejam Decimal e não None
        self.quantidade = Decimal(str(self.quantidade)) if self.quantidade else Decimal('1.000')
        self.valor_unitario = Decimal(str(self.valor_unitario)) if self.valor_unitario else Decimal('0.0000')
        self.desconto = Decimal(str(self.desconto)) if self.desconto else Decimal('0.00')
        
        subtotal = self.quantidade * self.valor_unitario
        self.valor_total = subtotal - self.desconto
        super().save(*args, **kwargs)


class OrcamentoParcela(models.Model):
    """Parcelas do orçamento com forma de pagamento individual"""
    FORMA_PAGAMENTO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('PIX', 'PIX'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('BOLETO', 'Boleto'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
        ('CHEQUE', 'Cheque'),
        ('DINHEIRO', 'Dinheiro'),
    ]
    
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='parcelas', verbose_name='Orçamento')
    numero_parcela = models.IntegerField('Número da Parcela')
    descricao = models.CharField('Descrição', max_length=200, blank=True, help_text='Ex: Entrada, 1/2, 2/2')
    data_vencimento = models.DateField('Data de Vencimento')
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='A_VISTA')
    
    class Meta:
        db_table = 'orcamento_parcelas'
        verbose_name = 'Parcela do Orçamento'
        verbose_name_plural = 'Parcelas do Orçamento'
        ordering = ['numero_parcela']
    
    def __str__(self):
        return f"{self.descricao or f'Parcela {self.numero_parcela}'} - {self.get_forma_pagamento_display()} - R$ {self.valor}"


class OrcamentoHistorico(models.Model):
    """Histórico de alterações do orçamento para auditoria"""
    ACAO_CHOICES = [
        ('CRIADO', 'Criado'),
        ('ALTERADO', 'Alterado'),
        ('DESCONTO', 'Desconto Aplicado'),
        ('PARCELA', 'Parcelas Alteradas'),
    ]
    
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='historico', verbose_name='Orçamento')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orcamentos_projeto_historico', verbose_name='Usuário')
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True, db_index=True)
    acao = models.CharField('Ação', max_length=20, choices=ACAO_CHOICES)
    diff = models.JSONField('Diferenças', default=dict, help_text='Alterações antes/depois')
    
    class Meta:
        db_table = 'orcamento_historico'
        verbose_name = 'Histórico do Orçamento'
        verbose_name_plural = 'Históricos dos Orçamentos'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'orcamento']),
        ]
    
    def __str__(self):
        return f"{self.orcamento.codigo} - {self.get_acao_display()} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"


class Projeto(models.Model):
    """Projeto/Obra com controle completo"""
    STATUS_CHOICES = [
        ('ORCAMENTO', 'Em Orçamento'),
        ('AGUARDANDO', 'Aguardando Início'),
        ('ANDAMENTO', 'Em Andamento'),
        ('PAUSADO', 'Pausado'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='projetos',
        verbose_name='Empresa',
        default=1
    )
    
    codigo = models.CharField('Código do Projeto', max_length=50, unique=True, editable=False)
    
    # Nota: O relacionamento com CentroCusto existe via OneToOne reverso
    # Acesse através de projeto.centro_custo (definido em financeiro.models.CentroCusto)
    
    orcamento = models.ForeignKey(Orcamento, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos', verbose_name='Orçamento Original')
    cliente = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='projetos', verbose_name='Cliente', limit_choices_to={'cliente': True})
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='projetos_vendedor', verbose_name='Vendedor/Responsável')
    descricao = models.CharField('Descrição do Projeto', max_length=200)
    
    # Datas
    data_orcamento = models.DateField('Data do Orçamento', null=True, blank=True)
    data_contratacao = models.DateField('Data da Contratação', null=True, blank=True)
    data_inicio_prevista = models.DateField('Data Início Prevista', null=True, blank=True)
    data_inicio_real = models.DateField('Data Início Real', null=True, blank=True)
    data_previsao_termino = models.DateField('Previsão de Término', null=True, blank=True, help_text='Previsão de término do projeto')
    data_termino_prevista = models.DateField('Data Término Prevista', null=True, blank=True)
    data_termino_real = models.DateField('Término do Projeto', null=True, blank=True, help_text='Data real de conclusão')
    prazo_obra = models.CharField('Prazo da Obra', max_length=200, blank=True, null=True)
    
    # Endereço da obra
    logradouro = models.CharField('Logradouro', max_length=200, blank=True, null=True)
    complemento = models.CharField('Complemento', max_length=200, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True, null=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True, null=True)
    uf = models.CharField('UF', max_length=2, blank=True, null=True)
    cep = models.CharField('CEP', max_length=9, blank=True, null=True)
    
    # Valores
    valor_orcado = models.DecimalField('Valor Orçado (Budget)', max_digits=12, decimal_places=2, default=0.00)
    valor_contratado = models.DecimalField('Valor Contratado', max_digits=12, decimal_places=2, default=0.00)
    
    # Visitas técnicas
    num_visitas_tecnicas = models.IntegerField('Número de Visitas Técnicas', default=0, help_text='Total de visitas técnicas realizadas')
    num_visitas_cobradas = models.IntegerField('Visitas Técnicas Cobradas', default=0, help_text='Quantidade de visitas cobradas')
    valor_visita = models.DecimalField('Valor por Visita', max_digits=10, decimal_places=2, default=0.00)
    valor_total_visitas = models.DecimalField('Valor Total Visitas Cobradas', max_digits=12, decimal_places=2, default=0.00, help_text='Valor total das visitas técnicas cobradas')
    visitas_viraram_desconto = models.BooleanField('Visitas Viraram Desconto?', default=False)
    
    # Status e observações
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ORCAMENTO')
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='projetos_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='projetos_atualizados', verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'projetos'
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['-data_contratacao']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    def _gerar_codigo_automatico(self):
        """Gera código automático no formato PROJ-AAAA-NNNN"""
        from datetime import datetime
        ano = datetime.now().year
        
        # Buscar último projeto do ano
        ultimo_projeto = Projeto.objects.filter(
            codigo__startswith=f'PROJ-{ano}'
        ).order_by('-codigo').first()
        
        if ultimo_projeto:
            # Extrair número sequencial do último código
            try:
                ultimo_numero = int(ultimo_projeto.codigo.split('-')[-1])
                novo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        
        return f'PROJ-{ano}-{novo_numero:04d}'
    
    def save(self, *args, **kwargs):
        # Gerar código automático se for novo projeto
        if not self.pk and not self.codigo:
            self.codigo = self._gerar_codigo_automatico()
        
        super().save(*args, **kwargs)
    
    @property
    def valor_total_alocado(self):
        """Calcula total de todas as alocações"""
        return self.alocacoes.aggregate(total=models.Sum('valor_total'))['total'] or Decimal('0.00')
    
    @property
    def margem(self):
        """Calcula margem do projeto"""
        return self.valor_contratado - self.valor_total_alocado
    
    @property
    def percentual_margem(self):
        """Calcula percentual de margem"""
        if self.valor_contratado > 0:
            return (self.margem / self.valor_contratado) * 100
        return Decimal('0.00')


class VisitaTecnica(models.Model):
    """Visitas técnicas realizadas no orçamento"""
    STATUS_CHOICES = [
        ('AGENDADA', 'Agendada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='visitas_tecnicas',
        verbose_name='Empresa',
        default=1
    )
    
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='visitas_tecnicas', verbose_name='Orçamento', null=True, blank=True)
    
    # Quem agendou e quem vai fazer  
    agendado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='visitas_agendadas', verbose_name='Agendado por', null=True, blank=True)
    tecnico = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='visitas_tecnico', verbose_name='Técnico Responsável', limit_choices_to={'vendedor': True})
    
    # Datas e horários
    data_agendamento = models.DateTimeField('Data do Agendamento', null=True, blank=True)
    data_visita = models.DateField('Data da Visita')
    hora_inicio = models.TimeField('Horário Início', null=True, blank=True)
    hora_fim = models.TimeField('Horário Fim', null=True, blank=True)
    
    # Valores
    custo_visita = models.DecimalField('Custo da Visita', max_digits=10, decimal_places=2, default=0.00, help_text='Custo interno da visita')
    valor_cobrado = models.DecimalField('Valor Cobrado', max_digits=10, decimal_places=2, default=0.00, help_text='Valor cobrado do cliente')
    
    # Controle
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='AGENDADA')
    descricao = models.TextField('Descrição/Objetivo', blank=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    virou_desconto = models.BooleanField('Virou Desconto?', default=False)
    data_desconto = models.DateField('Data que Virou Desconto', null=True, blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'visitas_tecnicas'
        verbose_name = 'Visita Técnica'
        verbose_name_plural = 'Visitas Técnicas'
        ordering = ['-data_visita', '-hora_inicio']
    
    def __str__(self):
        return f"Visita - {self.orcamento.codigo} - {self.data_visita.strftime('%d/%m/%Y')}"


class AlocacaoProjeto(models.Model):
    """Tudo que foi alocado ao projeto"""
    TIPO_CHOICES = [
        ('MATERIAL', 'Material/Produto'),
        ('MO_INTERNA', 'Mão de Obra Interna'),
        ('MO_TERCEIRO', 'Mão de Obra Terceirizada'),
        ('SERVICO', 'Serviço Terceirizado'),
        ('EQUIPAMENTO', 'Equipamento'),
        ('TRANSPORTE', 'Transporte'),
        ('OUTROS', 'Outros'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='alocacoes_projeto',
        verbose_name='Empresa',
        default=1
    )
    
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='alocacoes', verbose_name='Projeto')
    data_alocacao = models.DateField('Data da Alocação')
    tipo = models.CharField('Tipo de Alocação', max_length=20, choices=TIPO_CHOICES)
    
    # Se for Material
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Item')
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3, null=True, blank=True)
    valor_unitario = models.DecimalField('Valor Unitário', max_digits=12, decimal_places=4, null=True, blank=True)
    movimentacao_estoque = models.ForeignKey(MovimentoEstoque, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Movimentação Estoque')
    
    # Se for Mão de Obra Interna
    funcionario = models.ForeignKey(Pessoa, on_delete=models.PROTECT, null=True, blank=True, related_name='alocacoes_trabalho', verbose_name='Funcionário', limit_choices_to={'funcionario': True})
    horas_trabalhadas = models.DecimalField('Horas Trabalhadas', max_digits=8, decimal_places=2, null=True, blank=True)
    valor_hora = models.DecimalField('Valor/Hora', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Se for Terceiro/Serviço
    fornecedor = models.ForeignKey(Pessoa, on_delete=models.PROTECT, null=True, blank=True, related_name='alocacoes_fornecimento', verbose_name='Fornecedor', limit_choices_to={'fornecedor': True})
    descricao_servico = models.CharField('Descrição do Serviço', max_length=255, blank=True, null=True)
    
    # Comum a todos
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0.00)
    documento = models.CharField('Documento (NF, Recibo)', max_length=100, blank=True, null=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='alocacoes_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'alocacoes_projeto'
        verbose_name = 'Alocação de Projeto'
        verbose_name_plural = 'Alocações de Projeto'
        ordering = ['-data_alocacao']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.projeto.codigo} - {self.valor_total}"
    
    def save(self, *args, **kwargs):
        # Calcula valor total baseado no tipo
        if self.tipo == 'MATERIAL' and self.quantidade and self.valor_unitario:
            self.valor_total = Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario))
            
            # Cria movimentação de estoque se for material e tiver item
            if self.item and not self.movimentacao_estoque:
                movimentacao = MovimentoEstoque.objects.create(
                    item=self.item,
                    tipo_movimento='SAIDA',
                    quantidade=self.quantidade,
                    custo_unitario=self.valor_unitario,
                    custo_total=self.valor_total,
                    documento=f"PROJ-{self.projeto.codigo}",
                    observacao=f"Alocação para projeto {self.projeto.codigo}",
                    data_movimento=timezone.now(),
                    criado_por=self.criado_por
                )
                self.movimentacao_estoque = movimentacao
        
        elif self.tipo == 'MO_INTERNA' and self.horas_trabalhadas and self.valor_hora:
            self.valor_total = Decimal(str(self.horas_trabalhadas)) * Decimal(str(self.valor_hora))
        
        super().save(*args, **kwargs)
        
        # Cria lançamento na conta corrente
        ContaCorrenteProjeto.objects.create(
            projeto=self.projeto,
            data_movimento=self.data_alocacao,
            tipo='PAGAMENTO',
            descricao=f"{self.get_tipo_display()} - {self.descricao_servico or (self.item.descricao if self.item else '')}",
            valor=self.valor_total,
            documento=self.documento,
            alocacao=self,
            criado_por=self.criado_por
        )


class ContaCorrenteProjeto(models.Model):
    """Conta corrente do projeto - todas as movimentações financeiras"""
    TIPO_CHOICES = [
        ('RECEBIMENTO', 'Recebimento'),
        ('PAGAMENTO', 'Pagamento/Custo'),
        ('VISITA', 'Visita Técnica'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='contas_correntes_projeto',
        verbose_name='Empresa',
        default=1
    )
    
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='conta_corrente', verbose_name='Projeto')
    data_movimento = models.DateField('Data Movimento')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    descricao = models.CharField('Descrição', max_length=255)
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    documento = models.CharField('Documento', max_length=100, blank=True, null=True)
    
    # Referências
    alocacao = models.ForeignKey(AlocacaoProjeto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Alocação')
    visita = models.ForeignKey(VisitaTecnica, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Visita')
    
    # Saldo
    saldo_anterior = models.DecimalField('Saldo Anterior', max_digits=12, decimal_places=2, default=0.00)
    saldo_apos = models.DecimalField('Saldo Após', max_digits=12, decimal_places=2, default=0.00)
    
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='conta_corrente_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'conta_corrente_projeto'
        verbose_name = 'Conta Corrente do Projeto'
        verbose_name_plural = 'Contas Correntes dos Projetos'
        ordering = ['data_movimento', 'id']
    
    def __str__(self):
        return f"{self.projeto.codigo} - {self.data_movimento} - {self.valor}"
    
    def save(self, *args, **kwargs):
        # Calcula saldo
        movimentos_anteriores = ContaCorrenteProjeto.objects.filter(
            projeto=self.projeto,
            data_movimento__lt=self.data_movimento
        ).order_by('-data_movimento', '-id').first()
        
        self.saldo_anterior = movimentos_anteriores.saldo_apos if movimentos_anteriores else Decimal('0.00')
        
        if self.tipo == 'RECEBIMENTO' or (self.tipo == 'VISITA' and self.valor > 0):
            self.saldo_apos = self.saldo_anterior + self.valor
        else:
            self.saldo_apos = self.saldo_anterior - abs(self.valor)
        
        super().save(*args, **kwargs)


class VendaDireta(models.Model):
    """Venda simples de produtos sem projeto"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('PAGO', 'Pago'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='vendas_diretas',
        verbose_name='Empresa',
        default=1
    )
    
    codigo = models.CharField('Código da Venda', max_length=50, unique=True)
    cliente = models.ForeignKey(Pessoa, on_delete=models.PROTECT, related_name='vendas', verbose_name='Cliente', limit_choices_to={'cliente': True})
    vendedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='vendas', verbose_name='Vendedor')
    data_venda = models.DateField('Data da Venda')
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0.00)
    desconto = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0.00)
    valor_final = models.DecimalField('Valor Final', max_digits=12, decimal_places=2, default=0.00)
    forma_pagamento = models.CharField('Forma de Pagamento', max_length=50, blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vendas_criadas', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='vendas_atualizadas', verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'vendas_diretas'
        verbose_name = 'Venda Direta'
        verbose_name_plural = 'Vendas Diretas'
        ordering = ['-data_venda']
    
    def __str__(self):
        return f"{self.codigo} - {self.cliente.nome} - {self.valor_final}"
    
    def save(self, *args, **kwargs):
        self.valor_final = self.valor_total - self.desconto
        super().save(*args, **kwargs)


class VendaDiretaItem(models.Model):
    """Itens da venda direta"""
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='vendas_diretas_itens',
        verbose_name='Empresa',
        default=1
    )
    
    venda = models.ForeignKey(VendaDireta, on_delete=models.CASCADE, related_name='itens', verbose_name='Venda')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name='Item')
    quantidade = models.DecimalField('Quantidade', max_digits=12, decimal_places=3)
    valor_unitario = models.DecimalField('Valor Unitário', max_digits=12, decimal_places=4)
    desconto = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0.00)
    valor_total = models.DecimalField('Valor Total', max_digits=12, decimal_places=2, default=0.00)
    movimentacao_estoque = models.ForeignKey(MovimentoEstoque, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Movimentação Estoque')
    
    class Meta:
        db_table = 'vendas_diretas_itens'
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'
    
    def __str__(self):
        return f"{self.item.descricao} - {self.quantidade}"
    
    def save(self, *args, **kwargs):
        subtotal = Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario))
        self.valor_total = subtotal - self.desconto
        
        # Cria movimentação de estoque se não existir e a venda não estiver cancelada
        if self.venda.status != 'CANCELADO' and not self.movimentacao_estoque:
            movimentacao = MovimentoEstoque.objects.create(
                item=self.item,
                tipo_movimento='SAIDA',
                quantidade=self.quantidade,
                custo_unitario=self.valor_unitario,
                custo_total=self.valor_total,
                documento=f"VENDA-{self.venda.codigo}",
                observacao=f"Venda {self.venda.codigo} para {self.venda.cliente.nome}",
                data_movimento=timezone.now(),
                criado_por=self.venda.criado_por
            )
            self.movimentacao_estoque = movimentacao
        
        super().save(*args, **kwargs)


class DiarioObra(models.Model):
    """Diário da Obra - Registro diário de atividades do projeto"""
    CLIMA_CHOICES = [
        ('ENSOLARADO', 'Ensolarado'),
        ('NUBLADO', 'Nublado'),
        ('CHUVOSO', 'Chuvoso'),
        ('TEMPESTADE', 'Tempestade'),
    ]
    
    PERIODO_CHOICES = [
        ('MANHA', 'Manhã'),
        ('TARDE', 'Tarde'),
        ('INTEGRAL', 'Dia Integral'),
        ('NOITE', 'Noite'),
    ]
    
    # Empresa (multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='diarios_obra',
        verbose_name='Empresa',
        default=1
    )
    
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='diario_obra', verbose_name='Projeto')
    data = models.DateField('Data', help_text='Data do registro no diário')
    periodo = models.CharField('Período', max_length=20, choices=PERIODO_CHOICES, default='INTEGRAL')
    clima = models.CharField('Clima', max_length=20, choices=CLIMA_CHOICES, default='ENSOLARADO')
    temperatura = models.CharField('Temperatura', max_length=50, blank=True, null=True, help_text='Ex: 25°C')
    
    # Equipe e Recursos
    num_trabalhadores = models.IntegerField('Número de Trabalhadores', default=0, help_text='Quantidade de trabalhadores presentes')
    equipe_descricao = models.TextField('Descrição da Equipe', blank=True, null=True, help_text='Funções e nomes dos trabalhadores')
    equipamentos_utilizados = models.TextField('Equipamentos Utilizados', blank=True, null=True, help_text='Liste os equipamentos usados no dia')
    
    # Atividades
    atividades_realizadas = models.TextField('Atividades Realizadas', help_text='Descrição detalhada das atividades executadas')
    percentual_progresso = models.DecimalField('Progresso do Dia (%)', max_digits=5, decimal_places=2, default=0.00, 
                                                help_text='Percentual de conclusão das atividades planejadas para o dia')
    
    # Materiais
    materiais_recebidos = models.TextField('Materiais Recebidos', blank=True, null=True, help_text='Materiais que chegaram na obra')
    materiais_utilizados = models.TextField('Materiais Utilizados', blank=True, null=True, help_text='Materiais consumidos durante o dia')
    
    # Problemas e Observações
    problemas_encontrados = models.TextField('Problemas Encontrados', blank=True, null=True, help_text='Descreva problemas ou imprevistos')
    solucoes_aplicadas = models.TextField('Soluções Aplicadas', blank=True, null=True, help_text='Como os problemas foram resolvidos')
    visitas_fiscalizacao = models.TextField('Visitas e Fiscalização', blank=True, null=True, 
                                             help_text='Registre visitas de fiscais, engenheiros, clientes, etc.')
    
    # Segurança
    incidentes_seguranca = models.TextField('Incidentes de Segurança', blank=True, null=True, 
                                            help_text='Acidentes, quase-acidentes ou questões de segurança')
    epi_utilizado = models.BooleanField('EPIs Utilizados?', default=True, help_text='Todos os trabalhadores usaram EPIs adequados?')
    
    # Observações Gerais
    observacoes = models.TextField('Observações Gerais', blank=True, null=True, help_text='Outras informações relevantes')
    
    # Anexos (fotos serão implementadas posteriormente)
    # fotos = models.ManyToManyField('DiarioObraFoto', blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='diarios_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diarios_atualizados', verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'diario_obra'
        verbose_name = 'Diário da Obra'
        verbose_name_plural = 'Diários da Obra'
        ordering = ['-data', '-criado_em']
        unique_together = [['projeto', 'data', 'periodo']]  # Evita duplicação de registro para mesmo dia/período
    
    def __str__(self):
        return f"{self.projeto.codigo} - {self.data.strftime('%d/%m/%Y')} - {self.get_periodo_display()}"
