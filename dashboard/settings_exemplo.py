"""
CONFIGURAÇÕES - DASHBOARD BI
=============================

Cole este código no final do seu settings.py

Autor: Sistema BI Profissional
Data: Dezembro 2025
"""

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
# CELERY - CONFIGURAÇÃO
# ============================================================================
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos

# ============================================================================
# CELERY BEAT - TAREFAS AGENDADAS
# ============================================================================
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Atualizar KPIs do dashboard a cada hora
    'atualizar-dashboard-hourly': {
        'task': 'dashboard.atualizar_kpis',
        'schedule': crontab(minute=0),  # A cada hora cheia (00:00, 01:00, 02:00...)
    },
    
    # Refresh de views materializadas (PostgreSQL) - Diariamente às 00:00
    'refresh-materialized-views-daily': {
        'task': 'dashboard.refresh_materialized_views',
        'schedule': crontab(hour=0, minute=0),
    },
    
    # Calcular previsão de ruptura de estoque - Diariamente às 06:00
    'calcular-previsao-estoque-daily': {
        'task': 'dashboard.calcular_previsao_estoque',
        'schedule': crontab(hour=6, minute=0),
    },
    
    # Enviar relatório gerencial por email - Segundas-feiras às 08:00
    'enviar-relatorio-gerencial-weekly': {
        'task': 'dashboard.gerar_relatorio_gerencial',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # 1 = Segunda
        'kwargs': {
            'destinatarios': [
                'gerencia@serranaesquadrias.com.br',
                'diretoria@serranaesquadrias.com.br',
            ]
        }
    },
}

# ============================================================================
# EMAIL - CONFIGURAÇÃO (PARA RELATÓRIOS)
# ============================================================================
# OPÇÃO 1: Gmail (Desenvolvimento)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha-app'  # Gerar senha de app no Gmail
DEFAULT_FROM_EMAIL = 'Sistema Serrana <sistema@serranaesquadrias.com.br>'

# OPÇÃO 2: SendGrid (Produção - Recomendado)
"""
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = 'SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
DEFAULT_FROM_EMAIL = 'sistema@serranaesquadrias.com.br'
"""

# OPÇÃO 3: Console (Testes - mostra no terminal)
"""
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
"""

# ============================================================================
# LOGGING - DASHBOARD
# ============================================================================
import os

# Criar diretório de logs se não existir
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_dashboard': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'dashboard.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_celery': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'celery.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'dashboard': {
            'handlers': ['console', 'file_dashboard'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file_celery'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# INSTALLED APPS - ADICIONAR DASHBOARD
# ============================================================================
"""
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
    'financeiro',
    'dashboard',  # <<<< ADICIONAR
]
"""

# ============================================================================
# CONFIGURAÇÕES ADICIONAIS (OPCIONAIS)
# ============================================================================

# Timeout de sessão (1 hora de inatividade)
SESSION_COOKIE_AGE = 3600

# Configuração de fuso horário
TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True

# Configuração de internacionalização
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True

# Formatos de data/número brasileiros
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'

USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','

# ============================================================================
# CONFIGURAÇÕES DE PERFORMANCE (PRODUÇÃO)
# ============================================================================
"""
# Comprimir respostas
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # <<<< ADICIONAR NO TOPO
    # ... outros middlewares
]

# Configurar ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'seu-dominio.com.br',
    'www.seu-dominio.com.br',
]

# Segurança (produção)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
"""

# ============================================================================
# FIM DAS CONFIGURAÇÕES
# ============================================================================

print("✅ Configurações do Dashboard BI carregadas com sucesso!")
