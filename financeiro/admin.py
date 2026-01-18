from django.contrib import admin
from .models import (
    Banco, ContaFinanceira, FormaPagamento, CentroCusto,
    CategoriaCustoVariabilidade, TituloFinanceiro, ParcelaFinanceira,
    BaixaFinanceira, MovimentacaoConta, TransferenciaEntreContas,
    ReguaCobranca, ReguaEtapa, LogCobranca, RegimeTributario, AliquotaImposto,
    HistoricoRegimeEmpresa
)


@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ['codigo_compe', 'nome', 'ativo']
    list_filter = ['ativo']
    search_fields = ['codigo_compe', 'nome']


@admin.register(ContaFinanceira)
class ContaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'banco', 'saldo_inicial', 'ativo']
    list_filter = ['tipo', 'ativo', 'banco']
    search_fields = ['nome', 'agencia', 'conta']


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo', 'prazo_compensacao', 'taxa_percentual', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['codigo', 'descricao']


@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'tipo', 'responsavel', 'ativo']
    list_filter = ['tipo', 'ativo']
    search_fields = ['codigo', 'nome']


@admin.register(CategoriaCustoVariabilidade)
class CategoriaCustoVariabilidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'percentual_variavel']
    list_filter = ['tipo']
    search_fields = ['nome', 'observacao']


class ParcelaInline(admin.TabularInline):
    model = ParcelaFinanceira
    extra = 0
    readonly_fields = ['valor_pago', 'saldo_aberto', 'status']


@admin.register(TituloFinanceiro)
class TituloFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'tipo', 'pessoa', 'valor_total', 'data_emissao', 'status']
    list_filter = ['tipo', 'status', 'data_emissao']
    search_fields = ['numero_documento', 'descricao', 'pessoa__nome']
    inlines = [ParcelaInline]
    readonly_fields = ['status', 'criado_em', 'criado_por', 'atualizado_em']


class BaixaInline(admin.TabularInline):
    model = BaixaFinanceira
    extra = 0
    readonly_fields = ['valor_liquido', 'estornado']


@admin.register(ParcelaFinanceira)
class ParcelaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'numero_parcela', 'data_vencimento', 'valor_original', 'saldo_aberto', 'status']
    list_filter = ['status', 'data_vencimento']
    search_fields = ['titulo__numero_documento']
    inlines = [BaixaInline]
    readonly_fields = ['valor_pago', 'saldo_aberto', 'status']


@admin.register(BaixaFinanceira)
class BaixaFinanceiraAdmin(admin.ModelAdmin):
    list_display = ['parcela', 'data_pagamento', 'conta_financeira', 'valor_principal', 'valor_liquido', 'estornado']
    list_filter = ['estornado', 'data_pagamento', 'conta_financeira']
    search_fields = ['parcela__titulo__numero_documento']
    readonly_fields = ['valor_liquido', 'data_estorno', 'estornado_por']


@admin.register(MovimentacaoConta)
class MovimentacaoContaAdmin(admin.ModelAdmin):
    list_display = ['conta_financeira', 'tipo', 'data_movimentacao', 'valor', 'descricao', 'estornado']
    list_filter = ['tipo', 'estornado', 'data_movimentacao', 'conta_financeira']
    search_fields = ['descricao']


@admin.register(TransferenciaEntreContas)
class TransferenciaEntreContasAdmin(admin.ModelAdmin):
    list_display = ['data_transferencia', 'conta_origem', 'conta_destino', 'valor', 'estornado']
    list_filter = ['estornado', 'data_transferencia']
    search_fields = ['descricao']


# ============================================
# RÉGUA DE COBRANÇA
# ============================================

class ReguaEtapaInline(admin.TabularInline):
    model = ReguaEtapa
    extra = 1
    fields = ['ordem', 'nome', 'offset_dias', 'enviar_email', 'assunto_email', 'template_email', 'ativo']
    ordering = ['ordem']


@admin.register(ReguaCobranca)
class ReguaCobrancaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'ativa', 'total_etapas']
    list_filter = ['ativa', 'empresa']
    search_fields = ['nome', 'descricao']
    inlines = [ReguaEtapaInline]
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'empresa', 'ativa')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def total_etapas(self, obj):
        return obj.etapas.count()
    total_etapas.short_description = 'Total Etapas'


@admin.register(ReguaEtapa)
class ReguaEtapaAdmin(admin.ModelAdmin):
    list_display = ['regua', 'ordem', 'nome', 'offset_dias', 'enviar_email', 'ativo']
    list_filter = ['ativo', 'enviar_email', 'regua']
    search_fields = ['nome', 'regua__nome']
    ordering = ['regua', 'ordem']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('regua', 'nome', 'ordem', 'offset_dias', 'ativo')
        }),
        ('E-mail', {
            'fields': ('enviar_email', 'assunto_email', 'template_email')
        }),
    )


@admin.register(LogCobranca)
class LogCobrancaAdmin(admin.ModelAdmin):
    list_display = ['parcela', 'etapa', 'canal', 'status', 'tentativas', 'data_criacao', 'data_envio']
    list_filter = ['status', 'canal', 'data_criacao']
    search_fields = ['parcela__titulo__numero_documento', 'destinatario', 'assunto']
    readonly_fields = ['data_criacao', 'data_tentativa', 'data_envio']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('parcela', 'etapa', 'canal', 'status')
        }),
        ('Detalhes do Envio', {
            'fields': ('destinatario', 'assunto', 'mensagem')
        }),
        ('Controle', {
            'fields': ('tentativas', 'max_tentativas', 'erro', 'message_id')
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_tentativa', 'data_envio')
        }),
    )


@admin.register(RegimeTributario)
class RegimeTributarioAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'criado_em']
    list_filter = ['ativo', 'nome']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AliquotaImposto)
class AliquotaImpostoAdmin(admin.ModelAdmin):
    list_display = ['regime_tributario', 'tipo_imposto', 'aliquota_percentual', 'base_calculo', 'ativo', 'data_inicio_vigencia', 'data_fim_vigencia']
    list_filter = ['regime_tributario', 'tipo_imposto', 'ativo', 'base_calculo']
    search_fields = ['tipo_imposto', 'observacao']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'regime_tributario', 'tipo_imposto', 'ativo')
        }),
        ('Alíquotas e Base de Cálculo', {
            'fields': ('aliquota_percentual', 'base_calculo', 'observacao')
        }),
        ('Vigência', {
            'fields': ('data_inicio_vigencia', 'data_fim_vigencia'),
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HistoricoRegimeEmpresa)
class HistoricoRegimeEmpresaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'regime_tributario', 'data_inicio', 'data_fim', 'ativo', 'criado_por']
    list_filter = ['ativo', 'regime_tributario', 'data_inicio']
    search_fields = ['empresa__nome_fantasia', 'motivo_mudanca']
    readonly_fields = ['criado_em', 'criado_por']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'regime_tributario', 'ativo')
        }),
        ('Vigência', {
            'fields': ('data_inicio', 'data_fim', 'motivo_mudanca')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por'),
            'classes': ('collapse',)
        }),
    )
