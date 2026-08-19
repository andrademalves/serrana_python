"""
Teste: Verificar se vendedores estão sendo buscados corretamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa

print("=" * 80)
print("TESTE: Busca de Vendedores para Filtro do Kanban")
print("=" * 80)

empresa = Empresa.objects.get(id=1)

# Simular o que a view faz
vendedores = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True
).order_by('nome')

print(f"\n📊 VENDEDORES ENCONTRADOS: {vendedores.count()}")
print("-" * 80)

for v in vendedores:
    usuario_info = f"✓ Usuário: {v.usuario.username}" if v.usuario else "✗ Sem usuário"
    print(f"ID: {v.id:2} | {v.nome:30} | {usuario_info}")

print("\n" + "=" * 80)
print("✅ RESULTADO ESPERADO NO SELECT:")
print("=" * 80)
print("""
<select name="vendedor">
    <option value="">Todos os vendedores</option>
""")

for v in vendedores:
    usuario_txt = f" ({v.usuario.username})" if v.usuario else ""
    print(f'    <option value="{v.id}">{v.nome}{usuario_txt}</option>')

print("""</select>
""")
print("=" * 80)
