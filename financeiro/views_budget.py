"""
VIEWS E APIs - ETAPA 2
Endpoints para validação e controle de Budget
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal
import json

from .models import ProjectBudget, ProjectExpense, JustificativaBudget
from .services_budget import ValidadorBudget, AnalisadorPerformance, GeradorRelatorios
from cadastros.models import Pessoa
from usuarios.decorators import require_empresa


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_staff_or_manager(user):
    """Verifica se usuário é staff ou gerente"""
    return user.is_staff or user.groups.filter(name__in=['Gerentes', 'Administradores']).exists()


# ============================================================================
# API ENDPOINTS - LANÇAMENTO DE DESPESAS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_lancar_despesa(request):
    """
    API para lançar despesa em um budget
    Valida automaticamente se pode lançar
    
    POST /api/budget/despesa/lancar/
    {
        "budget_id": 123,
        "tipo_despesa": "MATERIAL",
        "descricao": "Compra de alumínio",
        "valor": 5000.00,
        "km_rodado": null,
        "horas_trabalhadas": null,
        "funcionario_id": null,
        "latitude": -23.5505,
        "longitude": -46.6333,
        "observacao": ""
    }
    """
    try:
        data = json.loads(request.body)
        
        # Buscar budget
        budget = get_object_or_404(ProjectBudget, id=data.get('budget_id'))
        
        # Validar se pode lançar
        valor = Decimal(str(data.get('valor', 0)))
        pode, msg = ValidadorBudget.validar_lancamento_despesa(budget, valor)
        
        if not pode:
            return JsonResponse({
                'success': False,
                'error': msg,
                'bloqueado': budget.bloqueado
            }, status=403)
        
        # Criar despesa
        despesa = ProjectExpense.objects.create(
            empresa=budget.empresa,
            budget=budget,
            tipo_despesa=data.get('tipo_despesa'),
            descricao=data.get('descricao'),
            valor=valor,
            km_rodado=data.get('km_rodado'),
            horas_trabalhadas=data.get('horas_trabalhadas'),
            funcionario_id=data.get('funcionario_id'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            observacao=data.get('observacao', ''),
            criado_por=request.user
        )
        
        # Atualizar budget (signals já fazem isso, mas garantimos)
        budget.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': msg,
            'despesa_id': despesa.id,
            'budget': {
                'codigo': budget.codigo,
                'percentual_uso': float(budget.percentual_uso_budget),
                'semaforo': budget.semaforo,
                'bloqueado': budget.bloqueado
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def api_aprovar_despesa(request, despesa_id):
    """
    API para aprovar despesa
    
    POST /api/budget/despesa/<id>/aprovar/
    """
    try:
        despesa = get_object_or_404(ProjectExpense, id=despesa_id)
        
        # Verificar permissão
        if not is_staff_or_manager(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Sem permissão para aprovar despesas'
            }, status=403)
        
        despesa.aprovar(request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'Despesa {despesa_id} aprovada com sucesso'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def api_rejeitar_despesa(request, despesa_id):
    """
    API para rejeitar despesa
    
    POST /api/budget/despesa/<id>/rejeitar/
    {
        "justificativa": "Falta comprovação"
    }
    """
    try:
        data = json.loads(request.body)
        despesa = get_object_or_404(ProjectExpense, id=despesa_id)
        
        # Verificar permissão
        if not is_staff_or_manager(request.user):
            return JsonResponse({
                'success': False,
                'error': 'Sem permissão para rejeitar despesas'
            }, status=403)
        
        justificativa = data.get('justificativa', '')
        despesa.rejeitar(request.user, justificativa)
        
        return JsonResponse({
            'success': True,
            'message': f'Despesa {despesa_id} rejeitada'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ============================================================================
# API ENDPOINTS - JUSTIFICATIVAS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_criar_justificativa(request):
    """
    API para criar justificativa de budget
    
    POST /api/budget/justificativa/criar/
    {
        "budget_id": 123,
        "motivo": "VARIACAO_PRECO",
        "descricao": "Aumento de preço...",
        "valor_adicional_necessario": 5000.00
    }
    """
    try:
        data = json.loads(request.body)
        budget = get_object_or_404(ProjectBudget, id=data.get('budget_id'))
        
        justificativa = JustificativaBudget.objects.create(
            budget=budget,
            motivo=data.get('motivo'),
            descricao=data.get('descricao'),
            valor_adicional_necessario=Decimal(str(data.get('valor_adicional_necessario', 0))),
            solicitado_por=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Justificativa criada. Aguardando aprovação.',
            'justificativa_id': justificativa.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(is_staff_or_manager)
@require_http_methods(["POST"])
def api_aprovar_justificativa(request, justificativa_id):
    """
    API para aprovar justificativa
    
    POST /api/budget/justificativa/<id>/aprovar/
    {
        "parecer": "Aprovado após análise"
    }
    """
    try:
        data = json.loads(request.body)
        justificativa = get_object_or_404(JustificativaBudget, id=justificativa_id)
        
        parecer = data.get('parecer', '')
        justificativa.aprovar(request.user, parecer)
        
        return JsonResponse({
            'success': True,
            'message': f'Justificativa aprovada. Budget {justificativa.budget.codigo} desbloqueado.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(is_staff_or_manager)
@require_http_methods(["POST"])
def api_rejeitar_justificativa(request, justificativa_id):
    """
    API para rejeitar justificativa
    
    POST /api/budget/justificativa/<id>/rejeitar/
    {
        "parecer": "Valores não justificados"
    }
    """
    try:
        data = json.loads(request.body)
        justificativa = get_object_or_404(JustificativaBudget, id=justificativa_id)
        
        parecer = data.get('parecer', 'Rejeitado')
        justificativa.rejeitar(request.user, parecer)
        
        return JsonResponse({
            'success': True,
            'message': 'Justificativa rejeitada.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ============================================================================
# API ENDPOINTS - CONSULTAS
# ============================================================================

@login_required
def api_status_budget(request, budget_id):
    """
    API para consultar status de um budget
    
    GET /api/budget/<id>/status/
    """
    budget = get_object_or_404(ProjectBudget, id=budget_id)
    
    # Calcular gastos
    gastos = ProjectExpense.objects.filter(
        budget=budget,
        status__in=['APROVADO', 'PAGO']
    ).aggregate(
        total=Sum('valor'),
        count=Count('id')
    )
    
    return JsonResponse({
        'codigo': budget.codigo,
        'descricao': budget.descricao,
        'status': budget.get_status_display(),
        'custo_previsto': float(budget.custo_total_previsto),
        'valor_venda': float(budget.valor_venda),
        'gastos_reais': float(gastos['total'] or 0),
        'total_despesas': gastos['count'],
        'percentual_uso': float(budget.percentual_uso_budget),
        'semaforo': budget.get_semaforo_display(),
        'bloqueado': budget.bloqueado,
        'margem_prevista': float(budget.margem_prevista_percentual)
    })


@login_required
def api_budgets_criticos(request):
    """
    API para listar budgets em situação crítica
    
    GET /api/budget/criticos/
    """
    relatorio = GeradorRelatorios.relatorio_projetos_criticos()
    
    return JsonResponse({
        'criticos': relatorio['criticos'],
        'alertas': relatorio['alertas'],
        'total_criticos': len(relatorio['criticos']),
        'total_alertas': len(relatorio['alertas'])
    })


# ============================================================================
# VIEWS HTML - DASHBOARD
# ============================================================================

@login_required
@require_empresa
def dashboard_budget(request):
    """
    Dashboard principal de budgets
    """
    # Obter empresa do usuário
    empresa = request.user.usuario_empresas.first().empresa if hasattr(request.user, 'usuario_empresas') else None
    
    # Estatísticas gerais
    budgets_em_execucao = ProjectBudget.objects.filter(
        status='EM_EXECUCAO'
    )
    
    if empresa:
        budgets_em_execucao = budgets_em_execucao.filter(empresa=empresa)
    
    # Contadores
    total_budgets = budgets_em_execucao.count()
    budgets_verdes = budgets_em_execucao.filter(semaforo='VERDE').count()
    budgets_amarelos = budgets_em_execucao.filter(semaforo='AMARELO').count()
    budgets_vermelhos = budgets_em_execucao.filter(semaforo='VERMELHO').count()
    budgets_bloqueados = budgets_em_execucao.filter(bloqueado=True).count()
    
    # Justificativas pendentes
    justificativas_pendentes = JustificativaBudget.objects.filter(
        status='PENDENTE'
    ).count()
    
    # Despesas pendentes
    despesas_pendentes = ProjectExpense.objects.filter(
        status='PENDENTE'
    ).count()
    
    # Budgets em situação crítica
    relatorio_criticos = GeradorRelatorios.relatorio_projetos_criticos()
    
    context = {
        'current_module': 'financeiro',  # Para exibir o menu lateral
        'total_budgets': total_budgets,
        'budgets_verdes': budgets_verdes,
        'budgets_amarelos': budgets_amarelos,
        'budgets_vermelhos': budgets_vermelhos,
        'budgets_bloqueados': budgets_bloqueados,
        'justificativas_pendentes': justificativas_pendentes,
        'despesas_pendentes': despesas_pendentes,
        'budgets_criticos': relatorio_criticos['criticos'],
        'budgets_alertas': relatorio_criticos['alertas']
    }
    
    return render(request, 'financeiro/dashboard_budget.html', context)


@login_required
def detalhe_budget(request, budget_id):
    """
    Página de detalhes de um budget específico
    """
    budget = get_object_or_404(ProjectBudget, id=budget_id)
    
    # Despesas do budget
    despesas = ProjectExpense.objects.filter(budget=budget).order_by('-data_despesa')
    
    # Totais por tipo
    totais_por_tipo = ProjectExpense.objects.filter(
        budget=budget,
        status__in=['APROVADO', 'PAGO']
    ).values('tipo_despesa').annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    # Justificativas
    justificativas = JustificativaBudget.objects.filter(budget=budget).order_by('-data_solicitacao')
    
    context = {
        'budget': budget,
        'despesas': despesas,
        'totais_por_tipo': totais_por_tipo,
        'justificativas': justificativas
    }
    
    return render(request, 'financeiro/detalhe_budget.html', context)


# ============================================================================
# VIEWS HTML - PERFORMANCE (ETAPA 3)
# ============================================================================

@login_required
@user_passes_test(is_staff_or_manager)
def relatorio_vendedores(request):
    """
    Relatório de performance de vendedores
    """
    from datetime import date, timedelta
    
    # Período (último ano por padrão)
    periodo_inicio = request.GET.get('inicio')
    periodo_fim = request.GET.get('fim')
    
    if not periodo_inicio:
        periodo_inicio = date.today() - timedelta(days=365)
    else:
        periodo_inicio = date.fromisoformat(periodo_inicio)
    
    if not periodo_fim:
        periodo_fim = date.today()
    else:
        periodo_fim = date.fromisoformat(periodo_fim)
    
    # Buscar vendedores
    vendedores = Pessoa.objects.filter(
        vendedor=True,
        ativo=True
    )
    
    # Calcular performance de cada vendedor
    performances = []
    for vendedor in vendedores:
        perf = AnalisadorPerformance.calcular_assertividade_vendedor(
            vendedor,
            periodo_inicio,
            periodo_fim
        )
        if perf['total_projetos'] > 0:
            performances.append(perf)
    
    # Ordenar por assertividade
    performances.sort(key=lambda x: x['assertividade_media'], reverse=True)
    
    context = {
        'performances': performances,
        'periodo_inicio': periodo_inicio,
        'periodo_fim': periodo_fim
    }
    
    return render(request, 'financeiro/relatorio_vendedores.html', context)


@login_required
@user_passes_test(is_staff_or_manager)
def relatorio_instaladores(request):
    """
    Relatório de performance de instaladores
    """
    from datetime import date, timedelta
    
    # Período
    periodo_inicio = request.GET.get('inicio')
    periodo_fim = request.GET.get('fim')
    
    if not periodo_inicio:
        periodo_inicio = date.today() - timedelta(days=365)
    else:
        periodo_inicio = date.fromisoformat(periodo_inicio)
    
    if not periodo_fim:
        periodo_fim = date.today()
    else:
        periodo_fim = date.fromisoformat(periodo_fim)
    
    # Buscar instaladores/funcionários
    instaladores = Pessoa.objects.filter(
        funcionario=True,
        ativo=True
    )
    
    # Calcular performance de cada instalador
    performances = []
    for instalador in instaladores:
        perf = AnalisadorPerformance.calcular_indice_retrabalho_instalador(
            instalador,
            periodo_inicio,
            periodo_fim
        )
        if perf['total_projetos'] > 0:
            performances.append(perf)
    
    # Ordenar por índice de retrabalho (menor é melhor)
    performances.sort(key=lambda x: x['indice_retrabalho'])
    
    context = {
        'performances': performances,
        'periodo_inicio': periodo_inicio,
        'periodo_fim': periodo_fim
    }
    
    return render(request, 'financeiro/relatorio_instaladores.html', context)


@login_required
@user_passes_test(is_staff_or_manager)
def relatorio_lucratividade(request):
    """
    Relatório geral de lucratividade
    """
    from datetime import date, timedelta
    
    # Período
    periodo_inicio = request.GET.get('inicio')
    periodo_fim = request.GET.get('fim')
    
    if not periodo_inicio:
        periodo_inicio = date.today() - timedelta(days=365)
    else:
        periodo_inicio = date.fromisoformat(periodo_inicio)
    
    if not periodo_fim:
        periodo_fim = date.today()
    else:
        periodo_fim = date.fromisoformat(periodo_fim)
    
    # Obter empresa
    empresa = request.user.usuario_empresas.first().empresa if hasattr(request.user, 'usuario_empresas') else None
    
    if not empresa:
        # Se não tem empresa, usar a primeira
        from usuarios.models import Empresa
        empresa = Empresa.objects.first()
    
    # Gerar relatório
    relatorio = GeradorRelatorios.relatorio_lucratividade_geral(
        empresa,
        periodo_inicio,
        periodo_fim
    )
    
    context = {
        'relatorio': relatorio,
        'periodo_inicio': periodo_inicio,
        'periodo_fim': periodo_fim
    }
    
    return render(request, 'financeiro/relatorio_lucratividade.html', context)
