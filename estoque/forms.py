from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    Item, GrupoItem, LocalEstoque, DestinoEstoque,
    MovimentoEstoque, SaldoEstoque, BOM, BOMItem, OrdemProducao
)


class ItemForm(forms.ModelForm):
    """Formulário para cadastro de itens"""
    
    class Meta:
        model = Item
        fields = [
            'codigo', 'descricao', 'tipo_item', 'grupo',
            'material', 'marca', 'modelo', 'cor', 'unidade_medida',
            'estoque_minimo', 'estoque_maximo',
            'ncm', 'codigo_barras', 'url_foto',
            'ativo', 'observacoes'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ALU-001'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição completa do item'}),
            'tipo_item': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'cor': forms.TextInput(attrs={'class': 'form-control'}),
            'unidade_medida': forms.Select(attrs={'class': 'form-select'}),
            'estoque_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0'}),
            'estoque_maximo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0'}),
            'ncm': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'url_foto': forms.URLInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GrupoItemForm(forms.ModelForm):
    """Formulário para grupos de itens"""
    
    class Meta:
        model = GrupoItem
        fields = ['codigo', 'descricao', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LocalEstoqueForm(forms.ModelForm):
    """Formulário para locais de estoque"""
    
    class Meta:
        model = LocalEstoque
        fields = ['codigo', 'descricao', 'endereco', 'responsavel', 'permite_saldo_negativo', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ALMOX01'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Almoxarifado Geral'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'permite_saldo_negativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DestinoEstoqueForm(forms.ModelForm):
    """Formulário para destinos de estoque"""
    
    class Meta:
        model = DestinoEstoque
        fields = ['codigo', 'descricao', 'tipo', 'controla_custo', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'controla_custo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MovimentoEstoqueEntradaForm(forms.ModelForm):
    """Formulário para entrada de estoque (Nota Fiscal)"""
    
    class Meta:
        model = MovimentoEstoque
        fields = [
            'documento', 'documento_tipo', 'data_movimento',
            'item', 'local_destino', 'fornecedor',
            'quantidade', 'custo_unitario', 'observacao'
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº NF'}),
            'documento_tipo': forms.Select(attrs={'class': 'form-select'}),
            'data_movimento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'local_destino': forms.Select(attrs={'class': 'form-select'}),
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'custo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir tipo de movimento como ENTRADA
        self.instance.tipo_movimento = 'ENTRADA'
        
        # Filtrar apenas fornecedores ativos
        from cadastros.models import Pessoa
        self.fields['fornecedor'].queryset = Pessoa.objects.filter(
            tipo_pessoa__fornecedor=True,
            ativo=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        custo_unitario = cleaned_data.get('custo_unitario')
        
        if quantidade and quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        
        if custo_unitario and custo_unitario < 0:
            raise ValidationError('Custo unitário não pode ser negativo.')
        
        return cleaned_data


class MovimentoEstoqueSaidaForm(forms.ModelForm):
    """Formulário para saída de estoque (Requisição)"""
    
    class Meta:
        model = MovimentoEstoque
        fields = [
            'documento', 'documento_tipo', 'data_movimento',
            'item', 'local_origem', 'destino', 'projeto',
            'quantidade', 'solicitante', 'observacao'
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº Requisição'}),
            'documento_tipo': forms.Select(attrs={'class': 'form-select'}),
            'data_movimento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'local_origem': forms.Select(attrs={'class': 'form-select'}),
            'destino': forms.Select(attrs={'class': 'form-select'}),
            'projeto': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'solicitante': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir tipo de movimento como SAIDA
        self.instance.tipo_movimento = 'SAIDA'
        
        # Projeto é opcional
        self.fields['projeto'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        destino = cleaned_data.get('destino')
        projeto = cleaned_data.get('projeto')
        
        if quantidade and quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        
        # Se destino é PROJETO, deve ter projeto informado
        if destino and destino.tipo == 'PROJETO' and not projeto:
            raise ValidationError('Para destino "Projeto/Obra", é necessário informar o projeto.')
        
        return cleaned_data


class MovimentoEstoqueTransferenciaForm(forms.ModelForm):
    """Formulário para transferência entre locais"""
    
    class Meta:
        model = MovimentoEstoque
        fields = [
            'documento', 'data_movimento',
            'item', 'local_origem', 'local_destino',
            'quantidade', 'observacao'
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº Transferência'}),
            'data_movimento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'local_origem': forms.Select(attrs={'class': 'form-select'}),
            'local_destino': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir tipo de movimento como TRANSFERENCIA
        self.instance.tipo_movimento = 'TRANSFERENCIA'
        self.instance.documento_tipo = 'TRF'
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        local_origem = cleaned_data.get('local_origem')
        local_destino = cleaned_data.get('local_destino')
        
        if quantidade and quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        
        if local_origem and local_destino and local_origem == local_destino:
            raise ValidationError('Local origem e destino não podem ser iguais.')
        
        return cleaned_data


class MovimentoEstoqueAjusteForm(forms.ModelForm):
    """Formulário para ajuste/inventário de estoque"""
    
    tipo_ajuste = forms.ChoiceField(
        label='Tipo de Ajuste',
        choices=[('POSITIVO', 'Ajuste Positivo (Aumento)'), ('NEGATIVO', 'Ajuste Negativo (Redução)')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = MovimentoEstoque
        fields = [
            'documento', 'data_movimento',
            'item', 'local_destino',
            'quantidade', 'custo_unitario', 'observacao'
        ]
        widgets = {
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº Inventário'}),
            'data_movimento': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'local_destino': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'custo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'min': '0'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motivo do ajuste'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir tipo de movimento como AJUSTE
        self.instance.tipo_movimento = 'AJUSTE'
        self.instance.documento_tipo = 'INV'
        
        # Custo unitário é opcional em ajuste
        self.fields['custo_unitario'].required = False
        self.fields['observacao'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        quantidade = cleaned_data.get('quantidade')
        tipo_ajuste = cleaned_data.get('tipo_ajuste')
        
        if quantidade and quantidade <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        
        # Ajustar sinal da quantidade conforme tipo
        if tipo_ajuste == 'NEGATIVO':
            cleaned_data['quantidade'] = -abs(quantidade)
        else:
            cleaned_data['quantidade'] = abs(quantidade)
        
        return cleaned_data


class FiltroMovimentosForm(forms.Form):
    """Formulário para filtros de relatórios de movimentação"""
    
    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    tipo_movimento = forms.ChoiceField(
        label='Tipo de Movimento',
        required=False,
        choices=[('', 'Todos')] + list(MovimentoEstoque.TIPO_MOVIMENTO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    item = forms.ModelChoiceField(
        label='Item',
        required=False,
        queryset=Item.objects.filter(ativo=True).order_by('descricao'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    local = forms.ModelChoiceField(
        label='Local',
        required=False,
        queryset=LocalEstoque.objects.filter(ativo=True).order_by('descricao'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    projeto = forms.ModelChoiceField(
        label='Projeto',
        required=False,
        queryset=None,  # Será definido no __init__
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importar dinamicamente para evitar dependência circular
        from projetos.models import Projeto
        self.fields['projeto'].queryset = Projeto.objects.filter(ativo=True).order_by('codigo')


class BOMForm(forms.ModelForm):
    """Formulário para BOM (Bill of Materials)"""
    
    class Meta:
        model = BOM
        fields = ['produto', 'versao', 'descricao', 'ativo', 'data_vigencia']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'versao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1.0'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas produtos acabados e semi-acabados
        self.fields['produto'].queryset = Item.objects.filter(
            tipo_item__in=['PA', 'SEMI'],
            ativo=True
        ).order_by('descricao')


class BOMItemForm(forms.ModelForm):
    """Formulário para itens da BOM"""
    
    class Meta:
        model = BOMItem
        fields = ['item_componente', 'quantidade', 'percentual_perda', 'sequencia']
        widgets = {
            'item_componente': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'percentual_perda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'sequencia': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class OrdemProducaoForm(forms.ModelForm):
    """Formulário para Ordem de Produção"""
    
    class Meta:
        model = OrdemProducao
        fields = [
            'numero_op', 'produto', 'bom', 'quantidade_planejada',
            'local_producao', 'local_destino', 'data_planejada',
            'projeto', 'observacoes'
        ]
        widgets = {
            'numero_op': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'OP-001'}),
            'produto': forms.Select(attrs={'class': 'form-select'}),
            'bom': forms.Select(attrs={'class': 'form-select'}),
            'quantidade_planejada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'local_producao': forms.Select(attrs={'class': 'form-select'}),
            'local_destino': forms.Select(attrs={'class': 'form-select'}),
            'data_planejada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'projeto': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas produtos acabados e semi-acabados
        self.fields['produto'].queryset = Item.objects.filter(
            tipo_item__in=['PA', 'SEMI'],
            ativo=True
        ).order_by('descricao')
        
        # Projeto é opcional
        self.fields['projeto'].required = False
