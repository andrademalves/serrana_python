# 🎯 Guia Rápido: Como Identificar a Empresa Ativa

## 📍 Localização Visual

### No Navbar (Topo da Página)

Você sempre verá a empresa ativa no **canto superior direito**:

```
┌────────────────────────────────────────────────────────┐
│  Sistema Serrana     [🏢 Serrana ▼]  [👤 usuario ▼]   │
└────────────────────────────────────────────────────────┘
                           ↑
                    EMPRESA ATIVA
```

---

## 🔍 Como Usar

### **1. Ver Detalhes da Empresa**

Clique no nome da empresa no navbar:

```
┌─────────────────────────────┐
│ Empresa Ativa               │
├─────────────────────────────┤
│ 🏢 Serrana                  │
│ serrana (slug)              │
├─────────────────────────────┤
│ 🔄 Trocar de Empresa        │
└─────────────────────────────┘
```

### **2. Trocar de Empresa**

1. Clique em **"Trocar de Empresa"**
2. Selecione a empresa desejada
3. Continue trabalhando

---

## 💻 Para Desenvolvedores

### Acessar no Código

```python
# Em qualquer view
empresa_atual = request.empresa
print(f"Empresa: {empresa_atual.nome_fantasia}")
```

### Acessar no Template

```html
<p>Você está em: {{ empresa_nome }}</p>
<p>CNPJ: {{ empresa_ativa.cnpj }}</p>
```

---

## 🔐 Acesso

- **Superusuários:** Acesso a todas as empresas
- **Usuários normais:** Apenas empresas vinculadas

---

## ⚡ Atalhos

| Ação | URL |
|------|-----|
| Selecionar Empresa | `/empresas/selecionar/` |
| Trocar Empresa | Navbar → Empresa → Trocar |

---

**✅ Pronto! Agora você sabe como identificar e trocar de empresa no sistema.**

📚 Para mais detalhes, veja: [COMO_SABER_EMPRESA_ATIVA.md](COMO_SABER_EMPRESA_ATIVA.md)
