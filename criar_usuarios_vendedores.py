"""
Script para criar usuários para todos os vendedores automaticamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from django.contrib.auth.models import User
from usuarios.models import Empresa

print("=" * 80)
print("CRIAR USUÁRIOS PARA VENDEDORES")
print("=" * 80)

empresa = Empresa.objects.get(id=1)

# Mapeamento vendedor -> usuário
vendedores_config = {
    'Carlos Eduardo Mendes': {
        'username': 'carlos.mendes',
        'email': 'carlos.mendes@serrana.com',
        'first_name': 'Carlos Eduardo',
        'last_name': 'Mendes',
    },
    'Carlos Oliveira': {
        'username': 'carlos.oliveira',
        'email': 'carlos.oliveira@serrana.com',
        'first_name': 'Carlos',
        'last_name': 'Oliveira',
    },
    'João Silva': {
        'username': 'joao.silva',
        'email': 'joao.silva@serrana.com',
        'first_name': 'João',
        'last_name': 'Silva',
    },
    'Maria Santos': {
        'username': 'maria.santos',
        'email': 'maria.santos@serrana.com',
        'first_name': 'Maria',
        'last_name': 'Santos',
    },
}

print("\n📝 CRIANDO USUÁRIOS E VINCULANDO...")
print("-" * 80)

for nome_vendedor, config in vendedores_config.items():
    # Buscar vendedor
    vendedor = Pessoa.objects.filter(
        nome__icontains=nome_vendedor,
        empresa=empresa,
        vendedor=True
    ).first()
    
    if not vendedor:
        print(f"⚠️  Vendedor '{nome_vendedor}' não encontrado, pulando...")
        continue
    
    # Verificar se já tem usuário
    if vendedor.usuario:
        print(f"✓ {vendedor.nome:30} | Já vinculado a: {vendedor.usuario.username}")
        continue
    
    # Criar ou buscar usuário
    usuario, created = User.objects.get_or_create(
        username=config['username'],
        defaults={
            'email': config['email'],
            'first_name': config['first_name'],
            'last_name': config['last_name'],
        }
    )
    
    if created:
        # Definir senha padrão
        usuario.set_password('Serrana@2026')
        usuario.save()
        print(f"✓ Usuário '{usuario.username}' criado com senha: Serrana@2026")
    
    # Vincular vendedor ao usuário
    vendedor.usuario = usuario
    vendedor.save()
    
    print(f"✓ {vendedor.nome:30} | Vinculado a: {usuario.username}")

print("\n" + "=" * 80)
print("✅ CONCLUÍDO!")
print("=" * 80)

# Verificar resultado
print("\n📊 VENDEDORES COM USUÁRIO VINCULADO:")
print("-" * 80)
vendedores = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True
).order_by('nome')

for v in vendedores:
    if v.usuario:
        print(f"✓ {v.nome:30} | Usuário: {v.usuario.username:20} | Senha: Serrana@2026")
    else:
        print(f"✗ {v.nome:30} | SEM USUÁRIO VINCULADO")

print("\n" + "=" * 80)
print("🎉 AGORA VOCÊ PODE TRANSFERIR LEADS PARA QUALQUER VENDEDOR!")
print("=" * 80)
print("""
CREDENCIAIS CRIADAS:
- carlos.mendes / Serrana@2026
- carlos.oliveira / Serrana@2026
- joao.silva / Serrana@2026
- maria.santos / Serrana@2026

⚠️  IMPORTANTE: Alterar senhas no primeiro login!
""")
print("=" * 80)
