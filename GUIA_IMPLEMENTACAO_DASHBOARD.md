# GUIA DE IMPLEMENTAÇÃO - DASHBOARD BI PROFISSIONAL

**Sistema de Business Intelligence para Fábrica de Esquadrias**  
**Data:** Dezembro 2025  
**Versão:** 1.0

---

## 📋 ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Instalação e Configuração](#3-instalação-e-configuração)
4. [Estrutura de Arquivos](#4-estrutura-de-arquivos)
5. [Configuração do Banco de Dados](#5-configuração-do-banco-de-dados)
6. [Celery e Redis](#6-celery-e-redis)
7. [Testes](#7-testes)
8. [Deploy](#8-deploy)
9. [Troubleshooting](#9-troubleshooting)
10. [FAQ](#10-faq)

---

## 1. VISÃO GERAL

### 1.1 O que é o Dashboard BI?

Sistema de **Business Intelligence** integrado que consolida informações de:
- **ESTOQUE**: Valor imobilizado, curva ABC, giro, itens críticos
- **OBRAS**: Status, análise financeira, budget x realizado
- **FINANCEIRO**: Fluxo de caixa, DRE, inadimplência

### 1.2 Características

✅ **Tempo Real**: Atualização automática via Celery  
✅ **Performance**: Cache Redis + Materialized Views PostgreSQL  
✅ **Responsivo**: Bootstrap 5 + Chart.js  
✅ **Exportável**: PDF (ReportLab) e Excel (openpyxl)  
✅ **Rastreável**: Todos os KPIs com drill-down  

### 1.3 Arquitetura

```
┌─────────────────┐
│   Frontend      │  Django Templates + Chart.js + Bootstrap 5
│   (Templates)   │  HTMX para interatividade
└────────┬────────┘
         │
┌────────▼────────┐
│   Views         │  API REST + Renderização HTML
│   (views.py)    │  Endpoints AJAX para gráficos
└────────┬────────┘
         │
┌────────▼────────┐
│   Services      │  Lógica de negócio
│   (services_    │  Cálculo de KPIs
│   kpi.py)       │
└────────┬────────┘
         │
┌────────▼────────┐
│   Models        │  Django ORM
│   (cadastros,   │  Acesso aos dados
│   estoque...)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   PostgreSQL    │  Banco de dados
│   + Redis       │  Cache + Celery Broker
└─────────────────┘
```

---

## 2. PRÉ-REQUISITOS

### 2.1 Software Necessário

- **Python**: 3.10 ou superior
- **PostgreSQL**: 13 ou superior
- **Redis**: 6.0 ou superior (para cache e Celery)
- **Navegador**: Chrome, Firefox, Edge (versões recentes)

### 2.2 Dependências Python

```bash
# Core Django
Django>=4.2
psycopg2-binary>=2.9
python-decouple>=3.8

# Celery e Cache
celery>=5.3
redis>=5.0
django-redis>=5.3

# Exportação
reportlab>=4.0
WeasyPrint>=60.0
openpyxl>=3.1

# Utilitários
Pillow>=10.0
```

---

## 3. INSTALAÇÃO E CONFIGURAÇÃO

### PASSO 1: Criar Estrutura de Diretórios

```bash
cd "c:\HD_Antigo\01- Projetos Dev\1.5 Serrana"

# A estrutura já foi criada:
# dashboard/
#   __init__.py
#   apps.py
#   urls.py
#   views.py
#   services_kpi.py
#   tasks.py
#   templates/
#     dashboard/
#       principal.html
```

### PASSO 2: Instalar Dependências

```bash
# Ativar ambiente virtual (se houver)
# python -m venv venv
# venv\Scripts\activate

# Instalar pacotes
pip install celery redis django-redis reportlab openpyxl
```

### PASSO 3: Configurar `settings.py`

**Adicione ao `serrana/settings.py`:**

```python
# ============================================================================
# APLICAÇÕES
# ============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps do projeto
    'cadastros',
    'estoque',
    'projetos',
    'usuarios',
    'financeiro',  # CRIAR DEPOIS
    'dashboard',    # <<<< ADICIONAR
]

# ============================================================================
# CACHE - REDIS
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'serrana',
        'TIMEOUT': 3600,  # 1 hora padrão
    }
}

# ============================================================================
# CELERY
# ============================================================================
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# CELERY BEAT SCHEDULE (Tarefas Agendadas)
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'atualizar-dashboard-hourly': {
        'task': 'dashboard.atualizar_kpis',
        'schedule': crontab(minute=0),  # A cada hora cheia
    },
    'refresh-materialized-views-daily': {
        'task': 'dashboard.refresh_materialized_views',
        'schedule': crontab(hour=0, minute=0),  # Diariamente às 00:00
    },
    'calcular-previsao-estoque-daily': {
        'task': 'dashboard.calcular_previsao_estoque',
        'schedule': crontab(hour=6, minute=0),  # Diariamente às 06:00
    },
    'enviar-relatorio-gerencial-weekly': {
        'task': 'dashboard.gerar_relatorio_gerencial',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Segundas 08:00
        'kwargs': {
            'destinatarios': ['gerencia@serranaesquadrias.com.br']
        }
    },
}

# ============================================================================
# LOGGING
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/dashboard.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'dashboard': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### PASSO 4: Criar `celery.py`

**Criar arquivo `serrana/celery.py`:**

```python
import os
from celery import Celery

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')

app = Celery('serrana')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir tasks automaticamente
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

**Modificar `serrana/__init__.py`:**

```python
# Garantir que Celery seja carregado com Django
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### PASSO 5: Adicionar URLs

**Modificar `serrana/urls.py`:**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cadastros/', include('cadastros.urls')),
    path('estoque/', include('estoque.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('dashboard/', include('dashboard.urls')),  # <<<< ADICIONAR
    path('', include('cadastros.urls')),  # ou sua home
]
```

### PASSO 6: Criar Diretório de Logs

```bash
mkdir logs
```

---

## 4. ESTRUTURA DE ARQUIVOS

```
dashboard/
│
├── __init__.py                      # Inicialização do app
├── apps.py                          # Configuração do app
├── urls.py                          # Rotas (12 endpoints)
├── views.py                         # Views e APIs AJAX (17 funções)
├── services_kpi.py                  # Serviços de KPIs (4 classes, 20+ métodos)
├── tasks.py                         # Tarefas Celery (4 tasks)
│
└── templates/
    └── dashboard/
        ├── principal.html           # Dashboard principal ✅
        ├── estoque_detalhado.html   # Dashboard estoque (CRIAR)
        ├── obras_detalhado.html     # Dashboard obras (CRIAR)
        ├── financeiro_detalhado.html # Dashboard financeiro (CRIAR)
        └── email_relatorio_gerencial.html  # Template email (CRIAR)
```

### Arquivos Criados ✅

1. ✅ `dashboard/services_kpi.py` (634 linhas)
2. ✅ `dashboard/views.py` (477 linhas)
3. ✅ `dashboard/urls.py` (35 linhas)
4. ✅ `dashboard/tasks.py` (296 linhas)
5. ✅ `dashboard/templates/dashboard/principal.html` (524 linhas)
6. ✅ `dashboard/__init__.py`
7. ✅ `dashboard/apps.py`

**TOTAL: 1.966 linhas de código Python + 524 linhas HTML/JS**

---

## 5. CONFIGURAÇÃO DO BANCO DE DADOS

### PASSO 1: Instalar Redis (Windows)

```powershell
# Opção 1: Via Chocolatey
choco install redis-64

# Opção 2: Download manual
# https://github.com/microsoftarchive/redis/releases
# Extrair e executar redis-server.exe

# Verificar instalação
redis-cli ping
# Resposta: PONG
```

### PASSO 2: Criar Materialized Views (PostgreSQL)

**Conectar no PostgreSQL:**

```bash
psql -U seu_usuario -d serrana_db
```

**Executar SQL:**

```sql
-- ===========================================================================
-- VIEW MATERIALIZADA 1: Histórico de Movimentação de Estoque
-- ===========================================================================
CREATE MATERIALIZED VIEW mv_estoque_historico AS
SELECT 
    DATE(me.data_operacao) AS data,
    me.produto_id,
    p.codigo,
    p.descricao,
    SUM(CASE WHEN me.tipo_movimento = 'ENTRADA' THEN me.quantidade ELSE 0 END) AS entradas,
    SUM(CASE WHEN me.tipo_movimento = 'SAIDA' THEN me.quantidade ELSE 0 END) AS saidas,
    SUM(me.quantidade * me.custo_unitario_aplicado) AS valor_movimentado
FROM estoque_movimentoestoque me
INNER JOIN cadastros_produto p ON p.id = me.produto_id
WHERE me.estornado = FALSE
GROUP BY DATE(me.data_operacao), me.produto_id, p.codigo, p.descricao;

-- Índice único para refresh CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_estoque_historico_pk 
ON mv_estoque_historico (data, produto_id);

-- Índices adicionais para performance
CREATE INDEX idx_mv_estoque_historico_data ON mv_estoque_historico (data);
CREATE INDEX idx_mv_estoque_historico_produto ON mv_estoque_historico (produto_id);

-- ===========================================================================
-- VIEW MATERIALIZADA 2: Fluxo de Caixa Mensal (QUANDO FINANCEIRO EXISTIR)
-- ===========================================================================
-- IMPLEMENTAR APÓS CRIAR MODEL Titulo

-- ===========================================================================
-- REFRESH MANUAL (primeira vez)
-- ===========================================================================
REFRESH MATERIALIZED VIEW mv_estoque_historico;
```

### PASSO 3: Migrations

```bash
# Não há models novos no app dashboard, mas garantir que tudo está migrado
python manage.py makemigrations
python manage.py migrate
```

---

## 6. CELERY E REDIS

### Iniciar Serviços

**Terminal 1: Django**
```bash
python manage.py runserver
```

**Terminal 2: Redis** (se não estiver como serviço)
```bash
redis-server
```

**Terminal 3: Celery Worker**
```bash
# Windows
celery -A serrana worker -l info --pool=solo

# Linux/Mac
celery -A serrana worker -l info
```

**Terminal 4: Celery Beat** (agendador)
```bash
celery -A serrana beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Monitorar Celery

**Flower (opcional):**
```bash
pip install flower
celery -A serrana flower
# Acessar: http://localhost:5555
```

### Testar Tasks Manualmente

```python
# Python shell
python manage.py shell

from dashboard.tasks import atualizar_kpis_dashboard

# Executar agora
result = atualizar_kpis_dashboard.delay()

# Verificar resultado
print(result.get())
```

---

## 7. TESTES

### 7.1 Testar Services

```python
# python manage.py shell

from dashboard.services_kpi import EstoqueKPIService, DashboardService

# Testar KPI de valor total
valor = EstoqueKPIService.get_valor_total_estoque()
print(f"Valor total estoque: R$ {valor['valor_atual']}")

# Testar itens críticos
criticos = EstoqueKPIService.get_itens_abaixo_minimo()
print(f"Produtos críticos: {criticos['quantidade_total']}")

# Testar curva ABC
abc = EstoqueKPIService.get_curva_abc(limite=10)
for produto in abc:
    print(f"{produto['produto__codigo']} - Classe {produto['classe_abc']}")

# Testar KPIs principais
kpis = DashboardService.get_kpis_principais()
print(kpis)
```

### 7.2 Testar Views (APIs)

```bash
# Com servidor rodando
curl http://localhost:8000/dashboard/api/estoque/kpis/

# Ou acessar no navegador:
http://localhost:8000/dashboard/api/curva-abc/
http://localhost:8000/dashboard/api/fluxo-caixa/
```

### 7.3 Testar Cache

```python
from django.core.cache import cache

# Verificar conexão Redis
cache.set('test_key', 'Hello Redis!', 60)
value = cache.get('test_key')
print(value)  # Hello Redis!

# Limpar cache dashboard
from dashboard.services_kpi import DashboardService
DashboardService.limpar_cache_dashboard()
```

---

## 8. DEPLOY

### 8.1 Ambiente de Produção

**Usar supervisor ou systemd para gerenciar processos:**

**Arquivo: `/etc/supervisor/conf.d/serrana-dashboard.conf`**

```ini
[program:serrana-celery-worker]
command=/caminho/venv/bin/celery -A serrana worker -l info
directory=/caminho/projeto
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:serrana-celery-beat]
command=/caminho/venv/bin/celery -A serrana beat -l info
directory=/caminho/projeto
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

### 8.2 Nginx + Gunicorn

**Arquivo: `/etc/nginx/sites-available/serrana`**

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /caminho/staticfiles/;
    }

    location /media/ {
        alias /caminho/media/;
    }
}
```

### 8.3 Collectstatic

```bash
python manage.py collectstatic --noinput
```

---

## 9. TROUBLESHOOTING

### Problema 1: Erro ao conectar Redis

**Erro:**
```
ConnectionError: Error connecting to Redis
```

**Solução:**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Se não responder, iniciar:
redis-server

# Verificar porta (padrão 6379)
netstat -an | findstr 6379
```

### Problema 2: Tasks Celery não executam

**Verificar:**
```bash
# Ver logs do worker
celery -A serrana inspect active

# Ver tasks agendadas
celery -A serrana inspect scheduled

# Limpar fila
celery -A serrana purge
```

### Problema 3: Gráficos não carregam

**Solução:**
1. Abrir console do navegador (F12)
2. Verificar erros JavaScript
3. Confirmar que endpoints retornam JSON:
   ```
   http://localhost:8000/dashboard/api/curva-abc/
   ```
4. Verificar CSRF token no POST

### Problema 4: Performance lenta

**Otimizações:**

```python
# 1. Aumentar cache timeout
CACHES['default']['TIMEOUT'] = 7200  # 2 horas

# 2. Refresh views materializadas com frequência
CELERY_BEAT_SCHEDULE = {
    'refresh-views': {
        'task': 'dashboard.refresh_materialized_views',
        'schedule': crontab(hour='*/6'),  # A cada 6 horas
    },
}

# 3. Adicionar índices no banco
# Ver seção 5.2
```

---

## 10. FAQ

### Q1: Posso usar MySQL ao invés de PostgreSQL?

**R:** Sim, mas perderá views materializadas. Alternativas:
- Criar tabelas de cache manualmente
- Usar Celery para atualizar tabelas agregadas

### Q2: Como adicionar novos KPIs?

**R:** 
1. Criar método no service correspondente (`services_kpi.py`)
2. Adicionar endpoint AJAX em `views.py`
3. Adicionar rota em `urls.py`
4. Atualizar template para exibir o KPI

**Exemplo:**
```python
# services_kpi.py
@staticmethod
def get_novo_kpi():
    # Lógica do KPI
    return {'valor': 123}

# views.py
@login_required
def api_novo_kpi(request):
    data = EstoqueKPIService.get_novo_kpi()
    return JsonResponse(data)

# urls.py
path('api/estoque/novo-kpi/', views.api_novo_kpi, name='api_novo_kpi'),
```

### Q3: Como personalizar período dos gráficos?

**R:** Já está implementado via query params:
```javascript
// Alterar dias do fluxo de caixa
fetch('/dashboard/api/fluxo-caixa/?dias=60')

// Alterar meses do DRE
fetch('/dashboard/api/dre-mensal/?meses=6')
```

### Q4: Como agendar envio de relatório por email?

**R:** Já configurado no Celery Beat:
```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    'enviar-relatorio-weekly': {
        'task': 'dashboard.gerar_relatorio_gerencial',
        'schedule': crontab(day_of_week=1, hour=8),
        'kwargs': {
            'destinatarios': ['seu@email.com']
        }
    },
}
```

### Q5: Dashboard funciona offline?

**R:** Não, requer conexão com:
- Servidor Django (APIs)
- Redis (cache)
- PostgreSQL (dados)

Para relatórios offline, use exportação PDF/Excel.

---

## 📊 PRÓXIMOS PASSOS

### Fase 1: Validação ✅ (CONCLUÍDO)
- [x] Criar services de KPIs
- [x] Criar views e APIs
- [x] Criar template principal
- [x] Configurar Celery tasks

### Fase 2: Templates Detalhados (FAZER)
- [ ] Criar `dashboard/templates/dashboard/estoque_detalhado.html`
- [ ] Criar `dashboard/templates/dashboard/obras_detalhado.html`
- [ ] Criar `dashboard/templates/dashboard/financeiro_detalhado.html`
- [ ] Criar `dashboard/templates/dashboard/email_relatorio_gerencial.html`

### Fase 3: Integração Módulos (FAZER)
- [ ] Criar app `financeiro` (models: Titulo, Baixa, Categoria)
- [ ] Criar app `projetos` (model: Obra, Etapa)
- [ ] Integrar custos de obras com estoque
- [ ] Implementar DRE real

### Fase 4: Testes (FAZER)
- [ ] Criar `dashboard/tests.py` com testes unitários
- [ ] Testar com dados reais
- [ ] Validar performance com 10.000+ registros

### Fase 5: Deploy (FAZER)
- [ ] Configurar servidor de produção
- [ ] Configurar backup Redis
- [ ] Monitoramento com Sentry
- [ ] Documentação de usuário

---

## 🎯 RECURSOS ADICIONAIS

### Documentação Completa

- [DASHBOARD_BI_DESIGN.md](DASHBOARD_BI_DESIGN.md) - Arquitetura e decisões técnicas
- [DESIGN_ESTOQUE_PROFISSIONAL.md](estoque/DESIGN_ESTOQUE_PROFISSIONAL.md) - Design do módulo estoque

### Suporte

- **Email**: suporte@serranaesquadrias.com.br
- **Docs Django**: https://docs.djangoproject.com/
- **Docs Celery**: https://docs.celeryq.dev/
- **Docs Chart.js**: https://www.chartjs.org/docs/

---

**Dashboard BI v1.0** - Sistema Profissional de Business Intelligence  
Desenvolvido para **Serrana Esquadrias** - Dezembro 2025
