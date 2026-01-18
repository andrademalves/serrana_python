"""
Script para corrigir vínculos de usuários com empresas
Vincula usuários sem empresa à primeira empresa disponível
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Empresa, UsuarioEmpresa

print("=" * 80)
print("CORRIGINDO VÍNCULOS DE USUÁRIOS SEM EMPRESA")
print("=" * 80)

# Buscar todos os usuários
usuarios = User.objects.filter(is_active=True)

# Buscar empresa padrão (primeira ativa)
empresa_padrao = Empresa.objects.filter(ativa=True).first()

if not empresa_padrao:
    print("❌ ERRO: Nenhuma empresa ativa encontrada!")
    print("   Cadastre uma empresa primeiro no Admin.")
    exit(1)

print(f"\n✓ Empresa padrão selecionada: {empresa_padrao.nome_fantasia}")

vinculos_criados = 0
usuarios_ja_vinculados = 0

for usuario in usuarios:
    # Verificar se usuário já tem vínculo ativo com alguma empresa
    if UsuarioEmpresa.objects.filter(usuario=usuario, ativo=True).exists():
        usuarios_ja_vinculados += 1
        print(f"  ✓ {usuario.username} - Já possui vínculo")
    else:
        # Criar vínculo com empresa padrão
        UsuarioEmpresa.objects.create(
            usuario=usuario,
            empresa=empresa_padrao,
            ativo=True,
            papel='Usuário'
        )
        vinculos_criados += 1
        print(f"  ✅ {usuario.username} - Vínculo criado com {empresa_padrao.nome_fantasia}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"  Usuários já vinculados: {usuarios_ja_vinculados}")
print(f"  Novos vínculos criados: {vinculos_criados}")
print(f"  Total de usuários: {usuarios.count()}")
print("=" * 80)
print("\n✅ Todos os usuários agora têm acesso a uma empresa!")
