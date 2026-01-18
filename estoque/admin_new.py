from django.contrib import admin
from .models import (
    Item, GrupoItem, LocalEstoque, DestinoEstoque,
    MovimentoEstoque, SaldoEstoque, BOM, BOMItem, OrdemProducao
)


@admin.register(GrupoItem)
class GrupoItemAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['codigo', 'descricao']
    ordering = ['descricao']


@admin.register(LocalEstoque)
class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'responsavel', 'permite_saldo_negativo', 'ativo', 'criado_em']
    list_filter = ['ativo', 'permite_saldo_negativo', 'criado_em']
    search_fields = ['codigo', 'descricao', 'endereco']
    ordering = ['descricao']
    raw_id_fields = ['responsavel', 'criado_por']


@admin.register(DestinoEstoque)
class DestinoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo', 'controla_custo', 'ativo', 'criado_em']
    list_filter = ['tipo', 'controla_custo', 'ativo', 'criado_em']
    search_fields = ['codigo', 'descricao']
    ordering = ['descricao']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo_item', 'grupo', 'unidade_medida', 'estoque_minimo', 'ativo']
    list_filter = ['tipo_item', 'grupo', 'ativo', 'criado_em']
    search_fields = ['codigo', 'descricao', 'marca', 'modelo', 'ncm', 'codigo_barras']
    ordering = ['codigo']
    raw_id_fields = ['criado_por', 'atualizado_por']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'descricao', 'tipo_item', 'grupo')
        }),
        ('Especificações', {
            'fields': ('marca', 'modelo', 'cor', 'unidade_medida', 'ncm', 'codigo_barras')
        }),
        ('Controle de Estoque', {
            'fields': ('estoque_minimo', 'estoque_maximo')
        }),
        ('Outros', {
            'fields': ('url_foto', 'ativo', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['item', 'local', 'quantidade', 'custo_medio', 'valor_total_display', 'atualizado_em']
    list_filter = ['local', 'item__tipo_item', 'atualizado_em']
    search_fields = ['item__codigo', 'item__descricao', 'local__codigo', 'local__descricao']
    ordering = ['item__codigo', 'local__codigo']
    raw_id_fields = ['item', 'local']
    readonly_fields = ['atualizado_em']
    
    def valor_total_display(self, obj):
        return f'R$ {obj.valor_total:,.2f}'
    valor_total_display.short_description = 'Valor Total'
    
    # Tornar readonly para evitar edição manual
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = [
        'data_movimento', 'tipo_movimento', 'documento', 'item_codigo',
        'quantidade', 'custo_total', 'local_origem', 'local_destino', 'criado_por'
    ]
    list_filter = ['tipo_movimento', 'documento_tipo', 'data_movimento', 'criado_em']
    search_fields = ['documento', 'item__codigo', 'item__descricao', 'observacao']
    ordering = ['-data_movimento', '-criado_em']
    raw_id_fields = [
        'item', 'local_origem', 'local_destino', 'destino',
        'projeto', 'fornecedor', 'solicitante', 'movimento_estornado', 'criado_por'
    ]
    readonly_fields = ['custo_total', 'criado_em', 'criado_por']
    date_hierarchy = 'data_movimento'
    
    fieldsets = (
        ('Movimento', {
            'fields': ('tipo_movimento', 'documento', 'documento_tipo', 'data_movimento')
        }),
        ('Item e Locais', {
            'fields': ('item', 'local_origem', 'local_destino')
        }),
        ('Destino/Projeto', {
            'fields': ('destino', 'projeto', 'fornecedor')
        }),
        ('Quantidade e Custo', {
            'fields': ('quantidade', 'custo_unitario', 'custo_total')
        }),
        ('Outras Informações', {
            'fields': ('solicitante', 'movimento_estornado', 'observacao')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def item_codigo(self, obj):
        return obj.item.codigo
    item_codigo.short_description = 'Item'
    item_codigo.admin_order_field = 'item__codigo'
    
    # Não permitir edição de movimentos (apenas visualização e criação)
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permitir delete apenas para superuser
        return request.user.is_superuser


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ['produto', 'versao', 'descricao', 'ativo', 'data_vigencia', 'criado_em']
    list_filter = ['ativo', 'data_vigencia', 'criado_em']
    search_fields = ['produto__codigo', 'produto__descricao', 'versao', 'descricao']
    ordering = ['produto__codigo', '-versao']
    raw_id_fields = ['produto', 'criado_por']
    readonly_fields = ['criado_em', 'criado_por']


class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1
    raw_id_fields = ['item_componente']
    fields = ['item_componente', 'quantidade', 'percentual_perda', 'sequencia']


@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ['bom', 'item_componente', 'quantidade', 'percentual_perda', 'sequencia', 'quantidade_com_perda']
    list_filter = ['bom__produto']
    search_fields = ['bom__produto__codigo', 'item_componente__codigo', 'item_componente__descricao']
    ordering = ['bom', 'sequencia']
    raw_id_fields = ['bom', 'item_componente']
    
    def quantidade_com_perda(self, obj):
        return f'{obj.get_quantidade_com_perda():.3f}'
    quantidade_com_perda.short_description = 'Qtd c/ Perda'


@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_op', 'produto', 'status', 'quantidade_planejada',
        'quantidade_produzida', 'data_planejada', 'projeto'
    ]
    list_filter = ['status', 'data_planejada', 'criado_em']
    search_fields = ['numero_op', 'produto__codigo', 'produto__descricao', 'projeto__codigo']
    ordering = ['-numero_op']
    raw_id_fields = [
        'produto', 'bom', 'local_producao', 'local_destino',
        'projeto', 'criado_por'
    ]
    readonly_fields = ['criado_em', 'criado_por']
    date_hierarchy = 'data_planejada'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_op', 'produto', 'bom', 'status')
        }),
        ('Quantidades', {
            'fields': ('quantidade_planejada', 'quantidade_produzida')
        }),
        ('Locais', {
            'fields': ('local_producao', 'local_destino')
        }),
        ('Datas', {
            'fields': ('data_planejada', 'data_inicio', 'data_fim')
        }),
        ('Projeto', {
            'fields': ('projeto', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por'),
            'classes': ('collapse',)
        }),
    )


# Configurações do Admin Site
admin.site.site_header = "Serrana - Sistema de Estoque"
admin.site.site_title = "Estoque Admin"
admin.site.index_title = "Administração do Estoque"
