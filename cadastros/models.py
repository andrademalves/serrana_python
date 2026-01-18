from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.

class Estado(models.Model):
    """
    Estados brasileiros (UF)
    """
    sigla = models.CharField(max_length=2, unique=True, verbose_name='Sigla')
    nome = models.CharField(max_length=100, verbose_name='Nome')
    
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.sigla} - {self.nome}"


class Cidade(models.Model):
    """
    Cidades brasileiras
    """
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name='cidades', verbose_name='Estado')
    nome = models.CharField(max_length=100, verbose_name='Nome')
    codigo_ibge = models.CharField(max_length=10, blank=True, null=True, verbose_name='Código IBGE')
    
    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'
        ordering = ['estado', 'nome']
        unique_together = ['estado', 'nome']
    
    def __str__(self):
        return f"{self.nome} - {self.estado.sigla}"


class Pessoa(models.Model):
    """
    Cadastro base de pessoas (física ou jurídica)
    """
    TIPO_CHOICES = [
        ('F', 'Física'),
        ('J', 'Jurídica'),
    ]
    
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]
    
    ESCOLARIDADE_CHOICES = [
        ('fundamental_incompleto', 'Fundamental Incompleto'),
        ('fundamental_completo', 'Fundamental Completo'),
        ('medio_incompleto', 'Médio Incompleto'),
        ('medio_completo', 'Médio Completo'),
        ('superior_incompleto', 'Superior Incompleto'),
        ('superior_completo', 'Superior Completo'),
        ('pos_graduacao', 'Pós-Graduação'),
        ('mestrado', 'Mestrado'),
        ('doutorado', 'Doutorado'),
    ]
    
    CNH_CATEGORIA_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
        ('C', 'C'),
        ('D', 'D'),
        ('E', 'E'),
    ]
    
    # Empresa (Multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='pessoas',
        verbose_name='Empresa',
        help_text='Empresa à qual esta pessoa pertence'
    )
    
    # Informações Básicas
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, verbose_name='Tipo')
    nome = models.CharField(max_length=200, verbose_name='Nome/Razão Social')
    nome_fantasia = models.CharField(max_length=200, blank=True, null=True, verbose_name='Nome Fantasia')
    cpf_cnpj = models.CharField(max_length=18, unique=True, verbose_name='CPF/CNPJ')
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name='RG')
    ie = models.CharField(max_length=20, blank=True, null=True, verbose_name='Inscrição Estadual')
    data_emissao_rg = models.DateField(blank=True, null=True, verbose_name='Data Emissão RG')
    orgao_emissor = models.CharField(max_length=20, blank=True, null=True, verbose_name='Órgão Emissor')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name='Sexo')
    
    # Endereço
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name='CEP')
    logradouro = models.CharField(max_length=200, blank=True, null=True, verbose_name='Logradouro')
    numero = models.CharField(max_length=20, blank=True, null=True, verbose_name='Número')
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name='Complemento')
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name='Bairro')
    cidade = models.CharField(max_length=50, blank=True, null=True, verbose_name='Cidade')
    uf = models.CharField(max_length=2, blank=True, null=True, verbose_name='UF')
    
    # Contato
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone')
    celular1 = models.CharField(max_length=20, blank=True, null=True, verbose_name='Celular 1')
    celular2 = models.CharField(max_length=20, blank=True, null=True, verbose_name='Celular 2')
    email = models.EmailField(blank=True, null=True, verbose_name='E-mail')
    
    # Classificação
    cliente = models.BooleanField(default=False, verbose_name='É Cliente')
    fornecedor = models.BooleanField(default=False, verbose_name='É Fornecedor')
    funcionario = models.BooleanField(default=False, verbose_name='É Funcionário')
    terceiro = models.BooleanField(default=False, verbose_name='É Terceiro')
    vendedor = models.BooleanField(default=False, verbose_name='É Vendedor')
    
    # Dados de Fornecedor/Cliente
    ramo_atividade = models.CharField(max_length=100, blank=True, null=True, verbose_name='Ramo de Atividade')
    descricao_ramo = models.CharField(max_length=100, blank=True, null=True, verbose_name='Descrição do Ramo')
    
    # Dados de Funcionário
    titulo_eleitoral = models.CharField(max_length=20, blank=True, null=True, verbose_name='Título de Eleitor')
    zona = models.CharField(max_length=20, blank=True, null=True, verbose_name='Zona')
    secao = models.CharField(max_length=20, blank=True, null=True, verbose_name='Seção')
    ctps = models.CharField(max_length=20, blank=True, null=True, verbose_name='CTPS')
    serie = models.CharField(max_length=20, blank=True, null=True, verbose_name='Série CTPS')
    uf_ctps = models.CharField(max_length=2, blank=True, null=True, verbose_name='UF CTPS')
    data_expedicao_ctps = models.DateField(blank=True, null=True, verbose_name='Data Expedição CTPS')
    cnh = models.CharField(max_length=20, blank=True, null=True, verbose_name='CNH')
    cnh_categoria = models.CharField(max_length=6, choices=CNH_CATEGORIA_CHOICES, blank=True, null=True, verbose_name='Categoria CNH')
    escolaridade = models.CharField(max_length=50, choices=ESCOLARIDADE_CHOICES, blank=True, null=True, verbose_name='Escolaridade')
    deficiencia = models.BooleanField(default=False, verbose_name='Possui Deficiência')
    cargo = models.CharField(max_length=50, blank=True, null=True, verbose_name='Cargo')
    data_admissao = models.DateField(blank=True, null=True, verbose_name='Data Admissão')
    data_demissao = models.DateField(blank=True, null=True, verbose_name='Data Demissão')
    
    # Observações
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pessoas_criadas', verbose_name='Criado por')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pessoas_atualizadas', verbose_name='Atualizado por')
    
    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        ordering = ['nome']
        unique_together = [
            ['empresa', 'cpf_cnpj'],  # CPF/CNPJ único por empresa
        ]
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['empresa', 'cliente']),
            models.Index(fields=['empresa', 'fornecedor']),
            models.Index(fields=['cpf_cnpj']),
        ]
    
    def __str__(self):
        if self.nome_fantasia:
            return f"{self.nome_fantasia} ({self.cpf_cnpj})"
        return f"{self.nome} ({self.cpf_cnpj})"


class Produto(models.Model):
    """
    Cadastro de produtos
    """
    TIPO_CHOICES = [
        ('produto', 'Produto'),
        ('servico', 'Serviço'),
    ]
    
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('KG', 'Quilograma'),
        ('M', 'Metro'),
        ('M2', 'Metro Quadrado'),
        ('M3', 'Metro Cúbico'),
        ('LT', 'Litro'),
        ('CX', 'Caixa'),
        ('PC', 'Peça'),
        ('HR', 'Hora'),
    ]
    
    # Empresa (Multiempresa)
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='produtos',
        verbose_name='Empresa'
    )
    
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='produto', verbose_name='Tipo')
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    descricao = models.CharField(max_length=200, verbose_name='Descrição')
    descricao_detalhada = models.TextField(blank=True, null=True, verbose_name='Descrição Detalhada')
    unidade = models.CharField(max_length=5, choices=UNIDADE_CHOICES, default='UN', verbose_name='Unidade')
    
    # Estoque
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Estoque Atual')
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Estoque Mínimo')
    
    # Valores
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Custo')
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço de Venda')
    
    # Fornecedor padrão
    fornecedor = models.ForeignKey(Pessoa, on_delete=models.SET_NULL, blank=True, null=True, 
                                    limit_choices_to={'fornecedor': True}, 
                                    related_name='produtos_fornecidos', verbose_name='Fornecedor Padrão')
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='produtos_criados', verbose_name='Criado por')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='produtos_atualizados', verbose_name='Atualizado por')
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['descricao']
        unique_together = [
            ['empresa', 'codigo'],  # Código único por empresa
        ]
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['empresa', 'tipo']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
