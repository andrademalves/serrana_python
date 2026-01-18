from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F, Count, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Item, GrupoItem, LocalEstoque, DestinoEstoque,
    MovimentoEstoque, SaldoEstoque, BOM, BOMItem, OrdemProducao
)
from .forms import (
    ItemForm, GrupoItemForm, LocalEstoqueForm, DestinoEstoqueForm,
    MovimentoEstoqueEntradaForm, MovimentoEstoqueSaidaForm,
    MovimentoEstoqueTransferenciaForm, MovimentoEstoqueAjusteForm,
    FiltroMovimentosForm, BOMForm, BOMItemForm, OrdemProducaoForm
)


# ===================================
# DASHBOARD
# ===================================

@login_required
def dashboard(request):
    """Dashboard do estoque com indicadores principais"""
    
    # Totais
    total_itens = Item.objects.filter(ativo=True).count()
    total_locais = LocalEstoque.objects.filter(ativo=True).count()
    
    # Itens abaixo do mínimo
    itens_baixo_estoque = Item.objects.filter(
        ativo=True,
        saldos__quantidade__lte=F('estoque_minimo')
    ).distinct().count()
    
    # Valor total do estoque (agregando saldos)
    valor_total = SaldoEstoque.objects.aggregate(
        total=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
    )['total'] or Decimal('0.00')
    
    # Movimentações recentes (últimos 10)
    movimentacoes_recentes = MovimentoEstoque.objects.select_related(
        'item', 'local_origem', 'local_destino', 'criado_por'
    ).order_by('-data_movimento', '-criado_em')[:10]
    
    # Itens por tipo
    itens_por_tipo = Item.objects.filter(ativo=True).values('tipo_item').annotate(
        total=Count('id')
    ).order_by('tipo_item')
    
    # Movimentações dos últimos 7 dias (por tipo)
    data_limite = timezone.now() - timedelta(days=7)
    movimentacoes_semana = MovimentoEstoque.objects.filter(
        data_movimento__gte=data_limite
    ).values('tipo_movimento').annotate(
        total=Count('id')
    ).order_by('tipo_movimento')
    
    context = {
        'total_itens': total_itens,
        'total_locais': total_locais,
        'itens_baixo_estoque': itens_baixo_estoque,
        'valor_total': valor_total,
        'movimentacoes_recentes': movimentacoes_recentes,
        'itens_por_tipo': itens_por_tipo,
        'movimentacoes_semana': movimentacoes_semana,
    }
    
    return render(request, 'estoque/dashboard.html', context)


# ===================================
# CRUD ITENS
# ===================================

@login_required
def listar_itens(request):
    """Lista todos os itens do estoque com filtros"""
    itens = Item.objects.select_related('grupo', 'criado_por').filter(ativo=True)
    
    # Filtros
    busca = request.GET.get('busca', '')
    tipo = request.GET.get('tipo', '')
    grupo = request.GET.get('grupo', '')
    
    if busca:
        itens = itens.filter(
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(marca__icontains=busca) |
            Q(modelo__icontains=busca)
        )
    
    if tipo:
        itens = itens.filter(tipo_item=tipo)
    
    if grupo:
        itens = itens.filter(grupo_id=grupo)
    
    # Adicionar saldo total para cada item
    itens = itens.annotate(
        saldo_total=Coalesce(Sum('saldos__quantidade'), Decimal('0.000'))
    )
    
    # Listas para filtros
    tipos = Item.TIPO_CHOICES
    grupos = GrupoItem.objects.filter(ativo=True).order_by('descricao')
    
    context = {
        'itens': itens,
        'tipos': tipos,
        'grupos': grupos,
        'busca': busca,
        'tipo_selecionado': tipo,
        'grupo_selecionado': grupo,
    }
    
    return render(request, 'estoque/listar_itens.html', context)


@login_required
def criar_item(request):
    """Cria um novo item"""
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.criado_por = request.user
            item.atualizado_por = request.user
            item.save()
            messages.success(request, f'Item "{item.codigo}" criado com sucesso!')
            return redirect('estoque:listar_itens')
    else:
        form = ItemForm()
    
    context = {'form': form, 'title': 'Novo Item'}
    return render(request, 'estoque/form_item.html', context)


@login_required
def editar_item(request, pk):
    """Edita um item existente"""
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.atualizado_por = request.user
            item.save()
            messages.success(request, f'Item "{item.codigo}" atualizado com sucesso!')
            return redirect('estoque:listar_itens')
    else:
        form = ItemForm(instance=item)
    
    context = {'form': form, 'item': item, 'title': 'Editar Item'}
    return render(request, 'estoque/form_item.html', context)


@login_required
def detalhe_item(request, pk):
    """Exibe detalhes de um item com saldos por local e movimentações recentes"""
    item = get_object_or_404(Item, pk=pk)
    
    # Saldos por local
    saldos = SaldoEstoque.objects.filter(item=item).select_related('local').order_by('local__descricao')
    
    # Movimentações recentes (últimas 20)
    movimentacoes = MovimentoEstoque.objects.filter(item=item).select_related(
        'local_origem', 'local_destino', 'destino', 'projeto', 'criado_por'
    ).order_by('-data_movimento', '-criado_em')[:20]
    
    # Saldo total
    saldo_total = saldos.aggregate(total=Sum('quantidade'))['total'] or Decimal('0.000')
    
    # Custo médio ponderado
    custo_medio = item.get_custo_medio_ponderado()
    
    context = {
        'item': item,
        'saldos': saldos,
        'saldo_total': saldo_total,
        'custo_medio': custo_medio,
        'movimentacoes': movimentacoes,
    }
    
    return render(request, 'estoque/detalhe_item.html', context)


# ===================================
# CRUD LOCAIS DE ESTOQUE
# ===================================

@login_required
def listar_locais(request):
    """Lista todos os locais de estoque"""
    locais = LocalEstoque.objects.select_related('responsavel').filter(ativo=True).order_by('descricao')
    context = {'locais': locais}
    return render(request, 'estoque/listar_locais.html', context)


@login_required
def criar_local(request):
    """Cria um novo local de estoque"""
    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST)
        if form.is_valid():
            local = form.save(commit=False)
            local.criado_por = request.user
            local.save()
            messages.success(request, f'Local "{local.codigo}" criado com sucesso!')
            return redirect('estoque:listar_locais')
    else:
        form = LocalEstoqueForm()
    
    context = {'form': form, 'title': 'Novo Local de Estoque'}
    return render(request, 'estoque/form_local.html', context)


@login_required
def editar_local(request, pk):
    """Edita um local existente"""
    local = get_object_or_404(LocalEstoque, pk=pk)
    
    if request.method == 'POST':
        form = LocalEstoqueForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            messages.success(request, f'Local "{local.codigo}" atualizado com sucesso!')
            return redirect('estoque:listar_locais')
    else:
        form = LocalEstoqueForm(instance=local)
    
    context = {'form': form, 'local': local, 'title': 'Editar Local'}
    return render(request, 'estoque/form_local.html', context)


# ===================================
# CRUD DESTINOS
# ===================================

@login_required
def listar_destinos(request):
    """Lista todos os destinos de estoque"""
    destinos = DestinoEstoque.objects.filter(ativo=True).order_by('descricao')
    context = {'destinos': destinos}
    return render(request, 'estoque/listar_destinos.html', context)


@login_required
def criar_destino(request):
    """Cria um novo destino"""
    if request.method == 'POST':
        form = DestinoEstoqueForm(request.POST)
        if form.is_valid():
            destino = form.save(commit=False)
            destino.criado_por = request.user
            destino.save()
            messages.success(request, f'Destino "{destino.codigo}" criado com sucesso!')
            return redirect('estoque:listar_destinos')
    else:
        form = DestinoEstoqueForm()
    
    context = {'form': form, 'title': 'Novo Destino'}
    return render(request, 'estoque/form_destino.html', context)


# ===================================
# MOVIMENTAÇÕES
# ===================================

@login_required
def entrada_estoque(request):
    """Registra entrada de estoque (Nota Fiscal)"""
    if request.method == 'POST':
        form = MovimentoEstoqueEntradaForm(request.POST)
        if form.is_valid():
            try:
                movimento = form.save(commit=False)
                movimento.criado_por = request.user
                movimento.save()
                messages.success(request, f'Entrada registrada com sucesso! Doc: {movimento.documento}')
                return redirect('estoque:dashboard')
            except Exception as e:
                messages.error(request, f'Erro ao registrar entrada: {str(e)}')
    else:
        form = MovimentoEstoqueEntradaForm(initial={
            'data_movimento': timezone.now(),
            'documento_tipo': 'NF'
        })
    
    context = {'form': form, 'title': 'Entrada de Estoque', 'tipo': 'entrada'}
    return render(request, 'estoque/form_movimento.html', context)


@login_required
def saida_estoque(request):
    """Registra saída de estoque (Requisição)"""
    if request.method == 'POST':
        form = MovimentoEstoqueSaidaForm(request.POST)
        if form.is_valid():
            try:
                movimento = form.save(commit=False)
                movimento.criado_por = request.user
                movimento.save()
                messages.success(request, f'Saída registrada com sucesso! Doc: {movimento.documento}')
                return redirect('estoque:dashboard')
            except Exception as e:
                messages.error(request, f'Erro ao registrar saída: {str(e)}')
    else:
        form = MovimentoEstoqueSaidaForm(initial={
            'data_movimento': timezone.now(),
            'documento_tipo': 'REQ'
        })
    
    context = {'form': form, 'title': 'Saída de Estoque', 'tipo': 'saida'}
    return render(request, 'estoque/form_movimento.html', context)


@login_required
def transferencia_estoque(request):
    """Registra transferência entre locais"""
    if request.method == 'POST':
        form = MovimentoEstoqueTransferenciaForm(request.POST)
        if form.is_valid():
            try:
                movimento = form.save(commit=False)
                movimento.criado_por = request.user
                movimento.save()
                messages.success(request, f'Transferência registrada com sucesso! Doc: {movimento.documento}')
                return redirect('estoque:dashboard')
            except Exception as e:
                messages.error(request, f'Erro ao registrar transferência: {str(e)}')
    else:
        form = MovimentoEstoqueTransferenciaForm(initial={
            'data_movimento': timezone.now()
        })
    
    context = {'form': form, 'title': 'Transferência entre Locais', 'tipo': 'transferencia'}
    return render(request, 'estoque/form_movimento.html', context)


@login_required
def ajuste_estoque(request):
    """Registra ajuste/inventário de estoque"""
    if request.method == 'POST':
        form = MovimentoEstoqueAjusteForm(request.POST)
        if form.is_valid():
            try:
                movimento = form.save(commit=False)
                movimento.criado_por = request.user
                movimento.save()
                messages.success(request, f'Ajuste registrado com sucesso! Doc: {movimento.documento}')
                return redirect('estoque:dashboard')
            except Exception as e:
                messages.error(request, f'Erro ao registrar ajuste: {str(e)}')
    else:
        form = MovimentoEstoqueAjusteForm(initial={
            'data_movimento': timezone.now(),
            'tipo_ajuste': 'POSITIVO'
        })
    
    context = {'form': form, 'title': 'Ajuste de Estoque', 'tipo': 'ajuste'}
    return render(request, 'estoque/form_movimento.html', context)


@login_required
def listar_movimentos(request):
    """Lista movimentações com filtros"""
    movimentos = MovimentoEstoque.objects.select_related(
        'item', 'local_origem', 'local_destino', 'destino', 'projeto', 'criado_por'
    ).order_by('-data_movimento', '-criado_em')
    
    # Aplicar filtros
    form = FiltroMovimentosForm(request.GET)
    if form.is_valid():
        if form.cleaned_data.get('data_inicio'):
            movimentos = movimentos.filter(data_movimento__gte=form.cleaned_data['data_inicio'])
        
        if form.cleaned_data.get('data_fim'):
            data_fim = datetime.combine(form.cleaned_data['data_fim'], datetime.max.time())
            movimentos = movimentos.filter(data_movimento__lte=data_fim)
        
        if form.cleaned_data.get('tipo_movimento'):
            movimentos = movimentos.filter(tipo_movimento=form.cleaned_data['tipo_movimento'])
        
        if form.cleaned_data.get('item'):
            movimentos = movimentos.filter(item=form.cleaned_data['item'])
        
        if form.cleaned_data.get('local'):
            local = form.cleaned_data['local']
            movimentos = movimentos.filter(
                Q(local_origem=local) | Q(local_destino=local)
            )
        
        if form.cleaned_data.get('projeto'):
            movimentos = movimentos.filter(projeto=form.cleaned_data['projeto'])
    
    # Paginação simples (primeiros 100)
    movimentos = movimentos[:100]
    
    context = {
        'movimentos': movimentos,
        'form': form,
    }
    
    return render(request, 'estoque/listar_movimentos.html', context)


# ===================================
# RELATÓRIOS
# ===================================

@login_required
def relatorio_posicao_estoque(request):
    """Relatório de posição atual de estoque"""
    saldos = SaldoEstoque.objects.select_related('item', 'local').filter(
        item__ativo=True,
        local__ativo=True
    ).order_by('item__codigo', 'local__codigo')
    
    # Filtros
    item = request.GET.get('item', '')
    local = request.GET.get('local', '')
    tipo = request.GET.get('tipo', '')
    
    if item:
        saldos = saldos.filter(item_id=item)
    
    if local:
        saldos = saldos.filter(local_id=local)
    
    if tipo:
        saldos = saldos.filter(item__tipo_item=tipo)
    
    # Totalizadores
    total_itens = saldos.values('item').distinct().count()
    total_valor = saldos.aggregate(
        total=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
    )['total'] or Decimal('0.00')
    
    # Listas para filtros
    itens = Item.objects.filter(ativo=True).order_by('descricao')
    locais = LocalEstoque.objects.filter(ativo=True).order_by('descricao')
    tipos = Item.TIPO_CHOICES
    
    context = {
        'saldos': saldos,
        'total_itens': total_itens,
        'total_valor': total_valor,
        'itens': itens,
        'locais': locais,
        'tipos': tipos,
    }
    
    return render(request, 'estoque/relatorio_posicao.html', context)


@login_required
def relatorio_itens_minimo(request):
    """Relatório de itens abaixo do estoque mínimo"""
    # Itens com saldo abaixo do mínimo
    itens_baixos = Item.objects.filter(
        ativo=True,
        estoque_minimo__gt=0
    ).annotate(
        saldo_total=Coalesce(Sum('saldos__quantidade'), Decimal('0.000'))
    ).filter(
        saldo_total__lte=F('estoque_minimo')
    ).order_by('descricao')
    
    # Adicionar quantidade a repor
    for item in itens_baixos:
        item.quantidade_repor = item.estoque_minimo - item.saldo_total
    
    context = {'itens_baixos': itens_baixos}
    return render(request, 'estoque/relatorio_minimo.html', context)


@login_required
def relatorio_consumo_projeto(request, projeto_id=None):
    """Relatório de consumo de materiais por projeto"""
    from projetos.models import Projeto
    
    projetos = Projeto.objects.filter(ativo=True).order_by('codigo')
    
    consumos = None
    projeto_selecionado = None
    total_custo = Decimal('0.00')
    
    if projeto_id:
        projeto_selecionado = get_object_or_404(Projeto, pk=projeto_id)
        
        # Buscar movimentos de saída para o projeto
        consumos = MovimentoEstoque.objects.filter(
            projeto=projeto_selecionado,
            tipo_movimento='SAIDA'
        ).select_related('item', 'destino', 'local_origem').values(
            'item__codigo',
            'item__descricao',
            'item__unidade_medida'
        ).annotate(
            quantidade_total=Sum('quantidade'),
            custo_total=Sum('custo_total')
        ).order_by('-custo_total')
        
        total_custo = consumos.aggregate(total=Sum('custo_total'))['total'] or Decimal('0.00')
    
    context = {
        'projetos': projetos,
        'projeto_selecionado': projeto_selecionado,
        'consumos': consumos,
        'total_custo': total_custo,
    }
    
    return render(request, 'estoque/relatorio_consumo_projeto.html', context)


@login_required
def relatorio_valorizacao(request):
    """Relatório de valorização do estoque"""
    # Agrupar por local e tipo
    valorizacao = SaldoEstoque.objects.filter(
        item__ativo=True,
        local__ativo=True
    ).select_related('local', 'item').values(
        'local__codigo',
        'local__descricao',
        'item__tipo_item'
    ).annotate(
        qtd_itens=Count('item', distinct=True),
        quantidade_total=Sum('quantidade'),
        valor_total=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
    ).order_by('local__codigo', 'item__tipo_item')
    
    # Total geral
    total_geral = SaldoEstoque.objects.filter(
        item__ativo=True,
        local__ativo=True
    ).aggregate(
        valor=Sum(F('quantidade') * F('custo_medio'), output_field=DecimalField())
    )['valor'] or Decimal('0.00')
    
    context = {
        'valorizacao': valorizacao,
        'total_geral': total_geral,
    }
    
    return render(request, 'estoque/relatorio_valorizacao.html', context)


# ===================================
# AJAX / API HELPERS
# ===================================

@login_required
def api_saldo_item(request, item_id, local_id):
    """Retorna saldo de um item em um local (para uso em formulários)"""
    try:
        saldo = SaldoEstoque.objects.get(item_id=item_id, local_id=local_id)
        data = {
            'quantidade': float(saldo.quantidade),
            'custo_medio': float(saldo.custo_medio),
            'valor_total': float(saldo.valor_total),
        }
    except SaldoEstoque.DoesNotExist:
        data = {
            'quantidade': 0.0,
            'custo_medio': 0.0,
            'valor_total': 0.0,
        }
    
    return JsonResponse(data)
