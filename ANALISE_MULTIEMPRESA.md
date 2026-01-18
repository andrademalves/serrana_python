# ANÁLISE E IMPLEMENTAÇÃO MULTIEMPRESA - SISTEMA SERRANA

## 📊 SITUAÇÃO ATUAL

### ✅ O QUE JÁ EXISTE

1. **Modelo Empresa Criado** (`usuarios/models.py`)
   - ✅ Tabela `empresas` criada com todos os campos
   - ✅ Modelo `UsuarioEmpresa` (relacionamento M2M)
   - ✅ Empresa padrão "Serrana" (CNPJ: 00000000000000)
   - ✅ Interface administrativa configurada
   - ✅ Menu de gestão de empresas

2. **Estrutura Preparada**
   - ✅ Validações de CNPJ
   - ✅ Slug automático
   - ✅ Campos de auditoria (criado_em, criado_por, etc.)
   - ✅ Logo e identidade visual

### ❌ O QUE FALTA IMPLEMENTAR

**NENHUM modelo operacional tem FK para Empresa ainda!**

Os modelos abaixo **NÃO têm** controle de empresa:
- ❌ `cadastros.Pessoa`
- ❌ `cadastros.Produto`
- ❌ `estoque.Item`
- ❌ `estoque.MovimentoEstoque`
- ❌ `estoque.LocalEstoque`
- ❌ `projetos.Orcamento`
- ❌ `projetos.Projeto`
- ❌ `financeiro.ContaFinanceira`
- ❌ `financeiro.TituloFinanceiro`

---

## 🎯 ESTRATÉGIA DE IMPLEMENTAÇÃO

### FASE 1: Adicionar FK `empresa` nos Modelos

#### 1.1 Cadastros (Prioridade ALTA)

```python
# cadastros/models.py

class Pessoa(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='pessoas',
        verbose_name='Empresa',
        help_text='Empresa à qual esta pessoa pertence'
    )
    
    class Meta:
        # ... configurações existentes ...
        unique_together = [
            ['empresa', 'cpf_cnpj'],  # CPF/CNPJ único por empresa
        ]
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['empresa', 'cliente']),
            models.Index(fields=['empresa', 'fornecedor']),
        ]


class Produto(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='produtos',
        verbose_name='Empresa'
    )
    
    class Meta:
        # ... configurações existentes ...
        unique_together = [
            ['empresa', 'codigo'],  # Código único por empresa
        ]
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['empresa', 'tipo']),
        ]
```

#### 1.2 Estoque (Prioridade ALTA)

```python
# estoque/models.py

class Item(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='itens_estoque',
        verbose_name='Empresa'
    )
    
    class Meta:
        # ... configurações existentes ...
        unique_together = [
            ['empresa', 'codigo'],
        ]
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['empresa', 'tipo_item']),
        ]


class LocalEstoque(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='locais_estoque',
        verbose_name='Empresa'
    )
    
    class Meta:
        unique_together = [
            ['empresa', 'codigo'],
        ]


class MovimentoEstoque(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='movimentos_estoque',
        verbose_name='Empresa'
    )
    
    class Meta:
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'data_movimento']),
            models.Index(fields=['empresa', 'tipo_movimento']),
        ]
```

#### 1.3 Projetos (Prioridade MÉDIA)

```python
# projetos/models.py

class Orcamento(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        verbose_name='Empresa'
    )
    
    class Meta:
        # ... configurações existentes ...
        unique_together = [
            ['empresa', 'codigo'],  # Código único por empresa
        ]
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['empresa', 'data_orcamento']),
        ]


class Projeto(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='projetos',
        verbose_name='Empresa'
    )
```

#### 1.4 Financeiro (Prioridade MÉDIA)

```python
# financeiro/models.py

class ContaFinanceira(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='contas_financeiras',
        verbose_name='Empresa'
    )
    
    class Meta:
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'tipo']),
            models.Index(fields=['empresa', 'ativo']),
        ]


class TituloFinanceiro(models.Model):
    # ... campos existentes ...
    
    # ADICIONAR:
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='titulos_financeiros',
        verbose_name='Empresa'
    )
    
    class Meta:
        indexes = [
            # ... índices existentes ...
            models.Index(fields=['empresa', 'tipo']),
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['empresa', 'data_vencimento']),
        ]
```

---

## 🔄 PROCESSO DE MIGRAÇÃO SEGURA (3 PASSOS)

### ⚠️ IMPORTANTE: Migração em 3 etapas para dados existentes

```python
# Passo 1: Adicionar campo NULLABLE
# cadastros/migrations/0003_adicionar_empresa_nullable.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('cadastros', '0002_...'),
        ('usuarios', '0002_empresa_usuarioempresa_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                null=True,  # ← NULLABLE temporariamente
                blank=True,
                on_delete=models.PROTECT,
                related_name='pessoas',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        migrations.AddField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(
                null=True,  # ← NULLABLE temporariamente
                blank=True,
                on_delete=models.PROTECT,
                related_name='produtos',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
    ]


# Passo 2: Popular com empresa padrão
# cadastros/migrations/0004_popular_empresa_padrao.py

from django.db import migrations

def popular_empresa_padrao(apps, schema_editor):
    """Vincula todos os registros existentes à empresa padrão 'Serrana'"""
    Pessoa = apps.get_model('cadastros', 'Pessoa')
    Produto = apps.get_model('cadastros', 'Produto')
    Empresa = apps.get_model('usuarios', 'Empresa')
    
    # Buscar empresa padrão (primeira criada ou CNPJ específico)
    empresa_padrao = Empresa.objects.filter(cnpj='00000000000000').first()
    if not empresa_padrao:
        empresa_padrao = Empresa.objects.first()
    
    if empresa_padrao:
        # Atualizar pessoas sem empresa
        Pessoa.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)
        
        # Atualizar produtos sem empresa
        Produto.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)
        
        print(f"✅ Registros vinculados à empresa: {empresa_padrao.nome_fantasia}")

def reverter_empresa_padrao(apps, schema_editor):
    """Reverter: limpar empresa dos registros"""
    Pessoa = apps.get_model('cadastros', 'Pessoa')
    Produto = apps.get_model('cadastros', 'Produto')
    
    Pessoa.objects.all().update(empresa=None)
    Produto.objects.all().update(empresa=None)

class Migration(migrations.Migration):
    dependencies = [
        ('cadastros', '0003_adicionar_empresa_nullable'),
    ]

    operations = [
        migrations.RunPython(
            popular_empresa_padrao,
            reverter_empresa_padrao
        ),
    ]


# Passo 3: Tornar campo OBRIGATÓRIO
# cadastros/migrations/0005_empresa_required.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('cadastros', '0004_popular_empresa_padrao'),
    ]

    operations = [
        # Tornar empresa obrigatória em Pessoa
        migrations.AlterField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                on_delete=models.PROTECT,  # null=False, blank=False (padrão)
                related_name='pessoas',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        
        # Tornar empresa obrigatória em Produto
        migrations.AlterField(
            model_name='produto',
            name='empresa',
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name='produtos',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        
        # Adicionar unique_together
        migrations.AlterUniqueTogether(
            name='pessoa',
            unique_together={('empresa', 'cpf_cnpj')},
        ),
        migrations.AlterUniqueTogether(
            name='produto',
            unique_together={('empresa', 'codigo')},
        ),
        
        # Adicionar índices
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['empresa', 'ativo'], name='pessoa_emp_ativo_idx'),
        ),
        migrations.AddIndex(
            model_name='produto',
            index=models.Index(fields=['empresa', 'ativo'], name='produto_emp_ativo_idx'),
        ),
    ]
```

---

## 🔧 FASE 2: Atualizar Views e Forms

### 2.1 Criar Decorator para Empresa Ativa

```python
# usuarios/decorators.py

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def require_empresa(view_func):
    """
    Decorator que garante que o usuário tem uma empresa ativa na sessão
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        empresa_id = request.session.get('empresa_ativa_id')
        
        if not empresa_id:
            # Tentar definir empresa padrão do usuário
            from usuarios.models import UsuarioEmpresa
            vinculo = UsuarioEmpresa.objects.filter(
                usuario=request.user,
                ativo=True
            ).first()
            
            if vinculo:
                request.session['empresa_ativa_id'] = vinculo.empresa_id
                request.empresa = vinculo.empresa
            else:
                messages.error(request, 'Nenhuma empresa ativa. Contate o administrador.')
                return redirect('usuarios:selecionar_empresa')
        else:
            from usuarios.models import Empresa
            try:
                request.empresa = Empresa.objects.get(id=empresa_id, ativa=True)
            except Empresa.DoesNotExist:
                messages.error(request, 'Empresa inválida ou inativa.')
                del request.session['empresa_ativa_id']
                return redirect('usuarios:selecionar_empresa')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
```

### 2.2 Atualizar Views de Cadastros

```python
# cadastros/views.py

from usuarios.decorators import require_empresa

@login_required
@require_empresa  # ← ADICIONAR
def listar_pessoas(request):
    # Filtrar apenas da empresa ativa
    pessoas = Pessoa.objects.filter(
        empresa=request.empresa,  # ← ADICIONAR
        ativo=True
    )
    # ... resto do código ...


@login_required
@require_empresa  # ← ADICIONAR
def criar_pessoa(request):
    if request.method == 'POST':
        # ... validações ...
        
        pessoa = Pessoa(
            empresa=request.empresa,  # ← ADICIONAR automaticamente
            tipo=request.POST.get('tipo'),
            nome=request.POST.get('nome'),
            # ... outros campos ...
            criado_por=request.user
        )
        pessoa.save()
        # ... resto ...


@login_required
@require_empresa  # ← ADICIONAR
def editar_pessoa(request, pessoa_id):
    # Garantir que só edita da empresa ativa
    pessoa = get_object_or_404(
        Pessoa, 
        id=pessoa_id,
        empresa=request.empresa  # ← ADICIONAR
    )
    # ... resto do código ...
```

### 2.3 Atualizar Forms

```python
# cadastros/forms.py (criar se não existir)

from django import forms
from .models import Pessoa, Produto

class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['tipo', 'nome', 'cpf_cnpj', ...]  # empresa NÃO aparece
        # O campo empresa será definido automaticamente na view
    
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        
        # Filtrar fornecedores da mesma empresa
        if 'fornecedor' in self.fields:
            self.fields['fornecedor'].queryset = Pessoa.objects.filter(
                empresa=empresa,
                fornecedor=True,
                ativo=True
            )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa and not instance.empresa_id:
            instance.empresa = self.empresa
        if commit:
            instance.save()
        return instance


# Uso na view:
def criar_pessoa(request):
    if request.method == 'POST':
        form = PessoaForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            pessoa = form.save()
            messages.success(request, 'Pessoa criada com sucesso!')
            return redirect('cadastros:listar_pessoas')
    else:
        form = PessoaForm(empresa=request.empresa)
    
    return render(request, 'cadastros/criar_pessoa.html', {'form': form})
```

---

## 🎨 FASE 3: Interface de Seleção de Empresa

### 3.1 View de Seleção

```python
# usuarios/views.py

@login_required
def selecionar_empresa(request):
    """Permite usuário selecionar empresa ativa"""
    empresas_usuario = Empresa.objects.filter(
        empresa_usuarios__usuario=request.user,
        empresa_usuarios__ativo=True,
        ativa=True
    ).distinct()
    
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        empresa = get_object_or_404(
            empresas_usuario,
            id=empresa_id
        )
        request.session['empresa_ativa_id'] = empresa.id
        messages.success(request, f'Empresa alterada para: {empresa.nome_fantasia}')
        
        # Redirecionar para página original ou dashboard
        next_url = request.GET.get('next', 'usuarios:home_modulos')
        return redirect(next_url)
    
    context = {
        'empresas': empresas_usuario,
        'empresa_ativa_id': request.session.get('empresa_ativa_id'),
    }
    return render(request, 'usuarios/selecionar_empresa.html', context)


@login_required
@require_empresa
def trocar_empresa(request, empresa_id):
    """Atalho para trocar empresa"""
    empresa = get_object_or_404(
        Empresa,
        id=empresa_id,
        empresa_usuarios__usuario=request.user,
        empresa_usuarios__ativo=True,
        ativa=True
    )
    request.session['empresa_ativa_id'] = empresa.id
    messages.success(request, f'Agora você está operando como: {empresa.nome_fantasia}')
    return redirect(request.META.get('HTTP_REFERER', 'usuarios:home_modulos'))
```

### 3.2 Template de Seleção

```html
<!-- usuarios/templates/usuarios/selecionar_empresa.html -->
{% extends 'base.html' %}

{% block title %}Selecionar Empresa{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">
                        <i class="bi bi-building"></i> Selecione a Empresa
                    </h4>
                </div>
                <div class="card-body">
                    {% if empresas %}
                        <form method="post">
                            {% csrf_token %}
                            <div class="list-group mb-3">
                                {% for empresa in empresas %}
                                <label class="list-group-item list-group-item-action">
                                    <input type="radio" name="empresa_id" value="{{ empresa.id }}" 
                                           {% if empresa.id == empresa_ativa_id %}checked{% endif %}>
                                    <div class="d-flex align-items-center">
                                        {% if empresa.logo %}
                                        <img src="{{ empresa.logo.url }}" alt="Logo" class="me-3" style="height: 40px;">
                                        {% endif %}
                                        <div>
                                            <strong>{{ empresa.nome_fantasia }}</strong>
                                            <br>
                                            <small class="text-muted">{{ empresa.razao_social }}</small>
                                        </div>
                                        {% if empresa.empresa_matriz %}
                                        <span class="badge bg-primary ms-auto">Matriz</span>
                                        {% endif %}
                                    </div>
                                </label>
                                {% endfor %}
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="bi bi-check-circle"></i> Selecionar
                            </button>
                        </form>
                    {% else %}
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle"></i>
                            Você não tem acesso a nenhuma empresa. 
                            Contate o administrador do sistema.
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 3.3 Adicionar Seletor na Navbar

```html
<!-- templates/base.html ou partials/navbar.html -->

{% if request.empresa %}
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="empresaDropdown" 
       data-bs-toggle="dropdown" aria-expanded="false">
        <i class="bi bi-building"></i> 
        {{ request.empresa.nome_fantasia }}
    </a>
    <ul class="dropdown-menu" aria-labelledby="empresaDropdown">
        {% for empresa in user.usuario_empresas.all %}
            {% if empresa.ativo %}
            <li>
                <a class="dropdown-item {% if empresa.empresa_id == request.empresa.id %}active{% endif %}" 
                   href="{% url 'usuarios:trocar_empresa' empresa.empresa_id %}">
                    <i class="bi bi-{% if empresa.empresa_id == request.empresa.id %}check-circle{% else %}building{% endif %}"></i>
                    {{ empresa.empresa.nome_fantasia }}
                </a>
            </li>
            {% endif %}
        {% endfor %}
        <li><hr class="dropdown-divider"></li>
        <li>
            <a class="dropdown-item" href="{% url 'usuarios:selecionar_empresa' %}">
                <i class="bi bi-arrow-left-right"></i> Alterar Empresa
            </a>
        </li>
    </ul>
</li>
{% endif %}
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Cadastros
- [ ] Adicionar campo `empresa` em `Pessoa`
- [ ] Adicionar campo `empresa` em `Produto`
- [ ] Criar migration 3-passos (nullable → popular → required)
- [ ] Atualizar `listar_pessoas` com filtro de empresa
- [ ] Atualizar `criar_pessoa` para setar empresa automaticamente
- [ ] Atualizar `editar_pessoa` para verificar empresa
- [ ] Atualizar `listar_produtos` com filtro de empresa
- [ ] Criar `PessoaForm` e `ProdutoForm` com empresa

### Estoque
- [ ] Adicionar campo `empresa` em `Item`
- [ ] Adicionar campo `empresa` em `LocalEstoque`
- [ ] Adicionar campo `empresa` em `MovimentoEstoque`
- [ ] Criar migrations 3-passos
- [ ] Atualizar todas as views com `@require_empresa`
- [ ] Filtrar querysets por `empresa=request.empresa`

### Projetos
- [ ] Adicionar campo `empresa` em `Orcamento`
- [ ] Adicionar campo `empresa` em `Projeto`
- [ ] Criar migrations 3-passos
- [ ] Atualizar views e forms

### Financeiro
- [ ] Adicionar campo `empresa` em `ContaFinanceira`
- [ ] Adicionar campo `empresa` em `TituloFinanceiro`
- [ ] Criar migrations 3-passos
- [ ] Atualizar views e forms

### Interface
- [ ] Criar view `selecionar_empresa`
- [ ] Criar template `selecionar_empresa.html`
- [ ] Criar view `trocar_empresa`
- [ ] Adicionar seletor de empresa na navbar
- [ ] Testar fluxo completo de troca de empresa

### Testes
- [ ] Criar testes de isolamento de dados
- [ ] Testar que Empresa A não vê dados de Empresa B
- [ ] Testar validação de unique_together
- [ ] Testar performance com índices

---

## 🚀 ORDEM DE EXECUÇÃO RECOMENDADA

1. **Dia 1-2: Cadastros**
   - Implementar empresa em Pessoa e Produto
   - Executar migrations
   - Atualizar views básicas (listar, criar)
   - Testar isolamento básico

2. **Dia 3-4: Estoque**
   - Implementar empresa em Item, LocalEstoque, MovimentoEstoque
   - Executar migrations
   - Atualizar views
   - Testar movimentações isoladas

3. **Dia 5: Interface de Seleção**
   - Criar seletor de empresa
   - Adicionar na navbar
   - Testar troca de empresa
   - Validar sessão

4. **Dia 6-7: Projetos e Financeiro**
   - Implementar empresa em Orcamento, Projeto
   - Implementar empresa em módulo financeiro
   - Atualizar todas as views

5. **Dia 8-10: Testes e Ajustes**
   - Testes de isolamento
   - Performance com índices
   - Documentação
   - Treinamento equipe

---

## ⚠️ PONTOS DE ATENÇÃO

1. **Backup Obrigatório**: Fazer backup completo antes de iniciar migrations
2. **Ambiente de Teste**: Testar todas as migrations em ambiente de desenvolvimento primeiro
3. **Dados Existentes**: A estratégia 3-passos garante que dados existentes sejam preservados
4. **Performance**: Todos os índices foram planejados para queries com filtro de empresa
5. **Rollback**: Cada migration tem operação reversa definida

---

## 📌 RESUMO EXECUTIVO

**Situação**: Sistema tem estrutura de empresa criada mas **nenhum dado operacional está vinculado**

**Solução**: Adicionar FK `empresa` em todos os modelos usando migração segura em 3 passos

**Resultado Esperado**: 
- ✅ Isolamento completo de dados entre empresas
- ✅ Um usuário pode acessar múltiplas empresas
- ✅ Dados existentes migrados automaticamente para empresa padrão
- ✅ Interface para troca de empresa ativa
- ✅ Performance otimizada com índices corretos

**Tempo Estimado**: 8-10 dias de desenvolvimento + testes
