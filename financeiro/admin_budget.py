"""
Admin para módulo de Budget e Controle de Lucratividade
Gerenciamento via Django Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal

from .models import (
    RegimeTributario, AliquotaImposto, ProjectBudget, 
    ProjectExpense, JustificativaBudget
)


# ============================================================================
# REGIME TRIBUTÁRIO
# ============================================================================

@admin.register(RegimeTributario)
class RegimeTributarioAdmin(admin.ModelAdmin):
    """Admin para Regime Tributário"""
    
    list_display = ['nome_display', 'descricao_curta', 'ativo', 'total_empresas']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    
    fieldsets = [
        ('Informações Básicas', {
            'fields': ['nome', 'descricao', 'ativo']
        }),
        ('Auditoria', {
            'fields': ['criado_em', 'atualizado_em'],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['criado_em', 'atualizado_em']
    
    def nome_display(self, obj):
        return obj.get_nome_display()
    nome_display.short_description = 'Regime'
    
    def descricao_curta(self, obj):
        return obj.descricao[:80] + '...' if len(obj.descricao) > 80 else obj.descricao
    descricao_curta.short_description = 'Descrição'
    
    def total_empresas(self, obj):
        from usuarios.models import Empresa
        count = Empresa.objects.filter(regime_tributario=obj).count()
        return format_html('<b>{}</b> empresa(s)', count)
    total_empresas.short_description = 'Empresas'


# ============================================================================
# ALÍQUOTA DE IMPOSTO
# ============================================================================

@admin.register(AliquotaImposto)
class AliquotaImpostoAdmin(admin.ModelAdmin):
    """Admin para Alíquota de Imposto"""
    
    list_display = [
        'tipo_imposto_display', 'regime_tributario', 'empresa',
        'aliquota_display', 'base_calculo_display', 'ativo_badge'
    ]
    list_filter = ['regime_tributario', 'tipo_imposto', 'base_calculo', 'ativo', 'empresa']
    search_fields = ['tipo_imposto', 'observacao']
    
    fieldsets = [
        ('Identificação', {
            'fields': ['empresa', 'regime_tributario', 'tipo_imposto']
        }),
        ('Configuração', {
            'fields': ['aliquota_percentual', 'base_calculo', 'ativo']
        }),
        ('Observações', {
            'fields': ['observacao']
        }),
        ('Auditoria', {
            'fields': ['criado_em', 'criado_por', 'atualizado_em'],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['criado_em', 'atualizado_em']
    autocomplete_fields = ['empresa']
    
    def tipo_imposto_display(self, obj):
        return obj.get_tipo_imposto_display()
    tipo_imposto_display.short_description = 'Tipo de Imposto'
    
    def aliquota_display(self, obj):
        return format_html('<b>{:.2f}%</b>', obj.aliquota_percentual)
    aliquota_display.short_description = 'Alíquota'
    
    def base_calculo_display(self, obj):
        return obj.get_base_calculo_display()
    base_calculo_display.short_description = 'Base'
    
    def ativo_badge(self, obj):
        if obj.ativo:
            return format_html('<span style="color: green;">● Ativo</span>')
        return format_html('<span style="color: red;">● Inativo</span>')
    ativo_badge.short_description = 'Status'


# ============================================================================
# PROJECT BUDGET
# ============================================================================

class ProjectExpenseInline(admin.TabularInline):
    """Inline para despesas do budget"""
    model = ProjectExpense
    extra = 0
    fields = [
        'tipo_despesa', 'descricao', 'valor', 'data_despesa', 
        'status', 'funcionario'
    ]
    readonly_fields = ['criado_em']
    autocomplete_fields = ['funcionario']


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    """Admin para Budget de Projeto"""
    
    list_display = [
        'codigo', 'descricao_curta', 'empresa', 'status_badge',
        'valor_venda_display', 'custo_previsto_display',
        'margem_display', 'semaforo_display', 'bloqueado_badge'
    ]
    list_filter = ['status', 'semaforo', 'bloqueado', 'empresa']
    search_fields = ['codigo', 'descricao', 'projeto__codigo']
    date_hierarchy = 'criado_em'
    
    fieldsets = [
        ('Identificação', {
            'fields': [
                ('codigo', 'status'),
                'empresa',
                ('projeto', 'orcamento'),
                'descricao'
            ]
        }),
        ('💰 Materiais', {
            'fields': [
                ('custo_aluminio_previsto', 'custo_vidro_previsto'),
                ('custo_acessorios_previsto', 'custo_outros_materiais_previsto')
            ]
        }),
        ('🚗 Operacional', {
            'fields': [
                ('km_estimado', 'consumo_medio_km_litro', 'valor_combustivel_litro'),
                ('custo_pedagios_previsto', 'custo_estacionamento_previsto')
            ]
        }),
        ('👷 Mão de Obra', {
            'fields': [
                ('horas_fabricacao_previstas', 'valor_hora_fabricacao'),
                ('horas_montagem_previstas', 'valor_hora_montagem')
            ]
        }),
        ('📊 Totalizadores (Calculados)', {
            'fields': [
                ('custo_total_previsto', 'valor_venda'),
                ('lucro_previsto', 'margem_prevista_percentual')
            ],
            'classes': ['collapse']
        }),
        ('🚦 Controle de Budget', {
            'fields': [
                ('percentual_uso_budget', 'semaforo'),
                'bloqueado'
            ],
            'classes': ['collapse']
        }),
        ('📅 Datas', {
            'fields': [
                ('data_inicio_prevista', 'data_termino_prevista'),
                ('data_inicio_real', 'data_termino_real')
            ],
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ['observacao'],
            'classes': ['collapse']
        }),
        ('Auditoria', {
            'fields': [
                ('criado_em', 'criado_por'),
                ('atualizado_em', 'atualizado_por')
            ],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = [
        'codigo', 'custo_total_previsto', 'lucro_previsto', 
        'margem_prevista_percentual', 'percentual_uso_budget',
        'semaforo', 'criado_em', 'atualizado_em'
    ]
    
    autocomplete_fields = ['empresa', 'projeto']
    inlines = [ProjectExpenseInline]
    
    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'
    
    def status_badge(self, obj):
        colors = {
            'RASCUNHO': 'gray',
            'APROVADO': 'blue',
            'EM_EXECUCAO': 'orange',
            'FINALIZADO': 'green',
            'CANCELADO': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def valor_venda_display(self, obj):
        return format_html('<b>R$ {:,.2f}</b>', obj.valor_venda)
    valor_venda_display.short_description = 'Venda'
    
    def custo_previsto_display(self, obj):
        return format_html('R$ {:,.2f}', obj.custo_total_previsto)
    custo_previsto_display.short_description = 'Custo Previsto'
    
    def margem_display(self, obj):
        if obj.margem_prevista_percentual < 0:
            color = 'red'
        elif obj.margem_prevista_percentual < 20:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}%</span>',
            color, obj.margem_prevista_percentual
        )
    margem_display.short_description = 'Margem'
    
    def semaforo_display(self, obj):
        icons = {
            'VERDE': '🟢',
            'AMARELO': '🟡',
            'VERMELHO': '🔴'
        }
        return format_html(
            '{} {} ({:.1f}%)',
            icons.get(obj.semaforo, '⚪'),
            obj.get_semaforo_display(),
            obj.percentual_uso_budget
        )
    semaforo_display.short_description = 'Semáforo'
    
    def bloqueado_badge(self, obj):
        if obj.bloqueado:
            return format_html('<span style="color: red; font-weight: bold;">🔒 SIM</span>')
        return format_html('<span style="color: green;">✓ Não</span>')
    bloqueado_badge.short_description = 'Bloqueado'


# ============================================================================
# PROJECT EXPENSE
# ============================================================================

@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    """Admin para Despesas de Projeto"""
    
    list_display = [
        'id', 'budget_display', 'tipo_despesa_badge', 'descricao_curta',
        'valor_display', 'data_despesa', 'status_badge', 'funcionario'
    ]
    list_filter = ['tipo_despesa', 'status', 'data_despesa', 'empresa']
    search_fields = ['descricao', 'budget__codigo', 'funcionario__nome']
    date_hierarchy = 'data_despesa'
    
    fieldsets = [
        ('Identificação', {
            'fields': [
                'empresa',
                'budget',
                ('tipo_despesa', 'status'),
                'descricao',
                'valor'
            ]
        }),
        ('Detalhes Específicos', {
            'fields': [
                ('km_rodado', 'litros_abastecidos'),
                ('horas_trabalhadas', 'funcionario')
            ],
            'classes': ['collapse']
        }),
        ('Comprovação', {
            'fields': [
                'recibo_imagem',
                'numero_nota_fiscal'
            ],
            'classes': ['collapse']
        }),
        ('Geolocalização', {
            'fields': [
                ('latitude', 'longitude'),
                'local_descricao'
            ],
            'classes': ['collapse']
        }),
        ('Aprovação/Rejeição', {
            'fields': [
                ('aprovado_por', 'data_aprovacao'),
                'justificativa_rejeicao'
            ],
            'classes': ['collapse']
        }),
        ('Observações', {
            'fields': ['observacao'],
            'classes': ['collapse']
        }),
        ('Auditoria', {
            'fields': [
                ('criado_em', 'criado_por'),
                'atualizado_em'
            ],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['criado_em', 'atualizado_em', 'data_hora_registro']
    autocomplete_fields = ['empresa', 'budget', 'funcionario']
    
    def budget_display(self, obj):
        return format_html('<b>{}</b>', obj.budget.codigo)
    budget_display.short_description = 'Budget'
    
    def tipo_despesa_badge(self, obj):
        icons = {
            'MATERIAL': '📦',
            'MAO_OBRA': '👷',
            'COMBUSTIVEL': '⛽',
            'PEDAGIO': '🛣️',
            'RETRABALHO': '🔧',
            'DESPERDICIO': '⚠️'
        }
        icon = icons.get(obj.tipo_despesa, '📄')
        return format_html('{} {}', icon, obj.get_tipo_despesa_display())
    tipo_despesa_badge.short_description = 'Tipo'
    
    def descricao_curta(self, obj):
        return obj.descricao[:40] + '...' if len(obj.descricao) > 40 else obj.descricao
    descricao_curta.short_description = 'Descrição'
    
    def valor_display(self, obj):
        return format_html('<b>R$ {:,.2f}</b>', obj.valor)
    valor_display.short_description = 'Valor'
    
    def status_badge(self, obj):
        colors = {
            'PENDENTE': 'orange',
            'APROVADO': 'green',
            'REJEITADO': 'red',
            'PAGO': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['aprovar_selecionados', 'rejeitar_selecionados']
    
    def aprovar_selecionados(self, request, queryset):
        """Action para aprovar despesas em lote"""
        count = 0
        for despesa in queryset.filter(status='PENDENTE'):
            despesa.aprovar(request.user)
            count += 1
        self.message_user(request, f'{count} despesa(s) aprovada(s) com sucesso.')
    aprovar_selecionados.short_description = '✓ Aprovar despesas selecionadas'
    
    def rejeitar_selecionados(self, request, queryset):
        """Action para rejeitar despesas em lote"""
        count = 0
        for despesa in queryset.filter(status='PENDENTE'):
            despesa.rejeitar(request.user, 'Rejeitado em lote via admin')
            count += 1
        self.message_user(request, f'{count} despesa(s) rejeitada(s).')
    rejeitar_selecionados.short_description = '✗ Rejeitar despesas selecionadas'


# ============================================================================
# JUSTIFICATIVA DE BUDGET
# ============================================================================

@admin.register(JustificativaBudget)
class JustificativaBudgetAdmin(admin.ModelAdmin):
    """Admin para Justificativas de Budget"""
    
    list_display = [
        'id', 'budget_display', 'motivo_badge', 'valor_adicional_display',
        'status_badge', 'solicitado_por', 'data_solicitacao'
    ]
    list_filter = ['status', 'motivo', 'data_solicitacao']
    search_fields = ['descricao', 'budget__codigo', 'solicitado_por__username']
    date_hierarchy = 'data_solicitacao'
    
    fieldsets = [
        ('Informações da Justificativa', {
            'fields': [
                'budget',
                ('motivo', 'status'),
                'descricao',
                'valor_adicional_necessario',
                'documento_comprobatorio'
            ]
        }),
        ('Solicitação', {
            'fields': [
                ('data_solicitacao', 'solicitado_por')
            ]
        }),
        ('Análise', {
            'fields': [
                ('aprovado_por', 'data_analise'),
                'parecer'
            ],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['data_solicitacao', 'data_analise']
    autocomplete_fields = ['budget', 'solicitado_por', 'aprovado_por']
    
    def budget_display(self, obj):
        return format_html(
            '<b>{}</b><br><small>{}</small>',
            obj.budget.codigo,
            obj.budget.descricao[:30]
        )
    budget_display.short_description = 'Budget'
    
    def motivo_badge(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.get_motivo_display()
        )
    motivo_badge.short_description = 'Motivo'
    
    def valor_adicional_display(self, obj):
        return format_html('<b>R$ {:,.2f}</b>', obj.valor_adicional_necessario)
    valor_adicional_display.short_description = 'Valor Adicional'
    
    def status_badge(self, obj):
        colors = {
            'PENDENTE': 'orange',
            'APROVADO': 'green',
            'REJEITADO': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['aprovar_selecionadas', 'rejeitar_selecionadas']
    
    def aprovar_selecionadas(self, request, queryset):
        """Action para aprovar justificativas em lote"""
        count = 0
        for justificativa in queryset.filter(status='PENDENTE'):
            justificativa.aprovar(request.user, 'Aprovado em lote via admin')
            count += 1
        self.message_user(request, f'{count} justificativa(s) aprovada(s). Budgets desbloqueados.')
    aprovar_selecionadas.short_description = '✓ Aprovar justificativas selecionadas'
    
    def rejeitar_selecionadas(self, request, queryset):
        """Action para rejeitar justificativas em lote"""
        count = 0
        for justificativa in queryset.filter(status='PENDENTE'):
            justificativa.rejeitar(request.user, 'Rejeitado em lote via admin')
            count += 1
        self.message_user(request, f'{count} justificativa(s) rejeitada(s).')
    rejeitar_selecionadas.short_description = '✗ Rejeitar justificativas selecionadas'
