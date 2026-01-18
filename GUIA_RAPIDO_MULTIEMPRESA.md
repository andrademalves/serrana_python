# 🚀 GUIA RÁPIDO - IMPLEMENTAÇÃO MULTIEMPRESA

## ⚡ INÍCIO RÁPIDO (15 minutos)

### 1️⃣ Importar Models Empresa no __init__.py

```python
# usuarios/__init__.py
from .models_empresa import Empresa, UsuarioEmpresa
```

### 2️⃣ Criar Migrations

```bash
# Criar migration para model Empresa
python manage.py makemigrations usuarios

# Aplicar
python manage.py migrate usuarios
```

### 3️⃣ Criar Empresa Padrão

```bash
# Executar script interativo
python manage.py shell < inicializar_multiempresa.py

# OU manualmente no shell:
python manage.py shell
>>> from usuarios.models_empresa import Empresa
>>> from django.contrib.auth.models import User
>>> admin = User.objects.filter(is_superuser=True).first()
>>> empresa = Empresa.objects.create(
...     razao_social='Serrana Ltda',
...     nome_fantasia='Serrana',
...     cnpj='00.000.000/0001-00',
...     slug='serrana',
...     ativa=True,
...     empresa_matriz=True,
...     criado_por=admin
... )
>>> print(f"✅ Empresa criada: {empresa}")
```

---

## 📝 EXEMPLO PRÁTICO: Adicionar Empresa a um Model

### ANTES (cadastros/models.py):
```python
class Pessoa(models.Model):
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    # ... outros campos
    
    class Meta:
        db_table = 'pessoas'
        ordering = ['nome']
```

### DEPOIS (cadastros/models.py):
```python
from usuarios.models_empresa import Empresa
from usuarios.managers_empresa import EmpresaManager

class Pessoa(models.Model):
    # ===== NOVO CAMPO =====
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='pessoa_set',
        verbose_name='Empresa'
    )
    # ======================
    
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18)  # Remover unique=True temporariamente
    # ... outros campos
    
    # ===== NOVO MANAGER =====
    objects = EmpresaManager()
    # ========================
    
    class Meta:
        db_table = 'pessoas'
        ordering = ['nome']
        
        # ===== NOVOS ÍNDICES E CONSTRAINTS =====
        indexes = [
            models.Index(fields=['empresa']),
            models.Index(fields=['cpf_cnpj']),
        ]
        
        # CPF/CNPJ único POR EMPRESA
        unique_together = [['empresa', 'cpf_cnpj']]
        # ======================================
```

### Migration Segura:

```bash
# 1. Criar migration
python manage.py makemigrations cadastros --name add_empresa_to_pessoa

# 2. Editar migration para adicionar campo nullable primeiro
# Ver exemplo em IMPLEMENTACAO_MULTIEMPRESA.md

# 3. Aplicar migration
python manage.py migrate cadastros

# 4. Popular empresa_id
python manage.py shell
>>> from cadastros.models import Pessoa
>>> from usuarios.models_empresa import Empresa
>>> empresa_padrao = Empresa.objects.first()
>>> Pessoa.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)
>>> print(f"Atualizado: {Pessoa.objects.filter(empresa=empresa_padrao).count()}")

# 5. Criar migration para tornar campo obrigatório
python manage.py makemigrations cadastros --name make_empresa_required

# 6. Aplicar
python manage.py migrate cadastros
```

---

## 🔧 EXEMPLO PRÁTICO: Atualizar Views

### ANTES (cadastros/views.py):
```python
@login_required
def listar_pessoas(request):
    pessoas = Pessoa.objects.all()
    
    return render(request, 'cadastros/listar_pessoas.html', {
        'pessoas': pessoas
    })


@login_required
def criar_pessoa(request):
    if request.method == 'POST':
        form = PessoaForm(request.POST)
        if form.is_valid():
            pessoa = form.save(commit=False)
            pessoa.criado_por = request.user
            pessoa.save()
            return redirect('cadastros:listar_pessoas')
    else:
        form = PessoaForm()
    
    return render(request, 'cadastros/criar_pessoa.html', {
        'form': form
    })
```

### DEPOIS (cadastros/views.py):
```python
from usuarios.decorators import require_empresa

@login_required
@require_empresa  # <--- ADICIONAR
def listar_pessoas(request):
    # Filtrar apenas pessoas da empresa ativa
    pessoas = Pessoa.objects.for_empresa(request.empresa)  # <--- MUDAR
    
    return render(request, 'cadastros/listar_pessoas.html', {
        'pessoas': pessoas
    })


@login_required
@require_empresa  # <--- ADICIONAR
def criar_pessoa(request):
    if request.method == 'POST':
        form = PessoaForm(request.POST, empresa=request.empresa)  # <--- ADICIONAR empresa
        if form.is_valid():
            pessoa = form.save(commit=False)
            pessoa.empresa = request.empresa  # <--- ADICIONAR
            pessoa.criado_por = request.user
            pessoa.save()
            return redirect('cadastros:listar_pessoas')
    else:
        form = PessoaForm(empresa=request.empresa)  # <--- ADICIONAR empresa
    
    return render(request, 'cadastros/criar_pessoa.html', {
        'form': form
    })
```

---

## 📋 EXEMPLO PRÁTICO: Atualizar Forms

### ANTES (cadastros/forms.py):
```python
class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['nome', 'cpf_cnpj', 'telefone', 'email']
```

### DEPOIS (cadastros/forms.py):
```python
class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['nome', 'cpf_cnpj', 'telefone', 'email']
        # NÃO incluir 'empresa' - será setado automaticamente
    
    def __init__(self, *args, **kwargs):
        # Receber empresa do contexto
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Se houver ForeignKeys para outros models da mesma empresa
        if self.empresa:
            # Exemplo: filtrar apenas fornecedores da mesma empresa
            if 'fornecedor' in self.fields:
                self.fields['fornecedor'].queryset = (
                    Pessoa.objects.for_empresa(self.empresa)
                    .filter(fornecedor=True)
                )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # SEGURANÇA: Validar que não está tentando alterar empresa
        if self.instance.pk:
            if self.instance.empresa != self.empresa:
                raise forms.ValidationError(
                    'Você não pode alterar a empresa deste registro.'
                )
        
        return cleaned_data
```

---

## ⚙️ CONFIGURAR SISTEMA

### settings.py:

```python
# Em INSTALLED_APPS (já existe)
INSTALLED_APPS = [
    ...
    'usuarios',  # Certifique-se que está aqui
    ...
]

# Em MIDDLEWARE - ADICIONAR
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'usuarios.middleware_empresa.EmpresaAtivaMiddleware',  # <--- ADICIONAR AQUI
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Em TEMPLATES - ADICIONAR context processor
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'serrana.context_processors.current_module',
                'serrana.context_processors.user_permissions',
                'usuarios.middleware_empresa.empresa_context_processor',  # <--- ADICIONAR
            ],
        },
    },
]
```

---

## 🧪 TESTAR IMPLEMENTAÇÃO

### 1. Criar Empresa de Teste:

```bash
python manage.py shell
>>> from usuarios.models_empresa import Empresa
>>> from django.contrib.auth.models import User
>>> 
>>> # Criar segunda empresa para teste
>>> empresa_teste = Empresa.objects.create(
...     razao_social='Empresa Teste Ltda',
...     nome_fantasia='Teste',
...     cnpj='11.111.111/0001-11',
...     slug='teste',
...     ativa=True
... )
>>> 
>>> # Criar usuário de teste
>>> user_teste = User.objects.create_user('teste', password='senha123')
>>> 
>>> # Vincular usuário à empresa teste
>>> from usuarios.models_empresa import UsuarioEmpresa
>>> UsuarioEmpresa.objects.create(
...     usuario=user_teste,
...     empresa=empresa_teste,
...     ativo=True
... )
```

### 2. Testar Isolamento:

```bash
python manage.py shell
>>> from cadastros.models import Pessoa
>>> from usuarios.models_empresa import Empresa
>>> 
>>> empresa_a = Empresa.objects.get(slug='serrana')
>>> empresa_b = Empresa.objects.get(slug='teste')
>>> 
>>> # Criar pessoa na empresa A
>>> pessoa_a = Pessoa.objects.create(
...     nome='Cliente A',
...     tipo='F',
...     cpf_cnpj='111.111.111-11',
...     empresa=empresa_a
... )
>>> 
>>> # Criar pessoa na empresa B
>>> pessoa_b = Pessoa.objects.create(
...     nome='Cliente B',
...     tipo='F',
...     cpf_cnpj='222.222.222-22',
...     empresa=empresa_b
... )
>>> 
>>> # Testar filtros
>>> print(f"Empresa A: {Pessoa.objects.for_empresa(empresa_a).count()}")  # Deve ser 1
>>> print(f"Empresa B: {Pessoa.objects.for_empresa(empresa_b).count()}")  # Deve ser 1
>>> 
>>> # Verificar isolamento
>>> assert pessoa_a in Pessoa.objects.for_empresa(empresa_a)
>>> assert pessoa_a not in Pessoa.objects.for_empresa(empresa_b)
>>> print("✅ Isolamento funcionando corretamente!")
```

### 3. Rodar Testes Automatizados:

```bash
# Rodar todos os testes
python manage.py test usuarios.tests_multiempresa -v 2

# Ver cobertura
coverage run --source='.' manage.py test usuarios.tests_multiempresa
coverage report
coverage html
```

---

## 🎨 ADICIONAR SELETOR DE EMPRESA NO TEMPLATE

### templates/partials/navbar.html:

```html
<!-- Adicionar após o nome do usuário -->
<div class="navbar-empresa">
    {% if empresa_ativa %}
        <div class="dropdown">
            <button class="btn btn-sm btn-outline-light dropdown-toggle" 
                    type="button" 
                    id="empresaDropdown" 
                    data-bs-toggle="dropdown">
                <i class="bi bi-building"></i>
                {{ empresa_ativa.nome_fantasia }}
            </button>
            <ul class="dropdown-menu" aria-labelledby="empresaDropdown">
                <li>
                    <span class="dropdown-item-text">
                        <strong>{{ empresa_ativa.nome_fantasia }}</strong><br>
                        <small class="text-muted">{{ empresa_ativa.cnpj }}</small>
                    </span>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li>
                    <a class="dropdown-item" href="{% url 'usuarios:selecionar_empresa' %}">
                        <i class="bi bi-arrow-left-right"></i>
                        Trocar Empresa
                    </a>
                </li>
            </ul>
        </div>
    {% else %}
        <a href="{% url 'usuarios:selecionar_empresa' %}" class="btn btn-sm btn-warning">
            <i class="bi bi-exclamation-triangle"></i>
            Selecionar Empresa
        </a>
    {% endif %}
</div>
```

---

## 📊 CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Setup Inicial (1 dia)
- [ ] Criar `usuarios/models_empresa.py`
- [ ] Criar `usuarios/middleware_empresa.py`
- [ ] Criar `usuarios/managers_empresa.py`
- [ ] Adicionar imports em `usuarios/__init__.py`
- [ ] Rodar migrations
- [ ] Criar empresa padrão
- [ ] Testar criação de empresa

### Fase 2: Migrations (2-3 dias)
- [ ] Adicionar FK `empresa` em `cadastros.Pessoa`
- [ ] Adicionar FK `empresa` em `cadastros.Produto`
- [ ] Adicionar FK `empresa` em `estoque.Item`
- [ ] Adicionar FK `empresa` em `estoque.LocalEstoque`
- [ ] Adicionar FK `empresa` em `estoque.MovimentoEstoque`
- [ ] Adicionar FK `empresa` em `projetos.Orcamento`
- [ ] Adicionar FK `empresa` em `projetos.Projeto`
- [ ] Adicionar FK `empresa` em `financeiro.TituloFinanceiro`
- [ ] Adicionar FK `empresa` em `financeiro.ContaFinanceira`
- [ ] Popular empresa_id em TODOS os registros existentes
- [ ] Tornar campo `empresa` obrigatório (NOT NULL)
- [ ] Adicionar índices

### Fase 3: Views e Forms (2 dias)
- [ ] Adicionar decorator `@require_empresa` em todas as views
- [ ] Alterar queries para `.for_empresa(request.empresa)`
- [ ] Setar `obj.empresa = request.empresa` em creates
- [ ] Atualizar forms para receber `empresa`
- [ ] Validar empresa em `clean()` dos forms

### Fase 4: Configuração (1 dia)
- [ ] Adicionar middleware em `settings.py`
- [ ] Adicionar context processor em `settings.py`
- [ ] Criar view `selecionar_empresa`
- [ ] Criar template de seleção de empresa
- [ ] Adicionar seletor de empresa no navbar
- [ ] Testar login e seleção de empresa

### Fase 5: Testes (1 dia)
- [ ] Rodar `tests_multiempresa.py`
- [ ] Testar isolamento de dados manualmente
- [ ] Testar alternância de empresa
- [ ] Testar bloqueio de acesso sem empresa
- [ ] Testar queries filtradas
- [ ] Validar performance com índices

### Fase 6: Documentação (1 dia)
- [ ] Documentar processo para equipe
- [ ] Criar guia de uso para usuários
- [ ] Atualizar README
- [ ] Registrar mudanças no sistema

---

## 🆘 TROUBLESHOOTING COMUM

### Erro: "empresa_id cannot be null"
**Solução:** Verificar se migration populou dados existentes antes de tornar campo NOT NULL

### Erro: "request object has no attribute 'empresa'"
**Solução:** Verificar se middleware está configurado em settings.py e se view tem decorator @require_empresa

### Usuário não consegue acessar sistema
**Solução:** 
1. Verificar se UsuarioEmpresa existe e está ativo
2. Verificar se empresa está ativa
3. Verificar se empresa_ativa_id está na sessão

### Dados de outra empresa aparecendo
**Solução:**
1. Verificar uso de `.for_empresa()` em queries
2. Verificar decorator `@require_empresa` nas views
3. Verificar middleware ativo

---

**🎉 PRONTO! Sistema multiempresa implementado com sucesso!**
