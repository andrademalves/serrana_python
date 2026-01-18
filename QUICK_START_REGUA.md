# 🚀 QUICK START - RÉGUA DE COBRANÇA

## 📦 Instalação Rápida

### 1. Instalar dependências
```powershell
pip install -r requirements.txt
```

### 2. Aplicar migrations (se ainda não aplicou)
```powershell
python manage.py migrate
```

### 3. Instalar e iniciar Redis

**Opção 1: Docker (recomendado)**
```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

**Opção 2: Windows**
- Download: https://github.com/microsoftarchive/redis/releases
- Executar: `redis-server.exe`

### 4. Testar Redis
```powershell
redis-cli ping
# Retorno esperado: PONG
```

---

## 🎬 Iniciar Sistema

### Terminal 1: Django
```powershell
python manage.py runserver
```

### Terminal 2: Celery Worker
```powershell
celery -A serrana worker -l info --pool=solo
```

### Terminal 3: Celery Beat (Agendador)
```powershell
celery -A serrana beat -l info
```

---

## ⚙️ Configuração Inicial

### 1. Acessar Admin
```
http://localhost:8000/admin/
```

### 2. Criar Régua de Cobrança

**Admin → Financeiro → Régua cobrança → Adicionar**

**Dados:**
- Nome: Régua Padrão
- Descrição: Cobrança automática em 5 etapas
- Empresa: [Selecionar sua empresa]
- Ativa: ✓

**Adicionar Etapas (Inline):**

| Ordem | Nome | Offset | E-mail | Assunto | Mensagem |
|-------|------|--------|--------|---------|----------|
| 1 | Lembrete | -3 | ✓ | Lembrete - Parcela vence em 3 dias | Olá {cliente_nome}, sua parcela vence em 3 dias... |
| 2 | Vencimento | 0 | ✓ | Vencimento HOJE | Sua parcela vence hoje... |
| 3 | Atraso | +2 | ✓ | Pagamento em atraso | Parcela vencida há {dias_atraso} dias... |
| 4 | Cobrança | +7 | ✓ | URGENTE - Cobrança | Favor regularizar pagamento... |
| 5 | Final | +15 | ✓ | ÚLTIMO AVISO | Medidas cabíveis serão tomadas... |

### 3. Vincular Parcelas

**Admin → Financeiro → Parcela financeira → [Editar parcela]**

- Regua: [Selecionar "Régua Padrão"]
- Regua ativa: ✓
- Status cobranca: NORMAL

---

## 📧 Configurar E-mail

### Desenvolvimento (Console - Já configurado)
Mostra e-mails no terminal do runserver.

### Produção (Gmail)

**Editar:** `serrana/settings.py`

```python
# Comentar:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Descomentar e configurar:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # Senha de app
DEFAULT_FROM_EMAIL = 'Sistema Serrana <seu-email@gmail.com>'
```

**Gerar senha de app Gmail:**
1. https://myaccount.google.com/apppasswords
2. Criar "Sistema Serrana"
3. Copiar senha gerada (16 caracteres)

---

## 🎯 Usar Sistema

### Acessar Painel
```
http://localhost:8000/financeiro/cobranca/
```

### Ações Disponíveis

**🚀 Disparar Agora**
- Envia cobrança imediata (síncrona)

**⏸️ Pausar Régua**
- Pausa automação por X dias

**▶️ Retomar Régua**
- Retoma automação

**📅 Promessa**
- Registra promessa de pagamento

**🕒 Histórico**
- Ver timeline de envios

---

## 🧪 Testar

### Teste 1: SMTP
```python
python manage.py shell

from financeiro.services.email_service import EmailService
EmailService.testar_configuracao()
# Retorno esperado: True
```

### Teste 2: Calcular Etapas
```python
from financeiro.models import ParcelaFinanceira
from financeiro.services.regua_service import ReguaService

parcela = ParcelaFinanceira.objects.first()
etapas = ReguaService.calcular_etapas_disponiveis(parcela)
print(etapas)
```

### Teste 3: Processar Manual
```python
from financeiro.tasks import processar_reguas_diarias
resultado = processar_reguas_diarias()
print(resultado)
```

---

## 📊 Agendamento Automático

**Já configurado em settings.py:**

| Tarefa | Horário | Função |
|--------|---------|--------|
| processar_reguas_diarias | 08:00 | Enfileira envios do dia |
| reprocessar_falhas | A cada 2h | Retenta envios com falha |
| limpar_logs_antigos | Segunda 03:00 | Remove logs >90 dias |

---

## 🔧 Comandos Úteis

### Ver tasks Celery
```powershell
celery -A serrana inspect active
```

### Ver fila Redis
```powershell
redis-cli
KEYS *
```

### Limpar fila
```powershell
redis-cli FLUSHALL
```

### Logs Celery (verbose)
```powershell
celery -A serrana worker -l debug --pool=solo
```

---

## 📱 URLs Principais

| URL | Descrição |
|-----|-----------|
| `/admin/` | Admin Django |
| `/financeiro/` | Dashboard Financeiro |
| `/financeiro/cobranca/` | Painel de Cobrança |
| `/financeiro/cobranca/historico/<id>/` | Histórico de envios |
| `/admin/financeiro/reguacobranca/` | Gerenciar réguas |
| `/admin/financeiro/logcobranca/` | Logs de envio |

---

## ✅ Checklist de Validação

- [ ] Redis rodando (`redis-cli ping`)
- [ ] Celery worker rodando
- [ ] Celery beat rodando
- [ ] Régua criada no admin
- [ ] Etapas configuradas
- [ ] Parcela vinculada à régua
- [ ] `regua_ativa = True` na parcela
- [ ] SMTP testado (EmailService.testar_configuracao())
- [ ] Painel acessível
- [ ] Disparo manual funcionando

---

## 🚨 Troubleshooting

### Redis não conecta
```powershell
# Windows: Reiniciar Redis
taskkill /IM redis-server.exe /F
redis-server.exe

# Docker: Reiniciar container
docker restart redis
```

### Celery não processa
```powershell
# Parar worker (Ctrl+C) e reiniciar
celery -A serrana worker -l info --pool=solo
```

### E-mail não envia
1. Verificar SMTP settings
2. Testar: `EmailService.testar_configuracao()`
3. Gmail: Ativar senha de app
4. Ver logs Celery Worker

### Etapas não disparam
1. Verificar `offset_dias` (ex: -3, 0, +2, +7, +15)
2. Verificar se parcela.vencimento está correto
3. Ver LogCobranca no admin (duplicação?)
4. Processar manual: `processar_reguas_diarias()`

---

## 📚 Documentação Completa

Ver: `GUIA_REGUA_COBRANCA.md`

---

## 🎉 Pronto!

Sistema funcionando em 3 terminais:
1. Django (`runserver`)
2. Celery Worker (processa tasks)
3. Celery Beat (agenda tasks)

**Próximo passo:** Criar régua, vincular parcelas e monitorar painel! 🚀
