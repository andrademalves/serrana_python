"""
============================================================================
INSTRUÇÕES DE INTEGRAÇÃO - ETAPAS 2 e 3
Sistema de Budget e Controle de Lucratividade
============================================================================
"""

# ============================================================================
# PASSO 1: INTEGRAR URLS NO PROJETO PRINCIPAL
# ============================================================================

"""
Abrir arquivo: serrana/urls.py
Adicionar a linha:
"""

from django.urls import path, include

urlpatterns = [
    # ... URLs existentes ...
    
    # Budget e Controle de Lucratividade
    path('financeiro/budget/', include('financeiro.urls_budget')),
]


# ============================================================================
# PASSO 2: EXECUTAR MIGRATIONS
# ============================================================================

"""
Terminal:
"""
# python manage.py makemigrations financeiro
# python manage.py migrate


# ============================================================================
# PASSO 3: INICIALIZAR REGIMES TRIBUTÁRIOS E ALÍQUOTAS
# ============================================================================

"""
Terminal:
"""
# python inicializar_impostos.py


# ============================================================================
# PASSO 4: EXECUTAR QUERIES SQL DE BI NO MYSQL
# ============================================================================

"""
Terminal:
"""
# mysql -u root -p serrana_db < financeiro/queries_bi.sql

"""
OU via Django shell:
"""
# python manage.py dbshell < financeiro/queries_bi.sql


# ============================================================================
# PASSO 5: REGISTRAR ADMIN NO DJANGO ADMIN
# ============================================================================

"""
Abrir arquivo: financeiro/admin.py
Adicionar no final:
"""

from financeiro.admin_budget import (
    RegimeTributarioAdmin,
    AliquotaImpostoAdmin, 
    ProjectBudgetAdmin,
    ProjectExpenseAdmin,
    JustificativaBudgetAdmin
)

# Os admins já estão registrados em admin_budget.py
# Apenas importar para garantir que sejam carregados


# ============================================================================
# PASSO 6: CONFIGURAR EMAIL (settings.py)
# ============================================================================

"""
Adicionar em serrana/settings.py:
"""

# Configuração de Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # ou seu servidor SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@empresa.com'
EMAIL_HOST_PASSWORD = 'sua-senha-ou-app-password'
DEFAULT_FROM_EMAIL = 'Serrana Gestão 360 <noreply@serranagestao.com>'

# Emails de gestores (recebem notificações)
GESTORES_EMAILS = [
    'gestor1@empresa.com',
    'gestor2@empresa.com',
]


# ============================================================================
# PASSO 7: CONFIGURAR CELERY PARA TAREFAS AGENDADAS (OPCIONAL)
# ============================================================================

"""
Criar arquivo: serrana/celery.py
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')

app = Celery('serrana')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Agendamento de tarefas
app.conf.beat_schedule = {
    # Verificar budgets críticos todos os dias às 8h
    'verificar-budgets-criticos-diario': {
        'task': 'financeiro.tasks.verificar_budgets_criticos_diario',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Verificar budgets atrasados todos os dias às 9h
    'verificar-budgets-atrasados-diario': {
        'task': 'financeiro.tasks.verificar_budgets_atrasados_diario',
        'schedule': crontab(hour=9, minute=0),
    },
}

"""
Criar arquivo: financeiro/tasks.py
"""

from celery import shared_task
from financeiro.signals import verificar_budgets_zona_critica, verificar_budgets_atrasados

@shared_task
def verificar_budgets_criticos_diario():
    """Tarefa agendada para verificar budgets críticos"""
    return verificar_budgets_zona_critica()

@shared_task
def verificar_budgets_atrasados_diario():
    """Tarefa agendada para verificar budgets atrasados"""
    return verificar_budgets_atrasados()

"""
Atualizar serrana/__init__.py:
"""

from .celery import app as celery_app

__all__ = ('celery_app',)

"""
Rodar Celery Worker e Beat:
"""
# celery -A serrana worker --loglevel=info
# celery -A serrana beat --loglevel=info


# ============================================================================
# PASSO 8: CRIAR TEMPLATES HTML (OPCIONAL - APIs JÁ FUNCIONAM)
# ============================================================================

"""
Criar pasta: templates/financeiro/budget/

Arquivos necessários:
- base_budget.html (template base)
- dashboard.html
- detalhe.html
- relatorio_vendedores.html
- relatorio_instaladores.html
- relatorio_lucratividade.html
"""


# ============================================================================
# PASSO 9: TESTAR O SISTEMA
# ============================================================================

"""
1. Acessar Django Admin:
   http://localhost:8000/admin/
   
2. Criar um Budget de teste:
   - Criar Projeto
   - Criar ProjectBudget
   - Verificar que semáforo está VERDE
   
3. Lançar despesas:
   - Criar ProjectExpense até 50% do budget
   - Verificar que semáforo continua VERDE
   
4. Testar Zona Amarela:
   - Lançar despesa que atinja 85% do budget
   - Verificar que semáforo muda para AMARELO
   - Verificar email enviado
   
5. Testar Zona Vermelha e Bloqueio:
   - Lançar despesa que atinja 96% do budget
   - Verificar que semáforo muda para VERMELHO
   - Verificar campo bloqueado = True
   - Tentar lançar nova despesa (deve ser bloqueado)
   - Verificar email enviado
   
6. Testar Justificativa:
   - Criar JustificativaBudget
   - Verificar email ao gestor
   - Aprovar justificativa
   - Verificar que budget foi desbloqueado
   
7. Testar APIs:
   curl -X POST http://localhost:8000/financeiro/budget/api/despesa/lancar/ \
     -H "Content-Type: application/json" \
     -d '{"budget_id": 1, "tipo_despesa": "MATERIAL", "valor": 500.00, "descricao": "Teste"}'
   
8. Testar Relatórios:
   - Acessar /financeiro/budget/relatorio/vendedores/
   - Acessar /financeiro/budget/relatorio/instaladores/
   - Acessar /financeiro/budget/relatorio/lucratividade/
"""


# ============================================================================
# PASSO 10: EXECUTAR TESTES UNITÁRIOS
# ============================================================================

"""
Terminal:
"""
# python manage.py test financeiro.tests_budget -v 2


# ============================================================================
# URLS DISPONÍVEIS APÓS INTEGRAÇÃO
# ============================================================================

"""
DASHBOARD:
- /financeiro/budget/dashboard/
- /financeiro/budget/budget/<id>/

APIS REST:
- POST /financeiro/budget/api/despesa/lancar/
- POST /financeiro/budget/api/despesa/<id>/aprovar/
- POST /financeiro/budget/api/despesa/<id>/rejeitar/
- POST /financeiro/budget/api/justificativa/criar/
- POST /financeiro/budget/api/justificativa/<id>/aprovar/
- POST /financeiro/budget/api/justificativa/<id>/rejeitar/
- GET  /financeiro/budget/api/budget/<id>/status/
- GET  /financeiro/budget/api/budgets/criticos/

RELATÓRIOS:
- /financeiro/budget/relatorio/vendedores/
- /financeiro/budget/relatorio/instaladores/
- /financeiro/budget/relatorio/lucratividade/
"""


# ============================================================================
# PERMISSÕES RECOMENDADAS
# ============================================================================

"""
Criar grupos de permissão no Django Admin:

1. GRUPO: Instaladores/Funcionários
   - Pode adicionar ProjectExpense
   - Pode visualizar ProjectExpense (próprias)
   - Pode adicionar JustificativaBudget
   - Pode visualizar ProjectBudget (próprios)

2. GRUPO: Gestores
   - Pode visualizar ProjectBudget (todos)
   - Pode editar ProjectBudget
   - Pode aprovar/rejeitar ProjectExpense
   - Pode aprovar/rejeitar JustificativaBudget
   - Acesso total aos relatórios

3. GRUPO: Vendedores
   - Pode visualizar ProjectBudget (próprios projetos)
   - Pode visualizar ProjectExpense (próprios projetos)
   - Acesso ao relatório de vendedores

4. GRUPO: Diretoria
   - Acesso total a todos os módulos
   - Acesso a todos os relatórios
   - Pode alterar RegimeTributario e AliquotaImposto
"""


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
PROBLEMA: Signals não estão sendo disparados
SOLUÇÃO: Verificar que financeiro/apps.py tem o método ready() e que
         o app está em INSTALLED_APPS como 'financeiro.apps.FinanceiroConfig'

PROBLEMA: Emails não estão sendo enviados
SOLUÇÃO: Verificar configurações EMAIL_* no settings.py e testar:
         python manage.py shell
         >>> from django.core.mail import send_mail
         >>> send_mail('Teste', 'Corpo', 'from@example.com', ['to@example.com'])

PROBLEMA: Queries SQL não estão funcionando
SOLUÇÃO: Executar manualmente no MySQL Workbench/CLI e verificar erros

PROBLEMA: Semáforo não atualiza
SOLUÇÃO: Verificar que ProjectExpense.save() está sendo chamado (não .update())
         e que o signal atualizar_budget_apos_despesa está ativo

PROBLEMA: Performance lenta nos relatórios
SOLUÇÃO: Executar os índices do arquivo queries_bi.sql:
         CREATE INDEX idx_project_expenses_budget_status ON project_expenses(budget_id, status);
         etc.
"""


# ============================================================================
# CONCLUSÃO
# ============================================================================

print("""
✅ SISTEMA DE BUDGET PRONTO PARA USO!

Funcionalidades Implementadas:
- ✅ Controle de Budget em tempo real
- ✅ Semáforo automático (Verde/Amarelo/Vermelho)
- ✅ Bloqueio automático aos 95%
- ✅ Sistema de justificativas
- ✅ Notificações por email
- ✅ APIs REST para mobile
- ✅ KPIs de vendedores (assertividade)
- ✅ KPIs de instaladores (retrabalho)
- ✅ Análise de lucratividade
- ✅ Queries SQL otimizadas

Próximos Passos:
1. Integrar URLs (5 minutos)
2. Executar migrations (2 minutos)
3. Inicializar impostos (1 minuto)
4. Executar SQL de BI (2 minutos)
5. Configurar email (5 minutos)
6. TESTAR! (30 minutos)

TOTAL: ~45 minutos para o sistema estar em produção!
""")
