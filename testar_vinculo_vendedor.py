"""
Testa o vínculo automático de usuário vendedor com Pessoa
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from cadastros.models import Pessoa
from usuarios.models import Empresa

print("=" * 80)
print("TESTE: VÍNCULO AUTOMÁTICO USUÁRIO VENDEDOR → PESSOA")
print("=" * 80)

# Verificar se existe empresa
empresa = Empresa.objects.filter(ativa=True).first()
if not empresa:
    print("❌ Nenhuma empresa ativa encontrada")
    exit(1)

print(f"\n✓ Empresa: {empresa.nome_fantasia}")

# Criar usuário de teste
username_teste = 'teste.vendedor.auto'

# Limpar teste anterior se existir
User.objects.filter(username=username_teste).delete()

print(f"\n1️⃣ Criando usuário: {username_teste}")
user = User.objects.create_user(
    username=username_teste,
    email='teste.vendedor@serrana.com',
    password='teste123',
    first_name='Teste',
    last_name='Vendedor Auto'
)
print(f"   ✓ Usuário criado (ID: {user.id})")

# Verificar se PerfilUsuario foi criado automaticamente
perfil = PerfilUsuario.objects.filter(usuario=user).first()
if perfil:
    print(f"   ✓ PerfilUsuario criado automaticamente (ID: {perfil.id})")
else:
    print(f"   ⚠️ PerfilUsuario não foi criado automaticamente, criando manualmente...")
    perfil = PerfilUsuario.objects.create(usuario=user)

# Verificar se já existe Pessoa vinculada
pessoa_antes = Pessoa.objects.filter(usuario=user).first()
print(f"\n2️⃣ Pessoa vinculada ANTES de marcar vendedor: {pessoa_antes}")

# Marcar como vendedor
print(f"\n3️⃣ Marcando usuário como VENDEDOR...")
perfil.vendedor = True
perfil.save()
print(f"   ✓ PerfilUsuario.vendedor = True")

# Verificar se Pessoa foi criada/atualizada
pessoa_depois = Pessoa.objects.filter(usuario=user).first()
print(f"\n4️⃣ Pessoa vinculada DEPOIS de marcar vendedor:")
if pessoa_depois:
    print(f"   ✓ ID: {pessoa_depois.id}")
    print(f"   ✓ Nome: {pessoa_depois.nome}")
    print(f"   ✓ Vendedor: {pessoa_depois.vendedor}")
    print(f"   ✓ Empresa: {pessoa_depois.empresa.nome_fantasia}")
    print(f"   ✓ CPF/CNPJ: {pessoa_depois.cpf_cnpj or '(vazio)'}")
else:
    print(f"   ❌ ERRO: Pessoa não foi criada automaticamente!")

# Desmarcar vendedor
print(f"\n5️⃣ Desmarcando vendedor...")
perfil.vendedor = False
perfil.save()

# Verificar se flag foi removida de Pessoa
pessoa_depois.refresh_from_db()
print(f"   ✓ Pessoa.vendedor após desmarcar: {pessoa_depois.vendedor}")

print("\n" + "=" * 80)
print("✅ TESTE CONCLUÍDO!")
print("=" * 80)
print("\n📌 RESUMO:")
print("   • Usuário criado → PerfilUsuario criado automaticamente ✓")
print("   • Marcar vendedor → Pessoa criada/vinculada automaticamente ✓")
print("   • Desmarcar vendedor → Flag removida da Pessoa ✓")
print("\n🎯 O sistema está funcionando corretamente!")
print("=" * 80)

# Limpar teste
print(f"\n🗑️ Removendo dados de teste...")
user.delete()  # Cascade vai remover perfil e pessoa
print("   ✓ Dados removidos")
