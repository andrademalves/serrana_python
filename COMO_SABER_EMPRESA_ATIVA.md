# 📋 Como Saber Qual Empresa Está Sendo Administrada

## 🎯 Visão Geral

O sistema Serrana foi configurado com **suporte multiempresa**, permitindo que você gerencie múltiplas empresas em uma única instalação. Aqui está tudo que você precisa saber:

---

## 🏢 Indicadores da Empresa Ativa

### 1. **Navbar Superior** (Principal)

No canto superior direito da tela, você verá um **dropdown com o nome da empresa ativa**:

```
┌─────────────────────────────────────────────────┐
│ 🏢 Serrana [Ativa ▼]  👤 usuario ▼             │
└─────────────────────────────────────────────────┘
```

**Detalhes exibidos ao clicar:**
- Logo da empresa (se cadastrado)
- Nome Fantasia
- Slug da empresa
- Botão para trocar de empresa

### 2. **Variável de Template**

Em qualquer template do sistema, você tem acesso a:

```django
{{ empresa_ativa }}       → Objeto completo da empresa
{{ empresa_nome }}        → Nome fantasia da empresa
{{ empresa_logo }}        → URL da logo (se houver)
{{ empresa_slug }}        → Identificador único
```

**Exemplo de uso:**
```html
<h1>Bem-vindo à {{ empresa_nome }}</h1>
<p>CNPJ: {{ empresa_ativa.cnpj }}</p>
```

---

## 🔄 Como Trocar de Empresa

### Método 1: Via Navbar
1. Clique no nome da empresa no canto superior direito
2. Selecione **"Trocar de Empresa"**
3. Escolha a empresa desejada na lista

### Método 2: Via URL
Acesse diretamente: `http://127.0.0.1:8000/empresas/selecionar/`

### Método 3: Programaticamente
```python
# Em uma view
request.session['empresa_ativa_id'] = empresa.id
```

---

## 🔐 Controle de Acesso

### Como o Sistema Decide Quais Empresas Você Pode Acessar

**Superusuários:**
- Têm acesso a **todas as empresas ativas**
- Sem restrições

**Usuários Normais:**
- Apenas empresas vinculadas através do modelo `UsuarioEmpresa`
- Vínculo deve estar **ativo**
- Empresa deve estar **ativa**

### Verificar Acesso no Código

```python
# views.py
from usuarios.decorators import empresa_ativa_required

@login_required
@empresa_ativa_required
def minha_view(request):
    # request.empresa estará disponível aqui
    empresa = request.empresa
    return render(request, 'template.html')
```

---

## 📊 Isolamento de Dados

### Como Funciona

O middleware `EmpresaAtivaMiddleware` **injeta automaticamente** a empresa ativa em todas as requisições:

```python
# Middleware adiciona:
request.empresa = <Empresa Ativa>
```

### Filtrar Dados por Empresa

**Em Views:**
```python
# Listar apenas itens da empresa ativa
items = Item.objects.filter(empresa=request.empresa)

# Criar novo item vinculado à empresa
novo_item = Item.objects.create(
    nome='Produto X',
    empresa=request.empresa  # ← CRÍTICO!
)
```

**Em Forms:**
```python
class ItemForm(forms.ModelForm):
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.empresa = self.empresa  # ← Vincula à empresa
        if commit:
            instance.save()
        return instance

# Na view:
form = ItemForm(request.POST, empresa=request.empresa)
```

---

## ⚙️ Configuração Técnica

### Middleware Ativo

No `settings.py`:
```python
MIDDLEWARE = [
    # ... outros middlewares
    'usuarios.middleware_empresa.EmpresaAtivaMiddleware',
]
```

### Context Processor

```python
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ... outros processors
            'usuarios.middleware_empresa.empresa_context_processor',
        ],
    },
}]
```

### URLs Isentas

Estas URLs **não** requerem empresa selecionada:
- `/accounts/login/`
- `/accounts/logout/`
- `/admin/`
- `/empresas/selecionar/`
- `/empresas/trocar/`
- `/static/`
- `/media/`

---

## 🧪 Exemplos Práticos

### 1. Verificar Empresa Ativa em View

```python
from django.shortcuts import render

@login_required
def dashboard(request):
    # Empresa automaticamente disponível
    empresa = request.empresa
    
    # Filtrar dados
    clientes = Pessoa.objects.filter(
        empresa=empresa,
        cliente=True
    )
    
    context = {
        'total_clientes': clientes.count(),
        # empresa_ativa já está no context via processor
    }
    return render(request, 'dashboard.html', context)
```

### 2. Exibir no Template

```html
<!-- templates/dashboard.html -->
<div class="alert alert-info">
    Você está administrando: <strong>{{ empresa_nome }}</strong>
    <br>
    CNPJ: {{ empresa_ativa.cnpj }}
</div>

<h2>Clientes da {{ empresa_nome }}</h2>
```

### 3. Form com Empresa

```python
# views.py
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST, empresa=request.empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente criado!')
            return redirect('listar_clientes')
    else:
        form = ClienteForm(empresa=request.empresa)
    
    return render(request, 'criar_cliente.html', {'form': form})
```

---

## 🚨 Troubleshooting

### Erro: "Selecione uma empresa para continuar"

**Causa:** Nenhuma empresa foi selecionada ou a sessão expirou.

**Solução:**
1. Acesse `/empresas/selecionar/`
2. Escolha uma empresa
3. Continue navegando

### Erro: "Você não tem acesso a nenhuma empresa"

**Causa:** Usuário não está vinculado a nenhuma empresa.

**Solução:**
1. Acesse o Django Admin (se for superuser)
2. Vá em **Usuários x Empresas**
3. Vincule o usuário à empresa desejada

**Ou via Shell:**
```python
python manage.py shell

from django.contrib.auth.models import User
from usuarios.models import Empresa, UsuarioEmpresa

user = User.objects.get(username='fulano')
empresa = Empresa.objects.get(slug='serrana')

UsuarioEmpresa.objects.create(
    usuario=user,
    empresa=empresa,
    ativo=True
)
```

### Dados de Outras Empresas Aparecem

**Causa:** Filtro `empresa=request.empresa` não foi aplicado.

**Solução:**
```python
# ❌ ERRADO
items = Item.objects.all()

# ✅ CORRETO
items = Item.objects.filter(empresa=request.empresa)
```

---

## 📝 Checklist de Implementação

Ao criar novos módulos/apps, certifique-se de:

- [ ] Adicionar campo `empresa` como ForeignKey nos models
- [ ] Filtrar queries com `empresa=request.empresa`
- [ ] Vincular novos registros à empresa ativa
- [ ] Usar `unique_together` com empresa quando apropriado
- [ ] Adicionar índices com empresa para performance

**Exemplo de Model:**
```python
class MeuModel(models.Model):
    empresa = models.ForeignKey(
        'usuarios.Empresa',
        on_delete=models.PROTECT,
        related_name='meus_models',
        verbose_name='Empresa'
    )
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=50)
    
    class Meta:
        unique_together = [['empresa', 'codigo']]
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
        ]
```

---

## 📚 Arquivos Relacionados

| Arquivo | Função |
|---------|--------|
| `usuarios/middleware_empresa.py` | Middleware que injeta empresa |
| `usuarios/models.py` | Models Empresa e UsuarioEmpresa |
| `usuarios/views.py` | Views de seleção/troca |
| `usuarios/templates/usuarios/selecionar_empresa.html` | Interface de seleção |
| `templates/base.html` | Navbar com indicador |

---

## 🎓 Próximos Passos

1. **Cadastrar Empresas:**
   - Acesse: Sistema → Empresas → Criar Empresa

2. **Vincular Usuários:**
   - Edite a empresa e adicione usuários

3. **Testar Troca:**
   - Faça login e selecione diferentes empresas
   - Verifique que os dados mudam conforme a empresa ativa

4. **Implementar Filtros:**
   - Adicione `empresa=request.empresa` em todas as queries

---

## 💡 Dicas

- **Performance:** Use `select_related('empresa')` ao listar objetos
- **Segurança:** Sempre valide que usuário tem acesso à empresa
- **UX:** Mostre o nome da empresa em relatórios e documentos
- **Auditoria:** Registre qual empresa estava ativa nas ações

---

✅ **Sistema Multiempresa Configurado e Funcionando!**
