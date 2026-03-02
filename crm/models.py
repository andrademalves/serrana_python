from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Empresa
from cadastros.models import Pessoa


class Pipeline(models.Model):
    """Funil de vendas (pode ter múltiplos por empresa)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pipelines')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    padrao = models.BooleanField(default=False, help_text='Pipeline padrão para novos cards')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pipelines_criados')
    
    class Meta:
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering = ['empresa', 'nome']
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.empresa.nome_fantasia})"


class EtapaFunil(models.Model):
    """Etapas/Colunas do Kanban"""
    TIPO_FINAL_CHOICES = [
        ('ganho', 'Ganho (Deal fechado)'),
        ('perdido', 'Perdido (Deal não fechado)'),
        ('none', 'Não é final'),
    ]
    
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='etapas')
    nome = models.CharField(max_length=100)
    ordem = models.IntegerField(default=0)
    cor = models.CharField(max_length=7, default='#3498db', help_text='Cor em hexadecimal (#RRGGBB)')
    
    is_final = models.BooleanField(default=False, help_text='Etapa final do funil')
    tipo_final = models.CharField(max_length=10, choices=TIPO_FINAL_CHOICES, default='none')
    
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Etapa do Funil'
        verbose_name_plural = 'Etapas do Funil'
        ordering = ['pipeline', 'ordem', 'nome']
        indexes = [
            models.Index(fields=['pipeline', 'ordem']),
            models.Index(fields=['pipeline', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.pipeline.nome})"


class Oportunidade(models.Model):
    """Lead/Oportunidade - Card do Kanban"""
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('ganho', 'Ganho'),
        ('perdido', 'Perdido'),
        ('cancelado', 'Cancelado'),
    ]
    
    ORIGEM_CHOICES = [
        ('site', 'Site'),
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('indicacao', 'Indicação'),
        ('rede_social', 'Rede Social'),
        ('visita', 'Visita Presencial'),
        ('evento', 'Evento'),
        ('outro', 'Outro'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='oportunidades')
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='oportunidades')
    etapa = models.ForeignKey(EtapaFunil, on_delete=models.PROTECT, related_name='oportunidades')
    
    # Dados do Lead
    cliente = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='oportunidades', help_text='Cliente cadastrado (opcional)')
    nome_contato = models.CharField(max_length=200, help_text='Nome do contato principal')
    empresa_contato = models.CharField(max_length=200, blank=True, help_text='Nome da empresa do lead')
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Dados comerciais
    titulo = models.CharField(max_length=200, help_text='Título/resumo da oportunidade')
    descricao = models.TextField(blank=True)
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default='outro')
    valor_estimado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Novos campos para BI e previsões
    valor_previsto = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Valor previsto para este negócio'
    )
    valor_fechado = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Valor real quando fechado'
    )
    probabilidade_conversao = models.IntegerField(
        default=50,
        help_text='Probabilidade de conversão (0-100%)',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    numero_projeto = models.CharField(
        max_length=50, 
        blank=True,
        help_text='Número do projeto quando convertido'
    )
    
    # Controle
    responsavel = models.ForeignKey(User, on_delete=models.PROTECT, related_name='oportunidades_responsavel')
    primeiro_atendente = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='oportunidades_primeiro_atendente',
        help_text='Primeiro responsável/atendente que criou o lead'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    
    # Integração com Orçamento/Projeto
    orcamento = models.ForeignKey('projetos.Orcamento', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='oportunidade_origem')
    projeto = models.ForeignKey('projetos.Projeto', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='oportunidade_origem')
    
    # Datas
    data_entrada = models.DateTimeField(default=timezone.now)
    data_prevista_fechamento = models.DateField(null=True, blank=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='oportunidades_criadas')
    
    class Meta:
        verbose_name = 'Oportunidade'
        verbose_name_plural = 'Oportunidades'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['empresa', 'etapa', 'responsavel']),
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['responsavel', 'status']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['data_entrada']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.nome_contato}"
    
    def save(self, *args, **kwargs):
        # Atualizar status baseado na etapa
        if self.etapa.is_final:
            if self.etapa.tipo_final == 'ganho':
                self.status = 'ganho'
                if not self.data_fechamento:
                    self.data_fechamento = timezone.now()
            elif self.etapa.tipo_final == 'perdido':
                self.status = 'perdido'
                if not self.data_fechamento:
                    self.data_fechamento = timezone.now()
        
        super().save(*args, **kwargs)


class AtividadeCRM(models.Model):
    """Registro de atividades/interações (mini CRM)"""
    TIPO_CHOICES = [
        ('nota', 'Nota/Observação'),
        ('ligacao', 'Ligação'),
        ('email', 'E-mail'),
        ('reuniao', 'Reunião'),
        ('whatsapp', 'WhatsApp'),
        ('visita', 'Visita'),
        ('proposta', 'Proposta Enviada'),
        ('negociacao', 'Negociação'),
        ('outro', 'Outro'),
    ]
    
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, related_name='atividades')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='nota')
    titulo = models.CharField(max_length=200, blank=True)
    descricao = models.TextField()
    
    data_atividade = models.DateTimeField(default=timezone.now)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Atividade CRM'
        verbose_name_plural = 'Atividades CRM'
        ordering = ['-data_atividade']
        indexes = [
            models.Index(fields=['oportunidade', '-data_atividade']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.oportunidade.titulo} ({self.data_atividade.strftime('%d/%m/%Y')})"


class AlertaRetorno(models.Model):
    """Alertas/Tarefas/Lembretes por oportunidade"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, related_name='alertas')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    
    data_hora = models.DateTimeField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')
    
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='alertas_criados')
    concluido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertas_concluidos')
    concluido_em = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Alerta/Tarefa'
        verbose_name_plural = 'Alertas/Tarefas'
        ordering = ['data_hora', '-prioridade']
        indexes = [
            models.Index(fields=['oportunidade', 'status']),
            models.Index(fields=['data_hora', 'status']),
            models.Index(fields=['criado_por', 'status']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.oportunidade.titulo}"
    
    def marcar_concluido(self, usuario):
        """Marca alerta como concluído"""
        self.status = 'concluido'
        self.concluido_por = usuario
        self.concluido_em = timezone.now()
        self.save()


class AnexoOportunidade(models.Model):
    """Anexos/Arquivos por oportunidade"""
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='crm/anexos/%Y/%m/')
    descricao = models.CharField(max_length=200, blank=True)
    
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.descricao or self.arquivo.name} - {self.oportunidade.titulo}"


class HistoricoEtapa(models.Model):
    """Histórico de mudanças de etapa (auditoria)"""
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, related_name='historico_etapas')
    etapa_de = models.ForeignKey(EtapaFunil, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='historico_saida')
    etapa_para = models.ForeignKey(EtapaFunil, on_delete=models.SET_NULL, null=True,
                                  related_name='historico_entrada')
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Histórico de Etapa'
        verbose_name_plural = 'Históricos de Etapas'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['oportunidade', '-data_hora']),
        ]
    
    def __str__(self):
        etapa_de_nome = self.etapa_de.nome if self.etapa_de else 'Nova'
        etapa_para_nome = self.etapa_para.nome if self.etapa_para else 'Removida'
        return f"{self.oportunidade.titulo}: {etapa_de_nome} → {etapa_para_nome}"


class MetaVendedor(models.Model):
    """Metas mensais por vendedor"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='metas_vendedores')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas_vendas')
    
    # Período
    mes = models.IntegerField(help_text='Mês (1-12)')
    ano = models.IntegerField(help_text='Ano')
    
    # Metas
    meta_valor = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text='Meta de valor a ser fechado no mês'
    )
    meta_quantidade = models.IntegerField(
        default=0,
        help_text='Meta de quantidade de negócios a fechar'
    )
    
    # Controle
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='metas_criadas'
    )
    
    class Meta:
        verbose_name = 'Meta de Vendedor'
        verbose_name_plural = 'Metas de Vendedores'
        ordering = ['-ano', '-mes', 'vendedor__first_name']
        unique_together = [['empresa', 'vendedor', 'mes', 'ano']]
        indexes = [
            models.Index(fields=['empresa', 'vendedor', '-ano', '-mes']),
            models.Index(fields=['empresa', '-ano', '-mes']),
        ]
    
    def __str__(self):
        return f"{self.vendedor.get_full_name() or self.vendedor.username} - {self.mes:02d}/{self.ano}"
    
    def calcular_realizado(self):
        """Calcula o realizado do vendedor no período da meta"""
        from django.db.models import Sum, Count, Q
        from datetime import date
        
        # Data inicial e final do mês
        data_inicio = date(self.ano, self.mes, 1)
        if self.mes == 12:
            data_fim = date(self.ano + 1, 1, 1)
        else:
            data_fim = date(self.ano, self.mes + 1, 1)
        
        # Oportunidades fechadas (ganhas) no período
        oportunidades_fechadas = Oportunidade.objects.filter(
            empresa=self.empresa,
            responsavel=self.vendedor,
            status='ganho',
            data_fechamento__gte=data_inicio,
            data_fechamento__lt=data_fim
        )
        
        resultado = oportunidades_fechadas.aggregate(
            valor_total=Sum('valor_fechado'),
            quantidade=Count('id')
        )
        
        return {
            'valor': resultado['valor_total'] or 0,
            'quantidade': resultado['quantidade'] or 0,
            'percentual_valor': (float(resultado['valor_total'] or 0) / float(self.meta_valor) * 100) if self.meta_valor > 0 else 0,
            'percentual_quantidade': (resultado['quantidade'] / self.meta_quantidade * 100) if self.meta_quantidade > 0 else 0,
        }


class EtapaFunilConfig(models.Model):
    """Configuração adicional por etapa (probabilidade de conversão, etc)"""
    etapa = models.OneToOneField(EtapaFunil, on_delete=models.CASCADE, related_name='config')
    
    # Probabilidade padrão de conversão nesta etapa (%)
    probabilidade_padrao = models.IntegerField(
        default=50,
        help_text='Probabilidade padrão de conversão nesta etapa (0-100%)',
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # SLA (tempo médio esperado nesta etapa - em dias)
    sla_dias = models.IntegerField(
        default=7,
        help_text='Tempo médio esperado nesta etapa (em dias)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Etapa'
        verbose_name_plural = 'Configurações de Etapas'
    
    def __str__(self):
        return f"Config: {self.etapa.nome} ({self.probabilidade_padrao}%)"
