from django.contrib import admin
from .models import (
    Pipeline, EtapaFunil, Oportunidade, AtividadeCRM,
    AlertaRetorno, AnexoOportunidade, HistoricoEtapa
)


@admin.register(Pipeline)
class PipelineAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'ativo', 'padrao', 'created_at']
    list_filter = ['empresa', 'ativo', 'padrao']
    search_fields = ['nome', 'descricao']
    date_hierarchy = 'created_at'


@admin.register(EtapaFunil)
class EtapaFunilAdmin(admin.ModelAdmin):
    list_display = ['nome', 'pipeline', 'ordem', 'cor', 'is_final', 'tipo_final', 'ativo']
    list_filter = ['pipeline', 'is_final', 'tipo_final', 'ativo']
    search_fields = ['nome']
    ordering = ['pipeline', 'ordem']


@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'nome_contato', 'empresa', 'etapa', 'responsavel', 'status', 'valor_estimado', 'updated_at']
    list_filter = ['empresa', 'pipeline', 'etapa', 'status', 'origem', 'responsavel']
    search_fields = ['titulo', 'nome_contato', 'empresa_contato', 'email', 'telefone']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Dados Principais', {
            'fields': ('empresa', 'pipeline', 'etapa', 'titulo', 'descricao')
        }),
        ('Contato', {
            'fields': ('cliente', 'nome_contato', 'empresa_contato', 'telefone', 'email')
        }),
        ('Comercial', {
            'fields': ('origem', 'valor_estimado', 'responsavel', 'status')
        }),
        ('Integração', {
            'fields': ('orcamento', 'projeto')
        }),
        ('Datas', {
            'fields': ('data_entrada', 'data_prevista_fechamento', 'data_fechamento', 'created_at', 'updated_at')
        }),
    )


@admin.register(AtividadeCRM)
class AtividadeCRMAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'titulo', 'oportunidade', 'data_atividade', 'criado_por']
    list_filter = ['tipo', 'data_atividade']
    search_fields = ['titulo', 'descricao', 'oportunidade__titulo']
    date_hierarchy = 'data_atividade'


@admin.register(AlertaRetorno)
class AlertaRetornoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'oportunidade', 'data_hora', 'prioridade', 'status', 'criado_por']
    list_filter = ['status', 'prioridade', 'data_hora']
    search_fields = ['titulo', 'descricao', 'oportunidade__titulo']
    date_hierarchy = 'data_hora'


@admin.register(AnexoOportunidade)
class AnexoOportunidadeAdmin(admin.ModelAdmin):
    list_display = ['descricao', 'oportunidade', 'arquivo', 'criado_por', 'created_at']
    list_filter = ['created_at']
    search_fields = ['descricao', 'oportunidade__titulo']


@admin.register(HistoricoEtapa)
class HistoricoEtapaAdmin(admin.ModelAdmin):
    list_display = ['oportunidade', 'etapa_de', 'etapa_para', 'usuario', 'data_hora']
    list_filter = ['data_hora', 'etapa_de', 'etapa_para']
    search_fields = ['oportunidade__titulo', 'observacao']
    date_hierarchy = 'data_hora'
    readonly_fields = ['data_hora']
