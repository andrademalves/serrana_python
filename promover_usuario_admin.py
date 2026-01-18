"""
Script para dar permissões administrativas ao usuário marcos@mbrtecnologia.com.br
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PermissaoMenu, Menu

print("=" * 80)
print("CONFIGURANDO PERMISSÕES ADMINISTRATIVAS")
print("=" * 80)

username = 'marcos@mbrtecnologia.com.br'

try:
    user = User.objects.get(username=username)
    
    print(f"\n✓ Usuário encontrado: {user.username}")
    print(f"  Status atual:")
    print(f"    - Superuser: {user.is_superuser}")
    print(f"    - Staff: {user.is_staff}")
    print(f"    - Ativo: {user.is_active}")
    
    # Tornar o usuário staff (pode acessar admin)
    if not user.is_staff:
        user.is_staff = True
        user.save()
        print(f"\n  ✅ Usuário promovido a STAFF")
    
    # Verificar se tem permissões para o módulo Sistema
    sistema_modulo = Menu.objects.filter(modulo__nome__icontains='sistema', ativo=True)
    
    print(f"\n=== MÓDULO SISTEMA ===")
    print(f"  Menus encontrados: {sistema_modulo.count()}")
    
    for menu in sistema_modulo:
        perm, created = PermissaoMenu.objects.update_or_create(
            tipo='usuario',
            usuario=user,
            menu=menu,
            defaults={
                'pode_visualizar': True,
                'pode_criar': True,
                'pode_editar': True,
                'pode_excluir': True,
            }
        )
        
        status = "✅ Criada" if created else "🔄 Atualizada"
        print(f"    {status}: {menu.nome} ({menu.url})")
    
    print(f"\n{'=' * 80}")
    print("SOLUÇÃO ALTERNATIVA")
    print("=" * 80)
    print("\nComo as views de empresa verificam 'is_superuser', você tem 2 opções:")
    print("\n1. TORNAR SUPERUSUÁRIO (acesso total):")
    print("   Execute no shell: ")
    print(f"   >>> from django.contrib.auth.models import User")
    print(f"   >>> u = User.objects.get(username='{username}')")
    print(f"   >>> u.is_superuser = True")
    print(f"   >>> u.save()")
    
    print("\n2. MODIFICAR AS VIEWS (recomendado):")
    print("   Alterar verificação de 'is_superuser' para 'is_staff'")
    print("   nas views de empresas")
    
    print("\n" + "=" * 80)
    print("APLICANDO SOLUÇÃO 1 (TORNAR SUPERUSUÁRIO)")
    print("=" * 80)
    
    resposta = input("\nTornar o usuário SUPERUSUÁRIO? (s/n): ").strip().lower()
    
    if resposta == 's':
        user.is_superuser = True
        user.save()
        print(f"\n✅ {username} agora é SUPERUSUÁRIO!")
        print("   Tem acesso total ao sistema")
    else:
        print("\n⚠️  Usuário NÃO promovido a superusuário")
        print("   As views de empresa ainda estarão bloqueadas")
        print("   Considere modificar as views para aceitar 'is_staff'")
    
    print("\n" + "=" * 80)
    print("STATUS FINAL")
    print("=" * 80)
    
    user.refresh_from_db()
    print(f"\nUsuário: {user.username}")
    print(f"  - Superuser: {user.is_superuser}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Ativo: {user.is_active}")
    
    print("\n✅ Configuração concluída!")
    print("   Faça logout e login novamente para aplicar as mudanças")
    print("=" * 80)
    
except User.DoesNotExist:
    print(f"\n❌ Usuário '{username}' não encontrado!")
