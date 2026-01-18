# 🚀 COMANDOS ÚTEIS - DASHBOARD BI

## 🌐 Iniciar Sistema

### Iniciar Servidor Django
```powershell
python manage.py runserver
```
Acesse: http://localhost:8000/dashboard/

---

## 🧪 Testar Funcionalidades

### Testar Cache
```powershell
python manage.py shell
```
```python
from django.core.cache import cache
cache.set('test', 'OK', 60)
print(cache.get('test'))  # Deve retornar: OK
```

### Testar Services do Dashboard
```python
from dashboard.services_kpi import EstoqueKPIService, FinanceiroKPIService, ObrasKPIService

# Estoque
print(EstoqueKPIService.get_valor_total_estoque())
print(EstoqueKPIService.get_itens_criticos())
print(EstoqueKPIService.get_curva_abc())

# Financeiro
print(FinanceiroKPIService.get_saldo_caixa())
print(FinanceiroKPIService.get_contas_receber())

# Obras
print(ObrasKPIService.get_obras_status())
```

### Testar Dashboard Completo
```python
from dashboard.services_kpi import DashboardService
dados = DashboardService.get_dashboard_completo()
print(dados.keys())
```

---

## 🧹 Limpar Cache

### Via Shell
```python
from django.core.cache import cache
cache.clear()
print("Cache limpo!")
```

### Via Service
```python
from dashboard.services_kpi import DashboardService
DashboardService.limpar_cache_dashboard()
```

---

## 📊 Testar APIs REST

### Com servidor rodando (http://localhost:8000)

```powershell
# KPIs Estoque
Invoke-WebRequest -Uri "http://localhost:8000/dashboard/api/kpis/estoque/"

# KPIs Financeiro
Invoke-WebRequest -Uri "http://localhost:8000/dashboard/api/kpis/financeiro/"

# KPIs Obras
Invoke-WebRequest -Uri "http://localhost:8000/dashboard/api/kpis/obras/"

# Curva ABC
Invoke-WebRequest -Uri "http://localhost:8000/dashboard/api/curva-abc/"

# Fluxo de Caixa
Invoke-WebRequest -Uri "http://localhost:8000/dashboard/api/fluxo-caixa/"
```

---

## 🔄 Celery (após instalar Redis)

### Iniciar Worker
```powershell
celery -A serrana worker -l info --pool=solo
```

### Iniciar Beat (Agendador)
```powershell
celery -A serrana beat -l info
```

### Testar Task Manualmente
```python
from dashboard.tasks import atualizar_kpis_dashboard

# Executar agora (síncrono)
resultado = atualizar_kpis_dashboard()
print(resultado)

# Executar assíncrono (requer worker rodando)
task = atualizar_kpis_dashboard.delay()
print(task.id)
print(task.status)
```

---

## 📦 Migrations

### Verificar Status
```powershell
python manage.py showmigrations
```

### Criar Migrations
```powershell
python manage.py makemigrations
```

### Aplicar Migrations
```powershell
python manage.py migrate
```

---

## 🐛 Debugging

### Ver Logs do Django
Logs aparecem no terminal onde você rodou `runserver`

### Ver Erros Detalhados
Em `settings.py`, certifique-se que:
```python
DEBUG = True
```

### Verificar Configuração
```powershell
python manage.py check
python manage.py check --deploy
```

### Shell Django
```powershell
python manage.py shell
```

---

## 📝 Adicionar Dados de Teste

### Criar Usuário Admin
```powershell
python manage.py createsuperuser
```

### Popular Dados via Admin
1. Acesse: http://localhost:8000/admin/
2. Login com superuser
3. Adicione produtos, clientes, etc.

### Popular via Shell
```python
from cadastros.models import Pessoa
from estoque.models import Item, GrupoItem

# Criar grupo
grupo = GrupoItem.objects.create(
    codigo='ALU',
    descricao='Alumínio'
)

# Criar item
item = Item.objects.create(
    codigo='ALU-001',
    descricao='Perfil de Alumínio 6m',
    grupo=grupo,
    ativo=True,
    estoque_minimo=10,
    estoque_maximo=100
)

print(f"Item criado: {item}")
```

---

## 📤 Exportar Dados

### Exportar para Excel
Acesse: http://localhost:8000/dashboard/exportar/excel/

### Exportar para PDF
Acesse: http://localhost:8000/dashboard/exportar/pdf/

### Via Shell
```python
from dashboard.services_kpi import DashboardService

# Excel
excel_file = DashboardService.exportar_excel()
print(f"Excel gerado: {excel_file}")

# PDF
pdf_file = DashboardService.exportar_pdf()
print(f"PDF gerado: {pdf_file}")
```

---

## 🔍 Verificar Dependências

### Listar Pacotes Instalados
```powershell
pip list | Select-String -Pattern "celery|redis|django|reportlab|openpyxl"
```

### Verificar Versões
```powershell
python -c "import django; print(f'Django: {django.__version__}')"
python -c "import celery; print(f'Celery: {celery.__version__}')"
python -c "import redis; print(f'Redis: {redis.__version__}')"
```

---

## 🛠️ Manutenção

### Atualizar Dependências
```powershell
pip install --upgrade celery redis django-redis reportlab openpyxl
```

### Limpar Cache Python
```powershell
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
```

### Backup do Banco
```powershell
# MySQL
mysqldump -u root -p serrana_empresarial > backup_$(Get-Date -Format 'yyyyMMdd').sql
```

---

## 📊 Performance

### Verificar Queries SQL
```python
from django.conf import settings
settings.DEBUG = True

from django.db import connection
from dashboard.services_kpi import EstoqueKPIService

# Executar função
EstoqueKPIService.get_valor_total_estoque()

# Ver queries executadas
print(f"Queries: {len(connection.queries)}")
for q in connection.queries:
    print(q['sql'])
```

### Testar Performance do Cache
```python
import time
from dashboard.services_kpi import DashboardService

# Limpar cache
DashboardService.limpar_cache_dashboard()

# Primeira execução (sem cache)
start = time.time()
DashboardService.get_dashboard_completo()
tempo_sem_cache = time.time() - start

# Segunda execução (com cache)
start = time.time()
DashboardService.get_dashboard_completo()
tempo_com_cache = time.time() - start

print(f"Sem cache: {tempo_sem_cache:.2f}s")
print(f"Com cache: {tempo_com_cache:.2f}s")
print(f"Ganho: {tempo_sem_cache/tempo_com_cache:.1f}x mais rápido")
```

---

## 🎯 Atalhos Úteis

### Ver Todas as URLs
```powershell
python manage.py show_urls
```

### Coletar Arquivos Estáticos
```powershell
python manage.py collectstatic --noinput
```

### Criar App Novo
```powershell
python manage.py startapp nome_do_app
```

---

## 💡 Dicas

1. **Sempre rode `python manage.py check` após mudanças**
2. **Use `shell_plus` se tiver django-extensions**
3. **Para debug, use `import pdb; pdb.set_trace()`**
4. **Monitore logs do Celery para tasks assíncronas**
5. **Use Redis para produção (melhor performance)**

---

**Última atualização:** 12/01/2026
