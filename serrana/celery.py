"""
Celery Configuration
"""
import os
from celery import Celery

# Define o módulo de settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')

app = Celery('serrana')

# Carrega configurações do Django settings com namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descobre tasks nos arquivos tasks.py de cada app
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Task de debug"""
    print(f'Request: {self.request!r}')
