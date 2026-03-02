"""
Signals para automação de processos em Projetos
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from decimal import Decimal

from .models import (
    Orcamento, Projeto,
    OrcamentoItem, OrcamentoParcela,
    AlocacaoProjeto, ContaCorrenteProjeto
)
from financeiro.models import CentroCusto


@receiver(post_save, sender=Orcamento)
def criar_projeto_ao_aprovar_orcamento(sender, instance, created, **kwargs):
    """
    Quando um orçamento é APROVADO, cria automaticamente:
    1. Projeto vinculado ao orçamento
    2. Centro de Custo (criado automaticamente pelo signal de Projeto)
    3. Títulos financeiros (a receber) baseado nas parcelas
    
    O status CONVERTIDO indica que o orçamento já virou projeto
    """
    # Só executa se o status mudou para APROVADO e ainda não foi convertido
    if instance.status == 'APROVADO' and not instance.projetos.exists():
        
        # Buscar um User padrão para o vendedor (criado_por ou primeiro superuser)
        vendedor_user = instance.criado_por
        if not vendedor_user:
            from django.contrib.auth.models import User
            vendedor_user = User.objects.filter(is_superuser=True).first()
        
        # 1. Criar Projeto (o signal de Projeto criará automaticamente o Centro de Custo)
        projeto = Projeto.objects.create(
            empresa=instance.empresa,
            orcamento=instance,
            cliente=instance.cliente,
            vendedor=vendedor_user,
            descricao=instance.descricao,
            data_orcamento=instance.data_orcamento,
            data_contratacao=instance.data_aprovacao,
            valor_orcado=instance.valor_final,
            valor_contratado=instance.valor_final,
            status='AGUARDANDO',  # Aguardando início
            observacoes=f"Projeto criado automaticamente a partir do orçamento {instance.codigo}",
            criado_por=instance.criado_por
        )
        
        # 2. Buscar o centro de custo criado automaticamente
        try:
            centro_custo = projeto.centro_custo
        except:
            centro_custo = None
        
        # 3. Criar Títulos Financeiros (Contas a Receber) se houver centro de custo
        if centro_custo:
            from financeiro.models import TituloFinanceiro, ParcelaFinanceira, PlanoConta
            
            # Buscar plano de conta padrão para receita de vendas
            try:
                plano_receita = PlanoConta.objects.filter(
                    empresa=instance.empresa,
                    tipo='RECEITA',
                    nome__icontains='venda'
                ).first()
                
                if not plano_receita:
                    # Se não encontrar, pega o primeiro plano de receita
                    plano_receita = PlanoConta.objects.filter(
                        empresa=instance.empresa,
                        tipo='RECEITA'
                    ).first()
            except:
                plano_receita = None
            
            # Criar título financeiro principal
            if instance.parcelas.exists():
                numero_parcelas = instance.parcelas.count()
                
                titulo = TituloFinanceiro.objects.create(
                    empresa=instance.empresa,
                    tipo='RECEBER',
                    numero_documento=projeto.codigo,
                    descricao=f"Projeto {projeto.codigo} - {instance.descricao[:100]}",
                    pessoa=instance.cliente,
                    centro_custo=centro_custo,
                    projeto=projeto,
                    plano_conta=plano_receita,
                    data_emissao=instance.data_aprovacao or instance.data_orcamento,
                    data_primeiro_vencimento=instance.parcelas.first().data_vencimento,
                    valor_total=instance.valor_final,
                    num_parcelas=numero_parcelas,
                    status='ABERTO',
                    criado_por=instance.criado_por
                )
                
               # O método save() do TituloFinanceiro já cria as parcelas automaticamente
                # Mas vamos atualizar com as formas de pagamento das parcelas do orçamento
                for i, parcela_orc in enumerate(instance.parcelas.all(), start=1):
                    try:
                        parcela_fin = titulo.parcelas.get(numero_parcela=i)
                        parcela_fin.forma_pagamento = parcela_orc.forma_pagamento
                        parcela_fin.save()
                    except:
                        pass  # Se não encontrar, tudo bem
        
        # 4. Atualizar status do orçamento para CONVERTIDO
        Orcamento.objects.filter(pk=instance.pk).update(status='CONVERTIDO')
        
        # 5. Se o orçamento veio de uma oportunidade CRM, atualizar a oportunidade
        try:
            if hasattr(instance, 'oportunidade_origem') and instance.oportunidade_origem.exists():
                oportunidade = instance.oportunidade_origem.first()
                from crm.signals import vincular_oportunidade_ao_projeto
                vincular_oportunidade_ao_projeto(oportunidade, projeto)
        except Exception as e:
            # Se o módulo CRM não estiver instalado ou houver erro, continuar normalmente
            pass
        
        print(f"✅ Projeto {projeto.codigo} criado automaticamente a partir do orçamento {instance.codigo}")


@receiver(post_save, sender=OrcamentoItem)
def atualizar_totais_orcamento(sender, instance, **kwargs):
    """
    Atualiza os totais do orçamento quando um item é salvo
    """
    orcamento = instance.orcamento
    
    # Calcular total dos itens
    total_itens = sum(
        Decimal(str(item.valor_total)) 
        for item in orcamento.itens.all()
    )
    
    orcamento.valor_total = total_itens
    
    # Aplicar desconto geral
    if orcamento.tipo_desconto == 'PERCENTUAL' and orcamento.desconto_valor:
        valor_desconto = (total_itens * Decimal(str(orcamento.desconto_valor))) / Decimal('100')
    elif orcamento.tipo_desconto == 'VALOR_FIXO' and orcamento.desconto_valor:
        valor_desconto = Decimal(str(orcamento.desconto_valor))
    else:
        valor_desconto = Decimal('0.00')
    
    orcamento.desconto = valor_desconto
    orcamento.valor_final = total_itens - valor_desconto
    
    # Salvar sem acionar o signal novamente
    Orcamento.objects.filter(pk=orcamento.pk).update(
        valor_total=orcamento.valor_total,
        desconto=orcamento.desconto,
        valor_final=orcamento.valor_final
    )


@receiver(post_save, sender=AlocacaoProjeto)
def atualizar_conta_corrente_projeto(sender, instance, created, **kwargs):
    """
    Ao criar uma alocação de projeto, registra na conta corrente
    Este signal já está implementado no método save() do model,
    mas poderia ser movido para cá para melhor separação de responsabilidades
    """
    pass  # Implementação no model.save() por enquanto


@receiver(post_save, sender=Projeto)
def atualizar_centro_custo_projeto(sender, instance, created, **kwargs):
    """
    Garante que o nome do centro de custo esteja sincronizado com o projeto
    Ao criar projeto sem centro de custo, criar automaticamente
    """
    try:
        # Buscar centro de custo vinculado ao projeto
        centro_custo = CentroCusto.objects.filter(projeto=instance).first()
        
        if centro_custo:
            # Sincronizar nome e responsável
            nome_esperado = f"CC - {instance.cliente.nome} - {instance.descricao[:50]}"
            if centro_custo.nome != nome_esperado or centro_custo.responsavel != instance.vendedor:
                CentroCusto.objects.filter(pk=centro_custo.pk).update(
                    nome=nome_esperado,
                    responsavel=instance.vendedor
                )
        elif created:
            # Se o projeto foi criado sem centro de custo, criar um
            CentroCusto.objects.create(
                empresa=instance.empresa,
                projeto=instance,
                nome=f"CC - {instance.cliente.nome} - {instance.descricao[:50]}",
                tipo='OBRA',
                responsavel=instance.vendedor,
                ativo=True,
                criado_por=instance.criado_por
            )
    except Exception as e:
        # Não interromper o save se houver erro
        print(f"⚠️ Erro ao sincronizar centro de custo: {e}")
