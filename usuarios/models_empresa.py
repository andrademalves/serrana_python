"""
Models de Multiempresa
Sistema de múltiplas empresas com isolamento de dados
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Empresa(models.Model):
    """
    Representa uma empresa no sistema multiempresa
    Todos os dados operacionais devem estar vinculados a uma empresa
    """
    # Dados da Empresa
    razao_social = models.CharField('Razão Social', max_length=200)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=200)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=20, blank=True)
    inscricao_municipal = models.CharField('Inscrição Municipal', max_length=20, blank=True)
    
    # Endereço
    cep = models.CharField('CEP', max_length=9, blank=True)
    logradouro = models.CharField('Logradouro', max_length=200, blank=True)
    numero = models.CharField('Número', max_length=20, blank=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    uf = models.CharField('UF', max_length=2, blank=True)
    
    # Contato
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    website = models.URLField('Website', blank=True)
    
    # Logo e Identidade Visual
    logo = models.ImageField('Logo', upload_to='empresas/logos/', blank=True, null=True)
    cor_primaria = models.CharField('Cor Primária', max_length=7, default='#0066cc', 
                                     help_text='Código hexadecimal (#RRGGBB)')
    cor_secundaria = models.CharField('Cor Secundária', max_length=7, default='#333333',
                                       help_text='Código hexadecimal (#RRGGBB)')
    
    # Configurações
    slug = models.SlugField('Slug', max_length=100, unique=True, blank=True,
                            help_text='Identificador único para URLs amigáveis')
    ativa = models.BooleanField('Ativa', default=True,
                                 help_text='Empresas inativas não podem ser acessadas')
    empresa_matriz = models.BooleanField('É Matriz', default=False,
                                          help_text='Define se é a empresa matriz do grupo')
    
    # Responsável / Administrador da Empresa
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='empresas_responsavel',
                                     verbose_name='Responsável',
                                     help_text='Usuário responsável pela empresa')
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='empresas_criadas',
                                    verbose_name='Criado por')
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                        related_name='empresas_atualizadas',
                                        verbose_name='Atualizado por')
    
    class Meta:
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['-empresa_matriz', 'razao_social']
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['slug']),
            models.Index(fields=['ativa']),
        ]
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social
    
    def save(self, *args, **kwargs):
        # Gerar slug automaticamente se não fornecido
        if not self.slug:
            self.slug = slugify(self.nome_fantasia or self.razao_social)
            
            # Garantir unicidade do slug
            base_slug = self.slug
            counter = 1
            while Empresa.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validações customizadas"""
        # Validar CNPJ (simplificado - adicionar validação completa depois)
        if self.cnpj:
            # Remove caracteres não numéricos
            cnpj_numeros = ''.join(filter(str.isdigit, self.cnpj))
            if len(cnpj_numeros) != 14:
                raise ValidationError({'cnpj': 'CNPJ deve conter 14 dígitos'})
    
    def usuarios_vinculados(self):
        """Retorna queryset de usuários com acesso a esta empresa"""
        return User.objects.filter(
            models.Q(usuario_empresas__empresa=self) | 
            models.Q(perfilusuario__empresa_padrao=self)
        ).distinct()
    
    def total_usuarios(self):
        """Total de usuários com acesso"""
        return self.usuarios_vinculados().count()


class UsuarioEmpresa(models.Model):
    """
    Relacionamento M2M entre Usuário e Empresa
    Permite que um usuário tenha acesso a múltiplas empresas
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='usuario_empresas',
                                 verbose_name='Usuário')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE,
                                 related_name='empresa_usuarios',
                                 verbose_name='Empresa')
    
    # Permissões específicas por empresa (opcional - futuro)
    papel = models.CharField('Papel', max_length=50, blank=True,
                             help_text='Ex: Administrador, Operador, Financeiro')
    
    # Controle de Acesso
    ativo = models.BooleanField('Acesso Ativo', default=True,
                                 help_text='Define se o usuário tem acesso ativo a esta empresa')
    data_inicio = models.DateField('Data de Início', auto_now_add=True)
    data_fim = models.DateField('Data de Término', null=True, blank=True,
                                 help_text='Data em que o acesso expira')
    
    # Auditoria
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='vinculos_empresa_criados',
                                    verbose_name='Criado por')
    
    class Meta:
        db_table = 'usuarios_empresas'
        verbose_name = 'Usuário x Empresa'
        verbose_name_plural = 'Usuários x Empresas'
        unique_together = ['usuario', 'empresa']
        ordering = ['usuario__username', 'empresa__nome_fantasia']
        indexes = [
            models.Index(fields=['usuario', 'empresa']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} → {self.empresa.nome_fantasia}"
    
    def clean(self):
        """Validações"""
        # Verificar se data_fim é posterior a data_inicio
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValidationError({'data_fim': 'Data de término deve ser posterior à data de início'})
