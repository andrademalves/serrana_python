"""
Vincular MARCOS ALVES DE ANDRADE ao usuário marcos existente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from django.contrib.auth.models import User

# Buscar vendedor Marcos
marcos_vendedor = Pessoa.objects.get(nome__icontains='MARCOS ALVES')
print(f"Vendedor encontrado: {marcos_vendedor.nome}")

# Buscar usuário marcos
marcos_usuario = User.objects.get(username='marcos')
print(f"Usuário encontrado: {marcos_usuario.username} ({marcos_usuario.get_full_name()})")

# Vincular
marcos_vendedor.usuario = marcos_usuario
marcos_vendedor.save()

print(f"\n✅ {marcos_vendedor.nome} vinculado ao usuário '{marcos_usuario.username}'!")
