# 📧 GUIA DE IMPLEMENTAÇÃO - RÉGUA DE COBRANÇA AUTOMÁTICA

## ✅ O QUE FOI IMPLEMENTADO

### 1. **Modelos de Dados** (`financeiro/models.py`)

#### `ReguaCobranca` - Régua Mestre
- Gerencia regras de cobrança automatizada
- Campos: nome, descrição, ativa, empresa
- Métodos: get_etapas_ativas(), total_parcelas_ativas()

#### `ReguaEtapa` - Etapas da Régua
- Define cada etapa de cobrança
- **offset_dias**: dias relativos ao vencimento (-3 = 3 dias antes, +7 = 7 dias depois)
- Campos de e-mail: canal_email, assunto_email, mensagem_email
- Unique constraint: (regua, offset_dias)

#### `ParcelaFinanceira` - Extensões
**Novos campos:**
- `regua`: FK para ReguaCobranca
- `regua_ativa`: Boolean (ativa/pausada)
- `pausar_regua_ate`: Data até quando pausar
- `status_cobranca`: NORMAL, NEGOCIACAO, PROMESSA, INTENSA, BLOQUEADA
- `contato_email_override`: Email alternativo
- `data_promessa_pagamento`: Data da promessa
- `observacao_promessa`: Observações

**Novos métodos:**
- `pode_enviar_cobranca()`: Valida se pode enviar
- `dias_atraso()`: Calcula dias em atraso
- `esta_vencida()`: Verifica se vencida

#### `LogCobranca` - Auditoria Completa
- Rastreia todos os envios
- Status: ENFILEIRADO, PROCESSANDO, ENVIADO, FALHA, CANCELADO
- Retry: tentativas, max_tentativas (3)
- Armazena: assunto, mensagem, erro, message_id
- Método: pode_reprocessar()

---

### 2. **Camada de Serviços**

#### `ReguaService` (`financeiro/services/regua_service.py`)

**Principais métodos:**

```python
# Calcular etapas que devem disparar hoje
calcular_etapas_disponiveis(parcela)
# Retorna: QuerySet de ReguaEtapa com offset = dias_desde_vencimento

# Buscar parcelas para processar
buscar_parcelas_para_processar(empresa)
# Filtra: regua_ativa, não quitadas, não bloqueadas, não pausadas

# Validar se deve disparar etapa
deve_disparar_etapa(parcela, etapa)
# Verifica: duplicação, email disponível, status válido

# Criar log de cobrança
criar_log_cobranca(parcela, etapa, canal)
# Cria: LogCobranca com status ENFILEIRADO

# Atualizar status automaticamente
atualizar_status_cobranca(parcela)
# Lógica: 15+ dias atraso → INTENSA

# Pausar régua temporariamente
pausar_regua(parcela, ate_data, motivo)

# Retomar régua
retomar_regua(parcela)

# Marcar promessa de pagamento
marcar_promessa_pagamento(parcela, data_promessa, observacao)
```

#### `TemplateService` (`financeiro/services/template_service.py`)

**Variáveis suportadas:**
- `{cliente_nome}`, `{parcela_numero}`, `{parcela_valor}`
- `{parcela_vencimento}`, `{dias_atraso}`, `{empresa_nome}`
- `{titulo_numero}`, `{saldo_aberto}`

**Templates pré-definidos:**
1. **LEMBRETE** (-3 dias): Tom amigável
2. **VENCIMENTO** (0 dias): Urgente mas educado
3. **ATRASO_LEVE** (+2 dias): Lembrete gentil
4. **COBRANCA** (+7 dias): Firme e urgente
5. **FINAL** (+15+ dias): Último aviso com advertência legal

#### `EmailService` (`financeiro/services/email_service.py`)

**Funcionalidades:**
- `enviar_cobranca(log_id)`: Envia e-mail via SMTP
- Renderiza template com variáveis
- Atualiza status do log
- Tratamento de erros com logging
- `testar_configuracao()`: Testa SMTP

---

### 3. **Tarefas Celery** (`financeiro/tasks.py`)

#### Tarefas Implementadas:

```python
@shared_task
processar_reguas_diarias()
# Executar: Todo dia às 08:00
# Função: Busca parcelas, calcula etapas, enfileira envios

@shared_task
enviar_email_task(log_id)
# Retry: 3 tentativas com backoff exponencial
# Função: Envia e-mail de forma assíncrona

@shared_task
reprocessar_falhas_task()
# Executar: A cada 2 horas
# Função: Reenvia e-mails com falha

@shared_task
limpar_logs_antigos()
# Executar: Toda segunda às 03:00
# Função: Remove logs >90 dias
```

---

### 4. **Interface Web**

#### Painel de Cobrança (`/financeiro/cobranca/`)

**KPIs:**
- Disparos Hoje
- A Vencer (7 dias)
- Vencidas
- Falhas
- Em Negociação

**Filtros:**
- Período (7, 15, 30 dias, todos)
- Status Cobrança
- Régua

**Ações por Parcela:**
- 🚀 **Disparar Agora**: Envia cobrança manual
- ⏸️ **Pausar Régua**: Pausa por X dias com motivo
- ▶️ **Retomar Régua**: Resume automação
- 📅 **Promessa**: Registra promessa de pagamento
- 🕒 **Histórico**: Timeline de envios

#### Histórico de Cobrança (`/financeiro/cobranca/historico/<id>/`)

**Exibe:**
- Timeline completa de envios
- Status de cada log (badges coloridos)
- Assunto e mensagem enviada
- Tentativas e erros
- Datas de criação/envio

---

### 5. **Admin Django**

**ReguaCobranca Admin:**
- Inline: ReguaEtapa
- List display: nome, empresa, ativa, total etapas
- Fieldsets organizados

**ReguaEtapa Admin:**
- Ordenação: regua → ordem
- Campos separados: Básico, E-mail

**LogCobranca Admin:**
- Read-only: datas
- Fieldsets: Básico, Detalhes, Controle, Datas
- Filtros: status, canal, data_criacao

---

## 📋 PRÓXIMOS PASSOS PARA ATIVAR

### 1. **Instalar Dependências**

```powershell
pip install celery redis
```

### 2. **Configurar Redis**

**Opção A: Docker**
```powershell
docker run -d -p 6379:6379 redis:latest
```

**Opção B: Windows (instalar Redis)**
- Download: https://github.com/microsoftarchive/redis/releases
- Executar: `redis-server.exe`

### 3. **Configurar E-mail SMTP** (Production)

Editar `serrana/settings.py`:

```python
# Comentar console backend:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Descomentar e configurar:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha-de-app'  # Senha de app do Gmail
DEFAULT_FROM_EMAIL = 'Sistema Serrana <seu-email@gmail.com>'
```

**Gmail - Como gerar senha de app:**
1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione: "Outras (nome personalizado)"
3. Digite: "Sistema Serrana"
4. Clique em "Gerar"
5. Use a senha gerada (16 caracteres)

### 4. **Iniciar Celery Worker**

```powershell
celery -A serrana worker -l info --pool=solo
```

### 5. **Iniciar Celery Beat (Agendador)**

```powershell
celery -A serrana beat -l info
```

---

## 🎯 COMO USAR

### **1. Criar Régua de Cobrança** (Admin)

1. Acessar: `/admin/financeiro/reguacobranca/add/`
2. Preencher:
   - Nome: "Régua Padrão Recebimentos"
   - Descrição: "Cobrança automática 5 etapas"
   - Empresa: Selecionar sua empresa
   - Ativa: ☑️

3. **Adicionar Etapas** (Inline):

| Ordem | Nome | Offset | Canal E-mail | Assunto | Mensagem |
|-------|------|--------|--------------|---------|----------|
| 1 | Lembrete | -3 | ☑️ | Parcela vence em breve | Olá {cliente_nome}, sua parcela... |
| 2 | Vencimento | 0 | ☑️ | Vence HOJE | Sua parcela vence hoje... |
| 3 | Atraso Leve | +2 | ☑️ | Pagamento em atraso | Identificamos atraso de {dias_atraso} dias... |
| 4 | Cobrança | +7 | ☑️ | URGENTE - Pagamento vencido | Parcela vencida há {dias_atraso} dias... |
| 5 | Final | +15 | ☑️ | ÚLTIMO AVISO | Última tentativa antes de medidas cabíveis... |

4. **Salvar**

### **2. Vincular Parcelas à Régua**

**Opção A: Manualmente (Admin)**
1. Editar parcela: `/admin/financeiro/parcelafinanceira/<id>/change/`
2. Campos:
   - **Regua**: Selecionar "Régua Padrão Recebimentos"
   - **Regua ativa**: ☑️
   - **Status cobranca**: NORMAL

**Opção B: Via Form (quando implementar)**
- Adicionar campo `regua` no ParcelaForm
- Checkbox "Ativar cobrança automática"

### **3. Monitorar no Painel**

1. Acessar: `/financeiro/cobranca/`
2. Visualizar KPIs
3. Filtrar parcelas por status/régua/período
4. Ações:
   - Disparar manual
   - Pausar/Retomar
   - Marcar promessa
   - Ver histórico

---

## 🔍 TESTES

### **Testar Configuração SMTP**

```python
# Shell Django
python manage.py shell

from financeiro.services.email_service import EmailService
EmailService.testar_configuracao()
```

### **Testar Cálculo de Etapas**

```python
from financeiro.models import ParcelaFinanceira
from financeiro.services.regua_service import ReguaService

parcela = ParcelaFinanceira.objects.get(id=1)
etapas = ReguaService.calcular_etapas_disponiveis(parcela)
print(etapas)
```

### **Processar Manualmente**

```python
from financeiro.tasks import processar_reguas_diarias
resultado = processar_reguas_diarias.delay()
print(resultado.get())
```

---

## 📊 FLUXO COMPLETO

```
1. Celery Beat (08:00) → processar_reguas_diarias()
   ↓
2. ReguaService.buscar_parcelas_para_processar()
   ↓
3. Para cada parcela:
   - ReguaService.calcular_etapas_disponiveis()
   - ReguaService.deve_disparar_etapa()
   ↓
4. ReguaService.criar_log_cobranca() → Status: ENFILEIRADO
   ↓
5. enviar_email_task.delay(log_id) → Celery Worker
   ↓
6. EmailService.enviar_cobranca(log_id)
   - TemplateService.renderizar()
   - Django send_mail()
   - LogCobranca.status = ENVIADO
   ↓
7. Se falha: Retry (max 3x) com backoff exponencial
   ↓
8. A cada 2h: reprocessar_falhas_task()
```

---

## ⚙️ CONFIGURAÇÕES IMPORTANTES

### **Status da Cobrança (Auto-escalação)**

```python
# Lógica em ReguaService.atualizar_status_cobranca()

if dias_atraso >= 15:
    status = 'INTENSA'  # Cobrança intensiva
elif data_promessa and data_promessa >= hoje:
    status = 'PROMESSA'  # Cliente prometeu pagar
else:
    status = 'NORMAL'  # Cobrança normal
```

### **Bloqueios Automáticos**

Não envia se:
- `parcela.status` in ['QUITADO', 'CANCELADO']
- `parcela.status_cobranca` == 'BLOQUEADA'
- `parcela.pausar_regua_ate` > hoje
- `parcela.regua_ativa` == False
- Sem email configurado (pessoa.email ou contato_email_override)
- Já enviado hoje (LogCobranca com mesma etapa+parcela)

---

## 🚨 TROUBLESHOOTING

### **Celery não conecta no Redis**

```powershell
# Verificar se Redis está rodando
redis-cli ping
# Deve retornar: PONG
```

### **E-mails não enviando**

1. Verificar settings SMTP
2. Testar: `EmailService.testar_configuracao()`
3. Verificar logs Celery Worker
4. Gmail: Ativar "Acesso a apps menos seguros" ou usar senha de app

### **Etapas não disparando**

1. Verificar se `regua_ativa` = True
2. Verificar `offset_dias` correto
3. Verificar se já existe LogCobranca (duplicação)
4. Logs em: `/admin/financeiro/logcobranca/`

### **Celery Worker não processa tasks**

```powershell
# Parar worker
Ctrl+C

# Reiniciar com verbose
celery -A serrana worker -l debug --pool=solo
```

---

## 📝 VARIÁVEIS DE TEMPLATE

Use no assunto/mensagem das etapas:

```
{cliente_nome}         → Nome do cliente/pessoa
{parcela_numero}       → Número da parcela (ex: 1)
{parcela_valor}        → Valor formatado (ex: R$ 1.500,00)
{parcela_vencimento}   → Data vencimento (ex: 15/01/2025)
{dias_atraso}          → Dias em atraso (ex: 5)
{empresa_nome}         → Nome da empresa
{titulo_numero}        → Número do título
{saldo_aberto}         → Saldo devedor formatado
```

**Exemplo de mensagem:**

```
Olá {cliente_nome},

Identificamos que a parcela {parcela_numero} no valor de {parcela_valor}, 
com vencimento em {parcela_vencimento}, encontra-se em atraso há {dias_atraso} dia(s).

Saldo devedor: {saldo_aberto}

Atenciosamente,
{empresa_nome}
```

---

## ✅ CHECKLIST DE ATIVAÇÃO

- [ ] Redis instalado e rodando
- [ ] Celery worker iniciado
- [ ] Celery beat iniciado
- [ ] SMTP configurado
- [ ] SMTP testado (EmailService.testar_configuracao())
- [ ] Régua criada no admin
- [ ] Etapas configuradas (com offsets corretos)
- [ ] Parcelas vinculadas à régua
- [ ] Painel de cobrança acessível
- [ ] Teste manual de disparo
- [ ] Histórico funcionando

---

## 🎉 PRONTO!

Sistema de Régua de Cobrança totalmente funcional com:

✅ Automação completa via Celery
✅ 5 etapas de cobrança progressiva
✅ Painel visual com KPIs
✅ Histórico completo de envios
✅ Controle manual (pausar/retomar/promessa)
✅ Retry automático de falhas
✅ Templates com variáveis dinâmicas
✅ Auditoria completa (LogCobranca)
✅ Admin integrado

**Futuras melhorias:**
- WhatsApp (arquitetura pronta, implementação pendente)
- Relatórios de performance
- Dashboard analytics
- Integração com gateway de pagamento
