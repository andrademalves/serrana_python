# 🚀 QUICK START - DASHBOARD BI

**Guia Rápido de Início em 10 Minutos**

---

## ✅ PRÉ-REQUISITOS

Antes de começar, certifique-se de ter:

- [x] Python 3.10+ instalado
- [x] PostgreSQL rodando (banco `serrana_db`)
- [x] Projeto Django funcionando (`python manage.py runserver`)

---

## 📦 PASSO 1: INSTALAR DEPENDÊNCIAS (2 min)

```powershell
# Ativar ambiente virtual (se houver)
# venv\Scripts\activate

# Instalar pacotes necessários
pip install celery redis django-redis reportlab openpyxl
```

**Verificar instalação:**
```powershell
python -c "import celery, redis, reportlab, openpyxl; print('✅ Tudo OK!')"
```

---

## 🔴 PASSO 2: INSTALAR E INICIAR REDIS (3 min)

### Windows (Chocolatey):

```powershell
# Instalar Chocolatey (se não tiver):
# https://chocolatey.org/install

# Instalar Redis
choco install redis-64 -y

# Iniciar Redis
redis-server
```

### Windows (Download Manual):

1. Baixar: https://github.com/microsoftarchive/redis/releases
2. Extrair para `C:\Redis`
3. Executar `C:\Redis\redis-server.exe`

**Verificar Redis:**
```powershell
redis-cli ping
# Resposta esperada: PONG
```

---

## ⚙️ PASSO 3: CONFIGURAR DJANGO (3 min)

### 3.1 Editar `serrana/settings.py`

**Adicionar no final do arquivo:**

```python
# ============================================================================
# CACHE - REDIS
# ============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'serrana',
        'TIMEOUT': 3600,
    }
}

# ============================================================================
# CELERY
# ============================================================================
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'atualizar-dashboard-hourly': {
        'task': 'dashboard.atualizar_kpis',
        'schedule': crontab(minute=0),
    },
}
```

**Adicionar 'dashboard' em INSTALLED_APPS:**

```python
INSTALLED_APPS = [
    # ... apps existentes ...
    'dashboard',  # <<<< ADICIONAR
]
```

### 3.2 Criar `serrana/celery.py`

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')

app = Celery('serrana')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### 3.3 Editar `serrana/__init__.py`

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 3.4 Adicionar rotas em `serrana/urls.py`

```python
from django.urls import path, include

urlpatterns = [
    # ... rotas existentes ...
    path('dashboard/', include('dashboard.urls')),  # <<<< ADICIONAR
]
```

---

## 🗄️ PASSO 4: CONFIGURAR BANCO DE DADOS (2 min)

### 4.1 Criar Materialized View (PostgreSQL)

```powershell
# Abrir psql
psql -U seu_usuario -d serrana_db
```

**Executar SQL:**

```sql
-- View materializada para histórico de estoque
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

-- Índice para refresh concorrente
CREATE UNIQUE INDEX idx_mv_estoque_historico_pk ON mv_estoque_historico (data, produto_id);

-- Primeiro refresh
REFRESH MATERIALIZED VIEW mv_estoque_historico;

-- Sair do psql
\q
```

---

## ▶️ PASSO 5: INICIAR SERVIÇOS

### Abrir 3 terminais:

**Terminal 1: Django**
```powershell
cd "c:\HD_Antigo\01- Projetos Dev\1.5 Serrana"
python manage.py runserver
```

**Terminal 2: Celery Worker**
```powershell
cd "c:\HD_Antigo\01- Projetos Dev\1.5 Serrana"
celery -A serrana worker -l info --pool=solo
```

**Terminal 3: Celery Beat** (opcional - para tarefas agendadas)
```powershell
cd "c:\HD_Antigo\01- Projetos Dev\1.5 Serrana"
celery -A serrana beat -l info
```

---

## 🎉 PASSO 6: ACESSAR DASHBOARD

### Abrir navegador:

```
http://localhost:8000/dashboard/
```

### Você verá:

- ✅ 4 KPI cards (Estoque, Itens Críticos, Giro, Caixa)
- ✅ Alertas críticos (se houver)
- ✅ Gráfico de Curva ABC (Pareto)
- ✅ Gráfico de Fluxo de Caixa
- ✅ Gráfico de Obras por Status
- ✅ Gráfico DRE Mensal
- ✅ Tabela de Produtos Críticos

---

## 🧪 PASSO 7: TESTAR FUNCIONALIDADES

### 7.1 Testar Cache

```python
# Abrir shell Django
python manage.py shell

# Testar Redis
from django.core.cache import cache
cache.set('teste', 'OK', 60)
print(cache.get('teste'))  # Deve mostrar: OK

# Testar KPIs
from dashboard.services_kpi import EstoqueKPIService
valor = EstoqueKPIService.get_valor_total_estoque()
print(f"Valor estoque: R$ {valor['valor_atual']}")
```

### 7.2 Testar APIs AJAX

Acessar no navegador:

- http://localhost:8000/dashboard/api/estoque/kpis/
- http://localhost:8000/dashboard/api/curva-abc/
- http://localhost:8000/dashboard/api/fluxo-caixa/

**Esperado:** JSON com dados dos KPIs

### 7.3 Testar Exportação

Clicar nos botões no dashboard:

- **PDF** → Baixa `dashboard_YYYYMMDD_HHMMSS.pdf`
- **Excel** → Baixa `dashboard_YYYYMMDD_HHMMSS.xlsx`

### 7.4 Testar Celery Task

```python
python manage.py shell

from dashboard.tasks import atualizar_kpis_dashboard
result = atualizar_kpis_dashboard.delay()
print(result.get())  # Aguarda execução e mostra resultado
```

---

## ❌ TROUBLESHOOTING

### Erro: "No module named 'celery'"

```powershell
pip install celery redis django-redis
```

### Erro: "ConnectionError: Error connecting to Redis"

**Verificar se Redis está rodando:**
```powershell
redis-cli ping
```

**Se não responder:**
```powershell
redis-server
```

### Erro: "relation 'mv_estoque_historico' does not exist"

**Criar view materializada:**
```powershell
psql -U seu_usuario -d serrana_db -f criar_views.sql
# Ou executar SQL manualmente (Passo 4.1)
```

### Gráficos não aparecem

**Abrir console do navegador (F12) e verificar:**
- Erros JavaScript
- Erros 404 nas APIs
- CORS issues

**Solução comum:**
- Limpar cache do navegador (Ctrl+F5)
- Verificar se APIs retornam JSON:
  ```
  http://localhost:8000/dashboard/api/curva-abc/
  ```

### Performance lenta

**Se dashboard demorar > 3 segundos:**

1. Verificar cache hit:
   ```python
   from django.core.cache import cache
   cache.get('kpi:estoque:valor_total:all')  # Deve retornar dados
   ```

2. Forçar atualização:
   ```python
   from dashboard.services_kpi import DashboardService
   DashboardService.limpar_cache_dashboard()
   ```

3. Refresh view materializada:
   ```sql
   REFRESH MATERIALIZED VIEW mv_estoque_historico;
   ```

---

## 📚 DOCUMENTAÇÃO COMPLETA

Para mais detalhes, consulte:

| Documento | Quando usar |
|-----------|-------------|
| [DASHBOARD_INDICE.md](DASHBOARD_INDICE.md) | Navegação geral do projeto |
| [DASHBOARD_RESUMO_EXECUTIVO.md](DASHBOARD_RESUMO_EXECUTIVO.md) | Visão executiva, KPIs |
| [DASHBOARD_BI_DESIGN.md](DASHBOARD_BI_DESIGN.md) | Arquitetura técnica, SQL |
| [GUIA_IMPLEMENTACAO_DASHBOARD.md](GUIA_IMPLEMENTACAO_DASHBOARD.md) | Deploy produção, troubleshooting |

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após seguir todos os passos, marque:

- [ ] Redis instalado e rodando (`redis-cli ping` → PONG)
- [ ] Dependências Python instaladas (celery, redis, reportlab, openpyxl)
- [ ] `settings.py` configurado (CACHE, CELERY, INSTALLED_APPS)
- [ ] `celery.py` criado em `serrana/`
- [ ] URLs adicionadas (`dashboard/` em `urls.py`)
- [ ] View materializada criada no PostgreSQL
- [ ] Django rodando (Terminal 1)
- [ ] Celery worker rodando (Terminal 2)
- [ ] Dashboard acessível: http://localhost:8000/dashboard/
- [ ] Gráficos carregam corretamente
- [ ] APIs retornam JSON
- [ ] Cache funcionando (teste no shell)
- [ ] Exportação PDF/Excel funciona

---

## 🎯 PRÓXIMOS PASSOS

Após validar que tudo funciona:

1. **Popular dados de teste:**
   ```bash
   python manage.py shell
   # Criar produtos, movimentações, etc.
   ```

2. **Explorar dashboards específicos:**
   - http://localhost:8000/dashboard/estoque/
   - http://localhost:8000/dashboard/obras/
   - http://localhost:8000/dashboard/financeiro/

3. **Configurar tarefas agendadas:**
   - Editar horários em `settings.py` → `CELERY_BEAT_SCHEDULE`
   - Adicionar destinatários de email

4. **Personalizar KPIs:**
   - Adicionar novos em `services_kpi.py`
   - Criar endpoints em `views.py`
   - Atualizar template

5. **Criar templates detalhados** (Fase 2)

---

## 🆘 PRECISA DE AJUDA?

**Erro não documentado?**
1. Verificar logs:
   - Django: console do runserver
   - Celery: console do worker
   - Redis: `redis-cli MONITOR`

2. Consultar FAQ: [GUIA_IMPLEMENTACAO_DASHBOARD.md](GUIA_IMPLEMENTACAO_DASHBOARD.md#10-faq)

3. Abrir issue no repositório com:
   - Mensagem de erro completa
   - Versão Python (`python --version`)
   - Versão Django (`python manage.py --version`)
   - Versão Redis (`redis-cli --version`)

---

## 🎉 SUCESSO!

Se você chegou até aqui e todos os checkboxes estão marcados, **parabéns!**

Você tem um **Dashboard BI profissional** rodando com:
- ✅ 20+ KPIs calculados automaticamente
- ✅ 5 gráficos interativos (Chart.js)
- ✅ Cache Redis para performance
- ✅ Tarefas assíncronas (Celery)
- ✅ Exportação PDF/Excel

**Tempo investido:** ~10-15 minutos  
**Retorno:** Sistema de BI empresarial completo

---

**📊 Dashboard BI v1.0 - Quick Start**  
**Fábrica de Esquadrias Serrana**  
**Desenvolvido com ❤️ em Dezembro 2025**
