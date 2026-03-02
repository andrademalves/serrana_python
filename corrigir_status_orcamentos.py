"""
Script para corrigir status de orçamentos com espaço ' PENDENTE' → 'PENDENTE'
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from projetos.models import Orcamento

print("Corrigindo status de orçamentos...")

# Buscar orçamentos com status incorreto
orcamentos_com_espaco = Orcamento.objects.filter(status=' PENDENTE')
total = orcamentos_com_espaco.count()

if total > 0:
    print(f"Encontrados {total} orçamentos com status ' PENDENTE' (com espaço)")
    
    # Corrigir cada um
    for orc in orcamentos_com_espaco:
        print(f"  - Corrigindo orçamento {orc.codigo}...")
        orc.status = 'PENDENTE'
        orc.save()
    
    print(f"✅ {total} orçamentos corrigidos!")
else:
    print("✅ Nenhum orçamento com status incorreto encontrado.")

print("\nVerificando totais:")
print(f"  - PENDENTE: {Orcamento.objects.filter(status='PENDENTE').count()}")
print(f"  - APROVADO: {Orcamento.objects.filter(status='APROVADO').count()}")
print(f"  - REJEITADO: {Orcamento.objects.filter(status='REJEITADO').count()}")
print(f"  - CONVERTIDO: {Orcamento.objects.filter(status='CONVERTIDO').count()}")
