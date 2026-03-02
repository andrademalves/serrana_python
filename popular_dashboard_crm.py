"""
Script para popular dados de exemplo no Dashboard CRM
Cria metas mensais e atualiza valores previstos nas oportunidades
"""
import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from crm.models import Oportunidade, MetaVendedor, EtapaFunil, EtapaFunilConfig
from usuarios.models import Empresa


def popular_dados_exemplo():
    """Popula dados de exemplo para o Dashboard CRM"""
    
    print("=" * 70)
    print("POPULANDO DADOS DE EXEMPLO - DASHBOARD CRM")
    print("=" * 70)
    
    # Empresa ativa
    try:
        empresa = Empresa.objects.filter(ativa=True).first()
        if not empresa:
            raise Empresa.DoesNotExist
        print(f"\n✓ Empresa ativa: {empresa.nome_fantasia}")
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        return
    
    # ========== 1. CONFIGURAR PROBABILIDADES DAS ETAPAS ==========
    print("\n" + "=" * 70)
    print("1. CONFIGURANDO PROBABILIDADES DAS ETAPAS")
    print("=" * 70)
    
    probabilidades = {
        'Primeiro Contato': 20,
        'Qualificado': 35,
        'Proposta': 60,
        'Negociação': 80,
        'Fechado - Ganho': 100,
        'Fechado - Perdido': 0,
    }
    
    etapas = EtapaFunil.objects.filter(pipeline__empresa=empresa)
    
    for etapa in etapas:
        prob = probabilidades.get(etapa.nome, 50)
        config, created = EtapaFunilConfig.objects.get_or_create(
            etapa=etapa,
            defaults={'probabilidade_padrao': prob, 'sla_dias': 7}
        )
        if created:
            print(f"   Criada configuração: {etapa.nome} - {prob}% probabilidade")
        else:
            if config.probabilidade_padrao != prob:
                config.probabilidade_padrao = prob
                config.save()
                print(f"   Atualizada configuração: {etapa.nome} - {prob}% probabilidade")
    
    # ========== 2. ATUALIZAR VALORES PREVISTOS NAS OPORTUNIDADES ==========
    print("\n" + "=" * 70)
    print("2. ATUALIZANDO VALORES PREVISTOS NAS OPORTUNIDADES")
    print("=" * 70)
    
    oportunidades = Oportunidade.objects.filter(empresa=empresa)
    
    for opp in oportunidades:
        # Usar valor_estimado se já existir, caso contrário gerar aleatório
        if opp.valor_estimado:
            opp.valor_previsto = opp.valor_estimado
        else:
            # Gerar valor aleatório razoável
            import random
            opp.valor_previsto = Decimal(random.randint(5000, 100000))
            opp.valor_estimado = opp.valor_previsto
        
        # Se já está fechado, copiar para valor_fechado
        if opp.status == 'ganho' and not opp.valor_fechado:
            opp.valor_fechado = opp.valor_previsto
        
        # Definir probabilidade baseada na etapa
        try:
            config = opp.etapa.config
            opp.probabilidade_conversao = config.probabilidade_padrao
        except EtapaFunilConfig.DoesNotExist:
            opp.probabilidade_conversao = 50
        
        opp.save()
        
        print(f"   {opp.titulo}: R$ {opp.valor_previsto:,.2f} ({opp.probabilidade_conversao}%)")
    
    print(f"\n✓ Total de {oportunidades.count()} oportunidades atualizadas")
    
    # ========== 3. CRIAR METAS MENSAIS PARA VENDEDORES ==========
    print("\n" + "=" * 70)
    print("3. CRIANDO METAS MENSAIS PARA VENDEDORES")
    print("=" * 70)
    
    # Pegar todos os usuários que são responsáveis por oportunidades
    vendedores = User.objects.filter(
        oportunidades_responsavel__empresa=empresa
    ).distinct()
    
    hoje = date.today()
    
    for vendedor in vendedores:
        # Criar meta para o mês atual
        meta, created = MetaVendedor.objects.get_or_create(
            empresa=empresa,
            vendedor=vendedor,
            mes=hoje.month,
            ano=hoje.year,
            defaults={
                'meta_valor': Decimal('100000.00'),  # R$ 100k
                'meta_quantidade': 5,  # 5 negócios
                'ativo': True,
                'observacoes': 'Meta gerada automaticamente pelo script de exemplo'
            }
        )
        
        if created:
            print(f"   ✓ Meta criada para {vendedor.get_full_name() or vendedor.username}:")
            print(f"     - Valor: R$ 100.000,00")
            print(f"     - Quantidade: 5 negócios")
        else:
            print(f"   • Meta já existe para {vendedor.get_full_name() or vendedor.username}")
    
    # ========== 4. RESUMO ==========
    print("\n" + "=" * 70)
    print("RESUMO DOS DADOS")
    print("=" * 70)
    
    print(f"\n📊 Estatísticas:")
    print(f"   - Etapas configuradas: {EtapaFunilConfig.objects.count()}")
    print(f"   - Oportunidades com valor previsto: {Oportunidade.objects.filter(empresa=empresa, valor_previsto__isnull=False).count()}")
    print(f"   - Metas mensais cadastradas: {MetaVendedor.objects.filter(empresa=empresa, mes=hoje.month, ano=hoje.year).count()}")
    print(f"   - Vendedores ativos: {vendedores.count()}")
    
    # Cálculo de previsão
    opp_abertas = Oportunidade.objects.filter(
        empresa=empresa,
        status__in=['aberto', 'em_andamento']
    )
    
    receita_potencial = sum(opp.valor_previsto or 0 for opp in opp_abertas)
    receita_provavel = sum(
        Decimal(str(opp.valor_previsto or 0)) * Decimal(str(opp.probabilidade_conversao)) / Decimal('100')
        for opp in opp_abertas
    )
    
    print(f"\n💰 Previsão de Faturamento:")
    print(f"   - Receita Potencial: R$ {receita_potencial:,.2f}")
    print(f"   - Receita Provável: R$ {receita_provavel:,.2f}")
    
    print("\n" + "=" * 70)
    print("✓ DADOS POPULADOS COM SUCESSO!")
    print("=" * 70)
    print("\n🎯 Próximos passos:")
    print("   1. Acesse: http://127.0.0.1:8000/crm/dashboard/")
    print("   2. Explore os gráficos e indicadores")
    print("   3. Teste os filtros por data e vendedor (se admin)")
    print("   4. Verifique o ranking de vendedores")
    print("   5. Analise a previsão de faturamento")
    print("\n")


if __name__ == '__main__':
    popular_dados_exemplo()
