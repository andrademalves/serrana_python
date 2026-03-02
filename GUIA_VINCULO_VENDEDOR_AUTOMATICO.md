# 🎯 GUIA: VÍNCULO AUTOMÁTICO DE VENDEDORES

## ✨ Funcionalidade Implementada

Agora quando você criar ou editar um usuário no Admin e marcar como **"É Vendedor"**, o sistema automaticamente:

1. ✓ Cria um registro de **Pessoa** vinculado ao usuário
2. ✓ Marca a pessoa como vendedor (`vendedor=True`)
3. ✓ Vincula o usuário à pessoa via campo `usuario`
4. ✓ Permite usar esse vendedor no CRM e em orçamentos

---

## 📋 Como Usar

### 1️⃣ **Criar Novo Vendedor**

1. Acesse **Admin Django** → **Usuários** → **Adicionar Usuário**
2. Preencha:
   - Username: `joao.silva`
   - Password: (defina a senha)
3. Clique em **Salvar e continuar editando**
4. Na seção **PERFIL**:
   - ✅ Marque: **"É Vendedor"**
   - Preencha: Nome completo, email, telefone, etc.
5. Clique em **Salvar**

**Pronto!** O sistema automaticamente:
- Criou o registro de `Pessoa` vinculado
- Marcou como vendedor
- Agora ele aparece na lista de vendedores do CRM

---

### 2️⃣ **Tornar Usuário Existente em Vendedor**

1. Acesse **Admin Django** → **Usuários**
2. Clique no usuário desejado
3. Na seção **PERFIL**:
   - ✅ Marque: **"É Vendedor"**
4. Clique em **Salvar**

**Pronto!** O vínculo foi criado automaticamente.

---

### 3️⃣ **Desmarcar Vendedor**

1. Acesse o usuário no Admin
2. Na seção **PERFIL**:
   - ❌ Desmarque: **"É Vendedor"**
3. Clique em **Salvar**

O sistema irá:
- Remover a flag `vendedor` do registro de Pessoa
- O usuário NÃO aparecerá mais nas listas de vendedores

⚠️ **Importante:** O registro de Pessoa **não** é excluído, apenas a flag é desmarcada.

---

## 🔍 Verificar Vínculo

Para verificar se o vínculo foi criado corretamente:

### Via Admin:
1. **Cadastros** → **Pessoas**
2. Busque pelo nome do vendedor
3. Verifique:
   - ✅ "É Vendedor" marcado
   - ✅ Campo "Usuário" preenchido

### Via Python Shell:
```python
python manage.py shell

from django.contrib.auth.models import User
from cadastros.models import Pessoa

# Buscar usuário
user = User.objects.get(username='joao.silva')

# Verificar perfil
print(f"É vendedor no perfil: {user.perfil.vendedor}")

# Verificar pessoa vinculada
try:
    pessoa = Pessoa.objects.get(usuario=user)
    print(f"Pessoa: {pessoa.nome}")
    print(f"É vendedor: {pessoa.vendedor}")
except Pessoa.DoesNotExist:
    print("Sem pessoa vinculada")
```

---

## 📌 Campos Criados Automaticamente

Quando marca "É Vendedor", o sistema cria a Pessoa com:

| Campo | Valor Automático |
|-------|------------------|
| **Nome** | Nome completo do usuário (first_name + last_name) |
| **Email** | Email do usuário |
| **Tipo** | Pessoa Física (F) |
| **Vendedor** | ✅ True |
| **Usuário** | Vinculado ao User |
| **Empresa** | Empresa ativa do usuário ou primeira empresa ativa |

⚠️ **Campos que precisam ser preenchidos manualmente depois:**
- CPF/CNPJ
- Telefone/Celular (se não preenchido no perfil do usuário)
- Endereço completo
- Outros dados cadastrais

---

## 🎯 Benefícios

✅ **Agilidade:** Não precisa mais criar Pessoa manualmente e vincular ao usuário
✅ **Consistência:** Sistema garante que vendedor sempre tem usuário vinculado
✅ **Praticidade:** Um único checkbox cria todo o vínculo necessário
✅ **CRM Funcional:** Vendedores automaticamente disponíveis para atribuição de leads

---

## 🔧 Implementação Técnica

### Arquivos Modificados:

1. **`usuarios/models.py`**
   - Adicionado campo `vendedor` ao `PerfilUsuario`

2. **`usuarios/signals.py`** (NOVO)
   - Signal `sync_vendedor_pessoa`: Sincroniza PerfilUsuario.vendedor → Pessoa
   - Signal `create_user_profile`: Cria PerfilUsuario automaticamente

3. **`usuarios/apps.py`**
   - Método `ready()` carrega os signals

4. **`usuarios/admin.py`**
   - Campo `vendedor` adicionado ao inline do PerfilUsuario

5. **Migration:**
   - `usuarios/migrations/0006_perfilusuario_vendedor.py`

---

## ✅ Testado e Funcionando

O teste automatizado confirmou:
- ✓ Criação automática de PerfilUsuario
- ✓ Criação automática de Pessoa ao marcar vendedor
- ✓ Remoção da flag ao desmarcar vendedor
- ✓ Sincronização de nome e email

---

**Data de Implementação:** 02/03/2026  
**Desenvolvedor:** GitHub Copilot  
**Status:** ✅ FUNCIONANDO
