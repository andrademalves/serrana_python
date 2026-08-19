from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q, Count, F
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from usuarios.decorators import verificar_permissao_menu, require_empresa
from .models import Item, MovimentoEstoque, LocalEstoque, DestinoEstoque
from projetos.models import Projeto
from datetime import datetime, timedelta


@login_required
@require_empresa
@verificar_permissao_menu('/estoque/')
def dashboard(request):
    """Dashboard do estoque com indicadores principais"""
    total_itens = Item.objects.filter(ativo=True).count()
    
    # Movimentações dos últimos 7 dias
    data_limite = timezone.now() - timedelta(days=7)
    movimentacoes_recentes = MovimentoEstoque.objects.filter(
        data_movimento__gte=data_limite
    ).select_related('item', 'criado_por').order_by('-data_movimento')[:10]
    
    # Itens por tipo
    itens_mp = Item.objects.filter(ativo=True, tipo_item='MP').count()
    itens_pa = Item.objects.filter(ativo=True, tipo_item='PA').count()
    itens_estoque_baixo = 0
    valor_total_estoque = 0
    
    context = {
        'total_itens': total_itens,
        'itens_estoque_baixo': itens_estoque_baixo,
        'movimentacoes_recentes': movimentacoes_recentes,
        'valor_total_estoque': valor_total_estoque,
        'itens_mp': itens_mp,
        'itens_pa': itens_pa,
    }
    
    return render(request, 'estoque/dashboard.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/estoque/')
def listar_itens(request):
    """Lista todos os itens do estoque com filtros"""
    itens = Item.objects.all().order_by('descricao')
    
    # Filtros
    tipo_item = request.GET.get('tipo_item')
    material = request.GET.get('material')
    status = request.GET.get('status')
    estoque_baixo = request.GET.get('estoque_baixo')
    busca = request.GET.get('busca', '')
    
    if tipo_item:
        itens = itens.filter(tipo_item=tipo_item)
    
    if material:
        itens = itens.filter(material=material)
    
    if status == 'ativo':
        itens = itens.filter(ativo=True)
    elif status == 'inativo':
        itens = itens.filter(ativo=False)
    
    if busca:
        itens = itens.filter(descricao__icontains=busca)
    
    # Filtro de estoque baixo (não pode usar filter direto pois estoque_atual é calculado)
    if estoque_baixo == 'sim':
        itens_filtrados = []
        for item in itens:
            if item.get_saldo_total() <= item.estoque_minimo:
                itens_filtrados.append(item)
        itens = itens_filtrados
    else:
        itens = list(itens)
    
    # Adicionar valor total calculado para cada item
    for item in itens:
        item.valor_total_calculado = item.get_saldo_total() * item.get_custo_medio_ponderado()
    
    context = {
        'itens': itens,
        'tipo_item_filtro': tipo_item,
        'material_filtro': material,
        'status_filtro': status,
        'estoque_baixo_filtro': estoque_baixo,
        'busca': busca,
    }
    
    return render(request, 'estoque/listar_itens.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/estoque/')
def criar_item(request):
    """Cria um novo item no estoque"""
    if request.method == 'POST':
        try:
            # Converte estoque_minimo para decimal, usando 0 se vazio
            estoque_minimo_valor = request.POST.get('estoque_minimo', '0').strip()
            estoque_minimo = float(estoque_minimo_valor) if estoque_minimo_valor else 0
            
            item = Item(
                tipo_item=request.POST.get('tipo_item'),
                descricao=request.POST.get('descricao'),
                material=request.POST.get('material') or None,
                marca=request.POST.get('marca', ''),
                modelo=request.POST.get('modelo', ''),
                cor=request.POST.get('cor', ''),
                unidade_medida=request.POST.get('unidade_medida'),
                estoque_minimo=estoque_minimo,
                url_foto=request.POST.get('url_foto', ''),
                observacoes=request.POST.get('observacoes', ''),
                ativo=request.POST.get('ativo') == 'on',
                criado_por=request.user,
                atualizado_por=request.user
            )
            
            # Processa upload de foto
            if request.FILES.get('foto'):
                item.foto = request.FILES['foto']
            
            item.save()
            messages.success(request, 'Item criado com sucesso!')
            return redirect('estoque:listar_itens')
        except Exception as e:
            # Mensagens de erro amigáveis para o usuário
            erro_msg = str(e)
            if "status_ativo" in erro_msg and "doesn't have a default value" in erro_msg:
                messages.error(request, 'Erro ao criar item: Campo obrigatório não preenchido. Por favor, entre em contato com o suporte técnico.')
            elif "doesn't have a default value" in erro_msg:
                campo = erro_msg.split("'")[1] if "'" in erro_msg else "desconhecido"
                messages.error(request, f'Erro ao criar item: O campo "{campo}" é obrigatório mas não foi preenchido. Entre em contato com o suporte.')
            elif "Duplicate entry" in erro_msg:
                messages.error(request, 'Erro ao criar item: Já existe um item com este código. Por favor, verifique os dados.')
            else:
                messages.error(request, f'Erro ao criar item. Por favor, verifique os dados e tente novamente. Se o problema persistir, entre em contato com o suporte.')
    
    return render(request, 'estoque/criar_item.html')


@login_required
def editar_item(request, id):
    """Edita um item existente"""
    item = get_object_or_404(Item, id=id)
    
    if request.method == 'POST':
        try:
            item.tipo_item = request.POST.get('tipo_item')
            item.descricao = request.POST.get('descricao')
            item.material = request.POST.get('material') or None
            item.marca = request.POST.get('marca', '')
            item.modelo = request.POST.get('modelo', '')
            item.cor = request.POST.get('cor', '')
            item.unidade_medida = request.POST.get('unidade_medida')
            
            # Converte estoque_minimo para decimal, usando 0 se vazio
            estoque_minimo_valor = request.POST.get('estoque_minimo', '0').strip()
            item.estoque_minimo = float(estoque_minimo_valor) if estoque_minimo_valor else 0
            
            item.url_foto = request.POST.get('url_foto', '')
            item.observacoes = request.POST.get('observacoes', '')
            item.ativo = request.POST.get('ativo') == 'on'
            
            # Processa upload de foto
            if request.FILES.get('foto'):
                item.foto = request.FILES['foto']
            elif request.POST.get('remover_foto'):
                item.foto = None
            
            item.atualizado_por = request.user
            item.save()
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('estoque:listar_itens')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar item: {str(e)}')
    
    context = {'item': item}
    return render(request, 'estoque/editar_item.html', context)


@login_required
def excluir_item(request, id):
    """Exclui um item (soft delete)"""
    item = get_object_or_404(Item, id=id)
    try:
        item.ativo = False
        item.atualizado_por = request.user
        item.save()
        messages.success(request, 'Item desativado com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao desativar item: {str(e)}')
    
    return redirect('estoque:listar_itens')


@login_required
def listar_movimentacoes(request):
    """Lista todas as movimentações de estoque"""
    movimentacoes = MovimentoEstoque.objects.select_related('item', 'criado_por').order_by('-data_movimento')
    
    # Filtros
    tipo_mov = request.GET.get('tipo_mov')
    item_id = request.GET.get('item')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if tipo_mov:
        movimentacoes = movimentacoes.filter(tipo_mov=tipo_mov)
    
    if item_id:
        movimentacoes = movimentacoes.filter(item_id=item_id)
    
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_mov__gte=data_inicio_dt)
    
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_mov__lte=data_fim_dt)
    
    itens_list = Item.objects.filter(ativo=True).order_by('descricao')
    
    context = {
        'movimentacoes': movimentacoes[:100],  # Limita a 100 registros
        'itens_list': itens_list,
        'tipo_mov_filtro': tipo_mov,
        'item_filtro': item_id,
        'data_inicio_filtro': data_inicio,
        'data_fim_filtro': data_fim,
    }
    
    return render(request, 'estoque/listar_movimentacoes.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/estoque/')
def criar_movimentacao(request):
    """Cria uma nova movimentação de estoque"""
    if request.method == 'POST':
        try:
            quantidade = float(request.POST.get('quantidade', 0))
            valor_unitario = float(request.POST.get('valor_unitario', 0))
            
            # Captura os campos de local e destino
            local_origem_id = request.POST.get('local_origem') or None
            local_destino_id = request.POST.get('local_destino') or None
            destino_id = request.POST.get('destino') or None
            solicitante_material_id = request.POST.get('solicitante_material') or None
            liberado_por_id = request.POST.get('liberado_por') or None
            projeto_id = request.POST.get('projeto') or None
            
            # Gera número do documento automaticamente no formato: diamesano-n
            from datetime import date
            hoje = date.today()
            data_str = hoje.strftime('%d%m%Y')
            
            # Conta quantas movimentações já existem hoje
            inicio_dia = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fim_dia = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            count_hoje = MovimentoEstoque.objects.filter(
                data_movimento__range=[inicio_dia, fim_dia]
            ).count()
            
            numero_sequencial = count_hoje + 1
            numero_documento = f"{data_str}-{numero_sequencial}"
            
            movimentacao = MovimentoEstoque(
                item_id=request.POST.get('item'),
                tipo_movimento=request.POST.get('tipo_mov'),
                quantidade=quantidade,
                custo_unitario=valor_unitario,
                custo_total=quantidade * valor_unitario,
                local_origem_id=local_origem_id,
                local_destino_id=local_destino_id,
                destino_id=destino_id,
                solicitante_material_id=solicitante_material_id,
                liberado_por_id=liberado_por_id,
                projeto_id=projeto_id,
                documento=numero_documento,
                observacao=request.POST.get('observacao', ''),
                data_movimento=timezone.now(),
                criado_por=request.user
            )
            movimentacao.save()
            messages.success(request, f'Movimentação registrada com sucesso! <a href="/estoque/movimentacoes/{movimentacao.id}/pdf/" class="alert-link">Gerar Documento PDF</a>')
            return redirect('estoque:listar_movimentacoes')
        except Exception as e:
            messages.error(request, f'Erro ao registrar movimentação: {str(e)}')
    
    # Busca os dados necessários para o formulário
    itens = Item.objects.filter(ativo=True).order_by('descricao')
    locais = LocalEstoque.objects.filter(ativo=True).order_by('descricao')
    destinos = DestinoEstoque.objects.filter(ativo=True).order_by('descricao')
    projetos = Projeto.objects.all().order_by('-criado_em')
    
    # Busca pessoas para solicitante de material
    from cadastros.models import Pessoa
    pessoas = Pessoa.objects.filter(ativo=True).order_by('nome')
    
    # Busca usuários ativos para liberador
    from django.contrib.auth.models import User
    usuarios_liberadores = User.objects.filter(is_active=True).order_by('first_name', 'username')
    
    context = {
        'itens': itens,
        'locais': locais,
        'destinos': destinos,
        'projetos': projetos,
        'pessoas': pessoas,
        'usuarios_liberadores': usuarios_liberadores,
    }
    
    return render(request, 'estoque/criar_movimentacao.html', context)


@login_required
def relatorio_estoque_atual(request):
    """Relatório de estoque atual com filtros"""
    itens = Item.objects.filter(ativo=True).order_by('descricao')
    
    # Filtros
    tipo_item = request.GET.get('tipo_item')
    estoque_baixo = request.GET.get('estoque_baixo')
    
    if tipo_item:
        itens = itens.filter(tipo_item=tipo_item)
    
    # Filtro de estoque baixo (não pode usar filter direto pois estoque_atual é calculado)
    if estoque_baixo == 'sim':
        itens_filtrados = []
        for item in itens:
            if item.get_saldo_total() <= item.estoque_minimo:
                itens_filtrados.append(item)
        itens = itens_filtrados
    else:
        itens = list(itens)
    
    # Adicionar valor total calculado para cada item
    for item in itens:
        item.valor_total_calculado = item.get_saldo_total() * item.get_custo_medio_ponderado()
    
    # Totalizadores
    total_itens = len(itens)
    valor_total = sum([item.valor_total_calculado for item in itens])
    
    context = {
        'itens': itens,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'tipo_item_filtro': tipo_item,
        'estoque_baixo_filtro': estoque_baixo,
    }
    
    return render(request, 'estoque/relatorio_estoque_atual.html', context)


@login_required
def relatorio_movimentacoes(request):
    """Relatório de movimentações por período"""
    movimentacoes = MovimentoEstoque.objects.select_related('item', 'criado_por').order_by('-data_movimento')
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    tipo_mov = request.GET.get('tipo_mov')
    item_id = request.GET.get('item')
    
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__gte=data_inicio_dt)
    
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__lte=data_fim_dt)
    
    if tipo_mov:
        movimentacoes = movimentacoes.filter(tipo_movimento=tipo_mov)
    
    if item_id:
        movimentacoes = movimentacoes.filter(item_id=item_id)
    
    # Totalizadores
    total_movimentacoes = movimentacoes.count()
    valor_total = movimentacoes.aggregate(total=Sum('custo_total'))['total'] or 0
    
    itens_list = Item.objects.filter(ativo=True).order_by('descricao')
    
    context = {
        'movimentacoes': movimentacoes,
        'total_movimentacoes': total_movimentacoes,
        'valor_total': valor_total,
        'itens_list': itens_list,
        'data_inicio_filtro': data_inicio,
        'data_fim_filtro': data_fim,
        'tipo_mov_filtro': tipo_mov,
        'item_filtro': item_id,
    }
    
    return render(request, 'estoque/relatorio_movimentacoes.html', context)


@login_required
def relatorio_materiais_obra_consolidado(request):
    """Relatório consolidado de custos de materiais por obra/projeto"""
    projeto_id = request.GET.get('projeto')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Busca todos os projetos para o filtro
    projetos = Projeto.objects.all().order_by('-criado_em')
    
    # Busca movimentações filtradas
    movimentacoes = MovimentoEstoque.objects.select_related('item', 'projeto').filter(
        tipo_movimento='SAIDA',
        projeto__isnull=False
    )
    
    if projeto_id:
        movimentacoes = movimentacoes.filter(projeto_id=projeto_id)
        projeto_selecionado = Projeto.objects.get(id=projeto_id)
    else:
        projeto_selecionado = None
    
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__gte=data_inicio_dt)
    
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__lte=data_fim_dt)
    
    # Agrupa por projeto e item
    from django.db.models import Sum, Count
    relatorio = movimentacoes.values(
        'projeto__id',
        'projeto__codigo',
        'projeto__descricao',
        'projeto__cliente__nome',
        'item__codigo',
        'item__descricao',
        'item__unidade_medida'
    ).annotate(
        total_movimentacoes=Count('id'),
        quantidade_total=Sum('quantidade'),
        custo_total=Sum('custo_total')
    ).order_by('projeto__codigo', 'item__descricao')
    
    # Total geral
    totais = {
        'quantidade_total': sum(r['quantidade_total'] for r in relatorio),
        'custo_total': sum(r['custo_total'] for r in relatorio),
    }
    
    context = {
        'relatorio': relatorio,
        'totais': totais,
        'projetos': projetos,
        'projeto_filtro': projeto_id,
        'projeto_selecionado': projeto_selecionado,
        'data_inicio_filtro': data_inicio,
        'data_fim_filtro': data_fim,
    }
    
    return render(request, 'estoque/relatorio_materiais_obra_consolidado.html', context)


@login_required
def relatorio_materiais_obra_analitico(request):
    """Relatório analítico detalhado de materiais por obra/projeto"""
    projeto_id = request.GET.get('projeto')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Busca todos os projetos para o filtro
    projetos = Projeto.objects.all().order_by('-criado_em')
    projeto_selecionado = None
    
    # Busca movimentações filtradas
    movimentacoes = MovimentoEstoque.objects.select_related(
        'item', 'projeto', 'projeto__cliente', 'criado_por', 'solicitante_material', 'liberado_por'
    ).filter(
        tipo_movimento='SAIDA',
        projeto__isnull=False
    ).order_by('projeto__codigo', '-data_movimento')
    
    if projeto_id:
        movimentacoes = movimentacoes.filter(projeto_id=projeto_id)
        projeto_selecionado = Projeto.objects.get(id=projeto_id)
    
    if data_inicio:
        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__gte=data_inicio_dt)
    
    if data_fim:
        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
        movimentacoes = movimentacoes.filter(data_movimento__lte=data_fim_dt)
    
    # Agrupa movimentações por projeto para organização
    from collections import defaultdict
    movimentacoes_por_projeto = defaultdict(list)
    totais_por_projeto = defaultdict(lambda: {'quantidade': 0, 'custo': 0, 'itens': 0})
    
    for mov in movimentacoes:
        projeto_key = f"{mov.projeto.codigo} - {mov.projeto.descricao}"
        movimentacoes_por_projeto[projeto_key].append(mov)
        totais_por_projeto[projeto_key]['quantidade'] += mov.quantidade
        totais_por_projeto[projeto_key]['custo'] += mov.custo_total
        totais_por_projeto[projeto_key]['itens'] += 1
    
    # Total geral
    total_geral = {
        'itens': sum(t['itens'] for t in totais_por_projeto.values()),
        'quantidade': sum(t['quantidade'] for t in totais_por_projeto.values()),
        'custo': sum(t['custo'] for t in totais_por_projeto.values()),
    }
    
    context = {
        'movimentacoes_por_projeto': dict(movimentacoes_por_projeto),
        'totais_por_projeto': dict(totais_por_projeto),
        'total_geral': total_geral,
        'projetos': projetos,
        'projeto_filtro': projeto_id,
        'projeto_selecionado': projeto_selecionado,
        'data_inicio_filtro': data_inicio,
        'data_fim_filtro': data_fim,
    }
    
    return render(request, 'estoque/relatorio_materiais_obra_analitico.html', context)


# ============================================================
# CRUD de Locais de Estoque
# ============================================================

@login_required
def listar_locais(request):
    """Lista os locais de estoque cadastrados"""
    locais = LocalEstoque.objects.all().order_by('codigo')
    
    context = {
        'locais': locais,
    }
    
    return render(request, 'estoque/listar_locais.html', context)


@login_required
def criar_local(request):
    """Cria um novo local de estoque"""
    if request.method == 'POST':
        try:
            local = LocalEstoque(
                codigo=request.POST.get('codigo'),
                descricao=request.POST.get('descricao'),
                endereco=request.POST.get('endereco', ''),
                permite_saldo_negativo=request.POST.get('permite_saldo_negativo') == 'on',
                ativo=request.POST.get('ativo') == 'on',
                criado_por=request.user
            )
            local.save()
            messages.success(request, 'Local de estoque cadastrado com sucesso!')
            return redirect('estoque:listar_locais')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar local: {str(e)}')
    
    return render(request, 'estoque/form_local.html', {'acao': 'Cadastrar'})


@login_required
def editar_local(request, id):
    """Edita um local de estoque existente"""
    local = get_object_or_404(LocalEstoque, id=id)
    
    if request.method == 'POST':
        try:
            local.codigo = request.POST.get('codigo')
            local.descricao = request.POST.get('descricao')
            local.endereco = request.POST.get('endereco', '')
            local.permite_saldo_negativo = request.POST.get('permite_saldo_negativo') == 'on'
            local.ativo = request.POST.get('ativo') == 'on'
            local.save()
            messages.success(request, 'Local de estoque atualizado com sucesso!')
            return redirect('estoque:listar_locais')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar local: {str(e)}')
    
    context = {
        'local': local,
        'acao': 'Editar'
    }
    
    return render(request, 'estoque/form_local.html', context)
