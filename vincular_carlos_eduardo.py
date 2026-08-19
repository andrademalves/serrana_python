"""
Script para vincular vendedor Carlos Eduardo Mendes a um usuário
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from django.contrib.auth.models import User
from usuarios.models import Empresa

print("=" * 80)
print("VINCULAR VENDEDORES A USUÁRIOS")
print("=" * 80)

empresa = Empresa.objects.get(id=1)

# Listar vendedores sem usuário vinculado
print("\n📋 VENDEDORES SEM USUÁRIO VINCULADO:")
print("-" * 80)
vendedores_sem_usuario = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True,
    usuario__isnull=True
)

for v in vendedores_sem_usuario:
    print(f"ID: {v.id:2} | {v.nome:30} | Email: {v.email or 'N/A'}")

# Listar usuários disponíveis
print("\n👥 USUÁRIOS DISPONÍVEIS NO SISTEMA:")
print("-" * 80)
usuarios = User.objects.all()
for u in usuarios:
    pessoa_vinculada = hasattr(u, 'pessoa') and u.pessoa
    status = f"✓ Vinculado a: {u.pessoa.nome}" if pessoa_vinculada else "✗ Disponível"
    print(f"ID: {u.id} | {u.username:20} | {u.get_full_name() or '(sem nome)':25} | {status}")

print("\n" + "=" * 80)
print("🔧 OPÇÕES:")
print("=" * 80)
print("""
OPÇÃO 1: Criar novo usuário para Carlos Eduardo Mendes
---------------------------------------------------------
1. No Django Admin ou interface de usuários, crie um novo usuário:
   - Username: carlos.mendes
   - Email: (preencha se tiver)
   - Nome completo: Carlos Eduardo Mendes
   
2. Execute este código para vincular:
   pessoa = Pessoa.objects.get(nome__icontains='Carlos Eduardo')
   usuario = User.objects.get(username='carlos.mendes')
   pessoa.usuario = usuario
   pessoa.save()

OPÇÃO 2: Vincular a um usuário existente
---------------------------------------------------------
Se já existe um usuário que representa Carlos Eduardo, execute:
   pessoa = Pessoa.objects.get(id=4)  # ID do Carlos Eduardo Mendes
   pessoa.usuario_id = [ID_DO_USUARIO]
   pessoa.save()

OPÇÃO 3: Executar automaticamente (se quiser criar usuário agora)
---------------------------------------------------------
""")

resposta = input("\nDeseja criar usuário 'carlos.mendes' automaticamente? (s/n): ")

if resposta.lower() == 's':
    # Verificar se já existe
    if User.objects.filter(username='carlos.mendes').exists():
        print("❌ Usuário 'carlos.mendes' já existe!")
        usuario = User.objects.get(username='carlos.mendes')
    else:
        # Criar usuário
        usuario = User.objects.create_user(
            username='carlos.mendes',
            email='carlos.mendes@serrana.com',
            password='Temp@123',  # Senha temporária
            first_name='Carlos Eduardo',
            last_name='Mendes'
        )
        print(f"✅ Usuário '{usuario.username}' criado com sucesso!")
        print(f"   Senha temporária: Temp@123")
        print(f"   ⚠️  ALTERAR SENHA NO PRIMEIRO LOGIN!")
    
    # Vincular ao vendedor
    carlos = Pessoa.objects.get(nome__icontains='Carlos Eduardo')
    carlos.usuario = usuario
    carlos.save()
    
    print(f"\n✅ Vendedor '{carlos.nome}' vinculado ao usuário '{usuario.username}'!")
    print("\n🎉 PRONTO! Agora você pode transferir leads para Carlos Eduardo Mendes!")
else:
    print("\nOk, use uma das opções manuais acima.")

print("\n" + "=" * 80)
