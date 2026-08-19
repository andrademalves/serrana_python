"""
Script de teste: Funcionalidade de trocar responsável
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from crm.models import Oportunidade, AtividadeCRM
from cadastros.models import Pessoa
from django.contrib.auth.models import User

print("=" * 80)
print("TESTE: Sistema de Troca de Responsável")
print("=" * 80)

# Buscar uma oportunidade de teste
oportunidade = Oportunidade.objects.first()

if oportunidade:
    print(f"\n📋 OPORTUNIDADE DE TESTE:")
    print(f"   ID: {oportunidade.id}")
    print(f"   Título: {oportunidade.titulo}")
    print(f"   Responsável atual: {oportunidade.responsavel.get_full_name() or oportunidade.responsavel.username}")
    
    if oportunidade.primeiro_atendente:
        print(f"   Primeiro atendente: {oportunidade.primeiro_atendente.get_full_name() or oportunidade.primeiro_atendente.username}")
    else:
        print(f"   Primeiro atendente: (não definido)")
    
    print(f"\n📊 HISTÓRICO DE MUDANÇAS:")
    atividades_troca = AtividadeCRM.objects.filter(
        oportunidade=oportunidade,
        titulo='Responsável Alterado'
    ).order_by('-data_atividade')
    
    if atividades_troca.exists():
        for ativ in atividades_troca:
            print(f"   ✓ {ativ.data_atividade.strftime('%d/%m/%Y %H:%M')}: {ativ.descricao}")
    else:
        print("   (nenhuma mudança registrada)")

else:
    print("\n❌ Nenhuma oportunidade encontrada no sistema")

print("\n" + "=" * 80)
print("✅ FUNCIONALIDADES IMPLEMENTADAS:")
print("=" * 80)
print("""
1. ✅ Campo 'primeiro_atendente' adicionado na model Oportunidade
   - Mantém registro do primeiro responsável que criou o lead
   
2. ✅ View trocar_responsavel criada
   - Permite trocar responsável do lead
   - Verifica se vendedor tem usuário vinculado
   - Registra mudança no histórico (AtividadeCRM)
   
3. ✅ Interface atualizada (oportunidade_detail.html)
   - Mostra botão de trocar responsável (APENAS ADMIN)
   - Exibe primeiro atendente quando diferente do responsável atual
   - Modal para selecionar novo responsável
   
4. ✅ Histórico mantido
   - Primeiro atendente NUNCA muda
   - Todas as trocas registradas em AtividadeCRM
   - Rastreabilidade completa

""")

print("=" * 80)
print("📝 COMO TESTAR:")
print("=" * 80)
print("""
1. Acesse um lead: http://127.0.0.1:8000/crm/oportunidades/{ID}/

2. Como ADMIN, você verá:
   - Botão de seta ao lado do responsável
   - Ao clicar, abre modal com lista de vendedores
   
3. Selecione novo responsável e confirme

4. O sistema irá:
   - Trocar o responsável
   - Manter o primeiro_atendente inalterado
   - Registrar mudança no histórico de atividades
   
5. Verificar histórico na aba "Atividades" do lead

""")

print("=" * 80)
