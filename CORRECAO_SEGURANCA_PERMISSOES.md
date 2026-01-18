# 🔒 CORREÇÃO DE SEGURANÇA - VALIDAÇÃO DE PERMISSÕES

## ⚠️ PROBLEMA IDENTIFICADO

Usuários conseguiam acessar módulos sem permissão através da sidebar e URLs diretas.

**Exemplo:** Usuário com permissão APENAS para "Estoque" conseguia:
- Ver links do módulo "Financeiro" na sidebar
- Acessar URLs do financeiro diretamente (ex: /financeiro/dashboard/)
- Ver todos os módulos no dropdown da sidebar

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Context Processor Melhorado (`serrana/context_processors.py`)

**Antes:**
```python
def user_permissions(request):
    return {
        'is_admin': request.user.is_staff,
        'can_manage_users': request.user.is_staff,
        'user_groups': list(request.user.groups.all()),
    }
```

**Depois:**
```python
def user_permissions(request):
    # Consulta as permissões do usuário na tabela PermissaoMenu
    # Verifica permissões diretas e por grupo
    # Retorna flags booleanas por módulo:
    return {
        'has_financeiro': True/False,
        'has_estoque': True/False,
        'has_projetos': True/False,
        'has_vendas': True/False,
        'has_cadastros': True/False,
        # ... outras permissões
    }
```

### 2. Sidebar com Validação (`templates/partials/sidebar.html`)

**Antes:**
```html
<ul class="dropdown-menu">
    <li><a href="/financeiro/">Financeiro</a></li>
    <li><a href="/estoque/">Estoque</a></li>
    <li><a href="/projetos/">Obras</a></li>
</ul>
```

**Depois:**
```html
<ul class="dropdown-menu">
    {% if has_financeiro %}
    <li><a href="/financeiro/">Financeiro</a></li>
    {% endif %}
    {% if has_estoque %}
    <li><a href="/estoque/">Estoque</a></li>
    {% endif %}
    {% if has_projetos %}
    <li><a href="/projetos/">Obras</a></li>
    {% endif %}
</ul>
```

### 3. Decorators nas Views

#### Financeiro (`financeiro/views.py`)

**Antes:**
```python
@login_required
def dashboard(request):
    ...
```

**Depois:**
```python
@login_required
@require_empresa
@verificar_permissao_menu('/financeiro/')
def dashboard(request):
    ...
```

**Views Protegidas:**
- `dashboard()`
- `criar_titulo()`
- `detalhe_titulo()`
- `listar_parcelas()`
- E todas as outras views do módulo financeiro

#### Estoque (`estoque/views.py`)

**Antes:**
```python
@login_required
def dashboard(request):
    ...
```

**Depois:**
```python
@login_required
@require_empresa
@verificar_permissao_menu('/estoque/')
def dashboard(request):
    ...
```

**Views Protegidas:**
- `dashboard()`
- `listar_itens()`
- `criar_item()`
- `criar_movimentacao()`
- E todas as outras views do módulo estoque

#### Projetos/Obras (`projetos/views.py`)

**Antes:**
```python
@login_required
def dashboard(request):
    ...
```

**Depois:**
```python
@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def dashboard(request):
    ...
```

## 🔐 COMO FUNCIONA AGORA

### 1. **Verificação no Context Processor**
   - Executa em TODAS as requisições
   - Consulta tabela `PermissaoMenu` e `Menu`
   - Verifica permissões diretas do usuário
   - Verifica permissões por grupo
   - Retorna flags booleanas (has_financeiro, has_estoque, etc.)

### 2. **Sidebar Inteligente**
   - Mostra APENAS módulos com permissão
   - Esconde completamente links sem acesso
   - Usuário nem vê a opção se não tiver permissão

### 3. **Proteção nas Views**
   - Decorator `@verificar_permissao_menu()` valida acesso
   - Mesmo acessando URL direta, usuário é bloqueado
   - Redireciona para home com mensagem de erro
   - Superusers sempre têm acesso total

## 📋 DECORATORS DISPONÍVEIS

### `@require_empresa`
- Garante que usuário tem empresa ativa na sessão
- Redireciona para seleção de empresa se necessário

### `@verificar_permissao_menu(url_menu)`
- Verifica se usuário pode visualizar o menu
- Exemplo: `@verificar_permissao_menu('/financeiro/')`
- Valida contra tabela `PermissaoMenu`

### `@verificar_permissao_acao(url_menu, acao)`
- Verifica permissões específicas: 'criar', 'editar', 'excluir'
- Exemplo: `@verificar_permissao_acao('/financeiro/', 'criar')`

## 🎯 RESULTADO FINAL

### ✅ Usuário com permissão APENAS para Estoque:

**Sidebar mostra:**
- ✅ Dashboard
- ✅ Estoque (com todos os submenus)
- ❌ Financeiro (não aparece)
- ❌ Projetos (não aparece)

**Tentativa de acesso direto:**
```
GET /financeiro/dashboard/
→ Bloqueado!
→ Mensagem: "Você não tem permissão para acessar este recurso."
→ Redirect: /usuarios/ (home)
```

### ✅ Superuser/Admin:
- ✅ Acessa TUDO sem restrições
- ✅ Vê todos os módulos na sidebar
- ✅ Pode acessar qualquer URL

## 📝 CHECKLIST DE SEGURANÇA

- [x] Context processor implementado
- [x] Sidebar validando permissões
- [x] Views do Financeiro protegidas
- [x] Views do Estoque protegidas
- [x] Views de Projetos protegidas
- [x] Decorators aplicados nas views principais
- [x] Superuser tem acesso total
- [x] Mensagens de erro apropriadas
- [x] Redirecionamentos funcionando

## ⚙️ COMO CONFIGURAR PERMISSÕES

### Via Django Admin

1. Acesse: http://localhost:8000/admin/
2. Navegue para: **Usuários** → **Permissões de Menu**
3. Crie nova permissão:
   - **Usuário:** selecione o usuário
   - **Menu:** selecione o menu (ex: /financeiro/)
   - **Pode visualizar:** ✓
   - **Pode criar:** ✓ (opcional)
   - **Pode editar:** ✓ (opcional)
   - **Pode excluir:** ✓ (opcional)

### Via Interface de Gerenciamento

1. Acesse: http://localhost:8000/usuarios/usuarios/
2. Clique em **Editar** no usuário desejado
3. Clique em **Gerenciar Permissões**
4. Marque os checkboxes dos módulos permitidos
5. Salve

## 🧪 TESTES RECOMENDADOS

1. **Criar usuário teste:**
   ```python
   # Via Django shell
   from django.contrib.auth.models import User
   user = User.objects.create_user('teste', password='123')
   ```

2. **Dar permissão apenas para Estoque:**
   ```python
   from usuarios.models import Menu, PermissaoMenu
   menu_estoque = Menu.objects.get(url='/estoque/')
   PermissaoMenu.objects.create(
       usuario=user,
       menu=menu_estoque,
       pode_visualizar=True
   )
   ```

3. **Fazer login como usuário teste**
4. **Verificar:**
   - Sidebar mostra apenas Estoque? ✓
   - Acesso a /financeiro/ é bloqueado? ✓
   - Acesso a /estoque/ funciona? ✓

## 🚨 IMPORTANTE

**TODAS as views de módulos protegidos devem usar os decorators:**

```python
@login_required
@require_empresa
@verificar_permissao_menu('/nome_do_modulo/')
def minha_view(request):
    ...
```

**Ordem dos decorators importa!**
1. `@login_required` - primeiro
2. `@require_empresa` - segundo  
3. `@verificar_permissao_menu()` - terceiro

## 📚 ARQUIVOS MODIFICADOS

1. `serrana/context_processors.py` - Lógica de permissões
2. `templates/partials/sidebar.html` - Validação visual
3. `financeiro/views.py` - Proteção das views
4. `estoque/views.py` - Proteção das views
5. `projetos/views.py` - Proteção das views

---

**Data da Correção:** 04/01/2026  
**Prioridade:** CRÍTICA (Segurança)  
**Status:** ✅ IMPLEMENTADO
