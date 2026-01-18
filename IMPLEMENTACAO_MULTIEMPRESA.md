# 🏢 IMPLEMENTAÇÃO MULTIEMPRESA - SISTEMA SERRANA

## 📋 ÍNDICE
1. [Diagnóstico do Sistema](#1-diagnóstico-do-sistema)
2. [Estratégia Multiempresa](#2-estratégia-multiempresa)
3. [Alterações por Arquivo](#3-alterações-por-arquivo)
4. [Migrations](#4-migrations-e-cuidados)
5. [Testes Automatizados](#5-testes-automatizados)
6. [Observações Finais](#6-observações-finais)

---

## 1. DIAGNÓSTICO DO SISTEMA

### ✅ **Apps e Modelos Identificados:**

**USUÁRIOS:**
- User (Django Auth)
- PerfilUsuario
- Modulo, Menu, Permissao

**CADASTROS:**
- Pessoa (Cliente, Fornecedor, Funcionário)
- Produto

**ESTOQUE:**
- Item
- LocalEstoque
- MovimentoEstoque
- SaldoEstoque
- BOM, BOMItem
- OrdemProducao

**PROJETOS:**
- Orcamento, OrcamentoItem, OrcamentoParcela
- Projeto
- VendaDireta, VendaDiretaItem
- AlocacaoProjeto
- VisitaTecnica

**FINANCEIRO:**
- Banco
- ContaFinanceira
- FormaPagamento
- TituloFinanceiro
- ParcelaFinanceira
- BaixaFinanceira
- Categoria, PlanoContas

### ⚠️ **Riscos Mapeados:**

1. **DADOS EXISTENTES** - Sistema já tem dados em produção
2. **QUERIES SEM FILTRO** - Queries podem retornar dados de todas empresas
3. **FORMS SEM VALIDAÇÃO** - Possibilidade de alterar empresa_id via POST
4. **RELACIONAMENTOS** - ForeignKeys entre modelos precisam validar mesma empresa
5. **SALDOS/TOTALIZAÇÕES** - Cálculos agregados precisam filtrar por empresa
6. **PERFORMANCE** - Índices adicionais para empresa_id
7. **AUDITORIA** - Rastreio de alterações entre empresas

---

## 2. ESTRATÉGIA MULTIEMPRESA

### 🎯 **Abordagem: Row-Level Multi-Tenancy**

Cada registro tem uma FK para `Empresa`. Isolamento via filtros automáticos.

**Vantagens:**
- ✅ Implementação gradual e segura
- ✅ Backup unificado
- ✅ Relacionamentos entre modelos funcionam nativamente
- ✅ Queries simples com `.filter(empresa=request.empresa)`
- ✅ Suporte a relatórios consolidados (opcional)

**Estrutura:**
```
Empresa (M) ←─── (1) PerfilUsuario (1) ←─── (1) User
     ↑                                            ↓
     │                                   UsuarioEmpresa (M2M)
     │                                            ↓
     └────────── (FK) ─── Todos os Models Operacionais
```

### 🔐 **Segurança e Isolamento:**

1. **Middleware de Empresa Ativa**
   - Detecta empresa do contexto
   - Injeta `request.empresa` em todas as requests
   - Bloqueia acesso se usuário não tiver empresa ativa

2. **Managers Customizados**
   - `objects.for_empresa(empresa)` - filtra automaticamente
   - `objects.all_empresas()` - retorna tudo (admin only)

3. **Validações em Forms**
   - `clean()` valida que empresa do objeto == empresa do request
   - Previne alteração via POST

4. **Querysets Seguros**
   - Filtros automáticos em views
   - Decoradores `@require_empresa`

---

## 3. ALTERAÇÕES POR ARQUIVO

### 📁 **1. NOVOS ARQUIVOS CRIADOS**

#### `usuarios/models_empresa.py` ✅ (JÁ CRIADO)
```python
# Models: Empresa, UsuarioEmpresa
# Ver arquivo criado para detalhes completos
```

#### `usuarios/middleware.py` (CRIAR)
```python
"""
Middleware de Empresa Ativa
Injeta request.empresa em todas as requests
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models_empresa import Empresa, UsuarioEmpresa


class EmpresaAtivaMiddleware:
    """
    Middleware que garante que o usuário sempre tenha uma empresa ativa no contexto
    """
    
    # URLs que não requerem empresa (login, logout, seleção de empresa)
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/empresas/selecionar/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs isentas
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return self.get_response(request)
        
        # Usuário não autenticado
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Buscar empresa ativa na sessão
        empresa_id = request.session.get('empresa_ativa_id')
        
        if empresa_id:
            try:
                empresa = Empresa.objects.get(pk=empresa_id, ativa=True)
                
                # Verificar se usuário tem acesso a esta empresa
                if self._usuario_tem_acesso(request.user, empresa):
                    request.empresa = empresa
                else:
                    # Usuário perdeu acesso - limpar sessão
                    del request.session['empresa_ativa_id']
                    return self._redirecionar_selecao_empresa(request)
            except Empresa.DoesNotExist:
                # Empresa foi deletada ou desativada
                del request.session['empresa_ativa_id']
                return self._redirecionar_selecao_empresa(request)
        else:
            # Nenhuma empresa na sessão - redirecionar para seleção
            return self._redirecionar_selecao_empresa(request)
        
        response = self.get_response(request)
        return response
    
    def _usuario_tem_acesso(self, user, empresa):
        """Verifica se usuário tem acesso à empresa"""
        # Superuser tem acesso a tudo
        if user.is_superuser:
            return True
        
        # Verificar via PerfilUsuario.empresa_padrao
        if hasattr(user, 'perfilusuario') and user.perfilusuario.empresa_padrao == empresa:
            return True
        
        # Verificar via UsuarioEmpresa (M2M)
        return UsuarioEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            ativo=True
        ).exists()
    
    def _redirecionar_selecao_empresa(self, request):
        """Redireciona para página de seleção de empresa"""
        messages.warning(request, 'Selecione uma empresa para continuar.')
        return redirect('selecionar_empresa')  # View a ser criada


class EmpresaContextProcessor:
    """
    Context processor que adiciona empresa ao template context
    """
    def __call__(self, request):
        if hasattr(request, 'empresa'):
            return {
                'empresa_ativa': request.empresa,
                'empresa_nome': request.empresa.nome_fantasia,
                'empresa_logo': request.empresa.logo.url if request.empresa.logo else None,
            }
        return {}
```

#### `usuarios/managers.py` (CRIAR)
```python
"""
Managers customizados para filtro automático por empresa
"""
from django.db import models


class EmpresaQuerySet(models.QuerySet):
    """QuerySet que filtra automaticamente por empresa"""
    
    def for_empresa(self, empresa):
        """Filtra registros da empresa especificada"""
        return self.filter(empresa=empresa)
    
    def all_empresas(self):
        """Retorna todos os registros (sem filtro) - usar com cuidado!"""
        return self


class EmpresaManager(models.Manager):
    """Manager que adiciona métodos de filtro por empresa"""
    
    def get_queryset(self):
        return EmpresaQuerySet(self.model, using=self._db)
    
    def for_empresa(self, empresa):
        """Atalho para filtrar por empresa"""
        return self.get_queryset().for_empresa(empresa)
    
    def all_empresas(self):
        """Retorna tudo sem filtro - admin only"""
        return self.get_queryset().all_empresas()
```

#### `usuarios/decorators.py` (ADICIONAR)
```python
# ADICIONAR aos decorators existentes

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def require_empresa(view_func):
    """
    Decorator que garante que request.empresa existe
    Redireciona para seleção se não houver
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'empresa'):
            messages.error(request, 'Você precisa estar vinculado a uma empresa.')
            return redirect('selecionar_empresa')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def empresa_ativa_required(view_func):
    """
    Decorator que valida se a empresa ativa está ativa
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request, 'empresa') and not request.empresa.ativa:
            messages.error(request, 'A empresa selecionada está inativa.')
            return redirect('selecionar_empresa')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

---

### 📁 **2. ALTERAÇÕES EM MODELS EXISTENTES**

#### Padrão de Alteração para TODOS os models operacionais:

```python
# ANTES
class MinhaModel(models.Model):
    campo1 = models.CharField(...)
    
    class Meta:
        db_table = 'tabela'

# DEPOIS
from usuarios.models_empresa import Empresa
from usuarios.managers import EmpresaManager

class MinhaModel(models.Model):
    # ===== ADICIONAR ESTE CAMPO EM TODOS OS MODELS =====
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='%(class)s_set',  # Dinâmico: pessoa_set, produto_set, etc
        verbose_name='Empresa',
        help_text='Empresa dona deste registro'
    )
    # ===================================================
    
    campo1 = models.CharField(...)
    
    # ===== ADICIONAR MANAGER CUSTOMIZADO =====
    objects = EmpresaManager()
    # ========================================
    
    class Meta:
        db_table = 'tabela'
        # ===== ADICIONAR ÍNDICE =====
        indexes = [
            models.Index(fields=['empresa']),
            # ... outros índices
        ]
        # ============================
```

#### **MODELS A ALTERAR:**

**cadastros/models.py:**
- ✅ Pessoa (adicionar `empresa`)
- ✅ Produto (adicionar `empresa`)

**estoque/models.py:**
- ✅ Item (adicionar `empresa`)
- ✅ LocalEstoque (adicionar `empresa`)
- ✅ MovimentoEstoque (adicionar `empresa`)
- ✅ SaldoEstoque (adicionar `empresa`)
- ✅ BOM (adicionar `empresa`)
- ✅ OrdemProducao (adicionar `empresa`)

**projetos/models.py:**
- ✅ Orcamento (adicionar `empresa`)
- ✅ Projeto (adicionar `empresa`)
- ✅ VendaDireta (adicionar `empresa`)

**financeiro/models.py:**
- ✅ Banco (pode ser compartilhado - decidir)
- ✅ ContaFinanceira (adicionar `empresa`)
- ✅ FormaPagamento (pode ser compartilhado - decidir)
- ✅ TituloFinanceiro (adicionar `empresa`)
- ✅ PlanoContas (adicionar `empresa`)
- ✅ Categoria (adicionar `empresa`)

---

### 📁 **3. ALTERAÇÕES EM VIEWS**

#### Padrão para todas as views:

```python
# ANTES
@login_required
def listar_items(request):
    items = Item.objects.all()
    ...

# DEPOIS
from usuarios.decorators import require_empresa

@login_required
@require_empresa
def listar_items(request):
    # Filtrar automaticamente pela empresa ativa
    items = Item.objects.for_empresa(request.empresa)
    ...

# Para criar novos registros:
@login_required
@require_empresa
def criar_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.empresa = request.empresa  # <--- CRITICAL
            item.criado_por = request.user
            item.save()
            ...
```

---

### 📁 **4. ALTERAÇÕES EM FORMS**

```python
# ADICIONAR em todos os Forms de Models com empresa

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['codigo', 'descricao', ...]  # NÃO incluir 'empresa' aqui
        # empresa será setado automaticamente na view
    
    def __init__(self, *args, **kwargs):
        # Receber empresa do contexto
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Se empresa foi fornecida, filtrar ForeignKeys relacionados
        if self.empresa:
            # Exemplo: filtrar apenas locais da mesma empresa
            if 'local' in self.fields:
                self.fields['local'].queryset = LocalEstoque.objects.for_empresa(self.empresa)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # SEGURANÇA: Validar que não está tentando alterar empresa
        if self.instance.pk and self.instance.empresa != self.empresa:
            raise forms.ValidationError('Você não pode alterar a empresa deste registro.')
        
        return cleaned_data
```

---

### 📁 **5. CONFIGURAÇÕES**

#### `serrana/settings.py` - ADICIONAR:

```python
INSTALLED_APPS = [
    ...
    'usuarios',  # já existe
    'cadastros',
    'estoque',
    'projetos',
    'financeiro',
]

MIDDLEWARE = [
    ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'usuarios.middleware.EmpresaAtivaMiddleware',  # <--- ADICIONAR AQUI
    ...
]

# Context processors
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'usuarios.middleware.EmpresaContextProcessor',  # <--- ADICIONAR
            ],
        },
    },
]
```

---

## 4. MIGRATIONS E CUIDADOS

### 🚨 **ESTRATÉGIA DE MIGRAÇÃO**

#### **Passo 1: Criar Model Empresa**

```bash
# Criar models_empresa.py (já feito)
# Importar no __init__.py
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

#### **Passo 2: Criar Empresa Padrão**

```python
# Script: criar_empresa_padrao.py
from usuarios.models_empresa import Empresa
from django.contrib.auth.models import User

# Criar empresa padrão (Serrana)
empresa_padrao = Empresa.objects.create(
    razao_social='Serrana Ltda',
    nome_fantasia='Serrana',
    cnpj='00.000.000/0001-00',  # Ajustar CNPJ real
    slug='serrana',
    ativa=True,
    empresa_matriz=True,
    criado_por=User.objects.filter(is_superuser=True).first()
)

print(f"✅ Empresa padrão criada: {empresa_padrao}")
```

#### **Passo 3: Adicionar FK empresa aos Models** (CRÍTICO)

```bash
# Para CADA app (cadastros, estoque, projetos, financeiro)

# 1. Adicionar campo empresa nos models com null=True temporariamente
# 2. Criar migration
python manage.py makemigrations cadastros --name add_empresa_field

# 3. A migration terá empresa = models.ForeignKey(..., null=True, blank=True)
# 4. Rodar migration
python manage.py migrate cadastros

# 5. Popular empresa_id para registros existentes
python manage.py shell
>>> from cadastros.models import Pessoa
>>> from usuarios.models_empresa import Empresa
>>> empresa_padrao = Empresa.objects.first()
>>> Pessoa.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)

# 6. Alterar campo para NOT NULL
# Editar migration ou criar nova:
python manage.py makemigrations cadastros --name make_empresa_required

# 7. Aplicar
python manage.py migrate cadastros

# REPETIR para estoque, projetos, financeiro
```

#### **Exemplo de Migration Segura:**

```python
# cadastros/migrations/0003_add_empresa.py
from django.db import migrations, models
import django.db.models.deletion


def popular_empresa_padrao(apps, schema_editor):
    """Popula empresa padrão para registros existentes"""
    Pessoa = apps.get_model('cadastros', 'Pessoa')
    Empresa = apps.get_model('usuarios', 'Empresa')
    
    empresa_padrao = Empresa.objects.first()
    if empresa_padrao:
        Pessoa.objects.filter(empresa__isnull=True).update(empresa=empresa_padrao)


class Migration(migrations.Migration):
    dependencies = [
        ('cadastros', '0002_previous_migration'),
        ('usuarios', '0001_initial'),  # Depende de Empresa existir
    ]
    
    operations = [
        # Passo 1: Adicionar campo nullable
        migrations.AddField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pessoa_set',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        
        # Passo 2: Popular dados
        migrations.RunPython(popular_empresa_padrao, migrations.RunPython.noop),
        
        # Passo 3: Tornar campo obrigatório
        migrations.AlterField(
            model_name='pessoa',
            name='empresa',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pessoa_set',
                to='usuarios.empresa',
                verbose_name='Empresa'
            ),
        ),
        
        # Passo 4: Adicionar índice
        migrations.AddIndex(
            model_name='pessoa',
            index=models.Index(fields=['empresa'], name='pessoa_empresa_idx'),
        ),
    ]
```

---

## 5. TESTES AUTOMATIZADOS

```python
# usuarios/tests_multiempresa.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from usuarios.models_empresa import Empresa, UsuarioEmpresa
from cadastros.models import Pessoa


class MultiempresaTestCase(TestCase):
    """Testes de isolamento multiempresa"""
    
    def setUp(self):
        # Criar duas empresas
        self.empresa_a = Empresa.objects.create(
            razao_social='Empresa A Ltda',
            nome_fantasia='Empresa A',
            cnpj='11.111.111/0001-11',
            slug='empresa-a',
            ativa=True
        )
        
        self.empresa_b = Empresa.objects.create(
            razao_social='Empresa B Ltda',
            nome_fantasia='Empresa B',
            cnpj='22.222.222/0001-22',
            slug='empresa-b',
            ativa=True
        )
        
        # Criar usuários
        self.user_a = User.objects.create_user('user_a', password='senha123')
        self.user_b = User.objects.create_user('user_b', password='senha123')
        
        # Vincular usuários a empresas
        UsuarioEmpresa.objects.create(usuario=self.user_a, empresa=self.empresa_a, ativo=True)
        UsuarioEmpresa.objects.create(usuario=self.user_b, empresa=self.empresa_b, ativo=True)
    
    def test_isolamento_dados_entre_empresas(self):
        """Testar que usuário só vê dados da própria empresa"""
        # Criar pessoas em cada empresa
        pessoa_a = Pessoa.objects.create(
            nome='Cliente A',
            tipo='F',
            cpf_cnpj='111.111.111-11',
            empresa=self.empresa_a
        )
        
        pessoa_b = Pessoa.objects.create(
            nome='Cliente B',
            tipo='F',
            cpf_cnpj='222.222.222-22',
            empresa=self.empresa_b
        )
        
        # Verificar filtros
        self.assertEqual(Pessoa.objects.for_empresa(self.empresa_a).count(), 1)
        self.assertEqual(Pessoa.objects.for_empresa(self.empresa_b).count(), 1)
        
        # Verificar que pessoa_a não aparece no queryset de empresa_b
        self.assertNotIn(pessoa_a, Pessoa.objects.for_empresa(self.empresa_b))
        self.assertNotIn(pessoa_b, Pessoa.objects.for_empresa(self.empresa_a))
    
    def test_usuario_sem_empresa_bloqueado(self):
        """Usuário sem empresa não deve acessar sistema"""
        user_sem_empresa = User.objects.create_user('sem_empresa', password='senha123')
        
        client = Client()
        client.login(username='sem_empresa', password='senha123')
        
        response = client.get('/cadastros/pessoas/')
        # Deve redirecionar para seleção de empresa
        self.assertEqual(response.status_code, 302)
        self.assertIn('/empresas/selecionar/', response.url)
    
    def test_usuario_nao_pode_acessar_empresa_errada(self):
        """Usuário da empresa A não pode ver dados da empresa B"""
        client = Client()
        client.login(username='user_a', password='senha123')
        
        # Simular empresa_ativa na sessão
        session = client.session
        session['empresa_ativa_id'] = self.empresa_a.id
        session.save()
        
        # Tentar acessar pessoa da empresa B (não deve retornar)
        pessoa_b = Pessoa.objects.create(
            nome='Cliente B',
            tipo='F',
            cpf_cnpj='222.222.222-22',
            empresa=self.empresa_b
        )
        
        response = client.get(f'/cadastros/pessoas/{pessoa_b.id}/')
        # Deve dar 404 ou 403
        self.assertIn(response.status_code, [403, 404])
    
    def test_alternancia_de_empresa(self):
        """Usuário pode alternar entre empresas que tem acesso"""
        # Dar acesso a user_a em ambas empresas
        UsuarioEmpresa.objects.create(usuario=self.user_a, empresa=self.empresa_b, ativo=True)
        
        client = Client()
        client.login(username='user_a', password='senha123')
        
        # Selecionar empresa A
        session = client.session
        session['empresa_ativa_id'] = self.empresa_a.id
        session.save()
        
        # Verificar contexto
        response = client.get('/dashboard/')
        self.assertEqual(response.context['empresa_ativa'], self.empresa_a)
        
        # Trocar para empresa B
        session['empresa_ativa_id'] = self.empresa_b.id
        session.save()
        
        response = client.get('/dashboard/')
        self.assertEqual(response.context['empresa_ativa'], self.empresa_b)
    
    def test_criacao_registro_sempre_com_empresa(self):
        """Registros novos devem sempre ter empresa"""
        # Simular request com empresa
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.post('/cadastros/pessoas/criar/')
        request.user = self.user_a
        request.empresa = self.empresa_a
        
        # Criar pessoa (view simulada)
        pessoa = Pessoa.objects.create(
            nome='Nova Pessoa',
            tipo='F',
            cpf_cnpj='333.333.333-33',
            empresa=request.empresa
        )
        
        self.assertEqual(pessoa.empresa, self.empresa_a)
    
    def test_queries_sempre_filtradas_por_empresa(self):
        """Todas as queries devem filtrar por empresa"""
        # Criar 10 pessoas na empresa A
        for i in range(10):
            Pessoa.objects.create(
                nome=f'Pessoa A{i}',
                tipo='F',
                cpf_cnpj=f'111.111.{i:03d}-11',
                empresa=self.empresa_a
            )
        
        # Criar 5 pessoas na empresa B
        for i in range(5):
            Pessoa.objects.create(
                nome=f'Pessoa B{i}',
                tipo='F',
                cpf_cnpj=f'222.222.{i:03d}-22',
                empresa=self.empresa_b
            )
        
        # Verificar filtros
        self.assertEqual(Pessoa.objects.for_empresa(self.empresa_a).count(), 10)
        self.assertEqual(Pessoa.objects.for_empresa(self.empresa_b).count(), 5)
        self.assertEqual(Pessoa.objects.all().count(), 15)
```

---

## 6. OBSERVAÇÕES FINAIS

### ✅ **CHECKLIST DE IMPLEMENTAÇÃO**

- [ ] 1. Criar models Empresa e UsuarioEmpresa
- [ ] 2. Criar middleware EmpresaAtivaMiddleware
- [ ] 3. Criar managers customizados EmpresaManager
- [ ] 4. Criar decorators @require_empresa
- [ ] 5. Criar empresa padrão no banco
- [ ] 6. Adicionar FK empresa em TODOS os models (com migration segura)
- [ ] 7. Popular empresa_id para dados existentes
- [ ] 8. Atualizar TODAS as views com @require_empresa
- [ ] 9. Filtrar queries com .for_empresa(request.empresa)
- [ ] 10. Atualizar forms para validar empresa
- [ ] 11. Criar view de seleção de empresa
- [ ] 12. Criar template de seleção de empresa
- [ ] 13. Atualizar navbar para mostrar empresa ativa
- [ ] 14. Criar testes automatizados
- [ ] 15. Testar isolamento completo
- [ ] 16. Adicionar índices para performance
- [ ] 17. Documentar processo para time

### 🔒 **SEGURANÇA CRÍTICA**

**NUNCA:**
- ❌ Permitir `empresa_id` em forms POST
- ❌ Usar `.all()` em queries (sempre `.for_empresa()`)
- ❌ Confiar em `request.POST.get('empresa_id')`
- ❌ Pular validação de empresa em `clean()`

**SEMPRE:**
- ✅ Setar `obj.empresa = request.empresa` na view
- ✅ Validar empresa antes de save
- ✅ Filtrar ForeignKeys por mesma empresa
- ✅ Testar isolamento com testes automatizados

### 📊 **PERFORMANCE**

**Índices obrigatórios:**
```sql
CREATE INDEX idx_pessoa_empresa ON pessoas(empresa_id);
CREATE INDEX idx_item_empresa ON itens(empresa_id);
CREATE INDEX idx_orcamento_empresa ON orcamentos(empresa_id);
-- ... para TODOS os models
```

**Queries otimizadas:**
```python
# BOM
Pessoa.objects.for_empresa(request.empresa).select_related('empresa')

# RUIM (N+1 queries)
Pessoa.objects.all()  # sem filtro
for p in pessoas:
    if p.empresa == request.empresa:  # validação em Python
        ...
```

### 🎨 **UI/UX**

**Navbar - Seletor de Empresa:**
```html
<!-- Adicionar no header -->
<div class="empresa-selector">
    <i class="bi bi-building"></i>
    <span>{{ empresa_ativa.nome_fantasia }}</span>
    <a href="{% url 'selecionar_empresa' %}">Trocar</a>
</div>
```

**Página de Seleção:**
- Listar empresas que o usuário tem acesso
- Permitir troca rápida
- Mostrar empresa ativa destacada

### 📚 **PRÓXIMOS PASSOS**

1. **Fase 1 (1-2 dias):**
   - Criar models Empresa
   - Criar middleware
   - Testar com 1 empresa

2. **Fase 2 (2-3 dias):**
   - Migrations para adicionar FK empresa
   - Popular dados existentes
   - Testar isolamento

3. **Fase 3 (1-2 dias):**
   - Atualizar views e forms
   - Adicionar decorators
   - Criar view de seleção

4. **Fase 4 (1 dia):**
   - Testes automatizados
   - Testes manuais
   - Documentação

### 🆘 **TROUBLESHOOTING**

**Erro: "empresa_id cannot be null"**
- Verificar se migration populou dados existentes
- Verificar se view está setando `obj.empresa = request.empresa`

**Usuário não consegue acessar sistema:**
- Verificar UsuarioEmpresa ativo
- Verificar empresa_ativa_id na sessão
- Verificar se empresa está ativa

**Dados de outra empresa aparecendo:**
- Verificar filtro `.for_empresa()` em queries
- Verificar se decorator `@require_empresa` está presente
- Checar middleware está ativo

---

**🎉 FIM DA DOCUMENTAÇÃO**

**Autor:** Arquiteto Django Sênior  
**Data:** 2026-01-01  
**Versão:** 1.0  
**Sistema:** Serrana ERP Multiempresa
