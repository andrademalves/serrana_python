"""
Inicialização do projeto Serrana
"""

# Garante que o Celery app seja carregado quando Django iniciar
from .celery import app as celery_app

__all__ = ('celery_app',)
