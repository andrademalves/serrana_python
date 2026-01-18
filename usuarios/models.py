from django.db import models
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# Create your models here.

class Modulo(models.Model):
    """
    Representa um módulo do sistema (ex: Financeiro, RH, TI, etc)
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name='Nome do Módulo')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    icone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Ícone (classe CSS)')
    ordem = models.IntegerField(default=0, verbose_name='Ordem de Exibição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Menu(models.Model):
    """
    Representa um menu dentro de um módulo
    """
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='menus', verbose_name='Módulo')
    nome = models.CharField(max_length=100, verbose_name='Nome do Menu')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')
    url = models.CharField(max_length=200, verbose_name='URL')
    icone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Ícone (classe CSS)')
    ordem = models.IntegerField(default=0, verbose_name='Ordem de Exibição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    menu_pai = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, 
                                   related_name='submenus', verbose_name='Menu Pai')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Menu'
        verbose_name_plural = 'Menus'
        ordering = ['modulo', 'ordem', 'nome']
        unique_together = ['modulo', 'url']

    def __str__(self):
        if self.menu_pai:
            return f"{self.modulo.nome} > {self.menu_pai.nome} > {self.nome}"
        return f"{self.modulo.nome} > {self.nome}"


class PermissaoMenu(models.Model):
    """
    Define quais menus um usuário ou grupo tem acesso
    """
    TIPO_CHOICES = [
        ('usuario', 'Usuário'),
        ('grupo', 'Grupo'),
    ]
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, 
                                related_name='permissoes_menu', verbose_name='Usuário')
    grupo = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, 
                              related_name='permissoes_menu', verbose_name='Grupo')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='permissoes', verbose_name='Menu')
    pode_visualizar = models.BooleanField(default=True, verbose_name='Pode Visualizar')
    pode_criar = models.BooleanField(default=False, verbose_name='Pode Criar')
    pode_editar = models.BooleanField(default=False, verbose_name='Pode Editar')
    pode_excluir = models.BooleanField(default=False, verbose_name='Pode Excluir')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Permissão de Menu'
        verbose_name_plural = 'Permissões de Menus'
        unique_together = [
            ['usuario', 'menu'],
            ['grupo', 'menu']
        ]

    def __str__(self):
        if self.tipo == 'usuario':
            return f"{self.usuario.username} - {self.menu.nome}"
        return f"{self.grupo.name} - {self.menu.nome}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tipo == 'usuario' and not self.usuario:
            raise ValidationError('Usuário é obrigatório quando o tipo for "usuário"')
        if self.tipo == 'grupo' and not self.grupo:
            raise ValidationError('Grupo é obrigatório quando o tipo for "grupo"')


class PerfilUsuario(models.Model):
    """
    Estende o modelo User com informações adicionais
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil', verbose_name='Usuário')
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    celular = models.CharField(max_length=20, blank=True, null=True, verbose_name='Celular')
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Cargo')
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name='Departamento')
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True, verbose_name='Foto')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


# ============================================================================
# MODELS DE MULTIEMPRESA
# ============================================================================

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
    
    # Configurações SMTP para Envio de E-mails
    smtp_host = models.CharField('Servidor SMTP', max_length=200, blank=True,
                                  help_text='Ex: smtp.gmail.com')
    smtp_port = models.IntegerField('Porta SMTP', null=True, blank=True, default=587,
                                     help_text='Porta padrão: 587 (TLS) ou 465 (SSL)')
    smtp_use_tls = models.BooleanField('Usar TLS', default=True,
                                        help_text='Usar conexão TLS (recomendado)')
    smtp_use_ssl = models.BooleanField('Usar SSL', default=False,
                                        help_text='Usar conexão SSL (porta 465)')
    smtp_username = models.CharField('Usuário SMTP', max_length=200, blank=True,
                                      help_text='Geralmente é o e-mail')
    smtp_password = models.CharField('Senha SMTP', max_length=200, blank=True,
                                      help_text='Senha ou senha de aplicativo')
    smtp_from_email = models.EmailField('E-mail Remetente', blank=True,
                                         help_text='E-mail que aparecerá como remetente')
    smtp_from_name = models.CharField('Nome Remetente', max_length=100, blank=True,
                                       help_text='Nome que aparecerá como remetente')
    smtp_ativo = models.BooleanField('SMTP Ativo', default=False,
                                      help_text='Usar SMTP próprio ao invés do padrão do sistema')
    
    # Logo e Identidade Visual
    logo = models.ImageField('Logo', upload_to='empresas/logos/', blank=True, null=True)
    cor_primaria = models.CharField('Cor Primária', max_length=7, default='#0066cc', 
                                     help_text='Código hexadecimal (#RRGGBB)')
    cor_secundaria = models.CharField('Cor Secundária', max_length=7, default='#333333',
                                       help_text='Código hexadecimal (#RRGGBB)')
    
    # ===== REGIME TRIBUTÁRIO E IMPOSTOS =====
    regime_tributario = models.ForeignKey(
        'financeiro.RegimeTributario',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='empresas',
        verbose_name='Regime Tributário',
        help_text='Regime tributário da empresa (Simples, Lucro Presumido, etc)'
    )
    
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
        return User.objects.filter(usuario_empresas__empresa=self).distinct()
    
    def total_usuarios(self):
        """Total de usuários com acesso"""
        return self.usuarios_vinculados().count()
    
    def tem_smtp_configurado(self):
        """Verifica se empresa tem SMTP próprio configurado"""
        return (self.smtp_ativo and 
                self.smtp_host and 
                self.smtp_port and 
                self.smtp_username and 
                self.smtp_password and 
                self.smtp_from_email)
    
    def get_smtp_config(self):
        """Retorna configurações SMTP da empresa como dict"""
        if not self.tem_smtp_configurado():
            return None
        
        return {
            'host': self.smtp_host,
            'port': self.smtp_port,
            'username': self.smtp_username,
            'password': self.smtp_password,
            'use_tls': self.smtp_use_tls,
            'use_ssl': self.smtp_use_ssl,
            'from_email': self.smtp_from_email,
            'from_name': self.smtp_from_name or self.nome_fantasia,
        }


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

