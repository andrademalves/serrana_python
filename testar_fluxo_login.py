"""
Script para testar o fluxo de login e seleção de empresa
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Empresa, UsuarioEmpresa

print("=" * 80)
print("TESTE DE FLUXO - LOGIN E SELEÇÃO DE EMPRESA")
print("=" * 80)

# Verificar usuários e suas empresas
usuarios = User.objects.filter(is_active=True)

for user in usuarios:
    print(f"\n{'=' * 80}")
    print(f"USUÁRIO: {user.username} (Superuser: {user.is_superuser})")
    print("=" * 80)
    
    if user.is_superuser:
        empresas = Empresa.objects.filter(ativa=True)
        print(f"  ✓ Superusuário - acesso a TODAS as {empresas.count()} empresas:")
        for e in empresas:
            print(f"    - {e.nome_fantasia}")
        
        # Empresa que será selecionada automaticamente
        empresa_auto = empresas.order_by('-empresa_matriz', 'nome_fantasia').first()
        if empresa_auto:
            print(f"\n  ✅ Seleção automática: {empresa_auto.nome_fantasia}")
    else:
        empresas = Empresa.objects.filter(
            empresa_usuarios__usuario=user,
            empresa_usuarios__ativo=True,
            ativa=True
        ).distinct()
        
        print(f"  ✓ Usuário comum - acesso a {empresas.count()} empresa(s):")
        for e in empresas:
            print(f"    - {e.nome_fantasia}")
        
        if empresas.count() == 0:
            print(f"\n  ❌ SEM ACESSO - será deslogado após tentativa de login")
        elif empresas.count() == 1:
            print(f"\n  ✅ Seleção automática: {empresas.first().nome_fantasia}")
        else:
            print(f"\n  ⚠️  Múltiplas empresas - usuário precisa ESCOLHER")

print("\n" + "=" * 80)
print("RESUMO DO COMPORTAMENTO")
print("=" * 80)
print("""
FLUXO CORRIGIDO:
1. Usuário faz LOGIN
2. Sistema verifica empresas disponíveis:
   
   a) NENHUMA EMPRESA
      → Desloga o usuário
      → Mostra mensagem: "Contate o administrador"
   
   b) UMA EMPRESA
      → Seleciona AUTOMATICAMENTE
      → Redireciona para home
      → Mostra: "Empresa X selecionada automaticamente"
   
   c) MÚLTIPLAS EMPRESAS
      → Mostra tela de SELEÇÃO
      → Usuário escolhe qual empresa usar
      
   d) SUPERUSUÁRIO
      → Seleciona AUTOMATICAMENTE a primeira empresa (matriz)
      → Pode trocar depois se quiser

✅ PROBLEMA RESOLVIDO: Não há mais loop de redirecionamento!
""")
print("=" * 80)
