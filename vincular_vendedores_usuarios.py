"""
Script para vincular vendedores (Pessoa) a usuários (User) existentes
Facilita atribuição de leads por vendedor
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from django.contrib.auth.models import User

print("=" * 80)
print("VINCULAR VENDEDORES A USUÁRIOS")
print("=" * 80)

# Listar vendedores
vendedores = Pessoa.objects.filter(vendedor=True, ativo=True)
usuarios = User.objects.all()

print(f"\n📊 Vendedores cadastrados: {vendedores.count()}")
print(f"📊 Usuários do sistema: {usuarios.count()}")

print("\n" + "-" * 80)
print("VINCULAR MANUALMENTE:")
print("-" * 80)

for v in vendedores:
    print(f"\n👤 Vendedor: {v.nome}")
    print(f"   Email: {v.email or 'N/A'}")
    print(f"   CPF/CNPJ: {v.cpf_cnpj}")
    print(f"   Usuário vinculado: {v.usuario.username if v.usuario else 'NENHUM'}")
    
    if not v.usuario:
        # Tentar encontrar usuário compatível por email
        if v.email:
            user = User.objects.filter(email__iexact=v.email).first()
            if user:
                print(f"   ✓ SUGESTÃO: Vincular ao usuário '{user.username}' (email: {user.email})")
                print(f"   >>> Para vincular, execute:")
                print(f"       pessoa = Pessoa.objects.get(id={v.id})")
                print(f"       pessoa.usuario_id = {user.id}")
                print(f"       pessoa.save()")

print("\n" + "=" * 80)
print("\n📋 INSTRUÇÕES:")
print("1. Para CRIAR um novo usuário para um vendedor:")
print("   - Acesse Usuários > Criar Usuário")
print("   - Depois vincule manualmente usando:")
print("     pessoa = Pessoa.objects.get(id=ID_DA_PESSOA)")
print("     pessoa.usuario_id = ID_DO_USUARIO")
print("     pessoa.save()")
print()
print("2. Para VINCULAR vendedor existente a usuário existente:")
print("   - Use os comandos sugeridos acima")
print("   - OU edite a pessoa no admin e selecione o usuário")
print()
print("=" * 80)
