"""
Views do Dashboard CRM
Separadas para melhor organização
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from usuarios.models import Empresa
from crm.models import Pipeline, Oportunidade
from crm.services.metricas_crm import MetricasCRM
from django.contrib.auth.models import User


@login_required
def dashboard_crm(request):
    """
    Dashboard principal do CRM com BI comercial
    
    Controle de acesso:
    - Admin: vê todos os dados, pode filtrar por vendedor
    - Vendedor: vê apenas seus próprios dados
    """
    # Empresa ativa
    try:
        empresa = Empresa.objects.filter(ativa=True).first()
        if not empresa:
            raise Empresa.DoesNotExist
    except Empresa.DoesNotExist:
        return render(request, 'crm/erro_empresa.html')
    
    # Verificar se é admin
    is_admin = request.user.is_superuser or request.user.is_staff
    
    # Processar filtros
    filtros = _processar_filtros(request, is_admin)
    
    # Inicializar serviço de métricas
    metricas = MetricasCRM(
        empresa=empresa,
        usuario=request.user if not is_admin or not filtros['vendedor_id'] else None,
        is_admin=is_admin
    )
    
    # ========== KPIs PRINCIPAIS (Cards do topo) ==========
    kpis = metricas.kpis_principais(
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim'],
        vendedor_id=filtros['vendedor_id']
    )
    
    # ========== GRÁFICO: LEADS POR ETAPA ==========
    dados_etapas = metricas.leads_por_etapa(
        pipeline_id=filtros['pipeline_id'],
        vendedor_id=filtros['vendedor_id'],
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim']
    )
    
    # ========== RANKING DE VENDEDORES ==========
    ranking = metricas.ranking_vendedores(
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim'],
        top=10
    )
    
    # ========== GRÁFICO DE PERFORMANCE ==========
    performance = metricas.grafico_performance(
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim'],
        vendedor_id=filtros['vendedor_id']
    )
    
    # ========== GRÁFICO DE FUNIL ==========
    funil = metricas.grafico_funil(
        pipeline_id=filtros['pipeline_id'],
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim'],
        vendedor_id=filtros['vendedor_id']
    )
    
    # ========== META MENSAL ==========
    meta_atual = metricas.meta_vendedor(
        vendedor_id=filtros['vendedor_id'] or request.user.id,
        mes=filtros['mes'],
        ano=filtros['ano']
    )
    
    # ========== PREVISÃO DE FATURAMENTO ==========
    previsao = metricas.previsao_faturamento(
        data_inicio=filtros['data_inicio'],
        data_fim=filtros['data_fim'],
        vendedor_id=filtros['vendedor_id']
    )
    
    # ========== DADOS PARA FORMULÁRIO DE FILTROS ==========
    # Pipelines disponíveis
    pipelines = Pipeline.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    
    # Vendedores (apenas para admin)
    vendedores = []
    if is_admin:
        vendedores = User.objects.filter(
            oportunidades_responsavel__empresa=empresa
        ).distinct().order_by('first_name', 'username')
    
    # Nome do vendedor atual (para exibição no título)
    vendedor_nome = None
    if filtros['vendedor_id']:
        try:
            vendedor_obj = User.objects.get(id=filtros['vendedor_id'])
            vendedor_nome = vendedor_obj.get_full_name() or vendedor_obj.username
        except User.DoesNotExist:
            pass
    elif not is_admin:
        vendedor_nome = request.user.get_full_name() or request.user.username
    
    # ========== CONTEXTO ==========
    context = {
        'current_module': 'crm',
        'is_admin': is_admin,
        'empresa': empresa,
        
        # Filtros aplicados
        'filtros': filtros,
        'pipelines': pipelines,
        'vendedores': vendedores,
        'vendedor_nome': vendedor_nome,
        
        # KPIs
        'kpis': kpis,
        
        # Meta
        'meta': meta_atual,
        
        # Previsão
        'previsao': previsao,
        
        # Ranking
        'ranking': ranking,
        
        # Funil (para acesso no template)
        'funil': funil,
        
        # Dados para gráficos (JSON)
        'dados_etapas_json': json.dumps(dados_etapas, default=str),
        'dados_performance_json': json.dumps(performance, default=str),
        'dados_funil_json': json.dumps(funil, default=str),
    }
    
    return render(request, 'crm/dashboard.html', context)


def _processar_filtros(request, is_admin):
    """
    Processa e valida filtros do dashboard
    
    Returns:
        dict com filtros processados
    """
    hoje = date.today()
    
    # Pipeline
    pipeline_id = request.GET.get('pipeline')
    if pipeline_id:
        try:
            pipeline_id = int(pipeline_id)
        except (ValueError, TypeError):
            pipeline_id = None
    
    # Vendedor (apenas para admin)
    vendedor_id = None
    if is_admin:
        vendedor_id = request.GET.get('vendedor')
        if vendedor_id:
            try:
                vendedor_id = int(vendedor_id)
            except (ValueError, TypeError):
                vendedor_id = None
    
    # Datas (padrão: mês atual)
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')
    
    # Se não especificado, usar mês atual
    if not data_inicio_str:
        data_inicio = date(hoje.year, hoje.month, 1)
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = date(hoje.year, hoje.month, 1)
    
    if not data_fim_str:
        # Último dia do mês atual
        if hoje.month == 12:
            data_fim = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
    else:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            if hoje.month == 12:
                data_fim = date(hoje.year + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
    
    # Mês e ano para meta (baseado em data_inicio)
    mes = data_inicio.month
    ano = data_inicio.year
    
    return {
        'pipeline_id': pipeline_id,
        'vendedor_id': vendedor_id,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'data_inicio_str': data_inicio.strftime('%Y-%m-%d'),
        'data_fim_str': data_fim.strftime('%Y-%m-%d'),
        'mes': mes,
        'ano': ano,
    }
