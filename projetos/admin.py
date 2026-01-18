from django.contrib import admin
from .models import Orcamento, OrcamentoItem, OrcamentoParcela, OrcamentoHistorico, Projeto, DiarioObra


class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1


class OrcamentoParcelaInline(admin.TabularInline):
    model = OrcamentoParcela
    extra = 1


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'vendedor', 'data_orcamento', 'valor_total', 'desconto', 'valor_final', 'status']
    list_filter = ['status', 'tipo_desconto', 'data_orcamento']
    search_fields = ['codigo', 'cliente__nome', 'vendedor__nome']
    readonly_fields = ['codigo', 'desconto', 'valor_final', 'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    inlines = [OrcamentoItemInline, OrcamentoParcelaInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'cliente', 'vendedor', 'data_orcamento', 'validade_dias', 'status')
        }),
        ('Valores', {
            'fields': ('valor_total', 'tipo_desconto', 'desconto_valor', 'desconto', 'valor_final')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrcamentoHistorico)
class OrcamentoHistoricoAdmin(admin.ModelAdmin):
    list_display = ['orcamento', 'acao', 'usuario', 'timestamp']
    list_filter = ['acao', 'timestamp']
    search_fields = ['orcamento__codigo']
    readonly_fields = ['orcamento', 'usuario', 'timestamp', 'acao', 'diff']
    
    def has_add_permission(self, request):
        return False  # Não permite criar manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Não permite editar


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'status']
    list_filter = ['status']
    search_fields = ['codigo', 'cliente__nome']


@admin.register(DiarioObra)
class DiarioObraAdmin(admin.ModelAdmin):
    list_display = ['projeto', 'data', 'periodo', 'clima', 'num_trabalhadores', 'percentual_progresso', 'epi_utilizado', 'criado_por']
    list_filter = ['data', 'periodo', 'clima', 'epi_utilizado']
    search_fields = ['projeto__codigo', 'projeto__descricao', 'atividades_realizadas']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('projeto', 'data', 'periodo', 'clima', 'temperatura')
        }),
        ('Equipe e Recursos', {
            'fields': ('num_trabalhadores', 'equipe_descricao', 'equipamentos_utilizados')
        }),
        ('Atividades', {
            'fields': ('atividades_realizadas', 'percentual_progresso')
        }),
        ('Materiais', {
            'fields': ('materiais_recebidos', 'materiais_utilizados'),
            'classes': ('collapse',)
        }),
        ('Problemas e Soluções', {
            'fields': ('problemas_encontrados', 'solucoes_aplicadas', 'visitas_fiscalizacao'),
            'classes': ('collapse',)
        }),
        ('Segurança', {
            'fields': ('incidentes_seguranca', 'epi_utilizado')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )

