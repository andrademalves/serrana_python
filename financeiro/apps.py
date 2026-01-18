from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financeiro'
    verbose_name = 'Financeiro'
    
    def ready(self):
        """
        Método chamado quando o app está pronto.
        Importa os signals para ativar o monitoramento automático de Budget.
        """
        import financeiro.signals  # noqa: F401
