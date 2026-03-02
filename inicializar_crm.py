"""
Script de inicialização do módulo CRM
Cria pipeline padrão com etapas básicas se não existirem
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serrana.settings')
django.setup()

from django.contrib.auth.models import User, Group
from usuarios.models import Empresa
from crm.models import Pipeline, EtapaFunil


def criar_grupos_permissoes():
    """Cria grupos de permissão se não existirem"""
    print("\n=== CRIANDO GRUPOS DE PERMISSÃO ===")
    
    groups_created = []
    
    # Grupo Vendedor
    vendedor_group, created = Group.objects.get_or_create(name='Vendedor')
    if created:
        groups_created.append('Vendedor')
    
    # Grupo Gerente
    gerente_group, created = Group.objects.get_or_create(name='Gerente')
    if created:
        groups_created.append('Gerente')
    
    # Grupo Administrador
    admin_group, created = Group.objects.get_or_create(name='Administrador')
    if created:
        groups_created.append('Administrador')
    
    if groups_created:
        print(f"✅ Grupos criados: {', '.join(groups_created)}")
    else:
        print("ℹ️  Grupos já existiam")
    
    return vendedor_group, gerente_group, admin_group


def inicializar_pipeline_padrao():
    """Cria pipeline padrão com etapas básicas"""
    print("\n=== INICIALIZANDO PIPELINE PADRÃO ===")
    
    # Pegar empresa padrão
    try:
        empresa = Empresa.objects.get(id=1)
        print(f"✅ Empresa encontrada: {empresa.nome_fantasia}")
    except Empresa.DoesNotExist:
        print("❌ Empresa ID=1 não encontrada. Crie uma empresa primeiro.")
        return None
    
    # Pegar usuário para criar_por
    try:
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        print(f"✅ Usuário criador: {user.username}")
    except:
        print("❌ Nenhum usuário encontrado")
        return None
    
    # Verificar se já existe pipeline
    pipeline_existente = Pipeline.objects.filter(empresa=empresa).first()
    
    if pipeline_existente:
        print(f"ℹ️  Pipeline já existe: {pipeline_existente.nome}")
        pipeline = pipeline_existente
    else:
        # Criar pipeline padrão
        pipeline = Pipeline.objects.create(
            empresa=empresa,
            nome='Funil de Vendas Principal',
            descricao='Pipeline padrão para gestão de oportunidades e leads',
            ativo=True,
            padrao=True,
            criado_por=user
        )
        print(f"✅ Pipeline criado: {pipeline.nome}")
    
    # Verificar etapas
    etapas_existentes = EtapaFunil.objects.filter(pipeline=pipeline).count()
    
    if etapas_existentes > 0:
        print(f"ℹ️  Pipeline já possui {etapas_existentes} etapas")
        return pipeline
    
    # Criar etapas padrão
    etapas_config = [
        {
            'nome': 'Novo Lead',
            'ordem': 0,
            'cor': '#95a5a6',
            'is_final': False,
            'tipo_final': 'none'
        },
        {
            'nome': 'Qualificação',
            'ordem': 1,
            'cor': '#3498db',
            'is_final': False,
            'tipo_final': 'none'
        },
        {
            'nome': 'Proposta',
            'ordem': 2,
            'cor': '#f39c12',
            'is_final': False,
            'tipo_final': 'none'
        },
        {
            'nome': 'Negociação',
            'ordem': 3,
            'cor': '#e67e22',
            'is_final': False,
            'tipo_final': 'none'
        },
        {
            'nome': 'Fechado - Ganho',
            'ordem': 4,
            'cor': '#27ae60',
            'is_final': True,
            'tipo_final': 'ganho'
        },
        {
            'nome': 'Fechado - Perdido',
            'ordem': 5,
            'cor': '#c0392b',
            'is_final': True,
            'tipo_final': 'perdido'
        },
    ]
    
    print("\n📋 Criando etapas:")
    for etapa_config in etapas_config:
        etapa = EtapaFunil.objects.create(
            pipeline=pipeline,
            **etapa_config
        )
        final_str = f" (Final - {etapa.get_tipo_final_display()})" if etapa.is_final else ""
        print(f"  ✅ {etapa.nome}{final_str}")
    
    return pipeline


def criar_oportunidade_exemplo(pipeline):
    """Cria uma oportunidade de exemplo para teste"""
    print("\n=== CRIANDO OPORTUNIDADE DE EXEMPLO ===")
    
    from crm.models import Oportunidade, AtividadeCRM
    from datetime import datetime, timedelta
    
    # Verificar se já existe oportunidade
    if Oportunidade.objects.filter(pipeline=pipeline).exists():
        print("ℹ️  Já existem oportunidades neste pipeline")
        return
    
    # Pegar primeira etapa
    etapa_inicial = EtapaFunil.objects.filter(pipeline=pipeline).order_by('ordem').first()
    
    if not etapa_inicial:
        print("❌ Nenhuma etapa encontrada")
        return
    
    # Pegar usuário
    user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    
    # Criar oportunidade de exemplo
    oportunidade = Oportunidade.objects.create(
        empresa=pipeline.empresa,
        pipeline=pipeline,
        etapa=etapa_inicial,
        titulo='Projeto Construção Comercial',
        nome_contato='João Silva',
        empresa_contato='Construtora ABC Ltda',
        telefone='(11) 98765-4321',
        email='joao.silva@construtorabc.com.br',
        origem='indicacao',
        valor_estimado=150000.00,
        responsavel=user,
        criado_por=user,
        descricao='Projeto de construção de galpão comercial de 500m²'
    )
    
    print(f"✅ Oportunidade criada: {oportunidade.titulo}")
    
    # Criar algumas atividades de exemplo
    AtividadeCRM.objects.create(
        oportunidade=oportunidade,
        tipo='ligacao',
        titulo='Primeiro contato',
        descricao='Conversa inicial sobre o projeto. Cliente interessado em orçamento.',
        criado_por=user
    )
    
    AtividadeCRM.objects.create(
        oportunidade=oportunidade,
        tipo='reuniao',
        titulo='Reunião técnica',
        descricao='Reunião para levantamento de requisitos e medições iniciais.',
        criado_por=user
    )
    
    print(f"✅ Atividades de exemplo criadas")


def main():
    """Função principal"""
    print("=" * 60)
    print("INICIALIZAÇÃO DO MÓDULO CRM - FUNIL DE VENDAS")
    print("=" * 60)
    
    # 1. Criar grupos de permissão
    criar_grupos_permissoes()
    
    # 2. Criar pipeline padrão
    pipeline = inicializar_pipeline_padrao()
    
    # 3. Criar oportunidade de exemplo (opcional)
    if pipeline:
        resposta = input("\n❓ Deseja criar uma oportunidade de exemplo? (s/n): ")
        if resposta.lower() in ['s', 'sim', 'y', 'yes']:
            criar_oportunidade_exemplo(pipeline)
    
    print("\n" + "=" * 60)
    print("✅ INICIALIZAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print("\n🚀 Acesse o funil em: http://127.0.0.1:8000/crm/kanban/")
    print("\n📝 Próximos passos:")
    print("   1. Ajuste as etapas do funil conforme sua necessidade")
    print("   2. Configure permissões de usuários (Vendedor/Gerente/Admin)")
    print("   3. Comece a cadastrar oportunidades!")
    print()


if __name__ == '__main__':
    main()
