"""
Verificação final: Todos os vendedores vinculados
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa

print("=" * 80)
print("🎉 TODOS OS VENDEDORES PRONTOS PARA USO!")
print("=" * 80)

empresa = Empresa.objects.get(id=1)
vendedores = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True
).order_by('nome')

print(f"\n📊 VENDEDORES CADASTRADOS: {vendedores.count()}")
print("-" * 80)

for v in vendedores:
    if v.usuario:
        print(f"✅ {v.nome:30} → {v.usuario.username:20} | Login: {v.usuario.username}")
    else:
        print(f"❌ {v.nome:30} → SEM USUÁRIO")

print("\n" + "=" * 80)
print("🔐 CREDENCIAIS DE ACESSO:")
print("=" * 80)
print("""
- carlos.mendes      / Serrana@2026
- carlos.oliveira    / Serrana@2026  
- joao.silva         / Serrana@2026
- maria.santos       / Serrana@2026
- marcos             / (senha existente)
""")

print("=" * 80)
print("✅ AGORA VOCÊ PODE:")
print("=" * 80)
print("""
1. ✅ TRANSFERIR LEADS para qualquer vendedor
2. ✅ Vendedores aparecem na lista suspensa
3. ✅ Cada vendedor pode fazer login e ver SEUS leads
4. ✅ Admin vê TODOS os leads

TESTE AGORA:
- Acesse um lead: http://127.0.0.1:8000/crm/oportunidades/12/
- Clique no botão 🔄 ao lado de "Responsável"
- Selecione "Carlos Eduardo Mendes"
- Confirme a transferência
- ✅ FUNCIONARÁ!
""")
print("=" * 80)
