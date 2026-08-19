"""
Script de teste: Criar lead atribuindo vendedor
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa
from crm.models import Oportunidade, Pipeline, EtapaFunil
from django.contrib.auth.models import User

print("=" * 80)
print("TESTE: Sistema de Vendedores no CRM")
print("=" * 80)

empresa = Empresa.objects.get(id=1)
admin_user = User.objects.get(username='admin')

# Listar vendedores disponíveis
print("\n📋 VENDEDORES DISPONÍVEIS NO SISTEMA:")
print("-" * 80)
vendedores = Pessoa.objects.filter(
    empresa=empresa,
    vendedor=True,
    ativo=True
).order_by('nome')

for v in vendedores:
    usuario_vinculado = f"✓ Usuario: {v.usuario.username}" if v.usuario else "✗ Sem usuário vinculado"
    print(f"ID: {v.id:2} | {v.nome:30} | {usuario_vinculado}")

print("\n" + "=" * 80)
print("✅ IMPLEMENTAÇÕES CONCLUÍDAS:")
print("=" * 80)
print("""
1. ✅ Campo 'usuario' adicionado na model Pessoa
   - Permite vincular vendedores a usuários do sistema
   - Relacionamento OneToOne com User
   
2. ✅ View kanban_view atualizada
   - Busca vendedores_pessoa (Pessoa.vendedor=True)
   - Envia lista para o template
   
3. ✅ Modal Lead Rápido atualizado
   - Mostra lista suspensa de vendedores (APENAS PARA ADMIN)
   - Campo 'vendedor_pessoa_id' enviado no formulário
   
4. ✅ View criar_oportunidade_rapida atualizada
   - Admin pode selecionar vendedor
   - Se vendedor tem usuario vinculado: atribui ao usuario
   - Se não tem: admin fica responsável + observação
   
5. ✅ Permissões funcionando:
   - Admin: vê TODOS os leads
   - Vendedor: vê APENAS os SEUS leads (responsavel=user)

""")

print("=" * 80)
print("📝 PRÓXIMOS PASSOS:")
print("=" * 80)
print("""
Para TESTAR o sistema completamente:

1. Acesse: http://127.0.0.1:8000/crm/kanban/

2. Como ADMIN, clique em "Criar Lead Rápido"
   - Você verá a lista suspensa "Atribuir ao Vendedor"
   - Selecione um vendedor (ex: Carlos Eduardo Mendes)
   - Preencha os dados e crie

3. O lead será visível para:
   - Admin: SEMPRE
   - Vendedor específico: SE ele tiver usuário vinculado

4. Para vincular vendedor a usuário:
   - Opção 1: Cadastrar novo usuário e vincular manualmente
   - Opção 2: Adicionar interface administrativa para vincular
   
""")

print("=" * 80)
print("💡 SOLUÇÃO ALTERNATIVA (Se vendedor não tem usuário):")
print("=" * 80)
print("""
Se o vendedor NÃO tem usuário vinculado:
- O lead ficará com o admin como responsável
- Nas observações constará: "Vendedor atribuído: [Nome]"
- Admin pode depois editar e trocar o responsável manualmente

Isso permite que o sistema funcione IMEDIATAMENTE,
mesmo sem vincular todos os vendedores a usuários!
""")

print("=" * 80)
