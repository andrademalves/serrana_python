# 🖥️ VIEWS E FORMS - ESTOQUE PROFISSIONAL

## Visão Geral

Este documento contém exemplos prontos de Views e Forms para as principais operações do sistema de estoque.

---

## 📝 FORMS

### 1. Forms para Operações de Estoque

**Arquivo:** `estoque/forms.py`

```python
"""
Forms para operações de estoque
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from cadastros.models import Pessoa, Produto
from .models import (
    LocalEstoque,
    DestinoEstoque,
    MovimentoEstoque,
    SaldoEstoque
)


class EntradaEstoqueForm(forms.Form):
    """Form para entrada de estoque (NF)"""
    
    documento = forms.CharField(
        label='Nº Documento (NF)',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: NF-12345'})
    )
    data_operacao = forms.DateTimeField(
        label='Data/Hora da Operação',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        initial=timezone.now
    )
    fornecedor = forms.ModelChoiceField(
        label='Fornecedor',
        queryset=Pessoa.objects.filter(fornecedor=True, ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    local_destino = forms.ModelChoiceField(
        label='Local de Destino',
        queryset=LocalEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    observacao = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ItemEntradaForm(forms.Form):
    """Form para cada item da entrada (usado em formset)"""
    
    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantidade = forms.DecimalField(
        label='Quantidade',
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    custo_unitario = forms.DecimalField(
        label='Custo Unitário',
        max_digits=12,
        decimal_places=4,
        min_value=Decimal('0.0001'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        custo_unitario = cleaned_data.get('custo_unitario')
        
        if quantidade and custo_unitario:
            cleaned_data['custo_total'] = quantidade * custo_unitario
        
        return cleaned_data


class SaidaEstoqueForm(forms.Form):
    """Form para saída de estoque (requisição)"""
    
    documento = forms.CharField(
        label='Nº Requisição',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: REQ-001'})
    )
    data_operacao = forms.DateTimeField(
        label='Data/Hora da Operação',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        initial=timezone.now
    )
    local_origem = forms.ModelChoiceField(
        label='Local de Origem',
        queryset=LocalEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    destino = forms.ModelChoiceField(
        label='Destino/Finalidade',
        queryset=DestinoEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'verificarObra()'})
    )
    obra = forms.CharField(
        label='Obra/Projeto',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Selecione obra (se necessário)'})
        # AJUSTAR: Usar ModelChoiceField quando FK estiver pronta
        # obra = forms.ModelChoiceField(...)
    )
    solicitante = forms.ModelChoiceField(
        label='Funcionário Solicitante',
        queryset=Pessoa.objects.filter(funcionario=True, ativo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    entregador = forms.ModelChoiceField(
        label='Funcionário Entregador/Almoxarife',
        queryset=Pessoa.objects.filter(funcionario=True, ativo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    observacao = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        destino = cleaned_data.get('destino')
        obra = cleaned_data.get('obra')
        
        # Validar se destino exige obra
        if destino and destino.exige_obra and not obra:
            raise ValidationError({
                'obra': f'O destino "{destino.nome}" exige que uma obra seja informada.'
            })
        
        return cleaned_data


class ItemSaidaForm(forms.Form):
    """Form para cada item da saída"""
    
    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control', 'onchange': 'verificarSaldo(this)'})
    )
    quantidade = forms.DecimalField(
        label='Quantidade',
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    
    def __init__(self, *args, local_origem=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_origem = local_origem
    
    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        quantidade = cleaned_data.get('quantidade')
        
        if produto and quantidade and self.local_origem:
            # Verificar saldo disponível
            try:
                saldo = SaldoEstoque.objects.get(
                    produto=produto,
                    local=self.local_origem
                )
                
                if saldo.saldo_quantidade < quantidade:
                    if not self.local_origem.permite_saldo_negativo:
                        raise ValidationError({
                            'quantidade': f'Saldo insuficiente. Disponível: {saldo.saldo_quantidade} {produto.unidade}'
                        })
                    else:
                        # Apenas warning, mas permite
                        self.add_error('quantidade', 
                            f'AVISO: Saldo insuficiente ({saldo.saldo_quantidade} {produto.unidade}), '
                            f'mas local permite negativo.'
                        )
                
                cleaned_data['custo_unitario'] = saldo.custo_medio
                cleaned_data['saldo_disponivel'] = saldo.saldo_quantidade
            
            except SaldoEstoque.DoesNotExist:
                raise ValidationError({
                    'produto': f'Produto não possui saldo no local {self.local_origem.nome}'
                })
        
        return cleaned_data


class TransferenciaEstoqueForm(forms.Form):
    """Form para transferência entre locais"""
    
    documento = forms.CharField(
        label='Nº Transferência',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: TRANS-001'})
    )
    data_operacao = forms.DateTimeField(
        label='Data/Hora da Operação',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        initial=timezone.now
    )
    local_origem = forms.ModelChoiceField(
        label='Local de Origem',
        queryset=LocalEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    local_destino = forms.ModelChoiceField(
        label='Local de Destino',
        queryset=LocalEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    observacao = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        origem = cleaned_data.get('local_origem')
        destino = cleaned_data.get('local_destino')
        
        if origem and destino and origem == destino:
            raise ValidationError('Local de origem e destino não podem ser iguais.')
        
        return cleaned_data


class AjusteEstoqueForm(forms.Form):
    """Form para ajuste/inventário"""
    
    documento = forms.CharField(
        label='Nº Inventário',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: INV-2025-01'})
    )
    data_operacao = forms.DateTimeField(
        label='Data/Hora do Inventário',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        initial=timezone.now
    )
    local = forms.ModelChoiceField(
        label='Local',
        queryset=LocalEstoque.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    observacao = forms.CharField(
        label='Motivo do Ajuste',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 
                                     'placeholder': 'Descreva o motivo do ajuste...'})
    )


class ItemAjusteForm(forms.Form):
    """Form para cada item do ajuste"""
    
    produto = forms.ModelChoiceField(
        label='Produto',
        queryset=Produto.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    saldo_sistema = forms.DecimalField(
        label='Saldo Sistema',
        max_digits=12,
        decimal_places=3,
        disabled=True,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    saldo_fisico = forms.DecimalField(
        label='Saldo Físico (Contado)',
        max_digits=12,
        decimal_places=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    )
    diferenca = forms.DecimalField(
        label='Diferença',
        max_digits=12,
        decimal_places=3,
        disabled=True,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    custo_unitario = forms.DecimalField(
        label='Custo Unitário',
        max_digits=12,
        decimal_places=4,
        required=False,
        help_text='Informar custo apenas se diferença for positiva (entrada)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'})
    )


# Formsets
from django.forms import formset_factory

ItemEntradaFormSet = formset_factory(ItemEntradaForm, extra=1, can_delete=True)
ItemSaidaFormSet = formset_factory(ItemSaidaForm, extra=1, can_delete=True)
ItemTransferenciaFormSet = formset_factory(ItemEntradaForm, extra=1, can_delete=True)  # Reusa ItemEntrada sem custo
ItemAjusteFormSet = formset_factory(ItemAjusteForm, extra=1, can_delete=True)
```

---

## 🎨 VIEWS

### 2. Views para Operações

**Arquivo:** `estoque/views_operacoes.py`

```python
"""
Views para operações de estoque
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from .forms import (
    EntradaEstoqueForm,
    ItemEntradaFormSet,
    SaidaEstoqueForm,
    ItemSaidaFormSet,
    TransferenciaEstoqueForm,
    ItemTransferenciaFormSet,
    AjusteEstoqueForm,
    ItemAjusteFormSet
)
from .models import MovimentoEstoque, SaldoEstoque, LocalEstoque
from .services_profissional import OperacaoEstoqueService
from cadastros.models import Produto


@login_required
def entrada_estoque(request):
    """
    Tela de entrada de estoque (NF)
    """
    if request.method == 'POST':
        form = EntradaEstoqueForm(request.POST)
        formset = ItemEntradaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Preparar dados dos itens
                    itens = []
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                            itens.append({
                                'produto': item_form.cleaned_data['produto'],
                                'quantidade': item_form.cleaned_data['quantidade'],
                                'custo_unitario': item_form.cleaned_data['custo_unitario']
                            })
                    
                    # Criar entrada usando service
                    movimentos = OperacaoEstoqueService.criar_entrada(
                        documento=form.cleaned_data['documento'],
                        data_operacao=form.cleaned_data['data_operacao'],
                        fornecedor=form.cleaned_data['fornecedor'],
                        local_destino=form.cleaned_data['local_destino'],
                        itens=itens,
                        usuario=request.user,
                        observacao=form.cleaned_data.get('observacao', '')
                    )
                    
                    messages.success(
                        request,
                        f'Entrada {form.cleaned_data["documento"]} registrada com sucesso! '
                        f'{len(movimentos)} item(ns) lançado(s).'
                    )
                    
                    return redirect('estoque:posicao_estoque')
            
            except Exception as e:
                messages.error(request, f'Erro ao registrar entrada: {str(e)}')
    
    else:
        # Gerar próximo número de documento
        proximo_doc = OperacaoEstoqueService.gerar_proximo_numero_documento(
            'NF_ENTRADA', 
            prefixo=f'NF-{timezone.now().year}-'
        )
        
        form = EntradaEstoqueForm(initial={'documento': proximo_doc})
        formset = ItemEntradaFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Entrada de Estoque (NF)',
        'tipo_operacao': 'entrada'
    }
    
    return render(request, 'estoque/entrada_estoque.html', context)


@login_required
def saida_estoque(request):
    """
    Tela de saída de estoque (requisição)
    """
    if request.method == 'POST':
        form = SaidaEstoqueForm(request.POST)
        # Passar local_origem para validação de saldo
        local_origem_id = request.POST.get('local_origem')
        local_origem = LocalEstoque.objects.get(pk=local_origem_id) if local_origem_id else None
        
        formset = ItemSaidaFormSet(request.POST, form_kwargs={'local_origem': local_origem})
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Preparar dados dos itens
                    itens = []
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                            itens.append({
                                'produto': item_form.cleaned_data['produto'],
                                'quantidade': item_form.cleaned_data['quantidade']
                            })
                    
                    # Criar saída usando service
                    movimentos = OperacaoEstoqueService.criar_saida(
                        documento=form.cleaned_data['documento'],
                        data_operacao=form.cleaned_data['data_operacao'],
                        local_origem=form.cleaned_data['local_origem'],
                        destino=form.cleaned_data['destino'],
                        itens=itens,
                        usuario=request.user,
                        obra=form.cleaned_data.get('obra'),
                        solicitante=form.cleaned_data.get('solicitante'),
                        entregador=form.cleaned_data.get('entregador'),
                        observacao=form.cleaned_data.get('observacao', '')
                    )
                    
                    messages.success(
                        request,
                        f'Saída {form.cleaned_data["documento"]} registrada com sucesso! '
                        f'{len(movimentos)} item(ns) retirado(s).'
                    )
                    
                    return redirect('estoque:posicao_estoque')
            
            except Exception as e:
                messages.error(request, f'Erro ao registrar saída: {str(e)}')
    
    else:
        proximo_doc = OperacaoEstoqueService.gerar_proximo_numero_documento(
            'REQ_SAIDA',
            prefixo=f'REQ-{timezone.now().year}-'
        )
        
        form = SaidaEstoqueForm(initial={'documento': proximo_doc})
        formset = ItemSaidaFormSet(form_kwargs={'local_origem': None})
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Saída de Estoque (Requisição)',
        'tipo_operacao': 'saida'
    }
    
    return render(request, 'estoque/saida_estoque.html', context)


@login_required
def transferencia_estoque(request):
    """
    Tela de transferência entre locais
    """
    if request.method == 'POST':
        form = TransferenciaEstoqueForm(request.POST)
        formset = ItemTransferenciaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Preparar itens
                    itens = []
                    for item_form in formset:
                        if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE'):
                            itens.append({
                                'produto': item_form.cleaned_data['produto'],
                                'quantidade': item_form.cleaned_data['quantidade']
                            })
                    
                    # Criar transferência
                    movimentos = OperacaoEstoqueService.criar_transferencia(
                        documento=form.cleaned_data['documento'],
                        data_operacao=form.cleaned_data['data_operacao'],
                        local_origem=form.cleaned_data['local_origem'],
                        local_destino=form.cleaned_data['local_destino'],
                        itens=itens,
                        usuario=request.user,
                        observacao=form.cleaned_data.get('observacao', '')
                    )
                    
                    messages.success(
                        request,
                        f'Transferência {form.cleaned_data["documento"]} realizada com sucesso! '
                        f'{len(movimentos)} item(ns) transferido(s).'
                    )
                    
                    return redirect('estoque:posicao_estoque')
            
            except Exception as e:
                messages.error(request, f'Erro ao realizar transferência: {str(e)}')
    
    else:
        proximo_doc = OperacaoEstoqueService.gerar_proximo_numero_documento(
            'TRANS',
            prefixo=f'TRANS-{timezone.now().year}-'
        )
        
        form = TransferenciaEstoqueForm(initial={'documento': proximo_doc})
        formset = ItemTransferenciaFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Transferência de Estoque',
        'tipo_operacao': 'transferencia'
    }
    
    return render(request, 'estoque/transferencia_estoque.html', context)


# ============================================================================
# AJAX HELPERS
# ============================================================================

@login_required
def api_saldo_produto(request):
    """
    API para retornar saldo de um produto em um local (via AJAX)
    """
    produto_id = request.GET.get('produto_id')
    local_id = request.GET.get('local_id')
    
    if not produto_id or not local_id:
        return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
    
    try:
        saldo = SaldoEstoque.objects.get(
            produto_id=produto_id,
            local_id=local_id
        )
        
        return JsonResponse({
            'saldo_quantidade': float(saldo.saldo_quantidade),
            'custo_medio': float(saldo.custo_medio),
            'unidade': saldo.produto.unidade,
            'descricao': saldo.produto.descricao
        })
    
    except SaldoEstoque.DoesNotExist:
        return JsonResponse({
            'saldo_quantidade': 0,
            'custo_medio': 0,
            'unidade': '',
            'descricao': ''
        })


@login_required
def api_produto_info(request, produto_id):
    """
    API para retornar informações de um produto
    """
    try:
        produto = Produto.objects.get(pk=produto_id)
        
        # Saldo total
        saldo_total = sum(s.saldo_quantidade for s in produto.saldos_estoque.all())
        
        return JsonResponse({
            'codigo': produto.codigo,
            'descricao': produto.descricao,
            'unidade': produto.unidade,
            'saldo_total': float(saldo_total),
            'estoque_minimo': float(getattr(produto, 'estoque_minimo', 0) or 0),
            'fornecedor': produto.fornecedor.nome_razao_social if hasattr(produto, 'fornecedor') and produto.fornecedor else None
        })
    
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)
```

---

## 📊 VIEWS DE RELATÓRIOS

**Arquivo:** `estoque/views_relatorios.py`

```python
"""
Views para relatórios de estoque
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from datetime import datetime, timedelta

from .models import SaldoEstoque, MovimentoEstoque
from .services_profissional import RelatorioEstoqueService, EstoqueMinimoService
from cadastros.models import Produto


@login_required
def posicao_estoque(request):
    """
    Relatório de posição de estoque (saldos atuais)
    """
    # Filtros
    produto_id = request.GET.get('produto')
    local_id = request.GET.get('local')
    apenas_com_saldo = request.GET.get('apenas_com_saldo') == '1'
    
    # Buscar saldos usando service
    saldos = RelatorioEstoqueService.posicao_estoque(
        produto=Produto.objects.get(pk=produto_id) if produto_id else None,
        local=LocalEstoque.objects.get(pk=local_id) if local_id else None,
        apenas_com_saldo=apenas_com_saldo
    )
    
    # Totalizadores
    total_itens = saldos.count()
    total_valor = sum(s.valor_total for s in saldos)
    
    context = {
        'saldos': saldos,
        'total_itens': total_itens,
        'total_valor': total_valor,
        'filtros': {
            'produto_id': produto_id,
            'local_id': local_id,
            'apenas_com_saldo': apenas_com_saldo
        }
    }
    
    return render(request, 'estoque/posicao_estoque.html', context)


@login_required
def produtos_abaixo_minimo(request):
    """
    Relatório de produtos abaixo do estoque mínimo
    """
    produtos_criticos = RelatorioEstoqueService.produtos_abaixo_minimo()
    
    context = {
        'produtos': produtos_criticos,
        'total_produtos': len(produtos_criticos)
    }
    
    return render(request, 'estoque/produtos_abaixo_minimo.html', context)


@login_required
def extrato_movimentos(request):
    """
    Extrato de movimentos de estoque com filtros
    """
    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    produto_id = request.GET.get('produto')
    tipo_movimento = request.GET.get('tipo_movimento')
    
    # Converter datas
    data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date() if data_inicio else None
    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date() if data_fim else None
    
    # Buscar movimentos
    movimentos = RelatorioEstoqueService.extrato_movimentos(
        data_inicio=data_inicio,
        data_fim=data_fim,
        produto=Produto.objects.get(pk=produto_id) if produto_id else None,
        tipo_movimento=tipo_movimento
    )
    
    # Totalizadores
    total_entradas = movimentos.filter(tipo_movimento='ENTRADA').aggregate(
        total=Sum('custo_total')
    )['total'] or 0
    
    total_saidas = movimentos.filter(tipo_movimento='SAIDA').aggregate(
        total=Sum('custo_total')
    )['total'] or 0
    
    context = {
        'movimentos': movimentos[:100],  # Limitar para performance
        'total_movimentos': movimentos.count(),
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'filtros': {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'produto_id': produto_id,
            'tipo_movimento': tipo_movimento
        }
    }
    
    return render(request, 'estoque/extrato_movimentos.html', context)
```

---

**Próximo passo:** Criar templates HTML (base com Bootstrap 5)

**Arquivos necessários:**
- `templates/estoque/entrada_estoque.html`
- `templates/estoque/saida_estoque.html`
- `templates/estoque/posicao_estoque.html`
- `templates/estoque/produtos_abaixo_minimo.html`

Deseja que eu crie os templates também?
