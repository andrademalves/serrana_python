import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from cadastros.models import Pessoa

# Criar cliente de teste
cliente = Pessoa.objects.create(
    tipo='CLIENTE',
    nome='Cliente Teste Orçamento',
    cpf_cnpj='12345678901',
    telefone='(11) 98765-4321',
    email='cliente@teste.com',
    ativo=True
)

print(f"✅ Cliente criado: ID {cliente.id} - {cliente.nome}")
