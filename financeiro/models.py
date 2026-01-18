"""
Models do Módulo Financeiro
Arquitetura profissional de contas a pagar e receber
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta


# =========================================
# CADASTROS BASE
# =========================================

class Banco(models.Model):
    """Bancos (instituições financeiras)"""
    codigo_compe = models.CharField('Código COMPE', max_length=3, unique=True, help_text='Código de 3 dígitos do Banco Central')
    nome = models.CharField('Nome', max_length=100)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bancos_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'bancos'
        verbose_name = 'Banco'
        verbose_name_plural = 'Bancos'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['codigo_compe']),
        ]
    
    def __str__(self):
        return f"{self.codigo_compe} - {self.nome}"


class ContaFinanceira(models.Model):
    """Contas Bancárias, Caixas, Carteiras"""
    TIPO_CHOICES = [
        ('CONTA_CORRENTE', 'Conta Corrente'),
        ('CONTA_POUPANCA', 'Conta Poupança'),
        ('CONTA_INVESTIMENTO', 'Conta Investimento'),
        ('CAIXA', 'Caixa'),
        ('CARTEIRA_DIGITAL', 'Carteira Digital (PicPay, PayPal, etc)'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='contas_financeiras', verbose_name='Empresa')
    
    nome = models.CharField('Nome da Conta', max_length=100, help_text='Ex: Caixa Matriz, Bradesco CC 1234-5')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Banco', help_text='Obrigatório para contas bancárias')
    agencia = models.CharField('Agência', max_length=10, blank=True)
    conta = models.CharField('Conta', max_length=20, blank=True)
    
    saldo_inicial = models.DecimalField('Saldo Inicial', max_digits=15, decimal_places=2, default=0, help_text='Saldo na data de implantação')
    data_saldo_inicial = models.DateField('Data do Saldo Inicial', default=date.today)
    
    limite_credito = models.DecimalField('Limite de Crédito', max_digits=15, decimal_places=2, default=0, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contas_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'contas_financeiras'
        verbose_name = 'Conta Financeira'
        verbose_name_plural = 'Contas Financeiras'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return self.nome
    
    def saldo_atual(self):
        """Calcula saldo atual baseado em movimentações"""
        from financeiro.services.calculadora import CalculadoraSaldos
        return CalculadoraSaldos.saldo_conta(self.id)
    
    def saldo_disponivel(self):
        """Saldo atual + limite de crédito"""
        return self.saldo_atual() + self.limite_credito


class FormaPagamento(models.Model):
    """Formas de pagamento/recebimento"""
    TIPO_CHOICES = [
        ('PIX', 'PIX'),
        ('DINHEIRO', 'Dinheiro'),
        ('BOLETO', 'Boleto'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
        ('CARTAO_CREDITO', 'Cartão de Crédito'),
        ('CARTAO_DEBITO', 'Cartão de Débito'),
        ('CHEQUE', 'Cheque'),
        ('DEPOSITO', 'Depósito'),
        ('OUTROS', 'Outros'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='formas_pagamento', verbose_name='Empresa')
    
    codigo = models.CharField('Código', max_length=20)
    descricao = models.CharField('Descrição', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    
    prazo_compensacao = models.IntegerField('Prazo de Compensação (dias)', default=0, help_text='Dias até o dinheiro entrar efetivamente')
    taxa_percentual = models.DecimalField('Taxa %', max_digits=5, decimal_places=2, default=0, help_text='Taxa percentual sobre o valor')
    taxa_fixa = models.DecimalField('Taxa Fixa R$', max_digits=10, decimal_places=2, default=0)
    
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='formas_pagamento_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'formas_pagamento'
        verbose_name = 'Forma de Pagamento'
        verbose_name_plural = 'Formas de Pagamento'
        ordering = ['descricao']
        unique_together = [('empresa', 'codigo')]
        indexes = [
            models.Index(fields=['tipo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class CentroCusto(models.Model):
    """Centros de Custo / Departamentos / Obras"""
    TIPO_CHOICES = [
        ('OBRA', 'Obra/Projeto'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('PRODUCAO', 'Produção'),
        ('COMERCIAL', 'Comercial'),
        ('LOJA', 'Loja/Showroom'),
        ('OUTROS', 'Outros'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='centros_custo', verbose_name='Empresa')
    
    codigo = models.CharField('Código', max_length=20)
    nome = models.CharField('Nome', max_length=100)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    
    # Relacionamento opcional com projetos (se houver módulo de projetos)
    projeto = models.ForeignKey('projetos.Projeto', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Projeto Relacionado')
    
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='centros_custo_responsavel', verbose_name='Responsável')
    
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='centros_custo_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'centros_custo'
        verbose_name = 'Centro de Custo'
        verbose_name_plural = 'Centros de Custo'
        ordering = ['codigo']
        unique_together = [('empresa', 'codigo')]
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class PlanoConta(models.Model):
    """
    Plano de Contas Contábil
    Estrutura hierárquica para classificação de receitas e despesas
    """
    TIPO_CHOICES = [
        ('RECEITA', 'Receita'),
        ('DESPESA', 'Despesa'),
        ('ATIVO', 'Ativo'),
        ('PASSIVO', 'Passivo'),
        ('PATRIMONIO', 'Patrimônio Líquido'),
    ]
    
    NATUREZA_CHOICES = [
        ('ANALITICA', 'Analítica'),  # Conta movimentável (folha)
        ('SINTETICA', 'Sintética'),  # Conta totalizadora (pai)
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='planos_conta', verbose_name='Empresa')
    
    codigo = models.CharField('Código', max_length=20, help_text='Ex: 1.1.01, 3.2.01.001')
    nome = models.CharField('Nome', max_length=150)
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES)
    natureza = models.CharField('Natureza', max_length=10, choices=NATUREZA_CHOICES, default='ANALITICA')
    
    # Estrutura hierárquica
    conta_pai = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='contas_filhas',
        verbose_name='Conta Pai'
    )
    
    nivel = models.IntegerField('Nível', default=1, editable=False, help_text='Nível na hierarquia')
    caminho = models.CharField('Caminho', max_length=255, editable=False, help_text='Caminho completo na hierarquia')
    
    # Flags
    aceita_lancamento = models.BooleanField('Aceita Lançamento', default=True, help_text='Contas sintéticas não aceitam lançamento direto')
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='planos_conta_criados', verbose_name='Criado por')
    
    class Meta:
        db_table = 'plano_contas'
        verbose_name = 'Plano de Conta'
        verbose_name_plural = 'Plano de Contas'
        ordering = ['codigo']
        unique_together = [('empresa', 'codigo')]
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['natureza']),
            models.Index(fields=['ativo']),
            models.Index(fields=['caminho']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    def save(self, *args, **kwargs):
        """Calcula nível e caminho automaticamente"""
        if self.conta_pai:
            self.nivel = self.conta_pai.nivel + 1
            self.caminho = f"{self.conta_pai.caminho} > {self.nome}"
            
            # Conta sintética (pai) não pode aceitar lançamento
            if self.conta_pai.natureza == 'SINTETICA':
                self.conta_pai.aceita_lancamento = False
                self.conta_pai.save(update_fields=['aceita_lancamento'])
        else:
            self.nivel = 1
            self.caminho = self.nome
        
        # Valida natureza
        if self.natureza == 'SINTETICA':
            self.aceita_lancamento = False
        
        super().save(*args, **kwargs)
    
    def get_filhas(self):
        """Retorna todas as contas filhas (recursivo)"""
        return PlanoConta.objects.filter(caminho__startswith=f"{self.caminho} >")
    
    def get_hierarquia_display(self):
        """Retorna string formatada com indentação visual"""
        indent = '&nbsp;&nbsp;' * (self.nivel - 1)
        return f"{indent}{self.codigo} - {self.nome}"


class CategoriaCustoVariabilidade(models.Model):
    """
    Classifica categorias de custo como FIXA ou VARIÁVEL
    para cálculo de ponto de equilíbrio
    NOTA: Futuramente pode ser associada a um Plano de Contas quando implementado
    """
    TIPO_CHOICES = [
        ('FIXO', 'Custo Fixo'),
        ('VARIAVEL', 'Custo Variável'),
        ('MISTO', 'Custo Misto'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='categorias_custo', verbose_name='Empresa')
    
    nome = models.CharField('Nome da Categoria', max_length=100)
    tipo = models.CharField('Tipo de Custo', max_length=10, choices=TIPO_CHOICES, default='MISTO')
    percentual_variavel = models.DecimalField('% Variável', max_digits=5, decimal_places=2, default=0, help_text='Para custos mistos: % que é variável')
    
    observacao = models.TextField('Observação', blank=True)
    
    class Meta:
        db_table = 'categorias_custo_variabilidade'
        verbose_name = 'Classificação de Variabilidade'
        verbose_name_plural = 'Classificações de Variabilidade'
    
    def __str__(self):
        return f"{self.nome} - {self.get_tipo_display()}"


# =========================================
# OPERAÇÃO FINANCEIRA
# =========================================

class TituloFinanceiro(models.Model):
    """
    Título Financeiro (Conta a Pagar ou Receber)
    Representa o documento original (NF, Contrato, Ordem, etc)
    """
    TIPO_CHOICES = [
        ('PAGAR', 'Conta a Pagar'),
        ('RECEBER', 'Conta a Receber'),
    ]
    
    STATUS_CHOICES = [
        ('ABERTO', 'Em Aberto'),
        ('PARCIAL', 'Parcialmente Quitado'),
        ('QUITADO', 'Quitado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='titulos_financeiros', verbose_name='Empresa')
    
    # Identificação
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    numero_documento = models.CharField('Nº Documento', max_length=50, help_text='NF, Contrato, Ordem, etc')
    descricao = models.CharField('Descrição', max_length=255)
    
    # Pessoa (Cliente ou Fornecedor) - Opcional para casos como impostos
    pessoa = models.ForeignKey('cadastros.Pessoa', on_delete=models.PROTECT, null=True, blank=True, verbose_name='Cliente/Fornecedor')
    
    # Classificação Contábil
    plano_conta = models.ForeignKey(
        PlanoConta,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'aceita_lancamento': True, 'ativo': True},
        verbose_name='Plano de Contas',
        help_text='Classificação contábil da receita/despesa'
    )
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Centro de Custo')
    projeto = models.ForeignKey('projetos.Projeto', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Projeto', help_text='Vínculo direto com projeto/obra')
    
    # Conta Financeira Padrão (sugestão para baixas)
    conta_financeira_padrao = models.ForeignKey(ContaFinanceira, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Conta Financeira Padrão', help_text='Conta/banco de onde sairá o pagamento')
    
    # Valores
    data_emissao = models.DateField('Data de Emissão', default=date.today)
    data_primeiro_vencimento = models.DateField('Data do 1º Vencimento', null=True, blank=True, help_text='Data de vencimento da primeira parcela')
    valor_total = models.DecimalField('Valor Total', max_digits=15, decimal_places=2)
    
    # Parcelamento
    num_parcelas = models.IntegerField('Número de Parcelas', default=1)
    intervalo_dias = models.IntegerField('Intervalo entre Parcelas (dias)', default=30)
    intervalos_personalizados = models.CharField('Intervalos Personalizados', max_length=200, blank=True, null=True, help_text='Ex: 30/45/60 para vencimentos variáveis')
    
    # Status
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ABERTO')
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='titulos_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'titulos_financeiros'
        verbose_name = 'Título Financeiro'
        verbose_name_plural = 'Títulos Financeiros'
        ordering = ['-data_emissao', '-id']
        indexes = [
            models.Index(fields=['tipo', 'status']),
            models.Index(fields=['pessoa']),
            models.Index(fields=['data_emissao']),
            models.Index(fields=['centro_custo']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.numero_documento} - {self.pessoa}"
    
    def save(self, *args, **kwargs):
        criando = self.pk is None
        super().save(*args, **kwargs)
        
        # Cria parcelas automaticamente se for novo título
        if criando:
            self.gerar_parcelas()
    
    def gerar_parcelas(self):
        """Gera parcelas do título"""
        if self.num_parcelas < 1:
            self.num_parcelas = 1
            self.save()
        
        # Remove parcelas antigas (se houver)
        self.parcelas.all().delete()
        
        from decimal import Decimal, ROUND_DOWN
        
        # Data base para vencimentos: usa data_primeiro_vencimento se informada, senão data_emissao
        data_base = self.data_primeiro_vencimento if self.data_primeiro_vencimento else self.data_emissao
        
        # Verifica se usa intervalos personalizados
        if self.intervalos_personalizados and self.intervalos_personalizados.strip():
            # Processar intervalos personalizados (ex: "30/60/90" = vence em 30, 60 e 90 dias)
            intervalos_str = self.intervalos_personalizados.replace(',', '/').replace(';', '/').replace(' ', '')
            intervalos = [int(d.strip()) for d in intervalos_str.split('/') if d.strip().isdigit()]
            
            # Validar quantidade de intervalos
            if len(intervalos) != self.num_parcelas:
                # Se não bater, usar intervalo fixo como fallback
                intervalos = [(i + 1) * self.intervalo_dias for i in range(self.num_parcelas)]
            # Intervalos são ABSOLUTOS (30/60/90 = vence em 30, 60 e 90 dias respectivamente)
        else:
            # Usar intervalo fixo padrão
            intervalos = [(num) * self.intervalo_dias for num in range(1, self.num_parcelas + 1)]
        
        # Criar parcelas
        if self.num_parcelas == 1:
            # Para parcela única, usar o valor total exato
            dias = intervalos[0]
            data_vencimento = data_base + timedelta(days=dias)
            
            ParcelaFinanceira.objects.create(
                titulo=self,
                numero_parcela=1,
                data_vencimento=data_vencimento,
                valor_original=self.valor_total,
                saldo_aberto=self.valor_total,
                status='ABERTO'
            )
        else:
            # Para múltiplas parcelas, dividir com arredondamento
            valor_parcela_base = (self.valor_total / self.num_parcelas).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
            total_parcelas = Decimal('0.00')
            
            for num in range(1, self.num_parcelas + 1):
                dias = intervalos[num - 1]
                data_vencimento = data_base + timedelta(days=dias)
                
                # Última parcela absorve a diferença de centavos
                if num == self.num_parcelas:
                    valor_parcela = self.valor_total - total_parcelas
                else:
                    valor_parcela = valor_parcela_base
                    total_parcelas += valor_parcela
                
                ParcelaFinanceira.objects.create(
                    titulo=self,
                    numero_parcela=num,
                    data_vencimento=data_vencimento,
                    valor_original=valor_parcela,
                    saldo_aberto=valor_parcela,
                    status='ABERTO'
                )
        
        self.atualizar_status()
    
    def atualizar_status(self):
        """Atualiza status do título baseado nas parcelas"""
        parcelas = self.parcelas.all()
        
        if not parcelas.exists():
            self.status = 'ABERTO'
        elif all(p.status == 'QUITADO' for p in parcelas):
            self.status = 'QUITADO'
        elif all(p.status == 'CANCELADO' for p in parcelas):
            self.status = 'CANCELADO'
        elif any(p.status in ['QUITADO', 'PARCIAL'] for p in parcelas):
            self.status = 'PARCIAL'
        else:
            self.status = 'ABERTO'
        
        self.save()
    
    def valor_pago(self):
        """Total já pago/recebido"""
        return self.parcelas.aggregate(
            total=Sum('valor_pago')
        )['total'] or Decimal('0.00')
    
    def saldo_aberto(self):
        """Saldo em aberto"""
        return self.parcelas.aggregate(
            total=Sum('saldo_aberto')
        )['total'] or Decimal('0.00')


class ParcelaFinanceira(models.Model):
    """
    Parcela de um Título Financeiro
    Representa cada vencimento individual
    """
    STATUS_CHOICES = [
        ('ABERTO', 'Em Aberto'),
        ('PARCIAL', 'Parcialmente Quitado'),
        ('QUITADO', 'Quitado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    titulo = models.ForeignKey(TituloFinanceiro, on_delete=models.CASCADE, related_name='parcelas', verbose_name='Título')
    numero_parcela = models.IntegerField('Nº Parcela')
    
    data_vencimento = models.DateField('Data de Vencimento')
    valor_original = models.DecimalField('Valor Original', max_digits=15, decimal_places=2)
    
    # Controle de pagamento
    valor_pago = models.DecimalField('Valor Pago', max_digits=15, decimal_places=2, default=0)
    saldo_aberto = models.DecimalField('Saldo em Aberto', max_digits=15, decimal_places=2)
    
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='ABERTO')
    
    # Régua de Cobrança
    STATUS_COBRANCA_CHOICES = [
        ('NORMAL', 'Normal'),
        ('NEGOCIACAO', 'Em Negociação'),
        ('PROMESSA', 'Promessa de Pagamento'),
        ('INTENSA', 'Cobrança Intensa'),
        ('BLOQUEADA', 'Bloqueada'),
    ]
    
    regua = models.ForeignKey('ReguaCobranca', on_delete=models.SET_NULL, null=True, blank=True, related_name='parcelas', verbose_name='Régua de Cobrança')
    regua_ativa = models.BooleanField('Régua Ativa', default=False, help_text='Ativar régua de cobrança automática')
    pausar_regua_ate = models.DateField('Pausar Régua Até', null=True, blank=True, help_text='Pausar envios até esta data')
    status_cobranca = models.CharField('Status de Cobrança', max_length=20, choices=STATUS_COBRANCA_CHOICES, default='NORMAL')
    
    # Contatos (override do cadastro da pessoa)
    contato_email_override = models.EmailField('E-mail para Cobrança', max_length=255, blank=True, null=True, help_text='Deixe em branco para usar e-mail do cliente')
    
    # Promessa de pagamento
    data_promessa_pagamento = models.DateField('Data Promessa de Pagamento', null=True, blank=True)
    observacao_promessa = models.TextField('Observação da Promessa', blank=True, null=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'parcelas_financeiras'
        verbose_name = 'Parcela Financeira'
        verbose_name_plural = 'Parcelas Financeiras'
        ordering = ['titulo', 'numero_parcela']
        indexes = [
            models.Index(fields=['titulo', 'numero_parcela']),
            models.Index(fields=['data_vencimento', 'status']),
            models.Index(fields=['status']),
        ]
        unique_together = [['titulo', 'numero_parcela']]
    
    def __str__(self):
        return f"{self.titulo.numero_documento} - Parcela {self.numero_parcela}/{self.titulo.num_parcelas}"
    
    def esta_vencida(self):
        """Verifica se está vencida"""
        return self.status == 'ABERTO' and self.data_vencimento < date.today()
    
    def dias_atraso(self):
        """Dias de atraso"""
        if self.esta_vencida():
            return (date.today() - self.data_vencimento).days
        return 0
    
    def atualizar_status(self):
        """Atualiza status baseado no saldo"""
        if self.saldo_aberto <= 0:
            self.status = 'QUITADO'
        elif self.saldo_aberto < self.valor_original:
            self.status = 'PARCIAL'
        else:
            self.status = 'ABERTO'
        self.save()
        
        # Atualiza status do título
        self.titulo.atualizar_status()
    
    def pode_enviar_cobranca(self):
        """Verifica se pode enviar cobrança"""
        # Não envia se estiver quitada ou cancelada
        if self.status in ['QUITADO', 'CANCELADO']:
            return False
        
        # Não envia se régua estiver inativa
        if not self.regua_ativa or not self.regua:
            return False
        
        # Não envia se estiver pausada
        if self.pausar_regua_ate and self.pausar_regua_ate >= date.today():
            return False
        
        # Não envia se estiver bloqueada
        if self.status_cobranca == 'BLOQUEADA':
            return False
        
        return True
    
    def get_email_cobranca(self):
        """Retorna o e-mail para cobrança"""
        if self.contato_email_override:
            return self.contato_email_override
        
        # Busca do cliente (pessoa)
        if hasattr(self.titulo, 'pessoa') and self.titulo.pessoa:
            return self.titulo.pessoa.email
        
        return None
    
    def dias_para_vencimento(self):
        """Dias até o vencimento (negativo se já venceu)"""
        delta = self.data_vencimento - date.today()
        return delta.days


class BaixaFinanceira(models.Model):
    """
    Baixa/Pagamento/Recebimento de uma parcela
    Uma parcela pode ter múltiplas baixas (parciais)
    """
    parcela = models.ForeignKey(ParcelaFinanceira, on_delete=models.PROTECT, related_name='baixas', verbose_name='Parcela')
    
    # Dados da baixa
    data_pagamento = models.DateField('Data de Pagamento', default=date.today)
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.PROTECT, verbose_name='Conta Financeira')
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.PROTECT, verbose_name='Forma de Pagamento')
    
    # Valores
    valor_principal = models.DecimalField('Valor Principal', max_digits=15, decimal_places=2, help_text='Valor da parcela sendo baixado')
    juros = models.DecimalField('Juros', max_digits=15, decimal_places=2, default=0)
    multa = models.DecimalField('Multa', max_digits=15, decimal_places=2, default=0)
    desconto = models.DecimalField('Desconto', max_digits=15, decimal_places=2, default=0)
    taxas = models.DecimalField('Taxas', max_digits=15, decimal_places=2, default=0, help_text='Taxas da forma de pagamento')
    valor_liquido = models.DecimalField('Valor Líquido', max_digits=15, decimal_places=2, help_text='Valor efetivamente movimentado')
    
    # Estorno
    estornado = models.BooleanField('Estornado', default=False)
    data_estorno = models.DateTimeField('Data do Estorno', null=True, blank=True)
    motivo_estorno = models.TextField('Motivo do Estorno', blank=True)
    estornado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='baixas_estornadas', verbose_name='Estornado por')
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='baixas_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'baixas_financeiras'
        verbose_name = 'Baixa Financeira'
        verbose_name_plural = 'Baixas Financeiras'
        ordering = ['-data_pagamento', '-id']
        indexes = [
            models.Index(fields=['parcela']),
            models.Index(fields=['data_pagamento']),
            models.Index(fields=['conta_financeira']),
            models.Index(fields=['estornado']),
        ]
    
    def __str__(self):
        return f"Baixa {self.parcela} - R$ {self.valor_liquido}"
    
    def clean(self):
        """Validações"""
        # Validação: baixa não pode exceder saldo aberto
        if self.parcela:
            saldo_disponivel = self.parcela.saldo_aberto
            
            # Se está editando, adiciona o valor da própria baixa ao saldo
            if self.pk:
                saldo_disponivel += self.valor_principal
            
            if self.valor_principal > saldo_disponivel:
                raise ValidationError(f'Valor da baixa (R$ {self.valor_principal}) excede o saldo em aberto (R$ {saldo_disponivel})')
    
    def save(self, *args, **kwargs):
        # Calcula valor líquido
        self.valor_liquido = self.valor_principal + self.juros + self.multa - self.desconto - self.taxas
        
        # Validação
        self.clean()
        
        # Salva
        super().save(*args, **kwargs)
        
        # Atualiza parcela
        self.atualizar_parcela()
        
        # Cria movimentação na conta
        self.criar_movimentacao_conta()
    
    def atualizar_parcela(self):
        """Atualiza valores da parcela"""
        # Soma todas as baixas não estornadas
        total_baixado = self.parcela.baixas.filter(estornado=False).aggregate(
            total=Sum('valor_principal')
        )['total'] or Decimal('0.00')
        
        self.parcela.valor_pago = total_baixado
        self.parcela.saldo_aberto = self.parcela.valor_original - total_baixado
        self.parcela.atualizar_status()
    
    def criar_movimentacao_conta(self):
        """Cria movimentação no extrato da conta financeira"""
        if self.estornado:
            return
        
        # Verifica se já existe movimentação para esta baixa (evita duplicatas)
        if MovimentacaoConta.objects.filter(baixa_financeira=self, estornado=False).exists():
            return
        
        tipo = 'ENTRADA' if self.parcela.titulo.tipo == 'RECEBER' else 'SAIDA'
        
        MovimentacaoConta.objects.create(
            conta_financeira=self.conta_financeira,
            tipo=tipo,
            data_movimentacao=self.data_pagamento,
            valor=self.valor_liquido,
            descricao=f"{self.parcela.titulo.get_tipo_display()} - {self.parcela.titulo.numero_documento} - Parc {self.parcela.numero_parcela}",
            baixa_financeira=self
        )
    
    def estornar(self, motivo, usuario):
        """Estorna a baixa"""
        if self.estornado:
            raise ValidationError('Esta baixa já foi estornada')
        
        self.estornado = True
        self.data_estorno = timezone.now()
        self.motivo_estorno = motivo
        self.estornado_por = usuario
        self.save()
        
        # Atualiza parcela
        self.atualizar_parcela()
        
        # Estorna movimentação da conta
        MovimentacaoConta.objects.filter(baixa_financeira=self).update(estornado=True)
        
        # Cria movimentação de estorno (reversa)
        tipo_reverso = 'SAIDA' if self.parcela.titulo.tipo == 'RECEBER' else 'ENTRADA'
        
        MovimentacaoConta.objects.create(
            conta_financeira=self.conta_financeira,
            tipo=tipo_reverso,
            data_movimentacao=date.today(),
            valor=self.valor_liquido,
            descricao=f"ESTORNO - {self.parcela.titulo.numero_documento} - Parc {self.parcela.numero_parcela} - {motivo}",
            baixa_financeira=self,
            estornado=False  # Esta movimentação representa o estorno
        )


class MovimentacaoConta(models.Model):
    """
    Movimentações (extrato interno) da conta financeira
    Gerada automaticamente pelas baixas
    """
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    ]
    
    conta_financeira = models.ForeignKey(ContaFinanceira, on_delete=models.PROTECT, related_name='movimentacoes', verbose_name='Conta Financeira')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    data_movimentacao = models.DateField('Data', db_index=True)
    
    valor = models.DecimalField('Valor', max_digits=15, decimal_places=2)
    descricao = models.CharField('Descrição', max_length=255)
    
    # Relacionamentos
    baixa_financeira = models.ForeignKey(BaixaFinanceira, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Baixa Relacionada')
    # plano_conta = models.ForeignKey(PlanoConta, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Plano de Contas')
    # centro_custo = models.ForeignKey(CentroCusto, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Centro de Custo')
    
    # Controle
    estornado = models.BooleanField('Estornado', default=False)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        db_table = 'movimentacoes_contas'
        verbose_name = 'Movimentação de Conta'
        verbose_name_plural = 'Movimentações de Contas'
        ordering = ['-data_movimentacao', '-id']
        indexes = [
            models.Index(fields=['conta_financeira', 'data_movimentacao']),
            models.Index(fields=['tipo']),
            models.Index(fields=['estornado']),
        ]
    
    def __str__(self):
        return f"{self.conta_financeira} - {self.get_tipo_display()} - R$ {self.valor}"


class TransferenciaEntreContas(models.Model):
    """Transferência entre contas financeiras"""
    data_transferencia = models.DateField('Data da Transferência', default=date.today)
    
    conta_origem = models.ForeignKey(ContaFinanceira, on_delete=models.PROTECT, related_name='transferencias_saida', verbose_name='Conta Origem')
    conta_destino = models.ForeignKey(ContaFinanceira, on_delete=models.PROTECT, related_name='transferencias_entrada', verbose_name='Conta Destino')
    
    valor = models.DecimalField('Valor', max_digits=15, decimal_places=2)
    taxa = models.DecimalField('Taxa', max_digits=10, decimal_places=2, default=0)
    
    descricao = models.CharField('Descrição', max_length=255)
    
    # Movimentações geradas
    movimentacao_saida = models.OneToOneField(MovimentacaoConta, on_delete=models.SET_NULL, null=True, related_name='transferencia_saida_rel')
    movimentacao_entrada = models.OneToOneField(MovimentacaoConta, on_delete=models.SET_NULL, null=True, related_name='transferencia_entrada_rel')
    
    estornado = models.BooleanField('Estornado', default=False)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transferencias_criadas', verbose_name='Criado por')
    
    class Meta:
        db_table = 'transferencias_entre_contas'
        verbose_name = 'Transferência entre Contas'
        verbose_name_plural = 'Transferências entre Contas'
        ordering = ['-data_transferencia', '-id']
        indexes = [
            models.Index(fields=['data_transferencia']),
            models.Index(fields=['estornado']),
        ]
    
    def __str__(self):
        return f"{self.conta_origem} → {self.conta_destino} - R$ {self.valor}"
    
    def clean(self):
        if self.conta_origem == self.conta_destino:
            raise ValidationError('Conta origem e destino não podem ser iguais')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Cria movimentações
        if not self.movimentacao_saida:
            self.movimentacao_saida = MovimentacaoConta.objects.create(
                conta_financeira=self.conta_origem,
                tipo='SAIDA',
                data_movimentacao=self.data_transferencia,
                valor=self.valor + self.taxa,
                descricao=f"Transferência para {self.conta_destino.nome} - {self.descricao}"
            )
        
        if not self.movimentacao_entrada:
            self.movimentacao_entrada = MovimentacaoConta.objects.create(
                conta_financeira=self.conta_destino,
                tipo='ENTRADA',
                data_movimentacao=self.data_transferencia,
                valor=self.valor,
                descricao=f"Transferência de {self.conta_origem.nome} - {self.descricao}"
            )
        
        super().save(*args, **kwargs)


# =========================================
# RÉGUA DE COBRANÇA
# =========================================

class ReguaCobranca(models.Model):
    """Régua de cobrança configurável com etapas"""
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.CASCADE, related_name='reguas_cobranca', verbose_name='Empresa')
    nome = models.CharField('Nome', max_length=100, help_text='Ex: Régua Padrão, Régua Clientes VIP')
    descricao = models.TextField('Descrição', blank=True, null=True)
    ativa = models.BooleanField('Ativa', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reguas_criadas', verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'reguas_cobranca'
        verbose_name = 'Régua de Cobrança'
        verbose_name_plural = 'Réguas de Cobrança'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['empresa', 'ativa']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.empresa.razao_social})"


class ReguaEtapa(models.Model):
    """Etapa de uma régua de cobrança"""
    regua = models.ForeignKey(ReguaCobranca, on_delete=models.CASCADE, related_name='etapas', verbose_name='Régua')
    ordem = models.PositiveIntegerField('Ordem', help_text='Ordem de execução')
    nome = models.CharField('Nome', max_length=100, help_text='Ex: Lembrete Amigável, Cobrança Firme')
    offset_dias = models.IntegerField('Offset em Dias', help_text='Dias relativos ao vencimento. Negativo = antes, 0 = no dia, positivo = depois')
    
    # Canal (por enquanto só e-mail)
    enviar_email = models.BooleanField('Enviar E-mail', default=True)
    
    # Templates
    assunto_email = models.CharField('Assunto do E-mail', max_length=200, blank=True, null=True)
    template_email = models.TextField('Template E-mail', blank=True, null=True, help_text='Use variáveis: {cliente_nome}, {parcela_valor}, {parcela_vencimento}, {parcela_numero}, {empresa_nome}, {dias_atraso}')
    
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        db_table = 'reguas_etapas'
        verbose_name = 'Etapa da Régua'
        verbose_name_plural = 'Etapas das Réguas'
        ordering = ['regua', 'ordem']
        unique_together = [['regua', 'ordem']]
        indexes = [
            models.Index(fields=['regua', 'ativo']),
        ]
    
    def __str__(self):
        sinal = '+' if self.offset_dias > 0 else ''
        return f"{self.regua.nome} - {self.nome} ({sinal}{self.offset_dias}d)"


class LogCobranca(models.Model):
    """Log de disparos da régua de cobrança"""
    STATUS_CHOICES = [
        ('ENFILEIRADO', 'Enfileirado'),
        ('PROCESSANDO', 'Processando'),
        ('ENVIADO', 'Enviado com Sucesso'),
        ('FALHA', 'Falha no Envio'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    CANAL_CHOICES = [
        ('EMAIL', 'E-mail'),
    ]
    
    parcela = models.ForeignKey('ParcelaFinanceira', on_delete=models.CASCADE, related_name='logs_cobranca', verbose_name='Parcela')
    etapa = models.ForeignKey(ReguaEtapa, on_delete=models.SET_NULL, null=True, related_name='logs', verbose_name='Etapa')
    
    canal = models.CharField('Canal', max_length=20, choices=CANAL_CHOICES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ENFILEIRADO')
    
    destinatario = models.CharField('Destinatário', max_length=255, help_text='E-mail do destinatário')
    assunto = models.CharField('Assunto', max_length=500, blank=True, null=True)
    mensagem = models.TextField('Mensagem Enviada', blank=True, null=True)
    
    # Controle de tentativas
    tentativas = models.PositiveIntegerField('Tentativas', default=0)
    max_tentativas = models.PositiveIntegerField('Máximo de Tentativas', default=3)
    
    # Datas
    data_criacao = models.DateTimeField('Criado em', auto_now_add=True)
    data_tentativa = models.DateTimeField('Última Tentativa', null=True, blank=True)
    data_envio = models.DateTimeField('Data de Envio', null=True, blank=True)
    
    # Erros
    erro = models.TextField('Erro', blank=True, null=True)
    
    # Provider (para futuro)
    message_id = models.CharField('ID da Mensagem', max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'logs_cobranca'
        verbose_name = 'Log de Cobrança'
        verbose_name_plural = 'Logs de Cobrança'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['parcela', 'status']),
            models.Index(fields=['status', 'data_criacao']),
            models.Index(fields=['etapa']),
        ]
    
    def __str__(self):
        return f"{self.parcela} - {self.etapa.nome if self.etapa else 'N/A'} - {self.status}"
    
    def pode_reprocessar(self):
        """Verifica se pode tentar reenviar"""
        return self.status == 'FALHA' and self.tentativas < self.max_tentativas


# =========================================
# MÓDULO DE BUDGET E CONTROLE DE LUCRATIVIDADE
# =========================================

class RegimeTributario(models.Model):
    """
    Regimes Tributários disponíveis para as empresas
    Define como os impostos são calculados
    """
    REGIME_CHOICES = [
        ('SIMPLES_NACIONAL', 'Simples Nacional'),
        ('LUCRO_PRESUMIDO', 'Lucro Presumido'),
        ('LUCRO_REAL', 'Lucro Real'),
        ('MEI', 'Microempreendedor Individual'),
    ]
    
    nome = models.CharField('Regime', max_length=30, choices=REGIME_CHOICES, unique=True)
    descricao = models.TextField('Descrição', blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'regimes_tributarios'
        verbose_name = 'Regime Tributário'
        verbose_name_plural = 'Regimes Tributários'
        ordering = ['nome']
    
    def __str__(self):
        return self.get_nome_display()


class AliquotaImposto(models.Model):
    """
    Alíquotas de impostos por regime tributário
    Permite provisionamento automático de impostos no fechamento da venda
    """
    TIPO_IMPOSTO_CHOICES = [
        ('ISS', 'ISS - Imposto Sobre Serviços'),
        ('ICMS', 'ICMS - Imposto sobre Circulação de Mercadorias'),
        ('PIS', 'PIS - Programa de Integração Social'),
        ('COFINS', 'COFINS - Contribuição para Financiamento da Seguridade Social'),
        ('IRPJ', 'IRPJ - Imposto de Renda Pessoa Jurídica'),
        ('CSLL', 'CSLL - Contribuição Social sobre Lucro Líquido'),
        ('IPI', 'IPI - Imposto sobre Produtos Industrializados'),
        ('INSS', 'INSS Patronal'),
        ('OUTROS', 'Outros Impostos'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey(
        'usuarios.Empresa', 
        on_delete=models.PROTECT, 
        related_name='aliquotas_impostos', 
        verbose_name='Empresa'
    )
    
    regime_tributario = models.ForeignKey(
        RegimeTributario, 
        on_delete=models.PROTECT, 
        related_name='aliquotas', 
        verbose_name='Regime Tributário'
    )
    
    tipo_imposto = models.CharField('Tipo de Imposto', max_length=20, choices=TIPO_IMPOSTO_CHOICES)
    aliquota_percentual = models.DecimalField(
        'Alíquota (%)', 
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentual do imposto (0 a 100%)'
    )
    
    # Base de cálculo
    base_calculo = models.CharField(
        'Base de Cálculo', 
        max_length=20,
        choices=[
            ('FATURAMENTO', 'Faturamento Bruto'),
            ('LUCRO', 'Lucro Líquido'),
            ('CUSTO_MATERIAL', 'Custo de Material'),
            ('CUSTO_SERVICO', 'Custo de Serviço'),
        ],
        default='FATURAMENTO'
    )
    
    ativo = models.BooleanField('Ativo', default=True)
    observacao = models.TextField('Observação', blank=True)
    
    # Controle de Vigência (para histórico quando empresa muda de regime)
    data_inicio_vigencia = models.DateField(
        'Data Início Vigência',
        null=True,
        blank=True,
        help_text='Data em que esta alíquota começou a valer'
    )
    data_fim_vigencia = models.DateField(
        'Data Fim Vigência',
        null=True,
        blank=True,
        help_text='Data em que esta alíquota deixou de valer (preenchido automaticamente ao mudar regime)'
    )
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='aliquotas_criadas', 
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'aliquotas_impostos'
        verbose_name = 'Alíquota de Imposto'
        verbose_name_plural = 'Alíquotas de Impostos'
        ordering = ['regime_tributario', 'tipo_imposto']
        unique_together = [('empresa', 'regime_tributario', 'tipo_imposto')]
        indexes = [
            models.Index(fields=['regime_tributario', 'ativo']),
            models.Index(fields=['tipo_imposto']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_imposto_display()} - {self.aliquota_percentual}% ({self.regime_tributario})"
    
    def calcular_valor_imposto(self, base_valor):
        """Calcula o valor do imposto sobre uma base monetária"""
        if not self.ativo:
            return Decimal('0.00')
        return (base_valor * self.aliquota_percentual / Decimal('100.00')).quantize(Decimal('0.01'))


class HistoricoRegimeEmpresa(models.Model):
    """
    Registro histórico de mudanças de regime tributário da empresa
    Permite rastrear quando e por que a empresa mudou de regime
    """
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='historico_regimes',
        verbose_name='Empresa'
    )
    
    regime_tributario = models.ForeignKey(
        RegimeTributario,
        on_delete=models.PROTECT,
        related_name='historico_uso',
        verbose_name='Regime Tributário'
    )
    
    data_inicio = models.DateField('Data de Início', help_text='Data em que o regime começou a valer')
    data_fim = models.DateField('Data de Término', null=True, blank=True, help_text='Data em que o regime deixou de valer')
    
    ativo = models.BooleanField('Regime Ativo', default=True, help_text='Apenas um regime pode estar ativo por vez')
    
    motivo_mudanca = models.TextField(
        'Motivo da Mudança',
        blank=True,
        help_text='Justificativa para mudança de regime (ex: crescimento, redução de faturamento, etc)'
    )
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mudancas_regime_criadas',
        verbose_name='Criado por'
    )
    
    class Meta:
        db_table = 'historico_regime_empresa'
        verbose_name = 'Histórico de Regime'
        verbose_name_plural = 'Históricos de Regimes'
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['data_inicio', 'data_fim']),
        ]
    
    def __str__(self):
        status = "ATIVO" if self.ativo else "INATIVO"
        return f"{self.empresa.nome_fantasia} - {self.regime_tributario.get_nome_display()} ({status})"
    
    def clean(self):
        """Validação: apenas um regime ativo por empresa"""
        if self.ativo:
            outros_ativos = HistoricoRegimeEmpresa.objects.filter(
                empresa=self.empresa,
                ativo=True
            ).exclude(pk=self.pk)
            
            if outros_ativos.exists():
                raise ValidationError('Já existe um regime ativo para esta empresa. Desative-o antes de ativar outro.')


class ProjectBudget(models.Model):
    """
    Budget (Orçamento de Execução) vinculado ao Projeto/Orçamento
    Controla custos previstos vs reais para evitar sangramento financeiro
    """
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('APROVADO', 'Aprovado'),
        ('EM_EXECUCAO', 'Em Execução'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    SEMAFORO_CHOICES = [
        ('VERDE', 'Verde - Uso < 80%'),
        ('AMARELO', 'Amarelo - Uso 80-95%'),
        ('VERMELHO', 'Vermelho - Uso > 95%'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey(
        'usuarios.Empresa', 
        on_delete=models.PROTECT, 
        related_name='budgets_projetos', 
        verbose_name='Empresa'
    )
    
    # Vinculação
    projeto = models.OneToOneField(
        'projetos.Projeto', 
        on_delete=models.PROTECT, 
        related_name='budget', 
        verbose_name='Projeto',
        null=True,
        blank=True
    )
    
    orcamento = models.ForeignKey(
        'vendas.Orcamento', 
        on_delete=models.PROTECT, 
        related_name='budgets', 
        verbose_name='Orçamento',
        null=True,
        blank=True,
        help_text='Orçamento de vendas que originou este budget'
    )
    
    # Identificação
    codigo = models.CharField('Código', max_length=50, unique=True, editable=False, blank=True)
    descricao = models.CharField('Descrição', max_length=255)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='RASCUNHO')
    
    # ===== MATERIAIS =====
    # Puxa automaticamente via engenharia de corte
    custo_aluminio_previsto = models.DecimalField(
        'Custo Alumínio Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Custo total previsto de perfis de alumínio'
    )
    custo_vidro_previsto = models.DecimalField(
        'Custo Vidro Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Custo total previsto de vidros'
    )
    custo_acessorios_previsto = models.DecimalField(
        'Custo Acessórios Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Custo total previsto de acessórios (fechaduras, dobradiças, etc)'
    )
    custo_outros_materiais_previsto = models.DecimalField(
        'Custo Outros Materiais Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Outros materiais não classificados'
    )
    
    # ===== OPERACIONAL =====
    km_estimado = models.DecimalField(
        'KM Estimado', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Quilometragem estimada para o projeto'
    )
    valor_combustivel_litro = models.DecimalField(
        'Valor Combustível/Litro', 
        max_digits=6, 
        decimal_places=2, 
        default=0,
        help_text='Valor do litro do combustível'
    )
    consumo_medio_km_litro = models.DecimalField(
        'Consumo Médio (km/L)', 
        max_digits=5, 
        decimal_places=2, 
        default=10,
        help_text='Consumo médio do veículo em km/litro'
    )
    custo_pedagios_previsto = models.DecimalField(
        'Custo Pedágios Previsto', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Estimativa de gastos com pedágios'
    )
    custo_estacionamento_previsto = models.DecimalField(
        'Custo Estacionamento Previsto', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Estimativa de gastos com estacionamento'
    )
    
    # ===== MÃO DE OBRA =====
    horas_fabricacao_previstas = models.DecimalField(
        'Horas Fabricação Previstas', 
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text='Total de horas previstas para fabricação'
    )
    valor_hora_fabricacao = models.DecimalField(
        'Valor Hora Fabricação', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Custo por hora de fabricação'
    )
    horas_montagem_previstas = models.DecimalField(
        'Horas Montagem Previstas', 
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text='Total de horas previstas para montagem/instalação'
    )
    valor_hora_montagem = models.DecimalField(
        'Valor Hora Montagem', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Custo por hora de montagem/instalação'
    )
    
    # ===== OUTROS CUSTOS =====
    custos_administrativos_previsto = models.DecimalField(
        'Custos Administrativos Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Rateio de custos administrativos'
    )
    custos_extras_previsto = models.DecimalField(
        'Custos Extras Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Margem para imprevistos'
    )
    
    # ===== TOTALIZADORES (CALCULADOS) =====
    custo_total_previsto = models.DecimalField(
        'Custo Total Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        editable=False,
        help_text='Soma de todos os custos previstos'
    )
    
    # ===== RECEITA E LUCRO =====
    valor_venda = models.DecimalField(
        'Valor de Venda', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        help_text='Valor total da venda (do orçamento aprovado)'
    )
    lucro_previsto = models.DecimalField(
        'Lucro Previsto', 
        max_digits=15, 
        decimal_places=2, 
        default=0,
        editable=False,
        help_text='Valor de Venda - Custo Total Previsto'
    )
    margem_prevista_percentual = models.DecimalField(
        'Margem Prevista (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        editable=False,
        help_text='Percentual de lucro sobre a venda'
    )
    
    # ===== CONTROLE DE USO DO BUDGET =====
    percentual_uso_budget = models.DecimalField(
        'Percentual Uso Budget (%)', 
        max_digits=5, 
        decimal_places=2, 
        default=0,
        editable=False,
        help_text='Percentual do budget já utilizado (gastos reais / custo previsto)'
    )
    semaforo = models.CharField(
        'Semáforo', 
        max_length=10, 
        choices=SEMAFORO_CHOICES, 
        default='VERDE',
        editable=False,
        help_text='Indicador visual de status do budget'
    )
    bloqueado = models.BooleanField(
        'Bloqueado', 
        default=False,
        help_text='Budget bloqueado por estourar limite (>95%)'
    )
    
    # Datas
    data_inicio_prevista = models.DateField('Data Início Prevista', null=True, blank=True)
    data_termino_prevista = models.DateField('Data Término Prevista', null=True, blank=True)
    data_inicio_real = models.DateField('Data Início Real', null=True, blank=True)
    data_termino_real = models.DateField('Data Término Real', null=True, blank=True)
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='budgets_criados', 
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='budgets_atualizados', 
        verbose_name='Atualizado por'
    )
    
    class Meta:
        db_table = 'project_budgets'
        verbose_name = 'Budget de Projeto'
        verbose_name_plural = 'Budgets de Projetos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['status', 'semaforo']),
            models.Index(fields=['projeto']),
            models.Index(fields=['orcamento']),
            models.Index(fields=['bloqueado']),
        ]
    
    def __str__(self):
        if self.projeto:
            return f"Budget {self.codigo} - Projeto {self.projeto}"
        return f"Budget {self.codigo} - {self.descricao}"
    
    def save(self, *args, **kwargs):
        # Gerar código automático se for novo budget
        if not self.pk and not self.codigo:
            self.codigo = self._gerar_codigo_automatico()
        
        # Calcular totalizadores
        self.calcular_totais()
        
        # Atualizar semáforo e bloqueio
        self.atualizar_semaforo()
        
        super().save(*args, **kwargs)
    
    def _gerar_codigo_automatico(self):
        """Gera código automático no formato BDG-YYYY-0001"""
        ano = timezone.now().year
        ultimo_budget = ProjectBudget.objects.filter(
            codigo__startswith=f'BDG-{ano}-'
        ).order_by('-codigo').first()
        
        if ultimo_budget:
            try:
                ultimo_numero = int(ultimo_budget.codigo.split('-')[-1])
                novo_numero = ultimo_numero + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        
        return f'BDG-{ano}-{novo_numero:04d}'
    
    def calcular_totais(self):
        """Calcula os totalizadores do budget"""
        # Custo Total de Materiais
        custo_materiais = (
            self.custo_aluminio_previsto +
            self.custo_vidro_previsto +
            self.custo_acessorios_previsto +
            self.custo_outros_materiais_previsto
        )
        
        # Custo Total Operacional
        # Combustível: (KM / consumo médio) * valor por litro
        if self.consumo_medio_km_litro > 0:
            custo_combustivel = (
                self.km_estimado / self.consumo_medio_km_litro
            ) * self.valor_combustivel_litro
        else:
            custo_combustivel = Decimal('0.00')
        
        custo_operacional = (
            custo_combustivel +
            self.custo_pedagios_previsto +
            self.custo_estacionamento_previsto
        )
        
        # Custo Total de Mão de Obra
        custo_mao_obra = (
            (self.horas_fabricacao_previstas * self.valor_hora_fabricacao) +
            (self.horas_montagem_previstas * self.valor_hora_montagem)
        )
        
        # Custo Total Previsto
        self.custo_total_previsto = (
            custo_materiais +
            custo_operacional +
            custo_mao_obra +
            self.custos_administrativos_previsto +
            self.custos_extras_previsto
        )
        
        # Lucro Previsto
        self.lucro_previsto = self.valor_venda - self.custo_total_previsto
        
        # Margem Prevista Percentual
        if self.valor_venda > 0:
            self.margem_prevista_percentual = (
                (self.lucro_previsto / self.valor_venda) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
        else:
            self.margem_prevista_percentual = Decimal('0.00')
    
    def calcular_percentual_uso(self):
        """Calcula percentual de uso do budget baseado em gastos reais"""
        gastos_reais = self.gastos.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
        
        if self.custo_total_previsto > 0:
            percentual = (
                (gastos_reais / self.custo_total_previsto) * Decimal('100.00')
            ).quantize(Decimal('0.01'))
            self.percentual_uso_budget = percentual
        else:
            self.percentual_uso_budget = Decimal('0.00')
        
        return self.percentual_uso_budget
    
    def atualizar_semaforo(self):
        """Atualiza semáforo e status de bloqueio baseado no percentual de uso"""
        self.calcular_percentual_uso()
        
        if self.percentual_uso_budget < 80:
            self.semaforo = 'VERDE'
            self.bloqueado = False
        elif self.percentual_uso_budget < 95:
            self.semaforo = 'AMARELO'
            self.bloqueado = False
        else:
            self.semaforo = 'VERMELHO'
            # Bloqueia automaticamente se estourar 95%
            if self.status == 'EM_EXECUCAO':
                self.bloqueado = True
    
    def get_custo_material_total(self):
        """Retorna custo total de materiais"""
        return (
            self.custo_aluminio_previsto +
            self.custo_vidro_previsto +
            self.custo_acessorios_previsto +
            self.custo_outros_materiais_previsto
        )
    
    def get_custo_operacional_total(self):
        """Retorna custo operacional total"""
        if self.consumo_medio_km_litro > 0:
            custo_combustivel = (
                self.km_estimado / self.consumo_medio_km_litro
            ) * self.valor_combustivel_litro
        else:
            custo_combustivel = Decimal('0.00')
        
        return (
            custo_combustivel +
            self.custo_pedagios_previsto +
            self.custo_estacionamento_previsto
        )
    
    def get_custo_mao_obra_total(self):
        """Retorna custo total de mão de obra"""
        return (
            (self.horas_fabricacao_previstas * self.valor_hora_fabricacao) +
            (self.horas_montagem_previstas * self.valor_hora_montagem)
        )
    
    def pode_lancar_despesa(self):
        """Verifica se pode lançar nova despesa (não está bloqueado)"""
        return not self.bloqueado


class ProjectExpense(models.Model):
    """
    Lançamentos reais de despesas do projeto
    Registra gastos efetivos (KM, horas trabalhadas, compras extras, etc)
    """
    TIPO_DESPESA_CHOICES = [
        ('MATERIAL', 'Material'),
        ('MAO_OBRA', 'Mão de Obra'),
        ('COMBUSTIVEL', 'Combustível'),
        ('PEDAGIO', 'Pedágio'),
        ('ESTACIONAMENTO', 'Estacionamento'),
        ('ALIMENTACAO', 'Alimentação'),
        ('HOSPEDAGEM', 'Hospedagem'),
        ('RETRABALHO', 'Retrabalho'),
        ('DESPERDICIO', 'Desperdício de Material'),
        ('OUTROS', 'Outros'),
    ]
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente Aprovação'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
        ('PAGO', 'Pago'),
    ]
    
    # Multiempresa
    empresa = models.ForeignKey(
        'usuarios.Empresa', 
        on_delete=models.PROTECT, 
        related_name='despesas_projetos', 
        verbose_name='Empresa'
    )
    
    # Vinculação ao Budget
    budget = models.ForeignKey(
        ProjectBudget, 
        on_delete=models.PROTECT, 
        related_name='gastos', 
        verbose_name='Budget'
    )
    
    # Identificação
    tipo_despesa = models.CharField('Tipo de Despesa', max_length=20, choices=TIPO_DESPESA_CHOICES)
    descricao = models.CharField('Descrição', max_length=255)
    valor = models.DecimalField(
        'Valor', 
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Dados específicos por tipo
    # Para COMBUSTIVEL
    km_rodado = models.DecimalField(
        'KM Rodado', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Quilometragem rodada (via GPS se disponível)'
    )
    litros_abastecidos = models.DecimalField(
        'Litros Abastecidos', 
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Para MAO_OBRA
    horas_trabalhadas = models.DecimalField(
        'Horas Trabalhadas', 
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    funcionario = models.ForeignKey(
        'cadastros.Pessoa', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        limit_choices_to={'funcionario': True},
        verbose_name='Funcionário',
        related_name='despesas_trabalho'
    )
    
    # Comprovação
    recibo_imagem = models.ImageField(
        'Imagem do Recibo', 
        upload_to='budgets/recibos/%Y/%m/', 
        null=True, 
        blank=True,
        help_text='Upload de foto/scan do recibo'
    )
    numero_nota_fiscal = models.CharField(
        'Número da Nota Fiscal', 
        max_length=50, 
        blank=True
    )
    
    # Geolocalização (Check-in/Check-out)
    latitude = models.DecimalField(
        'Latitude', 
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        'Longitude', 
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True
    )
    local_descricao = models.CharField(
        'Descrição do Local', 
        max_length=255, 
        blank=True,
        help_text='Endereço ou descrição do local'
    )
    
    # Controle
    data_despesa = models.DateField('Data da Despesa', default=date.today)
    data_hora_registro = models.DateTimeField('Data/Hora Registro', auto_now_add=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Aprovação
    aprovado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='despesas_aprovadas',
        verbose_name='Aprovado por'
    )
    data_aprovacao = models.DateTimeField('Data Aprovação', null=True, blank=True)
    justificativa_rejeicao = models.TextField('Justificativa Rejeição', blank=True)
    
    # Observações
    observacao = models.TextField('Observação', blank=True)
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='despesas_criadas', 
        verbose_name='Criado por'
    )
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'project_expenses'
        verbose_name = 'Despesa de Projeto'
        verbose_name_plural = 'Despesas de Projetos'
        ordering = ['-data_despesa', '-criado_em']
        indexes = [
            models.Index(fields=['budget', 'status']),
            models.Index(fields=['tipo_despesa']),
            models.Index(fields=['data_despesa']),
            models.Index(fields=['funcionario']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_despesa_display()} - {self.descricao} - R$ {self.valor}"
    
    def save(self, *args, **kwargs):
        # Se aprovado, registrar data e usuário
        if self.status == 'APROVADO' and not self.data_aprovacao:
            self.data_aprovacao = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Atualizar semáforo do budget após salvar
        self.budget.atualizar_semaforo()
        self.budget.save(update_fields=['percentual_uso_budget', 'semaforo', 'bloqueado'])
    
    def aprovar(self, usuario):
        """Aprova a despesa"""
        self.status = 'APROVADO'
        self.aprovado_por = usuario
        self.data_aprovacao = timezone.now()
        self.save()
    
    def rejeitar(self, usuario, justificativa):
        """Rejeita a despesa"""
        self.status = 'REJEITADO'
        self.aprovado_por = usuario
        self.data_aprovacao = timezone.now()
        self.justificativa_rejeicao = justificativa
        self.save()


class JustificativaBudget(models.Model):
    """
    Justificativas para estouro de budget
    Requer aprovação de administrador quando budget > 95%
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente Análise'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    ]
    
    MOTIVO_CHOICES = [
        ('AUMENTO_ESCOPO', 'Aumento de Escopo'),
        ('ERRO_ORCAMENTO', 'Erro no Orçamento Original'),
        ('VARIACAO_PRECO', 'Variação de Preço de Insumos'),
        ('RETRABALHO', 'Retrabalho Necessário'),
        ('IMPREVISTO', 'Imprevisto na Obra'),
        ('SOLICITACAO_CLIENTE', 'Solicitação Extra do Cliente'),
        ('OUTROS', 'Outros Motivos'),
    ]
    
    # Vinculação
    budget = models.ForeignKey(
        ProjectBudget, 
        on_delete=models.PROTECT, 
        related_name='justificativas', 
        verbose_name='Budget'
    )
    
    # Justificativa
    motivo = models.CharField('Motivo', max_length=30, choices=MOTIVO_CHOICES)
    descricao = models.TextField('Descrição Detalhada')
    valor_adicional_necessario = models.DecimalField(
        'Valor Adicional Necessário', 
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Quanto a mais será necessário gastar'
    )
    
    # Anexos
    documento_comprobatorio = models.FileField(
        'Documento Comprobatório', 
        upload_to='budgets/justificativas/%Y/%m/', 
        null=True, 
        blank=True
    )
    
    # Status e Aprovação
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_solicitacao = models.DateTimeField('Data Solicitação', auto_now_add=True)
    solicitado_por = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='justificativas_solicitadas', 
        verbose_name='Solicitado por'
    )
    
    # Análise
    aprovado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='justificativas_analisadas',
        verbose_name='Analisado por'
    )
    data_analise = models.DateTimeField('Data Análise', null=True, blank=True)
    parecer = models.TextField('Parecer', blank=True)
    
    class Meta:
        db_table = 'justificativas_budget'
        verbose_name = 'Justificativa de Budget'
        verbose_name_plural = 'Justificativas de Budget'
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['budget', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Justificativa {self.budget.codigo} - {self.get_motivo_display()}"
    
    def aprovar(self, usuario, parecer=''):
        """Aprova a justificativa e desbloqueia o budget"""
        self.status = 'APROVADO'
        self.aprovado_por = usuario
        self.data_analise = timezone.now()
        self.parecer = parecer
        self.save()
        
        # Desbloquear budget
        self.budget.bloqueado = False
        self.budget.save(update_fields=['bloqueado'])
    
    def rejeitar(self, usuario, parecer):
        """Rejeita a justificativa"""
        self.status = 'REJEITADO'
        self.aprovado_por = usuario
        self.data_analise = timezone.now()
        self.parecer = parecer
        self.save()
