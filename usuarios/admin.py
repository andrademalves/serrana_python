from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Modulo, Menu, PermissaoMenu, PerfilUsuario, Empresa, UsuarioEmpresa

# Register your models here.

@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'descricao']
    list_editable = ['ordem', 'ativo']
    ordering = ['ordem', 'nome']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['nome', 'modulo', 'url', 'menu_pai', 'ordem', 'ativo']
    list_filter = ['modulo', 'ativo', 'menu_pai']
    search_fields = ['nome', 'url', 'descricao']
    list_editable = ['ordem', 'ativo']
    ordering = ['modulo', 'ordem', 'nome']
    autocomplete_fields = ['menu_pai']


@admin.register(PermissaoMenu)
class PermissaoMenuAdmin(admin.ModelAdmin):
    list_display = ['get_identificador', 'menu', 'pode_visualizar', 'pode_criar', 'pode_editar', 'pode_excluir']
    list_filter = ['tipo', 'pode_visualizar', 'pode_criar', 'pode_editar', 'pode_excluir', 'menu__modulo']
    search_fields = ['usuario__username', 'grupo__name', 'menu__nome']
    list_editable = ['pode_visualizar', 'pode_criar', 'pode_editar', 'pode_excluir']
    autocomplete_fields = ['usuario', 'grupo', 'menu']
    
    def get_identificador(self, obj):
        if obj.tipo == 'usuario':
            return f"Usuário: {obj.usuario.username}"
        return f"Grupo: {obj.grupo.name}"
    get_identificador.short_description = 'Identificador'


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ['telefone', 'celular', 'cargo', 'departamento', 'vendedor', 'foto', 'ativo']


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilUsuarioInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_perfil_ativo']
    
    def get_perfil_ativo(self, obj):
        try:
            return obj.perfil.ativo
        except PerfilUsuario.DoesNotExist:
            return False
    get_perfil_ativo.short_description = 'Perfil Ativo'
    get_perfil_ativo.boolean = True


# Re-registra o User com o inline do Perfil
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ============================================================================
# ADMIN DE MULTIEMPRESA
# ============================================================================

class UsuarioEmpresaInline(admin.TabularInline):
    model = UsuarioEmpresa
    extra = 1
    fields = ['usuario', 'papel', 'ativo', 'data_inicio', 'data_fim']
    autocomplete_fields = ['usuario']


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome_fantasia', 'razao_social', 'cnpj', 'slug', 'ativa', 'empresa_matriz', 'total_usuarios', 'criado_em']
    list_filter = ['ativa', 'empresa_matriz', 'criado_em', 'uf']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'slug']
    list_editable = ['ativa']
    readonly_fields = ['slug', 'criado_em', 'criado_por', 'atualizado_em', 'atualizado_por']
    autocomplete_fields = ['responsavel']
    inlines = [UsuarioEmpresaInline]
    
    fieldsets = (
        ('Dados da Empresa', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'inscricao_municipal')
        }),
        ('Endereço', {
            'fields': ('cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf'),
            'classes': ('collapse',)
        }),
        ('Contato', {
            'fields': ('telefone', 'email', 'website'),
            'classes': ('collapse',)
        }),
        ('Identidade Visual', {
            'fields': ('logo', 'cor_primaria', 'cor_secundaria'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('slug', 'ativa', 'empresa_matriz', 'responsavel')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por', 'atualizado_em', 'atualizado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo registro
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'empresa', 'papel', 'ativo', 'data_inicio', 'data_fim', 'criado_em']
    list_filter = ['ativo', 'papel', 'empresa', 'criado_em']
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'empresa__nome_fantasia', 'empresa__razao_social']
    list_editable = ['ativo']
    autocomplete_fields = ['usuario', 'empresa']
    readonly_fields = ['criado_em', 'criado_por']
    
    fieldsets = (
        ('Vínculo', {
            'fields': ('usuario', 'empresa', 'papel')
        }),
        ('Controle de Acesso', {
            'fields': ('ativo', 'data_inicio', 'data_fim')
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'criado_por'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo registro
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
