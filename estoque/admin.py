from django.contrib import admin
from .models import Item, MovimentoEstoque


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo_item', 'unidade_medida', 'estoque_minimo', 'ativo']
    list_filter = ['tipo_item', 'unidade_medida', 'ativo']
    search_fields = ['codigo', 'descricao']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'descricao', 'tipo_item', 'grupo', 'unidade_medida', 'marca', 'modelo', 'cor', 'ativo')
        }),
        ('Estoque', {
            'fields': ('estoque_minimo', 'estoque_maximo')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MovimentoEstoque)
class MovimentoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['item', 'tipo_movimento', 'quantidade', 'custo_unitario', 'custo_total', 'documento', 'data_movimento']
    list_filter = ['tipo_movimento', 'data_movimento']
    search_fields = ['item__descricao', 'documento']
    autocomplete_fields = ['item']
    readonly_fields = ['custo_total', 'data_movimento']
    
    fieldsets = (
        ('Movimentação', {
            'fields': ('item', 'tipo_movimento', 'quantidade', 'custo_unitario', 'custo_total')
        }),
        ('Documento', {
            'fields': ('documento', 'observacao')
        }),
        ('Auditoria', {
            'fields': ('data_movimento', 'criado_por')
        }),
    )
