import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa
from usuarios.models import Empresa

print("=" * 60)
print("TESTANDO EDIÇÃO DE PESSOA")
print("=" * 60)

# Buscar primeira pessoa
pessoa = Pessoa.objects.first()

if not pessoa:
    print("❌ Nenhuma pessoa encontrada no banco!")
    
    # Criar uma pessoa de teste
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ Nenhuma empresa encontrada!")
        exit(1)
    
    pessoa = Pessoa.objects.create(
        empresa=empresa,
        tipo='F',
        nome='TESTE PESSOA',
        cpf_cnpj='12345678900',
        cliente=True
    )
    print(f"✓ Pessoa de teste criada: {pessoa.nome}")

print(f"\n📋 Pessoa encontrada:")
print(f"   ID: {pessoa.id}")
print(f"   Nome: {pessoa.nome}")
print(f"   Tipo: {pessoa.get_tipo_display()}")
print(f"   CPF/CNPJ: {pessoa.cpf_cnpj}")
print(f"   Cliente: {pessoa.cliente}")
print(f"   Fornecedor: {pessoa.fornecedor}")
print(f"   Funcionário: {pessoa.funcionario}")

# Testar atualização
print(f"\n🔧 Testando atualização...")
try:
    pessoa.nome = "TESTE ATUALIZADO"
    pessoa.save()
    print("✅ Atualização bem-sucedida!")
except Exception as e:
    print(f"❌ Erro ao atualizar: {e}")

# Verificar campos obrigatórios
print(f"\n📝 Verificando campos obrigatórios do modelo:")
print(f"   - tipo: {'✓ OK' if pessoa.tipo else '❌ FALTA'}")
print(f"   - nome: {'✓ OK' if pessoa.nome else '❌ FALTA'}")
print(f"   - empresa: {'✓ OK' if pessoa.empresa else '❌ FALTA'}")

print(f"\n🔗 URL de edição: http://127.0.0.1:8000/cadastros/pessoas/{pessoa.id}/editar/")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
print("\nPróximos passos:")
print("1. Acesse a URL acima no navegador")
print("2. Preencha Nome e CPF/CNPJ")
print("3. Clique em Salvar")
print("4. Verifique se aparece a mensagem de sucesso")
print("5. Verifique se redireciona para a lista de pessoas")
