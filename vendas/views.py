"""
VIEWS - MÓDULO ORÇAMENTOS E VENDAS
===================================

Views para:
- Listar orçamentos (com filtros)
- Criar/Editar orçamentos
- Detalhar orçamento
- Aprovar/Reprovar
- Gerar PDF
- Relatórios comerciais

Autor: Sistema Comercial Profissional
Data: Dezembro 2025
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import datetime

from .models import (
    Orcamento, OrcamentoItem, OrcamentoHistorico,
    CondicaoPagamento, OrcamentoAnexo
)
from cadastros.models import Pessoa, Produto
from .services import OrcamentoService, RelatorioComercialService


# ==============================================================================
# LISTAR ORÇAMENTOS
# ==============================================================================

@login_required
def orcamento_list(request):
    """
    Lista orçamentos com filtros e paginação.
    """
    # Filtros
    orcamentos = Orcamento.objects.select_related(
        'cliente', 'vendedor', 'condicao_pagamento', 'obra_gerada'
    ).all()
    
    # Filtro por status
    status_filtro = request.GET.get('status', '')
    if status_filtro:
        orcamentos = orcamentos.filter(status=status_filtro)
    
    # Filtro por cliente
    cliente_id = request.GET.get('cliente', '')
    if cliente_id:
        orcamentos = orcamentos.filter(cliente_id=cliente_id)
    
    # Filtro por vendedor
    vendedor_id = request.GET.get('vendedor', '')
    if vendedor_id:
        orcamentos = orcamentos.filter(vendedor_id=vendedor_id)
    
    # Filtro por período
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    if data_inicio:
        orcamentos = orcamentos.filter(data_orcamento__gte=data_inicio)
    if data_fim:
        orcamentos = orcamentos.filter(data_orcamento__lte=data_fim)
    
    # Busca por número ou nome do cliente
    busca = request.GET.get('busca', '')
    if busca:
        orcamentos = orcamentos.filter(
            Q(numero__icontains=busca) |
            Q(cliente__nome_razao__icontains=busca)
        )
    
    # Ordenação
    ordem = request.GET.get('ordem', '-data_orcamento')
    orcamentos = orcamentos.order_by(ordem)
    
    # Paginação
    paginator = Paginator(orcamentos, 20)
    page = request.GET.get('page', 1)
    orcamentos_page = paginator.get_page(page)
    
    # Estatísticas
    stats = {
        'total_orcamentos': orcamentos.count(),
        'valor_total': orcamentos.aggregate(Sum('total'))['total__sum'] or Decimal('0.00'),
        'rascunho': orcamentos.filter(status='RASCUNHO').count(),
        'enviado': orcamentos.filter(status='ENVIADO').count(),
        'negociacao': orcamentos.filter(status='NEGOCIACAO').count(),
        'aprovado': orcamentos.filter(status='APROVADO').count(),
        'reprovado': orcamentos.filter(status='REPROVADO').count(),
    }
    
    context = {
        'orcamentos': orcamentos_page,
        'stats': stats,
        'status_choices': Orcamento.STATUS_CHOICES,
        'clientes': Pessoa.objects.filter(cliente=True).order_by('nome_razao'),
        'vendedores': request.user.__class__.objects.filter(is_active=True),
        'filtros': {
            'status': status_filtro,
            'cliente': cliente_id,
            'vendedor': vendedor_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'busca': busca,
        }
    }
    
    return render(request, 'vendas/orcamento_list.html', context)


# ==============================================================================
# CRIAR ORÇAMENTO
# ==============================================================================

@login_required
def orcamento_create(request):
    """
    Cria novo orçamento.
    """
    if request.method == 'POST':
        try:
            # Dados do orçamento
            cliente_id = request.POST.get('cliente')
            vendedor_id = request.POST.get('vendedor')
            condicao_id = request.POST.get('condicao_pagamento')
            
            cliente = get_object_or_404(Pessoa, id=cliente_id, cliente=True)
            vendedor = get_object_or_404(request.user.__class__, id=vendedor_id)
            condicao = get_object_or_404(CondicaoPagamento, id=condicao_id)
            
            # Criar orçamento
            orcamento = OrcamentoService.criar_orcamento(
                cliente=cliente,
                vendedor=vendedor,
                condicao_pagamento=condicao,
                criado_por=request.user,
                validade_dias=int(request.POST.get('validade_dias', 15)),
                prazo_execucao_dias=int(request.POST.get('prazo_execucao_dias', 30)),
                observacoes=request.POST.get('observacoes', '')
            )
            
            messages.success(request, f'Orçamento {orcamento.numero} criado com sucesso!')
            return redirect('vendas:orcamento_edit', pk=orcamento.pk)
        
        except Exception as e:
            messages.error(request, f'Erro ao criar orçamento: {str(e)}')
    
    # GET
    context = {
        'clientes': Pessoa.objects.filter(cliente=True, ativo=True).order_by('nome_razao'),
        'vendedores': request.user.__class__.objects.filter(is_active=True),
        'condicoes': CondicaoPagamento.objects.filter(ativo=True),
        'condicao_padrao': CondicaoPagamento.objects.filter(padrao=True).first(),
    }
    
    return render(request, 'vendas/orcamento_create.html', context)


# ==============================================================================
# EDITAR ORÇAMENTO
# ==============================================================================

@login_required
def orcamento_edit(request, pk):
    """
    Edita orçamento existente.
    Permite adicionar/editar/remover itens.
    """
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if request.method == 'POST':
        if not orcamento.pode_editar:
            messages.error(request, f'Orçamento {orcamento.numero} não pode ser editado (status: {orcamento.status})')
            return redirect('vendas:orcamento_detail', pk=pk)
        
        try:
            # Atualizar dados básicos
            orcamento.observacoes = request.POST.get('observacoes', '')
            orcamento.observacoes_internas = request.POST.get('observacoes_internas', '')
            orcamento.desconto = Decimal(request.POST.get('desconto', '0.00'))
            orcamento.frete = Decimal(request.POST.get('frete', '0.00'))
            orcamento.outras_despesas = Decimal(request.POST.get('outras_despesas', '0.00'))
            
            # Endereço de execução
            orcamento.endereco_execucao_logradouro = request.POST.get('endereco_logradouro', '')
            orcamento.endereco_execucao_numero = request.POST.get('endereco_numero', '')
            orcamento.endereco_execucao_complemento = request.POST.get('endereco_complemento', '')
            orcamento.endereco_execucao_bairro = request.POST.get('endereco_bairro', '')
            orcamento.endereco_execucao_cidade = request.POST.get('endereco_cidade', '')
            orcamento.endereco_execucao_estado = request.POST.get('endereco_estado', '')
            orcamento.endereco_execucao_cep = request.POST.get('endereco_cep', '')
            
            orcamento.calcular_totais()
            orcamento.save()
            
            messages.success(request, 'Orçamento atualizado com sucesso!')
            return redirect('vendas:orcamento_detail', pk=pk)
        
        except Exception as e:
            messages.error(request, f'Erro ao atualizar orçamento: {str(e)}')
    
    context = {
        'orcamento': orcamento,
        'itens': orcamento.itens.all(),
        'produtos': Produto.objects.filter(ativo=True).order_by('descricao'),
        'margem': OrcamentoService.calcular_margem_orcamento(orcamento),
    }
    
    return render(request, 'vendas/orcamento_edit.html', context)


# ==============================================================================
# ADICIONAR ITEM AO ORÇAMENTO (AJAX)
# ==============================================================================

@login_required
def orcamento_add_item(request, pk):
    """
    Adiciona item ao orçamento (AJAX).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if not orcamento.pode_editar:
        return JsonResponse({
            'success': False,
            'error': f'Orçamento não pode ser editado (status: {orcamento.status})'
        }, status=400)
    
    try:
        # Dados do item
        produto_id = request.POST.get('produto_id')
        produto = get_object_or_404(Produto, id=produto_id) if produto_id else None
        
        item = OrcamentoService.adicionar_item(
            orcamento=orcamento,
            produto=produto,
            descricao=request.POST.get('descricao', ''),
            quantidade=Decimal(request.POST.get('quantidade', '1.0')),
            unidade=request.POST.get('unidade', 'UN'),
            preco_unitario=Decimal(request.POST.get('preco_unitario', '0.00')),
            custo_unitario_estimado=Decimal(request.POST.get('custo_unitario', '0.00')),
            largura=Decimal(request.POST.get('largura', '0')) if request.POST.get('largura') else None,
            altura=Decimal(request.POST.get('altura', '0')) if request.POST.get('altura') else None,
            cor=request.POST.get('cor', ''),
            linha=request.POST.get('linha', ''),
            vidro=request.POST.get('vidro', ''),
            acabamento=request.POST.get('acabamento', ''),
            observacao_tecnica=request.POST.get('observacao_tecnica', '')
        )
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'total_orcamento': str(orcamento.total),
            'subtotal_orcamento': str(orcamento.subtotal)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
# REMOVER ITEM DO ORÇAMENTO (AJAX)
# ==============================================================================

@login_required
def orcamento_remove_item(request, pk, item_id):
    """
    Remove item do orçamento (AJAX).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    item = get_object_or_404(OrcamentoItem, pk=item_id, orcamento=orcamento)
    
    if not orcamento.pode_editar:
        return JsonResponse({
            'success': False,
            'error': f'Orçamento não pode ser editado (status: {orcamento.status})'
        }, status=400)
    
    try:
        item.delete()
        
        return JsonResponse({
            'success': True,
            'total_orcamento': str(orcamento.total),
            'subtotal_orcamento': str(orcamento.subtotal)
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==============================================================================
# DETALHAR ORÇAMENTO
# ==============================================================================

@login_required
def orcamento_detail(request, pk):
    """
    Exibe detalhes completos do orçamento.
    """
    orcamento = get_object_or_404(
        Orcamento.objects.select_related(
            'cliente', 'vendedor', 'condicao_pagamento', 'obra_gerada', 'aprovado_por'
        ),
        pk=pk
    )
    
    itens = orcamento.itens.all()
    historico = orcamento.historico.all()
    anexos = orcamento.anexos.all()
    margem = OrcamentoService.calcular_margem_orcamento(orcamento)
    
    context = {
        'orcamento': orcamento,
        'itens': itens,
        'historico': historico,
        'anexos': anexos,
        'margem': margem,
    }
    
    return render(request, 'vendas/orcamento_detail.html', context)


# ==============================================================================
# MUDAR STATUS
# ==============================================================================

@login_required
def orcamento_mudar_status(request, pk):
    """
    Muda status do orçamento.
    """
    if request.method != 'POST':
        messages.error(request, 'Método não permitido')
        return redirect('vendas:orcamento_detail', pk=pk)
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    novo_status = request.POST.get('novo_status')
    observacao = request.POST.get('observacao', '')
    
    try:
        OrcamentoService.mudar_status(
            orcamento=orcamento,
            novo_status=novo_status,
            usuario=request.user,
            observacao=observacao
        )
        
        messages.success(request, f'Status alterado para: {novo_status}')
    
    except Exception as e:
        messages.error(request, f'Erro ao mudar status: {str(e)}')
    
    return redirect('vendas:orcamento_detail', pk=pk)


# ==============================================================================
# APROVAR ORÇAMENTO
# ==============================================================================

@login_required
@transaction.atomic
def orcamento_aprovar(request, pk):
    """
    Aprova orçamento e gera Obra + Títulos.
    """
    if request.method != 'POST':
        messages.error(request, 'Método não permitido')
        return redirect('vendas:orcamento_detail', pk=pk)
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    observacao = request.POST.get('observacao', '')
    
    try:
        obra = OrcamentoService.aprovar_orcamento(
            orcamento=orcamento,
            usuario=request.user,
            observacao=observacao
        )
        
        messages.success(
            request, 
            f'Orçamento {orcamento.numero} aprovado com sucesso! ' +
            f'Obra {obra.codigo} criada.'
        )
        return redirect('projetos:obra_detail', pk=obra.pk)
    
    except Exception as e:
        messages.error(request, f'Erro ao aprovar orçamento: {str(e)}')
        return redirect('vendas:orcamento_detail', pk=pk)


# ==============================================================================
# REPROVAR ORÇAMENTO
# ==============================================================================

@login_required
def orcamento_reprovar(request, pk):
    """
    Reprova orçamento.
    """
    if request.method != 'POST':
        messages.error(request, 'Método não permitido')
        return redirect('vendas:orcamento_detail', pk=pk)
    
    orcamento = get_object_or_404(Orcamento, pk=pk)
    motivo = request.POST.get('motivo', '')
    
    if not motivo:
        messages.error(request, 'Motivo da reprovação é obrigatório')
        return redirect('vendas:orcamento_detail', pk=pk)
    
    try:
        OrcamentoService.reprovar_orcamento(
            orcamento=orcamento,
            usuario=request.user,
            motivo=motivo
        )
        
        messages.success(request, f'Orçamento {orcamento.numero} reprovado.')
        return redirect('vendas:orcamento_detail', pk=pk)
    
    except Exception as e:
        messages.error(request, f'Erro ao reprovar orçamento: {str(e)}')
        return redirect('vendas:orcamento_detail', pk=pk)


# ==============================================================================
# GERAR PDF (placeholder - implementar com ReportLab)
# ==============================================================================

@login_required
def orcamento_pdf(request, pk):
    """
    Gera proposta comercial em PDF.
    TODO: Implementar com ReportLab.
    """
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Placeholder - retornar HTML simples por enquanto
    return HttpResponse(
        f"<h1>Proposta Comercial - {orcamento.numero}</h1>" +
        f"<p>Cliente: {orcamento.cliente.nome_razao}</p>" +
        f"<p>Valor: R$ {orcamento.total:,.2f}</p>" +
        "<p><em>PDF em desenvolvimento (usar ReportLab)</em></p>",
        content_type='text/html'
    )


# ==============================================================================
# RELATÓRIOS COMERCIAIS
# ==============================================================================

@login_required
def relatorio_funil_vendas(request):
    """
    Relatório: Funil de vendas.
    """
    data_inicio = request.GET.get('data_inicio', str(datetime.date.today().replace(day=1)))
    data_fim = request.GET.get('data_fim', str(datetime.date.today()))
    
    funil = RelatorioComercialService.funil_vendas(
        datetime.date.fromisoformat(data_inicio),
        datetime.date.fromisoformat(data_fim)
    )
    
    context = {
        'funil': funil,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'vendas/relatorio_funil.html', context)


@login_required
def relatorio_conversao_vendedor(request):
    """
    Relatório: Taxa de conversão por vendedor.
    """
    data_inicio = request.GET.get('data_inicio', str(datetime.date.today().replace(day=1)))
    data_fim = request.GET.get('data_fim', str(datetime.date.today()))
    
    vendedores = RelatorioComercialService.taxa_conversao_vendedor(
        datetime.date.fromisoformat(data_inicio),
        datetime.date.fromisoformat(data_fim)
    )
    
    context = {
        'vendedores': vendedores,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'vendas/relatorio_conversao.html', context)


@login_required
def relatorio_backlog(request):
    """
    Relatório: Backlog de obras.
    """
    data_referencia = request.GET.get('data_referencia', str(datetime.date.today()))
    
    backlog = RelatorioComercialService.backlog_obras(
        datetime.date.fromisoformat(data_referencia)
    )
    
    context = {
        'backlog': backlog,
        'data_referencia': data_referencia,
    }
    
    return render(request, 'vendas/relatorio_backlog.html', context)
