# 📧 Configuração SMTP por Empresa - Guia Rápido

## ✅ Implementado

Agora cada empresa pode ter suas próprias configurações SMTP para envio de e-mails de cobrança!

### 🎯 Onde Configurar

**Admin → Empresas → [Editar Empresa]**
```
/usuarios/empresas/<id>/editar/
```

### 📋 Campos Adicionados ao Modelo Empresa

```python
# Configurações SMTP
smtp_ativo           # Ativar SMTP próprio (checkbox)
smtp_host            # Ex: smtp.gmail.com
smtp_port            # Ex: 587 (TLS) ou 465 (SSL)
smtp_use_tls         # Usar TLS (recomendado)
smtp_use_ssl         # Usar SSL
smtp_username        # Usuário (geralmente o e-mail)
smtp_password        # Senha ou senha de app
smtp_from_email      # E-mail remetente
smtp_from_name       # Nome remetente
```

### 🔧 Como Funciona

1. **SMTP Próprio Ativo**: Usa as configurações da empresa
2. **SMTP Desativado**: Usa configurações padrão do `settings.py`

### 📝 Exemplo de Configuração (Gmail)

```
Servidor SMTP:    smtp.gmail.com
Porta:           587
TLS:             ✓ Ativado
SSL:             ☐ Desativado
Usuário:         empresa@gmail.com
Senha:           xxxx xxxx xxxx xxxx  (senha de app)
Email Remetente: empresa@gmail.com
Nome Remetente:  Empresa XYZ
```

### 🔐 Gmail - Gerar Senha de Aplicativo

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione: "Outras (nome personalizado)"
3. Digite: "Sistema Serrana - [Nome Empresa]"
4. Clique em "Gerar"
5. Copie a senha de 16 caracteres
6. Cole no campo "Senha SMTP"

### ✅ Testar Configuração

Após salvar as configurações:

1. Botão **"Testar Envio"** aparece automaticamente
2. Clique para enviar e-mail de teste
3. Verifique a caixa de entrada do e-mail configurado

### 🔄 Integração com Régua de Cobrança

O `EmailService` foi atualizado para:

```python
# Detecta automaticamente qual SMTP usar
if empresa.tem_smtp_configurado():
    # Usa SMTP da empresa
    connection = get_connection(
        host=empresa.smtp_host,
        port=empresa.smtp_port,
        username=empresa.smtp_username,
        password=empresa.smtp_password,
        use_tls=empresa.smtp_use_tls,
    )
else:
    # Usa SMTP padrão do sistema
    connection = None  # Django usa settings.py
```

### 📊 Métodos Adicionados ao Modelo Empresa

```python
# Verifica se SMTP está configurado
empresa.tem_smtp_configurado()  # → True/False

# Retorna dict com configurações
empresa.get_smtp_config()
# → {
#     'host': 'smtp.gmail.com',
#     'port': 587,
#     'username': 'email@gmail.com',
#     'password': 'senha',
#     'use_tls': True,
#     'use_ssl': False,
#     'from_email': 'email@gmail.com',
#     'from_name': 'Empresa XYZ'
# }
```

### 🎨 Interface

Nova seção no formulário de edição da empresa:

- **Header**: "Configurações de E-mail (SMTP)" com toggle principal
- **Campos desabilitados**: Quando SMTP próprio está OFF
- **Alert informativo**: Instruções e links úteis
- **Badge de status**: Mostra se está configurado
- **Botão de teste**: Envia e-mail de teste

### 📦 Arquivos Modificados

```
✅ usuarios/models.py          - 9 novos campos SMTP
✅ usuarios/views.py            - testar_smtp() view
✅ usuarios/urls.py             - rota testar-smtp
✅ usuarios/templates/...       - Seção SMTP no form
✅ financeiro/services/email_service.py - Suporte multi-SMTP
✅ Migration: 0003_empresa_smtp_*
```

### 🚀 Usar na Prática

#### Cenário 1: Empresa com SMTP Próprio

```python
from financeiro.services.email_service import EmailService
from usuarios.models import Empresa

empresa = Empresa.objects.get(id=1)
# smtp_ativo = True

# E-mails de cobrança usarão SMTP da empresa
EmailService.testar_configuracao(empresa)
```

#### Cenário 2: Usar SMTP Padrão

```python
# smtp_ativo = False
# Sistema usa settings.EMAIL_HOST, EMAIL_PORT, etc
```

### 📧 E-mails Enviados

**Com SMTP Próprio:**
```
From: Empresa XYZ <empresa@gmail.com>
Reply-To: empresa@gmail.com
```

**Com SMTP Padrão:**
```
From: Sistema Serrana <sistema@serrana.com.br>
Reply-To: sistema@serrana.com.br
```

### ⚠️ Dicas Importantes

1. **TLS vs SSL**: Use TLS (porta 587) para Gmail
2. **Senha de App**: Obrigatório para Gmail com 2FA
3. **Teste sempre**: Clique em "Testar Envio" após configurar
4. **Segurança**: Senhas são armazenadas em texto plano no banco
   - Em produção: Considere criptografia (django-fernet-fields)

### 🔍 Troubleshooting

**Erro: "Authentication failed"**
- Verifique usuário e senha
- Gmail: Use senha de app, não senha normal

**Erro: "Connection refused"**
- Verifique host e porta
- Gmail: smtp.gmail.com:587

**E-mail não chega**
- Verifique spam/lixeira
- Teste com outro e-mail
- Verifique logs do Celery Worker

### ✨ Benefícios

- ✅ **Multi-empresa**: Cada empresa usa seu próprio e-mail
- ✅ **Personalização**: Nome e e-mail customizados
- ✅ **Confiabilidade**: Evita bloqueios por volume
- ✅ **Rastreamento**: E-mails vêm do domínio da empresa
- ✅ **Fallback**: Se SMTP próprio falhar, usa padrão

---

## 🎉 Pronto para Uso!

Configure o SMTP de cada empresa e os e-mails de cobrança serão enviados com a identidade visual correta!
