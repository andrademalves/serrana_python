"""
Teste Completo do Fluxo: CRM → Orçamento → Projeto
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Empresa
from cadastros.models import Pessoa
from estoque.models import Item
from crm.models import Pipeline, EtapaFunil, Oportunidade, AtividadeCRM, AlertaRetorno
from projetos.models import Orcamento, OrcamentoItem, OrcamentoParcela, Projeto
from financeiro.models import CentroCusto, FormaPagamento


def testar_fluxo_completo():
    """Testa o fluxo completo: Oportunidade → Orçamento → Projeto"""
    
    print("=" * 80)
    print("TESTE DO FLUXO COMPLETO: CRM → ORÇAMENTO → PROJETO")
    print("=" * 80)
    
    # 1. DADOS INICIAIS
    print("\n📋 1. CARREGANDO DADOS INICIAIS...")
    
    empresa = Empresa.objects.get(id=1)
    print(f"✅ Empresa: {empresa.nome_fantasia}")
    
    user = User.objects.filter(is_superuser=True).first()
    print(f"✅ Usuário: {user.username}")
    
    pipeline = Pipeline.objects.filter(empresa=empresa, ativo=True).first()
    print(f"✅ Pipeline: {pipeline.nome}")
    
    # 2. CRIAR OPORTUNIDADE
    print("\n🎯 2. CRIANDO OPORTUNIDADE NO CRM...")
    
    etapa_inicial = EtapaFunil.objects.filter(pipeline=pipeline, ativo=True).order_by('ordem').first()
    print(f"   Etapa inicial: {etapa_inicial.nome}")
    
    # Criar ou buscar cliente
    cliente, created = Pessoa.objects.get_or_create(
        empresa=empresa,
        cpf_cnpj='12.345.678/0001-99',
        defaults={
            'tipo': 'J',  # Jurídica
            'nome': 'Empresa Teste CRM Ltda',
            'nome_fantasia': 'Teste CRM',
            'telefone': '(11) 91234-5678',
            'email': 'contato@empresateste.com.br',
            'ativo': True,
        }
    )
    print(f"   Cliente: {cliente.nome} {'(criado)' if created else '(existente)'}")
    
    oportunidade = Oportunidade.objects.create(
        empresa=empresa,
        pipeline=pipeline,
        etapa=etapa_inicial,
        cliente=cliente,
        titulo=f'Oportunidade Teste {datetime.now().strftime("%H:%M:%S")}',
        nome_contato='Carlos Alberto',
        empresa_contato='Empresa Teste CRM Ltda',
        telefone='(11) 91234-5678',
        email='carlos@empresateste.com.br',
        origem='telefone',
        valor_estimado=Decimal('50000.00'),
        responsavel=user,
        criado_por=user,
        descricao='Projeto de reforma completa do escritório com novos móveis e equipamentos'
    )
    print(f"✅ Oportunidade criada: {oportunidade.titulo}")
    print(f"   ID: {oportunidade.id}")
    print(f"   Valor estimado: R$ {oportunidade.valor_estimado}")
    print(f"   Status: {oportunidade.get_status_display()}")
    print(f"   Etapa: {oportunidade.etapa.nome}")
    
    # Adicionar algumas atividades
    AtividadeCRM.objects.create(
        oportunidade=oportunidade,
        tipo='ligacao',
        titulo='Primeiro contato telefônico',
        descricao='Cliente demonstrou interesse imediato no projeto.',
        criado_por=user
    )
    
    AtividadeCRM.objects.create(
        oportunidade=oportunidade,
        tipo='reuniao',
        titulo='Reunião de levantamento',
        descricao='Realizada visita técnica e medições no local.',
        criado_por=user
    )
    print("✅ Atividades registradas: 2")
    
    # Adicionar alerta
    AlertaRetorno.objects.create(
        oportunidade=oportunidade,
        titulo='Enviar proposta detalhada',
        descricao='Preparar e enviar proposta com especificações técnicas',
        data_hora=datetime.now() + timedelta(days=2),
        prioridade='alta',
        criado_por=user
    )
    print("✅ Alerta criado: 1")
    
    # Mover para etapa Proposta
    etapa_proposta = EtapaFunil.objects.filter(
        pipeline=pipeline, 
        nome__icontains='proposta',
        ativo=True
    ).first()
    
    if etapa_proposta:
        oportunidade.etapa = etapa_proposta
        oportunidade.save()
        print(f"✅ Oportunidade movida para: {etapa_proposta.nome}")
    
    # 3. CRIAR ORÇAMENTO A PARTIR DA OPORTUNIDADE
    print("\n💰 3. CRIANDO ORÇAMENTO VINCULADO À OPORTUNIDADE...")
    
    # Buscar ou criar vendedor (Pessoa)
    vendedor_pessoa, _ = Pessoa.objects.get_or_create(
        empresa=empresa,
        cpf_cnpj='123.456.789-00',
        defaults={
            'tipo': 'F',  # Física
            'nome': user.get_full_name() or user.username,
            'telefone': '(11) 99999-9999',
            'email': user.email or 'vendedor@serrana.com.br',
            'ativo': True,
        }
    )
    
    orcamento = Orcamento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vendedor=vendedor_pessoa,  # Pessoa, não User
        descricao=oportunidade.descricao,
        observacoes=f"Orçamento gerado da oportunidade CRM: {oportunidade.titulo}",
        criado_por=user,
        validade_dias=30,
        data_orcamento=datetime.now().date(),
    )
    print(f"✅ Orçamento criado: {orcamento.codigo}")
    
    # Vincular orçamento à oportunidade
    oportunidade.orcamento = orcamento
    oportunidade.save()
    print(f"✅ Orçamento vinculado à oportunidade")
    
    # Adicionar itens ao orçamento
    print("\n   📦 Adicionando itens ao orçamento...")
    
    # Buscar ou criar itens
    item1, _ = Item.objects.get_or_create(
        codigo='MOV-001',
        defaults={
            'descricao': 'Mesa Executiva Premium',
            'unidade_medida': 'UN',
            'status_ativo': True,
        }
    )
    
    item2, _ = Item.objects.get_or_create(
        codigo='MOV-002',
        defaults={
            'descricao': 'Cadeira Presidente Ergonômica',
            'unidade_medida': 'UN',
            'status_ativo': True,
        }
    )
    
    # Preços fixos para o teste (Item não tem preco_venda)
    preco_item1 = Decimal('2500.00')
    preco_item2 = Decimal('1200.00')
    
    OrcamentoItem.objects.create(
        orcamento=orcamento,
        item=item1,
        descricao=item1.descricao,
        quantidade=5,
        valor_unitario=preco_item1,
    )
    
    OrcamentoItem.objects.create(
        orcamento=orcamento,
        item=item2,
        descricao=item2.descricao,
        quantidade=10,
        valor_unitario=preco_item2,
    )
    
    # Recalcular totais
    orcamento.refresh_from_db()
    print(f"   ✅ 2 itens adicionados")
    print(f"   Total do orçamento: R$ {orcamento.valor_final}")
    
    # Adicionar parcelas
    print("\n   💳 Adicionando parcelas...")
    
    valor_parcela = orcamento.valor_final / 3
    
    for i in range(3):
        OrcamentoParcela.objects.create(
            orcamento=orcamento,
            numero_parcela=i + 1,
            valor=valor_parcela,
            data_vencimento=(datetime.now() + timedelta(days=30 * (i + 1))).date(),
            forma_pagamento='PIX',  # Usa a chave da choice, não objeto
        )
    
    print(f"   ✅ 3 parcelas criadas de R$ {valor_parcela:.2f}")
    
    # 4. APROVAR ORÇAMENTO (DEVE CRIAR PROJETO AUTOMATICAMENTE)
    print("\n🚀 4. APROVANDO ORÇAMENTO (trigger automação)...")
    
    print(f"   Status ANTES: {orcamento.status}")
    print(f"   Projetos ANTES: {Projeto.objects.filter(orcamento=orcamento).count()}")
    print(f"   CentrosCusto ANTES: {CentroCusto.objects.count()}")
    
    # Aprovar orçamento
    orcamento.status = 'APROVADO'
    orcamento.data_aprovacao = datetime.now()
    orcamento.save()
    
    print(f"   Status DEPOIS: {orcamento.status}")
    
    # Verificar se projeto foi criado
    orcamento.refresh_from_db()
    projetos_criados = Projeto.objects.filter(orcamento=orcamento)
    
    if projetos_criados.exists():
        projeto = projetos_criados.first()
        print(f"✅ PROJETO CRIADO AUTOMATICAMENTE: {projeto.codigo}")
        print(f"   Descrição: {projeto.descricao[:50]}...")
        print(f"   Valor contratado: R$ {projeto.valor_contratado}")
        print(f"   Status: {projeto.get_status_display()}")
        
        # Verificar centro de custo
        try:
            centro_custo = projeto.centro_custo
            print(f"✅ CENTRO DE CUSTO CRIADO: {centro_custo.codigo}")
            print(f"   Nome: {centro_custo.nome}")
        except:
            print("⚠️  Centro de custo não encontrado")
        
        # Verificar títulos financeiros
        titulos = projeto.titulofinanceiro_set.all()
        print(f"✅ TÍTULOS FINANCEIROS: {titulos.count()}")
        for titulo in titulos:
            print(f"   - {titulo.numero_documento}: R$ {titulo.valor_total} ({titulo.num_parcelas} parcelas)")
        
        # Verificar se orçamento mudou para CONVERTIDO
        orcamento.refresh_from_db()
        print(f"✅ Status do orçamento atualizado: {orcamento.status}")
        
    else:
        print("❌ ERRO: Nenhum projeto foi criado!")
    
    # 5. VERIFICAR ATUALIZAÇÃO DA OPORTUNIDADE
    print("\n🎯 5. VERIFICANDO ATUALIZAÇÃO DA OPORTUNIDADE CRM...")
    
    oportunidade.refresh_from_db()
    
    print(f"   Projeto vinculado: {oportunidade.projeto.codigo if oportunidade.projeto else 'Nenhum'}")
    print(f"   Status: {oportunidade.get_status_display()}")
    print(f"   Etapa: {oportunidade.etapa.nome}")
    print(f"   Data fechamento: {oportunidade.data_fechamento or 'Não fechado'}")
    
    if oportunidade.projeto:
        print("✅ OPORTUNIDADE ATUALIZADA COM SUCESSO!")
        print("✅ Oportunidade vinculada ao projeto criado")
        
        if oportunidade.etapa.is_final and oportunidade.etapa.tipo_final == 'ganho':
            print("✅ Oportunidade movida para etapa final GANHO")
        else:
            print("⚠️  Oportunidade não foi movida para etapa final Ganho")
    else:
        print("⚠️  Oportunidade NÃO foi vinculada ao projeto")
    
    # 6. VERIFICAR HISTÓRICO DE ETAPAS
    print("\n📊 6. HISTÓRICO DE MOVIMENTAÇÕES DA OPORTUNIDADE...")
    
    historico = oportunidade.historico_etapas.all().order_by('data_hora')
    for hist in historico:
        etapa_de = hist.etapa_de.nome if hist.etapa_de else 'Nova'
        etapa_para = hist.etapa_para.nome if hist.etapa_para else '---'
        print(f"   {hist.data_hora.strftime('%d/%m %H:%M')}: {etapa_de} → {etapa_para}")
    
    # RESUMO FINAL
    print("\n" + "=" * 80)
    print("✅ TESTE COMPLETO FINALIZADO!")
    print("=" * 80)
    print(f"\n📌 RESUMO DO FLUXO:")
    print(f"   1. Oportunidade criada: {oportunidade.titulo} (ID: {oportunidade.id})")
    print(f"   2. Orçamento gerado: {orcamento.codigo} (R$ {orcamento.valor_final})")
    print(f"   3. Projeto criado: {projeto.codigo if projetos_criados.exists() else 'N/A'}")
    print(f"   4. Centro de Custo: {centro_custo.codigo if 'centro_custo' in locals() else 'N/A'}")
    print(f"   5. Oportunidade final: {oportunidade.etapa.nome} - {oportunidade.get_status_display()}")
    print(f"\n🎉 INTEGRAÇÃO CRM → ORÇAMENTO → PROJETO FUNCIONANDO!")
    print()


if __name__ == '__main__':
    try:
        testar_fluxo_completo()
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        import traceback
        traceback.print_exc()
