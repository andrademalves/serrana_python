from django.apps import AppConfig


class ProjetosConfig(AppConfig):
    name = 'projetos'
    verbose_name = 'Projetos e Orçamentos'
    
    def ready(self):
        """Importa signals quando o app é carregado"""
        import projetos.signals  # noqa
