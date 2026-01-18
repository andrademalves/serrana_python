from django.contrib import admin
from .models import Estado, Cidade, Pessoa, Produto

# Register your models here.

@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ['sigla', 'nome']
    search_fields = ['sigla', 'nome']
    ordering = ['nome']


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = ['nome', 'estado', 'codigo_ibge']
    list_filter = ['estado']
    search_fields = ['nome', 'codigo_ibge']
    autocomplete_fields = ['estado']
    ordering = ['estado', 'nome']


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'tipo', 'cliente', 'fornecedor', 'funcionario', 'ativo']
    list_filter = ['tipo', 'cliente', 'fornecedor', 'funcionario', 'ativo', 'criado_em']
    search_fields = ['nome', 'nome_fantasia', 'cpf_cnpj', 'email']
    autocomplete_fields = ['criado_por', 'atualizado_por']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'nome', 'nome_fantasia', 'cpf_cnpj', 'rg_ie')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade')
        }),
        ('Contato', {
            'fields': ('telefone', 'celular', 'email', 'site')
        }),
        ('Classificação', {
            'fields': ('cliente', 'fornecedor', 'funcionario')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('ativo', 'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por')
        }),
    )


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao', 'tipo', 'unidade', 'estoque_atual', 'preco_venda', 'ativo']
    list_filter = ['tipo', 'unidade', 'ativo', 'criado_em']
    search_fields = ['codigo', 'descricao']
    autocomplete_fields = ['fornecedor', 'criado_por', 'atualizado_por']
    readonly_fields = ['criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'codigo', 'descricao', 'descricao_detalhada', 'unidade')
        }),
        ('Estoque', {
            'fields': ('estoque_atual', 'estoque_minimo')
        }),
        ('Valores', {
            'fields': ('custo', 'preco_venda')
        }),
        ('Fornecedor', {
            'fields': ('fornecedor',)
        }),
        ('Controle', {
            'fields': ('ativo', 'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por')
        }),
    )
