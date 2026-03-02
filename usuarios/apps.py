from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Gestão de Usuários'
    
    def ready(self):
        # Importa signals para sincronizar usuários vendedores com Pessoa
        import usuarios.signals
