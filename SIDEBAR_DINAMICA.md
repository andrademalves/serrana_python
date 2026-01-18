# 📋 Documentação da Sidebar Dinâmica

## ✅ Implementação Completa

### **Arquivos Criados/Modificados:**

1. **serrana/context_processors.py** (NOVO)
   - Context processor `current_module()` - detecta módulo atual
   - Context processor `user_permissions()` - expõe permissões do usuário

2. **templates/partials/sidebar.html** (NOVO)
   - Sidebar única e reutilizável
   - Menus dinâmicos por módulo
   - Estilização completa integrada

3. **templates/base_with_sidebar.html** (MODIFICADO)
   - Simplificado para incluir a sidebar via `{% include %}`
   - Remove sidebar duplicada

4. **serrana/settings.py** (MODIFICADO)
   - Adicionados context processors customizados

5. **serrana/urls.py** (MODIFICADO)
   - Adicionados namespaces para estoque, projetos e financeiro

---

## 🎯 Como Funciona

### **Detecção Automática do Módulo**

O context processor detecta o módulo atual baseado em:

1. **Namespace da URL** (preferencial)
   ```python
   # Se a URL tiver namespace definido (ex: 'financeiro')
   namespace = request.resolver_match.namespace
   ```

2. **Prefixo do Path** (fallback)
   ```python
   # Se não tiver namespace, analisa o path:
   /financeiro/... → current_module = 'financeiro'
   /estoque/... → current_module = 'estoque'
   /projetos/... → current_module = 'obras'
   /cadastros/... → current_module = 'cadastros'
   ```

### **Variáveis Disponíveis em Todos os Templates**

```django
{{ current_module }}      → 'financeiro' | 'estoque' | 'obras' | 'vendas' | 'cadastros' | 'dashboard'
{{ current_path }}        → '/financeiro/dashboard/'
{{ is_admin }}            → True/False (staff ou superuser)
{{ can_manage_users }}    → True/False (apenas staff)
{{ user_groups }}         → ['Gerente', 'Vendedor', ...]
```

---

## 📁 Estrutura de Menus por Módulo

### **1. DASHBOARD** (`current_module='dashboard'`)
- Dashboard Geral
- Dashboard Financeiro
- Dashboard Estoque
- Dashboard Obras
- Relatórios Gerenciais (admin)

### **2. FINANCEIRO** (`current_module='financeiro'`)

**CONTAS:**
- ✅ Contas a Pagar
- ✅ Contas a Receber
- ✅ Títulos
- ✅ Parcelas

**BANCOS & CAIXA:**
- ✅ Contas Financeiras
- ⏳ Transferências (TODO)

**RELATÓRIOS:**
- ✅ Calendário Financeiro
- ✅ Fluxo de Caixa
- ✅ DRE
- ✅ Ponto de Equilíbrio
- ✅ Resultado por Centro de Custo

### **3. ESTOQUE** (`current_module='estoque'`)

**MOVIMENTAÇÕES:**
- ✅ Movimentações
- ✅ Nova Movimentação

**CADASTROS:**
- ✅ Itens
- ✅ Locais de Estoque
- ✅ Destinos

**RELATÓRIOS:**
- ✅ Estoque Atual
- ✅ Relatório de Movimentações
- ⏳ Estoque Crítico (TODO)

### **4. OBRAS/PROJETOS** (`current_module='obras'` ou `'projetos'`)

**OBRAS:**
- ✅ Obras
- ✅ Nova Obra

**GESTÃO:**
- ⏳ Visitas Técnicas (TODO)
- ⏳ Diário de Obra (TODO)
- ⏳ Custos da Obra (TODO)

**RELATÓRIOS:**
- ⏳ Resultado por Obra (TODO)

### **5. VENDAS/ORÇAMENTOS** (`current_module='vendas'`)
- ⏳ Módulo completo a implementar

### **6. CADASTROS** (`current_module='cadastros'`)
- ✅ Pessoas
- ✅ Nova Pessoa
- ✅ Produtos
- ✅ Novo Produto
- ⏳ Plano de Contas (admin, TODO)
- ⏳ Categorias (admin, TODO)

### **7. USUÁRIOS** (`current_module='usuarios'`)
- ✅ Usuários
- ✅ Novo Usuário (admin)
- ⏳ Grupos e Permissões (admin, TODO)

---

## 🔐 Controle de Permissões

### **No Template:**

```django
{% if is_admin %}
    <!-- Apenas para staff/superuser -->
    <a href="...">Configurações Avançadas</a>
{% endif %}

{% if 'Gerente' in user_groups %}
    <!-- Apenas para grupo específico -->
    <a href="...">Relatórios Gerenciais</a>
{% endif %}
```

### **Marcando Item Ativo:**

```django
<a href="{% url 'financeiro:dashboard' %}" 
   class="... {% if 'dashboard' in request.path %}active{% endif %}">
    Dashboard
</a>
```

---

## 🚀 Como Adicionar Novas Rotas

### **1. Criar a rota em urls.py do módulo:**

```python
# financeiro/urls.py
app_name = 'financeiro'

urlpatterns = [
    path('transferencias/', views.listar_transferencias, name='listar_transferencias'),
]
```

### **2. Adicionar link na sidebar:**

Edite `templates/partials/sidebar.html`:

```django
{% if current_module == 'financeiro' %}
    ...
    <a href="{% url 'financeiro:listar_transferencias' %}" 
       class="list-group-item list-group-item-action bg-dark text-white 
              {% if 'transferencias' in request.path %}active{% endif %}">
        <i class="bi bi-arrow-left-right"></i> Transferências
    </a>
    ...
{% endif %}
```

### **3. Remover classe "disabled":**

Se o link estava com `disabled`, remover:

```django
<!-- ANTES -->
<a href="#" class="... disabled">

<!-- DEPOIS -->
<a href="{% url 'financeiro:transferencias' %}" class="...">
```

---

## 🎨 Navegação Entre Módulos

No topo da sidebar há um **dropdown "Módulos"** que permite trocar entre:
- Dashboard Geral
- Financeiro
- Estoque
- Obras
- Cadastros
- Usuários (se admin)

Ao clicar, leva para a página inicial do módulo e a sidebar muda automaticamente.

---

## 📱 Responsividade

A sidebar é responsiva:

- **Desktop (>768px)**: Sidebar fixa à esquerda, conteúdo com margin-left
- **Mobile (<768px)**: Sidebar escondida, pode ser mostrada com toggle

---

## 🔧 Troubleshooting

### **Sidebar não muda de módulo:**
1. Verificar se o namespace está correto em `serrana/urls.py`
2. Verificar se `app_name` está definido em `urls.py` do módulo
3. Limpar cache do navegador

### **Link aparece como "disabled":**
1. Criar a rota em `urls.py` do módulo
2. Atualizar link na sidebar removendo `disabled` e adicionando `{% url %}`

### **Erro "Reverse not found":**
1. Verificar se a rota existe em `urls.py`
2. Verificar se o namespace está correto
3. Usar `python manage.py show_urls` para listar todas as rotas

### **Permissões não funcionam:**
1. Verificar se context processors estão em `settings.py`
2. Verificar se usuário tem flag `is_staff` ou `is_superuser`

---

## ✅ Checklist de Implementação

- [x] Context processor criado e configurado
- [x] Sidebar dinâmica criada em partials/
- [x] base_with_sidebar.html atualizado
- [x] Namespaces configurados nas URLs
- [x] Menus do Financeiro 100% funcionais
- [x] Menus do Estoque 100% funcionais
- [x] Menus de Obras parcialmente funcionais
- [x] Menus de Cadastros funcionais
- [ ] Módulo de Vendas/Orçamentos (a implementar)
- [ ] Links TODO precisam de rotas criadas

---

## 🎯 Próximos Passos

1. **Implementar rotas TODO:**
   - Transferências entre contas (Financeiro)
   - Estoque Crítico (Estoque)
   - Visitas Técnicas, Diário de Obra (Projetos)
   - Plano de Contas (Cadastros)

2. **Criar módulo de Vendas/Orçamentos**

3. **Adicionar mais relatórios conforme necessário**

4. **Implementar permissões granulares por grupo**

---

**Desenvolvido para Sistema Serrana - Dezembro 2025**
