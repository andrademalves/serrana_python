from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from usuarios.decorators import verificar_permissao_menu, require_empresa
from .models import Orcamento, OrcamentoItem, Projeto, VendaDireta, VendaDiretaItem, VisitaTecnica
from .forms import (
    OrcamentoForm, OrcamentoItemFormSet, OrcamentoParcelaFormSet, ProjetoForm,
    VendaDiretaForm, VendaDiretaItemFormSet, VisitaTecnicaForm
)
from estoque.models import Item
from cadastros.models import Produto

# Imports para geração de PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, KeepTogether
from reportlab.pdfgen import canvas
import io


@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def dashboard(request):
    """Dashboard do módulo de projetos"""
    # Estatísticas
    total_orcamentos = Orcamento.objects.count()
    orcamentos_pendentes = Orcamento.objects.filter(status='PENDENTE').count()
    
    total_projetos = Projeto.objects.count()
    projetos_ativos = Projeto.objects.filter(status__in=['ORCAMENTO', 'EM_ANDAMENTO']).count()
    
    total_vendas = VendaDireta.objects.count()
    vendas_mes = VendaDireta.objects.filter(
        data_venda__month=datetime.now().month,
        data_venda__year=datetime.now().year
    ).count()
    
    # Últimos orçamentos
    ultimos_orcamentos = Orcamento.objects.all().order_by('-criado_em')[:5]
    
    # Projetos em andamento
    projetos_andamento = Projeto.objects.filter(
        status='EM_ANDAMENTO'
    ).order_by('-data_inicio_real')[:5]
    
    context = {
        'titulo': 'Dashboard - Orçamentos e Projetos',
        'current_module': 'projetos',
        'total_orcamentos': total_orcamentos,
        'orcamentos_pendentes': orcamentos_pendentes,
        'total_projetos': total_projetos,
        'projetos_ativos': projetos_ativos,
        'total_vendas': total_vendas,
        'vendas_mes': vendas_mes,
        'ultimos_orcamentos': ultimos_orcamentos,
        'projetos_andamento': projetos_andamento,
    }
    return render(request, 'projetos/dashboard.html', context)


@login_required
def buscar_dados_visitas_orcamento(request, orcamento_id):
    """Retorna dados de visitas técnicas de um orçamento via AJAX"""
    try:
        orcamento = get_object_or_404(Orcamento, pk=orcamento_id)
        visitas = orcamento.visitas_tecnicas.all()
        
        total_visitas = visitas.count()
        visitas_cobradas = visitas.filter(valor_cobrado__gt=0).count()
        
        # Calcular valores
        valor_total_visitas = Decimal('0.00')
        for visita in visitas.filter(valor_cobrado__gt=0):
            valor_total_visitas += visita.valor_cobrado
        
        # Calcular valor médio por visita
        valor_por_visita = Decimal('0.00')
        if visitas_cobradas > 0:
            valor_por_visita = valor_total_visitas / visitas_cobradas
        
        return JsonResponse({
            'success': True,
            'num_visitas_tecnicas': total_visitas,
            'num_visitas_cobradas': visitas_cobradas,
            'valor_visita': float(valor_por_visita),
            'valor_total_visitas': float(valor_total_visitas)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def listar_orcamentos(request):
    """Lista todos os orçamentos com filtros e paginação"""
    from django.core.paginator import Paginator
    from cadastros.models import Pessoa
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Base queryset
    orcamentos = Orcamento.objects.select_related('cliente', 'vendedor').all()
    
    # Filtros
    numero = request.GET.get('numero', '').strip()
    cliente_id = request.GET.get('cliente', '').strip()
    vendedor_id = request.GET.get('vendedor', '').strip()
    data_inicial = request.GET.get('data_inicial', '').strip()
    data_final = request.GET.get('data_final', '').strip()
    status = request.GET.get('status', '').strip()
    
    # Aplicar filtros
    if numero:
        orcamentos = orcamentos.filter(codigo__icontains=numero)
    
    if cliente_id:
        orcamentos = orcamentos.filter(cliente_id=cliente_id)
    
    if vendedor_id:
        orcamentos = orcamentos.filter(vendedor_id=vendedor_id)
    
    if data_inicial:
        try:
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            orcamentos = orcamentos.filter(data_orcamento__gte=data_inicial_obj)
        except ValueError:
            pass
    
    if data_final:
        try:
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
            orcamentos = orcamentos.filter(data_orcamento__lte=data_final_obj)
        except ValueError:
            pass
    
    if status:
        orcamentos = orcamentos.filter(status=status)
    
    # Ordenação
    orcamentos = orcamentos.order_by('-criado_em')
    
    # Paginação
    por_pagina = request.GET.get('por_pagina', '10')
    try:
        por_pagina = int(por_pagina)
        if por_pagina not in [10, 20, 30, 40, 50, 100]:
            por_pagina = 10
    except ValueError:
        por_pagina = 10
    
    paginator = Paginator(orcamentos, por_pagina)
    pagina = request.GET.get('page', 1)
    
    try:
        orcamentos_paginados = paginator.page(pagina)
    except:
        orcamentos_paginados = paginator.page(1)
    
    # Dados para os selects
    clientes = Pessoa.objects.filter(cliente=True, ativo=True).order_by('nome')
    vendedores = Pessoa.objects.filter(vendedor=True, ativo=True).order_by('nome')
    
    context = {
        'titulo': 'Orçamentos',
        'current_module': 'projetos',
        'orcamentos': orcamentos_paginados,
        'clientes': clientes,
        'vendedores': vendedores,
        'status_choices': Orcamento.STATUS_CHOICES,
        'filtros': {
            'numero': numero,
            'cliente': cliente_id,
            'vendedor': vendedor_id,
            'data_inicial': data_inicial,
            'data_final': data_final,
            'status': status,
            'por_pagina': por_pagina,
        },
        'total_registros': paginator.count,
    }
    return render(request, 'projetos/listar_orcamentos.html', context)


@login_required
def visualizar_orcamento(request, pk):
    """Visualiza resumo do orçamento"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Calcular total dos itens
    total_itens = sum(item.valor_total for item in orcamento.itens.all())
    orcamento.valor_total = total_itens
    orcamento.valor_final = total_itens - orcamento.desconto
    orcamento.save()
    
    context = {
        'titulo': f'Orçamento {orcamento.codigo}',
        'current_module': 'projetos',
        'orcamento': orcamento,
        'itens': orcamento.itens.all()
    }
    return render(request, 'projetos/visualizar_orcamento.html', context)


@login_required
def buscar_itens_por_tipo(request):
    """Retorna itens filtrados por tipo (AJAX)"""
    tipo = request.GET.get('tipo', '')
    itens = []
    
    if tipo == 'PRODUTO':
        # Buscar do modelo Produto (cadastros)
        produtos = Produto.objects.filter(ativo=True, tipo='produto').order_by('descricao')
        itens = [{'id': f'produto_{p.id}', 'text': f'{p.codigo} - {p.descricao}'} for p in produtos]
        
        # Também buscar Itens do Estoque (produtos acabados)
        itens_estoque = Item.objects.filter(
            ativo=True, 
            tipo_item__in=['PA', 'SEMI']
        ).order_by('descricao')
        itens.extend([{'id': f'item_{i.id}', 'text': f'{i.codigo} - {i.descricao}'} for i in itens_estoque])
        
    elif tipo == 'MATERIAL':
        # Buscar Materiais do Estoque (matéria-prima e consumíveis)
        materiais = Item.objects.filter(
            ativo=True,
            tipo_item__in=['MP', 'CONSUMIVEL']
        ).order_by('descricao')
        itens = [{'id': f'item_{m.id}', 'text': f'{m.codigo} - {m.descricao}'} for m in materiais]
        
    elif tipo == 'SERVICO':
        # Buscar serviços do modelo Produto
        servicos = Produto.objects.filter(ativo=True, tipo='servico').order_by('descricao')
        itens = [{'id': f'servico_{s.id}', 'text': f'{s.codigo} - {s.descricao}'} for s in servicos]
        
    elif tipo == 'MAO_OBRA':
        # Para mão de obra, permitir entrada manual (sem vincular a um item específico)
        itens = [{'id': 'mao_obra_manual', 'text': 'Entrada Manual'}]
    
    return JsonResponse({'results': itens})


@login_required
def buscar_dados_item(request):
    """Retorna dados de um item específico (preço, unidade, etc) para preencher o formulário"""
    item_id = request.GET.get('item_id', '')
    
    if not item_id:
        return JsonResponse({'success': False, 'error': 'Item ID não fornecido'})
    
    try:
        # Identificar o tipo e ID do item
        tipo, id_num = item_id.split('_', 1)
        
        if tipo == 'produto' or tipo == 'servico':
            # Buscar do modelo Produto
            item = Produto.objects.get(id=id_num, ativo=True)
            return JsonResponse({
                'success': True,
                'preco_venda': float(item.preco_venda or 0),
                'unidade': item.unidade or 'UN',
                'descricao': item.descricao
            })
            
        elif tipo == 'item':
            # Buscar do modelo Item (estoque)
            item = Item.objects.get(id=id_num, ativo=True)
            return JsonResponse({
                'success': True,
                'preco_venda': float(item.preco_venda or 0),
                'unidade': item.unidade or 'UN',
                'descricao': item.descricao
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Item não encontrado'})


@login_required
def criar_orcamento(request):
    """Cria novo orçamento"""
    if request.method == 'POST':
        form = OrcamentoForm(request.POST)
        formset_itens = OrcamentoItemFormSet(request.POST, prefix='itens')
        formset_parcelas = OrcamentoParcelaFormSet(request.POST, prefix='parcelas')
        
        print("=== DEBUG CRIAR ORCAMENTO ===")
        print(f"Form válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"Erros do form: {form.errors}")
        
        print(f"Formset itens válido: {formset_itens.is_valid()}")
        if not formset_itens.is_valid():
            print(f"Erros do formset itens: {formset_itens.errors}")
            print(f"Erros non-form: {formset_itens.non_form_errors()}")
        
        print(f"Formset parcelas válido: {formset_parcelas.is_valid()}")
        if not formset_parcelas.is_valid():
            print(f"Erros do formset parcelas: {formset_parcelas.errors}")
            print(f"Erros non-form: {formset_parcelas.non_form_errors()}")
        
        if form.is_valid() and formset_itens.is_valid() and formset_parcelas.is_valid():
            orcamento = form.save(commit=False)
            orcamento.criado_por = request.user
            orcamento.atualizado_por = request.user
            
            # Calcular valor_total somando itens
            valor_total = Decimal('0.00')
            for item_form in formset_itens:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    qtd = item_form.cleaned_data.get('quantidade', 0) or 0
                    valor_unit = item_form.cleaned_data.get('valor_unitario', 0) or 0
                    desconto_item = item_form.cleaned_data.get('desconto', 0) or 0
                    
                    # Converter para Decimal tratando valores vazios
                    try:
                        qtd_decimal = Decimal(str(qtd)) if qtd else Decimal('0')
                        valor_unit_decimal = Decimal(str(valor_unit)) if valor_unit else Decimal('0')
                        desconto_decimal = Decimal(str(desconto_item)) if desconto_item else Decimal('0')
                        valor_total += (qtd_decimal * valor_unit_decimal) - desconto_decimal
                    except (ValueError, TypeError, InvalidOperation):
                        # Se houver erro na conversão, ignora o item
                        continue
            
            orcamento.valor_total = valor_total
            orcamento.save()
            
            # Salvar itens
            formset_itens.instance = orcamento
            itens_salvos = formset_itens.save(commit=False)
            
            # Processar cada item para buscar código
            for item in itens_salvos:
                # Se tem item_ref, buscar o código correspondente
                if item.item_ref and '_' in item.item_ref:
                    try:
                        prefixo, item_id = item.item_ref.split('_', 1)
                        
                        if prefixo in ['produto', 'servico']:
                            from cadastros.models import Produto
                            produto = Produto.objects.get(pk=int(item_id))
                            item.item_codigo = produto.codigo
                        elif prefixo == 'item':
                            from estoque.models import Item as EstoqueItem
                            estoque_item = EstoqueItem.objects.get(pk=int(item_id))
                            item.item_codigo = estoque_item.codigo
                    except:
                        pass  # Se não encontrar, deixa vazio
                
                item.save()
            
            # Deletar itens marcados para exclusão
            formset_itens.save_m2m()
            
            print(f"Itens salvos: {len(itens_salvos)}")
            for item in itens_salvos:
                print(f"  - {item.tipo}: {item.descricao} (ref: {item.item_ref}, cod: {item.item_codigo})")
            
            # Salvar parcelas
            formset_parcelas.instance = orcamento
            parcelas_salvas = formset_parcelas.save()
            print(f"Parcelas salvas: {len(parcelas_salvas)}")
            
            messages.success(request, f'Orçamento {orcamento.codigo} criado com sucesso!')
            return redirect('projetos:visualizar_orcamento', pk=orcamento.pk)
    else:
        form = OrcamentoForm()
        formset_itens = OrcamentoItemFormSet(prefix='itens')
        formset_parcelas = OrcamentoParcelaFormSet(prefix='parcelas')
    
    context = {
        'titulo': 'Novo Orçamento',
        'current_module': 'projetos',
        'form': form,
        'formset': formset_itens,
        'formset_parcelas': formset_parcelas
    }
    return render(request, 'projetos/criar_orcamento.html', context)


@login_required
def editar_orcamento(request, pk):
    """Edita um orçamento existente"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento)
        formset_itens = OrcamentoItemFormSet(request.POST, instance=orcamento, prefix='itens')
        formset_parcelas = OrcamentoParcelaFormSet(request.POST, instance=orcamento, prefix='parcelas')
        
        if form.is_valid() and formset_itens.is_valid() and formset_parcelas.is_valid():
            orcamento = form.save(commit=False)
            orcamento.atualizado_por = request.user
            
            # Calcular valor_total somando itens
            valor_total = Decimal('0.00')
            for item_form in formset_itens:
                if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                    qtd = item_form.cleaned_data.get('quantidade', 0) or 0
                    valor_unit = item_form.cleaned_data.get('valor_unitario', 0) or 0
                    desconto_item = item_form.cleaned_data.get('desconto', 0) or 0
                    
                    # Converter para Decimal tratando valores vazios
                    try:
                        qtd_decimal = Decimal(str(qtd)) if qtd else Decimal('0')
                        valor_unit_decimal = Decimal(str(valor_unit)) if valor_unit else Decimal('0')
                        desconto_decimal = Decimal(str(desconto_item)) if desconto_item else Decimal('0')
                        valor_total += (qtd_decimal * valor_unit_decimal) - desconto_decimal
                    except (ValueError, TypeError, InvalidOperation):
                        # Se houver erro na conversão, ignora o item
                        continue
            
            orcamento.valor_total = valor_total
            orcamento.save()
            
            # Salvar itens
            itens_salvos = formset_itens.save(commit=False)
            
            # Processar cada item para buscar código
            for item in itens_salvos:
                # Se tem item_ref, buscar o código correspondente
                if item.item_ref and '_' in item.item_ref:
                    try:
                        prefixo, item_id = item.item_ref.split('_', 1)
                        
                        if prefixo in ['produto', 'servico']:
                            from cadastros.models import Produto
                            produto = Produto.objects.get(pk=int(item_id))
                            item.item_codigo = produto.codigo
                        elif prefixo == 'item':
                            from estoque.models import Item as EstoqueItem
                            estoque_item = EstoqueItem.objects.get(pk=int(item_id))
                            item.item_codigo = estoque_item.codigo
                    except:
                        pass  # Se não encontrar, deixa vazio
                
                item.save()
            
            # Processar exclusões
            for item in formset_itens.deleted_objects:
                item.delete()
            
            # Salvar parcelas
            formset_parcelas.save()
            
            messages.success(request, f'Orçamento {orcamento.codigo} atualizado com sucesso!')
            return redirect('projetos:visualizar_orcamento', pk=orcamento.pk)
    else:
        form = OrcamentoForm(instance=orcamento)
        # Criar formset com select_related para carregar os itens relacionados
        formset_itens = OrcamentoItemFormSet(
            instance=orcamento, 
            prefix='itens',
            queryset=OrcamentoItem.objects.filter(orcamento=orcamento).select_related('item')
        )
        formset_parcelas = OrcamentoParcelaFormSet(instance=orcamento, prefix='parcelas')
    
    context = {
        'titulo': f'Editar Orçamento {orcamento.codigo}',
        'current_module': 'projetos',
        'form': form,
        'formset': formset_itens,
        'formset_parcelas': formset_parcelas,
        'orcamento': orcamento,
        'edicao': True
    }
    return render(request, 'projetos/criar_orcamento.html', context)


@login_required
def aprovar_orcamento(request, pk):
    """Aprova o orçamento e redireciona para criar projeto"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Atualizar status para APROVADO
    orcamento.status = 'APROVADO'
    orcamento.save()
    
    messages.success(request, f'Orçamento {orcamento.codigo} aprovado com sucesso!')
    
    # Redirecionar para criar projeto com o orçamento_id na URL
    return redirect(f'/projetos/projetos/criar/?orcamento_id={orcamento.pk}')


@login_required
def rejeitar_orcamento(request, pk):
    """Rejeita o orçamento"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Atualizar status para REJEITADO
    orcamento.status = 'REJEITADO'
    orcamento.save()
    
    messages.warning(request, f'Orçamento {orcamento.codigo} foi rejeitado.')
    
    # Redirecionar de volta para lista de orçamentos
    return redirect('projetos:listar_orcamentos')


@login_required
def listar_projetos(request):
    """Lista todos os projetos"""
    projetos = Projeto.objects.all().order_by('-criado_em')
    context = {
        'titulo': 'Projetos',
        'current_module': 'projetos',
        'projetos': projetos
    }
    return render(request, 'projetos/listar_projetos.html', context)


@login_required
def criar_projeto(request):
    """Cria novo projeto"""
    # Verificar se vem de um orçamento aprovado
    orcamento_id = request.GET.get('orcamento_id') or request.POST.get('orcamento_id')
    orcamento = None
    
    if orcamento_id:
        orcamento = get_object_or_404(Orcamento, pk=orcamento_id)
    
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        
        if form.is_valid():
            projeto = form.save(commit=False)
            projeto.criado_por = request.user
            
            # Se veio de um orçamento, garantir que o cliente seja o do orçamento
            # (campo disabled não é enviado pelo navegador)
            if orcamento:
                projeto.cliente = orcamento.cliente
                # Definir status como AGUARDANDO (já não é mais orçamento)
                if projeto.status == 'ORCAMENTO':
                    projeto.status = 'AGUARDANDO'
            
            projeto.save()
            
            # Se veio de um orçamento, atualizar status para CONVERTIDO
            if orcamento:
                orcamento.status = 'CONVERTIDO'
                orcamento.save()
            
            messages.success(request, f'Projeto "{projeto.descricao}" criado com sucesso!')
            return redirect('projetos:listar_projetos')
    else:
        # Se tem orçamento, pré-preencher os dados
        if orcamento:
            # Calcular dados de visitas técnicas
            visitas = orcamento.visitas_tecnicas.all()
            total_visitas = visitas.count()
            visitas_cobradas = visitas.filter(valor_cobrado__gt=0).count()
            
            # Calcular valores
            valor_total_visitas = Decimal('0.00')
            for visita in visitas.filter(valor_cobrado__gt=0):
                valor_total_visitas += visita.valor_cobrado
            
            # Calcular valor médio por visita
            valor_por_visita = Decimal('0.00')
            if visitas_cobradas > 0:
                valor_por_visita = valor_total_visitas / visitas_cobradas
            
            initial_data = {
                'orcamento': orcamento,
                'cliente': orcamento.cliente,
                'vendedor': orcamento.vendedor,
                'descricao': f'Projeto gerado do orçamento {orcamento.codigo}',
                'data_orcamento': orcamento.data_orcamento,
                'valor_orcado': orcamento.valor_total,
                'num_visitas_tecnicas': total_visitas,
                'num_visitas_cobradas': visitas_cobradas,
                'valor_visita': valor_por_visita,
                'valor_total_visitas': valor_total_visitas,
                'status': 'AGUARDANDO'  # Projeto criado a partir de orçamento já começa aguardando
            }
            form = ProjetoForm(initial=initial_data)
        else:
            form = ProjetoForm()
    
    context = {
        'titulo': 'Novo Projeto',
        'current_module': 'projetos',
        'form': form,
        'orcamento': orcamento
    }
    return render(request, 'projetos/criar_projeto.html', context)


@login_required
def visualizar_projeto(request, pk):
    """Visualiza detalhes do projeto"""
    projeto = get_object_or_404(Projeto, pk=pk)
    
    # Buscar visitas técnicas relacionadas ao orçamento do projeto
    total_visitas = 0
    visitas_cobradas = 0
    valor_total_visitas = Decimal('0.00')
    
    if projeto.orcamento:
        visitas = projeto.orcamento.visitas_tecnicas.all()
        total_visitas = visitas.count()
        visitas_cobradas = visitas.filter(valor_cobrado__gt=0).count()
        
        # Calcular valor total das visitas cobradas
        for visita in visitas.filter(valor_cobrado__gt=0):
            valor_total_visitas += visita.valor_cobrado
    
    context = {
        'titulo': f'Projeto {projeto.codigo}',
        'current_module': 'projetos',
        'projeto': projeto,
        'total_visitas': total_visitas,
        'visitas_cobradas': visitas_cobradas,
        'valor_total_visitas': valor_total_visitas,
    }
    return render(request, 'projetos/visualizar_projeto.html', context)


@login_required
def editar_projeto(request, pk):
    """Edita um projeto existente"""
    projeto = get_object_or_404(Projeto, pk=pk)
    
    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        
        if form.is_valid():
            projeto_editado = form.save(commit=False)
            projeto_editado.atualizado_por = request.user
            
            # Garantir que orçamento e cliente não sejam alterados
            # (campos disabled não são enviados pelo navegador)
            projeto_editado.orcamento = projeto.orcamento
            if projeto.orcamento:
                projeto_editado.cliente = projeto.cliente
            
            projeto_editado.save()
            
            messages.success(request, f'Projeto "{projeto_editado.descricao}" atualizado com sucesso!')
            return redirect('projetos:visualizar_projeto', pk=projeto_editado.pk)
    else:
        form = ProjetoForm(instance=projeto)
        
        # Se o projeto tem orçamento, buscar dados das visitas técnicas
        if projeto.orcamento:
            visitas = projeto.orcamento.visitas_tecnicas.all()
            total_visitas = visitas.count()
            visitas_cobradas = visitas.filter(valor_cobrado__gt=0).count()
            
            # Calcular valores
            valor_total_visitas = Decimal('0.00')
            for visita in visitas.filter(valor_cobrado__gt=0):
                valor_total_visitas += visita.valor_cobrado
            
            # Calcular valor médio por visita
            valor_por_visita = Decimal('0.00')
            if visitas_cobradas > 0:
                valor_por_visita = valor_total_visitas / visitas_cobradas
            
            # Atualizar os campos do formulário com dados atualizados das visitas
            form.fields['num_visitas_tecnicas'].initial = total_visitas
            form.fields['num_visitas_cobradas'].initial = visitas_cobradas
            form.fields['valor_visita'].initial = valor_por_visita
            form.fields['valor_total_visitas'].initial = valor_total_visitas
    
    context = {
        'titulo': f'Editar Projeto {projeto.codigo}',
        'current_module': 'projetos',
        'form': form,
        'projeto': projeto,
        'edicao': True
    }
    return render(request, 'projetos/criar_projeto.html', context)


@login_required
def listar_vendas(request):
    """Lista todas as vendas diretas"""
    vendas = VendaDireta.objects.all().order_by('-data_venda')
    context = {
        'titulo': 'Vendas Diretas',
        'current_module': 'projetos',
        'vendas': vendas
    }
    return render(request, 'projetos/listar_vendas.html', context)


@login_required
def criar_venda(request):
    """Cria nova venda direta"""
    if request.method == 'POST':
        form = VendaDiretaForm(request.POST)
        formset = VendaDiretaItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            venda = form.save(commit=False)
            venda.criado_por = request.user
            venda.save()
            
            formset.instance = venda
            formset.save()
            
            messages.success(request, f'Venda #{venda.numero} criada com sucesso!')
            return redirect('projetos:listar_vendas')
    else:
        form = VendaDiretaForm()
        formset = VendaDiretaItemFormSet()
    
    context = {
        'titulo': 'Nova Venda',
        'current_module': 'projetos',
        'form': form,
        'formset': formset
    }
    return render(request, 'projetos/criar_venda.html', context)


@login_required
def imprimir_orcamento_pdf(request, pk):
    """Gera PDF do orçamento com ReportLab"""
    orcamento = get_object_or_404(Orcamento, pk=pk)
    
    # Criar buffer de memória
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=10*mm,
        bottomMargin=20*mm
    )
    
    # Container para elementos do PDF
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    style_heading = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6
    )
    
    # Logo à direita no topo
    empresa = request.empresa
    
    # Tentar carregar logo
    if empresa and empresa.logo:
        try:
            import os
            if os.path.exists(empresa.logo.path):
                logo_img = Image(empresa.logo.path, width=3*cm, height=3*cm)
                logo_img.hAlign = 'RIGHT'
                elements.append(logo_img)
        except Exception:
            pass
    
    elements.append(Spacer(1, 0.5*cm))
    
    # Cabeçalho do Orçamento
    titulo_orcamento = ParagraphStyle(
        'TituloOrcamento',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    data_style = ParagraphStyle(
        'DataOrcamento',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_RIGHT
    )
    
    # Tabela com título e data
    header_data = [[
        Paragraph(f'ORÇAMENTO Nº {orcamento.codigo}', titulo_orcamento),
        Paragraph(f"Data: {orcamento.data_orcamento.strftime('%d/%m/%Y')}", data_style)
    ]]
    header_table = Table(header_data, colWidths=[12*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))
    
    # Validade
    validade_style = ParagraphStyle(
        'Validade',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT
    )
    elements.append(Paragraph(f"Válido por {orcamento.validade_dias} dias", validade_style))
    elements.append(Spacer(1, 6*mm))
    
    # Box de informações do Cliente
    cliente_heading = ParagraphStyle(
        'ClienteHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Construir endereço completo
    endereco_parts = []
    if orcamento.cliente.logradouro:
        endereco_parts.append(orcamento.cliente.logradouro)
    if orcamento.cliente.numero:
        endereco_parts.append(f"nº {orcamento.cliente.numero}")
    if orcamento.cliente.complemento:
        endereco_parts.append(orcamento.cliente.complemento)
    if orcamento.cliente.bairro:
        endereco_parts.append(orcamento.cliente.bairro)
    if orcamento.cliente.cidade and orcamento.cliente.uf:
        endereco_parts.append(f"{orcamento.cliente.cidade}/{orcamento.cliente.uf}")
    if orcamento.cliente.cep:
        endereco_parts.append(f"CEP: {orcamento.cliente.cep}")
    
    endereco_completo = ', '.join(endereco_parts) if endereco_parts else 'Não informado'
    
    # Cabeçalho do box cliente
    cliente_header = [[Paragraph('CLIENTE', cliente_heading)]]
    header_table = Table(cliente_header, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    
    # Dados do cliente
    cliente_data = [
        ['Nome:', orcamento.cliente.nome],
        ['CPF/CNPJ:', orcamento.cliente.cpf_cnpj or 'Não informado'],
        ['Telefone:', orcamento.cliente.telefone or orcamento.cliente.celular1 or 'Não informado'],
        ['E-mail:', orcamento.cliente.email or 'Não informado'],
        ['Endereço:', endereco_completo],
    ]
    
    cliente_table = Table(cliente_data, colWidths=[35*mm, 135*mm])
    cliente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 8*mm))
    
    # Box de informações do Vendedor
    vendedor_header = [[Paragraph('VENDEDOR', cliente_heading)]]
    vendedor_header_table = Table(vendedor_header, colWidths=[17*cm])
    vendedor_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(vendedor_header_table)
    
    # Telefone do vendedor - se não tiver, usa o telefone da empresa
    telefone_vendedor = orcamento.vendedor.telefone or orcamento.vendedor.celular1
    if not telefone_vendedor:
        telefone_vendedor = empresa.telefone or empresa.celular or 'Não informado'
    
    vendedor_data = [
        ['Vendedor:', orcamento.vendedor.nome],
        ['Telefone:', telefone_vendedor],
    ]
    
    vendedor_table = Table(vendedor_data, colWidths=[35*mm, 135*mm])
    vendedor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    elements.append(vendedor_table)
    elements.append(Spacer(1, 8*mm))
    
    # Itens do Orçamento
    itens_heading = ParagraphStyle(
        'ItensHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    itens_header = [[Paragraph('ITENS DO ORÇAMENTO', itens_heading)]]
    itens_header_table = Table(itens_header, colWidths=[17*cm])
    itens_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(itens_header_table)
    elements.append(Spacer(1, 3*mm))
    
    # Cabeçalho da tabela de itens
    itens_data = [
        ['#', 'Tipo', 'Item', 'Descrição', 'Qtd', 'Vlr. Unit.', 'Desconto', 'Total']
    ]
    
    # Adicionar itens
    for idx, item in enumerate(orcamento.itens.all(), 1):
        # Buscar o código e descrição do item original
        item_original = '-'
        if item.item_ref and '_' in item.item_ref:
            try:
                prefixo, item_id = item.item_ref.split('_', 1)
                
                if prefixo == 'produto':
                    from cadastros.models import Produto
                    produto = Produto.objects.get(pk=int(item_id))
                    item_original = f"{produto.codigo} - {produto.descricao[:25]}"
                elif prefixo == 'servico':
                    from cadastros.models import Produto
                    servico = Produto.objects.get(pk=int(item_id))
                    item_original = f"{servico.codigo} - {servico.descricao[:25]}"
                elif prefixo == 'item':
                    from estoque.models import Item
                    estoque_item = Item.objects.get(pk=int(item_id))
                    item_original = f"{estoque_item.codigo} - {estoque_item.descricao[:25]}"
            except:
                if item.item_codigo:
                    item_original = item.item_codigo
        elif item.item:
            item_original = f"{item.item.codigo} - {item.item.descricao[:25]}"
        
        itens_data.append([
            str(idx),
            item.get_tipo_display(),
            item_original,
            item.descricao[:25],  # Limitar descrição
            f'{item.quantidade:.2f}'.replace('.', ','),
            f'R$ {item.valor_unitario:.2f}'.replace('.', ','),
            f'R$ {item.desconto:.2f}'.replace('.', ','),
            f'R$ {item.valor_total:.2f}'.replace('.', ','),
        ])
    
    itens_table = Table(
        itens_data,
        colWidths=[8*mm, 17*mm, 42*mm, 33*mm, 15*mm, 20*mm, 20*mm, 15*mm],
        repeatRows=1
    )
    itens_table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Corpo da tabela
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Primeira coluna (número)
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Colunas numéricas à direita
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    elements.append(itens_table)
    elements.append(Spacer(1, 8*mm))
    
    # Totais com destaque
    totais_data = []
    
    if orcamento.tipo_desconto != 'NENHUM':
        totais_data.append(['Subtotal:', f'R$ {orcamento.valor_total:.2f}'.replace('.', ',')])
        if orcamento.tipo_desconto == 'PERCENTUAL':
            totais_data.append([
                f'Desconto ({orcamento.desconto_valor:.2f}%):',
                f'- R$ {orcamento.desconto:.2f}'.replace('.', ',')
            ])
        else:
            totais_data.append([
                'Desconto:',
                f'- R$ {orcamento.desconto:.2f}'.replace('.', ',')
            ])
    
    totais_data.append(['VALOR TOTAL:', f'R$ {orcamento.valor_final:.2f}'.replace('.', ',')])
    
    totais_table = Table(totais_data, colWidths=[14*cm, 3*cm])
    totais_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(totais_table)
    
    # Condições de Pagamento com box estilizado
    parcelas = orcamento.parcelas.all()
    if parcelas.exists():
        elements.append(Spacer(1, 10*mm))
        
        # Cabeçalho do box de condições de pagamento
        pagamento_heading = ParagraphStyle(
            'PagamentoHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        )
        
        pagamento_header = [[Paragraph('CONDIÇÕES DE PAGAMENTO', pagamento_heading)]]
        pagamento_header_table = Table(pagamento_header, colWidths=[17*cm])
        pagamento_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        # Dados das parcelas
        parcelas_data = [
            ['Parcela', 'Descrição', 'Vencimento', 'Valor', 'Forma Pagto.']
        ]
        
        parcela_desc_style = ParagraphStyle(
            'ParcelaDesc',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333')
        )
        
        for parcela in parcelas:
            parcelas_data.append([
                str(parcela.numero_parcela),
                Paragraph(parcela.descricao, parcela_desc_style),
                parcela.data_vencimento.strftime('%d/%m/%Y'),
                f'R$ {parcela.valor:.2f}'.replace('.', ','),
                Paragraph(parcela.get_forma_pagamento_display(), parcela_desc_style),
            ])
        
        parcelas_table = Table(
            parcelas_data,
            colWidths=[15*mm, 60*mm, 25*mm, 25*mm, 45*mm],
            repeatRows=1
        )
        parcelas_table.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Corpo
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        # Agrupar cabeçalho e tabela para ficarem sempre juntos na mesma página
        pagamento_elements = [
            pagamento_header_table,
            Spacer(1, 3*mm),
            parcelas_table
        ]
        elements.append(KeepTogether(pagamento_elements))
    
    # Observações
    if orcamento.observacoes:
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph('OBSERVAÇÕES', style_heading))
        elements.append(Paragraph(orcamento.observacoes, style_normal))
    
    # Espaço antes das assinaturas
    elements.append(Spacer(1, 20*mm))
    
    # Linha para assinatura do cliente
    assinatura_data = [
        [Paragraph('_' * 40, style_normal), Paragraph('_' * 40, style_normal)]
    ]
    assinatura_table = Table(assinatura_data, colWidths=[8.5*cm, 8.5*cm])
    assinatura_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(assinatura_table)
    
    # Labels das assinaturas
    label_style = ParagraphStyle(
        'LabelAssinatura',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    label_data = [[
        Paragraph('ASSINATURA DO CLIENTE', label_style),
        Paragraph('ASSINATURA DA EMPRESA', label_style)
    ]]
    label_table = Table(label_data, colWidths=[8.5*cm, 8.5*cm])
    label_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(label_table)
    
    # Dados adicionais abaixo das assinaturas
    elements.append(Spacer(1, 3*mm))
    dados_style = ParagraphStyle(
        'DadosAssinatura',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    
    dados_data = [[
        Paragraph(f'Nome: {orcamento.cliente.nome}<br/>CPF/CNPJ: {orcamento.cliente.cpf_cnpj or "_______________"}', dados_style),
        Paragraph(f'Nome: {empresa.nome_fantasia}<br/>CNPJ: {empresa.cnpj or "_______________"}', dados_style)
    ]]
    dados_table = Table(dados_data, colWidths=[8.5*cm, 8.5*cm])
    dados_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(dados_table)
    
    # Rodapé
    elements.append(Spacer(1, 10*mm))
    rodape_style = ParagraphStyle(
        'Rodape',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph(
        f'Orçamento gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        rodape_style
    ))
    
    # Gerar PDF
    doc.build(elements)
    
    # Retornar resposta HTTP
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="orcamento_{orcamento.codigo}.pdf"'
    
    return response


# ==================== VISITAS TÉCNICAS ====================

@login_required
def listar_visitas_tecnicas(request):
    """Lista todas as visitas técnicas"""
    visitas = VisitaTecnica.objects.select_related('orcamento', 'tecnico', 'agendado_por').all()
    
    # Filtros
    status = request.GET.get('status')
    orcamento_id = request.GET.get('orcamento')
    tecnico_id = request.GET.get('tecnico')
    
    if status:
        visitas = visitas.filter(status=status)
    if orcamento_id:
        visitas = visitas.filter(orcamento_id=orcamento_id)
    if tecnico_id:
        visitas = visitas.filter(tecnico_id=tecnico_id)
    
    context = {
        'titulo': 'Visitas Técnicas',
        'current_module': 'projetos',
        'visitas': visitas,
    }
    return render(request, 'projetos/listar_visitas_tecnicas.html', context)


@login_required
def criar_visita_tecnica(request):
    """Cria nova visita técnica"""
    orcamento_id = request.GET.get('orcamento_id')
    
    if request.method == 'POST':
        form = VisitaTecnicaForm(request.POST)
        
        if form.is_valid():
            visita = form.save(commit=False)
            visita.agendado_por = request.user
            visita.save()
            
            messages.success(request, 'Visita técnica agendada com sucesso!')
            return redirect('projetos:listar_visitas_tecnicas')
    else:
        initial_data = {}
        if orcamento_id:
            initial_data['orcamento'] = orcamento_id
        form = VisitaTecnicaForm(initial=initial_data)
    
    context = {
        'titulo': 'Agendar Visita Técnica',
        'current_module': 'projetos',
        'form': form,
    }
    return render(request, 'projetos/criar_visita_tecnica.html', context)


@login_required
def editar_visita_tecnica(request, pk):
    """Edita uma visita técnica"""
    visita = get_object_or_404(VisitaTecnica, pk=pk)
    
    if request.method == 'POST':
        form = VisitaTecnicaForm(request.POST, instance=visita)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Visita técnica atualizada com sucesso!')
            return redirect('projetos:visualizar_visita_tecnica', pk=visita.pk)
    else:
        form = VisitaTecnicaForm(instance=visita)
    
    context = {
        'titulo': f'Editar Visita Técnica',
        'current_module': 'projetos',
        'form': form,
        'visita': visita,
        'edicao': True,
    }
    return render(request, 'projetos/criar_visita_tecnica.html', context)


@login_required
def visualizar_visita_tecnica(request, pk):
    """Visualiza detalhes de uma visita técnica"""
    visita = get_object_or_404(VisitaTecnica, pk=pk)
    
    # Calcular duração da visita se houver hora_inicio e hora_fim
    duracao_minutos = None
    duracao_horas = None
    duracao_min_resto = None
    
    if visita.hora_inicio and visita.hora_fim:
        # Converter time para datetime para fazer cálculo
        from datetime import datetime, timedelta
        inicio = datetime.combine(visita.data_visita, visita.hora_inicio)
        fim = datetime.combine(visita.data_visita, visita.hora_fim)
        
        # Se fim for menor que inicio, assumir que passou para o dia seguinte
        if fim < inicio:
            fim += timedelta(days=1)
        
        duracao = fim - inicio
        duracao_minutos = int(duracao.total_seconds() / 60)
        
        # Calcular horas e minutos
        duracao_horas = duracao_minutos // 60
        duracao_min_resto = duracao_minutos % 60
    
    context = {
        'titulo': f'Visita Técnica - {visita.orcamento.codigo}',
        'current_module': 'projetos',
        'visita': visita,
        'duracao_minutos': duracao_minutos,
        'duracao_horas': duracao_horas,
        'duracao_min_resto': duracao_min_resto,
    }
    return render(request, 'projetos/visualizar_visita_tecnica.html', context)


@login_required
def cancelar_visita_tecnica(request, pk):
    """Cancela uma visita técnica"""
    visita = get_object_or_404(VisitaTecnica, pk=pk)
    visita.status = 'CANCELADA'
    visita.save()
    
    messages.success(request, 'Visita técnica cancelada!')
    return redirect('projetos:listar_visitas_tecnicas')


@login_required
def marcar_visita_realizada(request, pk):
    """Marca visita como realizada"""
    visita = get_object_or_404(VisitaTecnica, pk=pk)
    visita.status = 'REALIZADA'
    visita.save()
    
    messages.success(request, 'Visita técnica marcada como realizada!')
    return redirect('projetos:visualizar_visita_tecnica', pk=visita.pk)


# ========== DIÁRIO DA OBRA ==========

@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def listar_diario_obra(request, projeto_id):
    """Lista todas as entradas do diário de uma obra"""
    from .models import DiarioObra
    
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    periodo = request.GET.get('periodo')
    
    diarios = DiarioObra.objects.filter(projeto=projeto)
    
    if data_inicio:
        diarios = diarios.filter(data__gte=data_inicio)
    if data_fim:
        diarios = diarios.filter(data__lte=data_fim)
    if periodo:
        diarios = diarios.filter(periodo=periodo)
    
    # Estatísticas
    total_entradas = diarios.count()
    total_trabalhadores = diarios.aggregate(total=Sum('num_trabalhadores'))['total'] or 0
    media_trabalhadores = round(total_trabalhadores / total_entradas, 1) if total_entradas > 0 else 0
    
    context = {
        'titulo': f'Diário da Obra - {projeto.codigo}',
        'current_module': 'projetos',
        'projeto': projeto,
        'diarios': diarios,
        'total_entradas': total_entradas,
        'media_trabalhadores': media_trabalhadores,
    }
    return render(request, 'projetos/diario/listar_diario_obra.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def adicionar_diario_obra(request, projeto_id):
    """Adiciona nova entrada no diário da obra"""
    from .models import DiarioObra
    from .forms import DiarioObraForm
    
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    
    if request.method == 'POST':
        form = DiarioObraForm(request.POST)
        if form.is_valid():
            diario = form.save(commit=False)
            diario.projeto = projeto
            diario.criado_por = request.user
            diario.save()
            
            messages.success(request, 'Entrada adicionada ao diário da obra!')
            return redirect('projetos:listar_diario_obra', projeto_id=projeto.pk)
    else:
        # Pre-preencher com data de hoje
        form = DiarioObraForm(initial={'data': datetime.now().date()})
    
    context = {
        'titulo': f'Adicionar Entrada - Diário da Obra',
        'current_module': 'projetos',
        'projeto': projeto,
        'form': form,
    }
    return render(request, 'projetos/diario/form_diario_obra.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def visualizar_diario_obra(request, pk):
    """Visualiza uma entrada do diário"""
    from .models import DiarioObra
    
    diario = get_object_or_404(DiarioObra, pk=pk)
    
    context = {
        'titulo': f'Diário da Obra - {diario.data.strftime("%d/%m/%Y")}',
        'current_module': 'projetos',
        'diario': diario,
        'projeto': diario.projeto,
    }
    return render(request, 'projetos/diario/visualizar_diario_obra.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def editar_diario_obra(request, pk):
    """Edita entrada do diário da obra"""
    from .models import DiarioObra
    from .forms import DiarioObraForm
    
    diario = get_object_or_404(DiarioObra, pk=pk)
    projeto = diario.projeto
    
    if request.method == 'POST':
        form = DiarioObraForm(request.POST, instance=diario)
        if form.is_valid():
            diario = form.save(commit=False)
            diario.atualizado_por = request.user
            diario.save()
            
            messages.success(request, 'Entrada do diário atualizada!')
            return redirect('projetos:visualizar_diario_obra', pk=diario.pk)
    else:
        form = DiarioObraForm(instance=diario)
    
    context = {
        'titulo': f'Editar Entrada - Diário da Obra',
        'current_module': 'projetos',
        'projeto': projeto,
        'diario': diario,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'projetos/diario/form_diario_obra.html', context)


@login_required
@require_empresa
@verificar_permissao_menu('/projetos/')
def deletar_diario_obra(request, pk):
    """Deleta entrada do diário da obra"""
    from .models import DiarioObra
    
    diario = get_object_or_404(DiarioObra, pk=pk)
    projeto_id = diario.projeto.pk
    
    if request.method == 'POST':
        diario.delete()
        messages.success(request, 'Entrada do diário removida!')
        return redirect('projetos:listar_diario_obra', projeto_id=projeto_id)
    
    context = {
        'titulo': 'Confirmar Exclusão',
        'current_module': 'projetos',
        'diario': diario,
        'projeto': diario.projeto,
    }
    return render(request, 'projetos/diario/deletar_diario_obra.html', context)

