from django.contrib import admin
from .models import (
    CondicaoPagamento, 
    Orcamento, 
    OrcamentoItem, 
    OrcamentoAnexo, 
    OrcamentoHistorico
)


@admin.register(CondicaoPagamento)
class CondicaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo', 'ativo', 'padrao']
    list_filter = ['tipo', 'ativo', 'padrao']
    search_fields = ['codigo', 'descricao']


class OrcamentoItemInline(admin.TabularInline):
    model = OrcamentoItem
    extra = 1
    fields = ['produto', 'descricao', 'quantidade', 'unidade', 'preco_unitario', 'total_item']
    readonly_fields = ['total_item']


class OrcamentoAnexoInline(admin.TabularInline):
    model = OrcamentoAnexo
    extra = 0
    fields = ['tipo', 'descricao', 'arquivo', 'versao']


class OrcamentoHistoricoInline(admin.TabularInline):
    model = OrcamentoHistorico
    extra = 0
    fields = ['status_anterior', 'status_novo', 'observacao', 'criado_por', 'criado_em']
    readonly_fields = ['criado_em']


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'cliente', 'vendedor', 'data_orcamento', 'status', 'total', 'projeto_gerado']
    list_filter = ['status', 'data_orcamento', 'vendedor']
    search_fields = ['numero', 'cliente__nome_razao']
    readonly_fields = ['numero', 'subtotal', 'total', 'criado_em', 'atualizado_em']
    
    inlines = [OrcamentoItemInline, OrcamentoAnexoInline, OrcamentoHistoricoInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero', 'status', 'cliente', 'vendedor')
        }),
        ('Datas', {
            'fields': ('data_orcamento', 'validade_ate', 'prazo_execucao_dias')
        }),
        ('Endereço de Execução', {
            'fields': (
                'endereco_execucao_logradouro',
                'endereco_execucao_numero',
                'endereco_execucao_complemento',
                'endereco_execucao_bairro',
                'endereco_execucao_cidade',
                'endereco_execucao_estado',
                'endereco_execucao_cep'
            ),
            'classes': ('collapse',)
        }),
        ('Financeiro', {
            'fields': (
                'condicao_pagamento',
                'subtotal',
                'desconto',
                'frete',
                'outras_despesas',
                'total'
            )
        }),
        ('Observações', {
            'fields': ('observacoes', 'observacoes_internas')
        }),
        ('Aprovação', {
            'fields': (
                'projeto_gerado',
                'data_aprovacao',
                'aprovado_por',
                'motivo_reprovacao'
            )
        }),
        ('Auditoria', {
            'fields': ('criado_por', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrcamentoItem)
class OrcamentoItemAdmin(admin.ModelAdmin):
    list_display = ['orcamento', 'produto', 'descricao', 'quantidade', 'preco_unitario', 'total_item']
    list_filter = ['orcamento__status']
    search_fields = ['orcamento__numero', 'descricao']


@admin.register(OrcamentoAnexo)
class OrcamentoAnexoAdmin(admin.ModelAdmin):
    list_display = ['orcamento', 'tipo', 'descricao', 'versao', 'data_envio']
    list_filter = ['tipo', 'data_envio']
    search_fields = ['orcamento__numero', 'descricao']


@admin.register(OrcamentoHistorico)
class OrcamentoHistoricoAdmin(admin.ModelAdmin):
    list_display = ['orcamento', 'status_anterior', 'status_novo', 'criado_por', 'criado_em']
    list_filter = ['status_novo', 'criado_em']
    search_fields = ['orcamento__numero', 'observacao']
