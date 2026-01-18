import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Empresa, UsuarioEmpresa

# Criar ou atualizar usuário marcos
user, created = User.objects.get_or_create(username='marcos')
user.set_password('123456')
user.save()

# Vincular à empresa ativa
empresa = Empresa.objects.filter(ativa=True).first()
vinculo_criado = False

if empresa:
    vinculo, vinculo_criado = UsuarioEmpresa.objects.get_or_create(
        usuario=user,
        empresa=empresa,
        defaults={
            'papel': 'Usuário',
            'ativo': True
        }
    )
    print(f"✅ Usuário 'marcos' {'criado' if created else 'atualizado'} com senha '123456'")
    print(f"✅ Vinculado à empresa: {empresa.nome_fantasia}")
else:
    print(f"✅ Usuário 'marcos' {'criado' if created else 'atualizado'} com senha '123456'")
    print("⚠️ Nenhuma empresa ativa encontrada para vincular")
