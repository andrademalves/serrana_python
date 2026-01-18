"""
Script para tornar marcos@mbrtecnologia.com.br superusuário
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User

username = 'marcos@mbrtecnologia.com.br'

print("=" * 80)
print(f"TORNANDO {username} SUPERUSUÁRIO")
print("=" * 80)

try:
    user = User.objects.get(username=username)
    
    print(f"\n✓ Usuário encontrado")
    print(f"\nStatus ANTES:")
    print(f"  - Superuser: {user.is_superuser}")
    print(f"  - Staff: {user.is_staff}")
    
    # Tornar superusuário e staff
    user.is_superuser = True
    user.is_staff = True
    user.save()
    
    print(f"\nStatus DEPOIS:")
    print(f"  - Superuser: {user.is_superuser}")
    print(f"  - Staff: {user.is_staff}")
    
    print(f"\n{'=' * 80}")
    print("✅ SUCESSO!")
    print("=" * 80)
    print(f"\n{username} agora tem:")
    print("  ✅ Acesso total ao sistema (superuser)")
    print("  ✅ Acesso ao painel admin (staff)")
    print("  ✅ Pode gerenciar empresas")
    print("  ✅ Pode criar/editar usuários")
    print("  ✅ Acesso a todos os módulos")
    
    print("\n⚠️  IMPORTANTE:")
    print("  Faça LOGOUT e LOGIN novamente no navegador!")
    print("=" * 80)
    
except User.DoesNotExist:
    print(f"\n❌ ERRO: Usuário '{username}' não encontrado!")
