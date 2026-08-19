"""
Script para preparar migração com empresa default
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from usuarios.models import Empresa

# Verificar se existe pelo menos uma empresa
empresa_default = Empresa.objects.first()

if empresa_default:
    print(f"✅ Empresa padrão encontrada: ID={empresa_default.id}, Razão Social={empresa_default.razao_social}")
    print(f"\nVocê pode usar este ID ({empresa_default.id}) como default nas migrations.\n")
else:
    print("❌ ATENÇÃO: Nenhuma empresa cadastrada no sistema!")
    print("Você precisa criar uma empresa antes de executar as migrations.")
    print("\nDeseja criar uma empresa padrão agora? (S/N)")
    
    resposta = input().upper()
    
    if resposta == 'S':
        print("\nCriando empresa padrão...")
        empresa = Empresa.objects.create(
            razao_social='Empresa Padrão LTDA',
            nome_fantasia='Empresa Padrão',
            cnpj='00000000000000',
            ativo=True
        )
        print(f"✅ Empresa criada com sucesso! ID={empresa.id}")
    else:
        print("❌ Operação cancelada. Crie uma empresa antes de prosseguir.")
        sys.exit(1)
