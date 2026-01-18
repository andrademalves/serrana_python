from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal
from .models import (
    Orcamento, OrcamentoItem, OrcamentoParcela, Projeto, VisitaTecnica,
    AlocacaoProjeto, VendaDireta, VendaDiretaItem, ContaCorrenteProjeto
)
from cadastros.models import Pessoa
from estoque.models import Item


class OrcamentoForm(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ['cliente', 'vendedor', 'data_orcamento', 'validade_dias', 'status', 'tipo_desconto', 'desconto_valor', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'vendedor': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'data_orcamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}, format='%Y-%m-%d'),
            'validade_dias': forms.NumberInput(attrs={'class': 'form-control', 'value': '30'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'tipo_desconto': forms.Select(attrs={'class': 'form-control'}),
            'desconto_valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '0.00', 'min': '0'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar formato de data para HTML5
        self.fields['data_orcamento'].input_formats = ['%Y-%m-%d']
        
        # Tornar status opcional - na criação usa o padrão PENDENTE do modelo
        self.fields['status'].required = False
        
        # Definir valor padrão para data_orcamento como hoje
        if not self.instance.pk:
            from django.utils import timezone
            self.initial['data_orcamento'] = timezone.now().date()
        
        # Filtrar vendedores para mostrar apenas pessoas com flag vendedor
        self.fields['vendedor'].queryset = Pessoa.objects.filter(
            vendedor=True, 
            ativo=True
        ).order_by('nome')
        
        # Filtrar clientes para mostrar apenas pessoas ativas
        self.fields['cliente'].queryset = Pessoa.objects.filter(
            cliente=True,
            ativo=True
        ).order_by('nome')
        
        # Label customizado para tipo_desconto
        self.fields['tipo_desconto'].label = 'Aplicar Desconto'
        self.fields['desconto_valor'].label = 'Valor do Desconto'
    
    def clean_desconto_valor(self):
        desconto_valor = self.cleaned_data.get('desconto_valor', Decimal('0.00'))
        tipo_desconto = self.cleaned_data.get('tipo_desconto', 'NENHUM')
        
        if tipo_desconto == 'PERCENTUAL' and desconto_valor > 100:
            raise forms.ValidationError('O percentual de desconto não pode ser maior que 100%.')
        
        if desconto_valor < 0:
            raise forms.ValidationError('O desconto não pode ser negativo.')
        
        return desconto_valor
    
    def clean_vendedor(self):
        vendedor = self.cleaned_data.get('vendedor')
        if not vendedor:
            raise forms.ValidationError('Selecione um vendedor.')
        if not vendedor.vendedor:
            raise forms.ValidationError('A pessoa selecionada não é um vendedor.')
        return vendedor
    
    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        if not cliente:
            raise forms.ValidationError('Selecione um cliente.')
        if not cliente.cliente:
            raise forms.ValidationError('A pessoa selecionada não é um cliente.')
        return cliente


class OrcamentoItemForm(forms.ModelForm):
    # Usar CharField para aceitar qualquer valor do Select2 sem validar choices
    item = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = OrcamentoItem
        fields = ['tipo', 'item', 'descricao', 'quantidade', 'valor_unitario', 'desconto']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tornar desconto opcional com valor padrão 0
        self.fields['desconto'].required = False
        self.fields['desconto'].initial = 0.00
        
        # Se tem instância com item_ref salvo, usar para pré-popular
        if self.instance and self.instance.pk and self.instance.item_ref:
            # Usar o item_ref salvo (ex: produto_1)
            item_value = self.instance.item_ref
            item_text = None
            
            # Buscar o texto correto baseado no item_ref
            if '_' in self.instance.item_ref:
                try:
                    prefixo, item_id = self.instance.item_ref.split('_', 1)
                    
                    if prefixo == 'produto':
                        from cadastros.models import Produto
                        produto = Produto.objects.get(pk=int(item_id))
                        item_text = f"{produto.codigo} - {produto.descricao}"
                    elif prefixo == 'servico':
                        from cadastros.models import Produto
                        servico = Produto.objects.get(pk=int(item_id))
                        item_text = f"{servico.codigo} - {servico.descricao}"
                    elif prefixo == 'item':
                        from estoque.models import Item as EstoqueItem
                        estoque_item = EstoqueItem.objects.get(pk=int(item_id))
                        item_text = f"{estoque_item.codigo} - {estoque_item.descricao}"
                except:
                    # Se não encontrar, usar o código salvo + descrição
                    if self.instance.item_codigo:
                        item_text = f"{self.instance.item_codigo} - {self.instance.descricao}"
                    else:
                        item_text = self.instance.descricao
            
            # Se conseguiu buscar o texto, adicionar atributos data
            if item_text:
                self.fields['item'].widget.attrs.update({
                    'data-item-value': item_value,
                    'data-item-text': item_text
                })
        # Fallback: se tem item FK (Item de estoque)
        elif self.instance and self.instance.pk and self.instance.item:
            item = self.instance.item
            # Determinar o prefixo baseado no tipo
            if self.instance.tipo == 'PRODUTO':
                prefixo = 'produto'
            elif self.instance.tipo == 'MATERIAL':
                prefixo = 'item'
            elif self.instance.tipo == 'SERVICO':
                prefixo = 'servico'
            else:
                prefixo = 'item'
            
            item_value = f"{prefixo}_{item.id}"
            item_text = f"{item.codigo} - {item.descricao}"
            
            # Adicionar atributos data ao widget para o JavaScript usar
            self.fields['item'].widget.attrs.update({
                'data-item-value': item_value,
                'data-item-text': item_text
            })
    
    def clean_item(self):
        """Converte formato 'tipo_id' para objeto Item e salva item_ref"""
        # Se está marcado para delete, não validar
        if self.cleaned_data.get('DELETE'):
            return None
            
        item_str = self.cleaned_data.get('item')
        
        # Salvar item_ref para poder pré-popular na edição
        if item_str:
            self.instance.item_ref = item_str
        
        if not item_str:
            return None
        
        # Se for formato "tipo_id", extrair o prefixo e ID
        if '_' in str(item_str):
            try:
                prefixo, item_id = str(item_str).split('_', 1)
                
                # Buscar no modelo apropriado baseado no prefixo
                if prefixo in ['produto', 'servico']:
                    # Produtos e serviços estão na tabela Produto (cadastros)
                    # MAS o modelo OrcamentoItem só aceita FK para Item (estoque)
                    # Então vamos buscar se existe um Item correspondente
                    try:
                        return Item.objects.get(pk=int(item_id))
                    except Item.DoesNotExist:
                        # Se não existe no estoque, retornar None (vai usar só a descrição)
                        return None
                elif prefixo == 'item':
                    # Materiais estão na tabela Item (estoque)
                    return Item.objects.get(pk=int(item_id))
                    
            except (ValueError, Item.DoesNotExist):
                # Se não encontrar, continuar para tentar como ID direto
                pass
        
        # Tentar como ID direto
        try:
            return Item.objects.get(pk=int(item_str))
        except (ValueError, Item.DoesNotExist, TypeError):
            # Se não encontrar, retornar None (campo é opcional)
            return None


OrcamentoItemFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoItem,
    form=OrcamentoItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)


class OrcamentoParcelaForm(forms.ModelForm):
    class Meta:
        model = OrcamentoParcela
        fields = ['numero_parcela', 'descricao', 'data_vencimento', 'valor', 'forma_pagamento']
        widgets = {
            'numero_parcela': forms.HiddenInput(),
            'descricao': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: Entrada, 1/3'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control form-control-sm', 'type': 'date', 'required': True}, format='%Y-%m-%d'),
            'valor': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'required': True}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control form-control-sm', 'required': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_vencimento'].input_formats = ['%Y-%m-%d']


OrcamentoParcelaFormSet = inlineformset_factory(
    Orcamento,
    OrcamentoParcela,
    form=OrcamentoParcelaForm,
    extra=0,  # Não mostrar extras, apenas o min_num
    can_delete=True,
    min_num=1,
    validate_min=True
)


class ProjetoForm(forms.ModelForm):
    # Campo adicional para mostrar endereço do cliente (somente leitura)
    endereco_cliente = forms.CharField(
        label='Endereço do Cliente',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'readonly': 'readonly', 'style': 'background-color: #e9ecef;'})
    )
    
    # Checkbox para usar endereço do cliente
    usar_endereco_cliente = forms.BooleanField(
        label='Usar o mesmo endereço do cliente para a obra',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'usar_endereco_cliente'})
    )
    
    class Meta:
        model = Projeto
        fields = [
            'orcamento', 'cliente', 'vendedor', 'descricao',
            'data_orcamento', 'data_contratacao', 'data_inicio_real', 'data_previsao_termino', 
            'data_termino_real', 'prazo_obra',
            'logradouro', 'complemento', 'bairro', 'cidade', 'uf', 'cep',
            'valor_orcado', 'valor_contratado',
            'num_visitas_tecnicas', 'num_visitas_cobradas', 'valor_visita', 'valor_total_visitas',
            'status', 'observacoes'
        ]
        widgets = {
            'orcamento': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Obra'}),
            'data_orcamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'data_contratacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'data_inicio_real': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'data_previsao_termino': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'data_termino_real': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'prazo_obra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 60 dias'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rua, Avenida, etc.'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº, Apt, Bloco, etc.'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2', 'placeholder': 'Ex: SP'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'valor_orcado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'valor_contratado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'num_visitas_tecnicas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'num_visitas_cobradas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_visita': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'valor_total_visitas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': 'readonly', 'style': 'background-color: #e9ecef;'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'descricao': 'Nome da Obra',
            'data_orcamento': 'Data do Orçamento',
            'data_contratacao': 'Data da Contratação',
            'data_inicio_real': 'Início do Projeto',
            'data_previsao_termino': 'Previsão de Término do Projeto',
            'data_termino_real': 'Término do Projeto',
            'prazo_obra': 'Prazo da Obra',
            'logradouro': 'Endereço da Obra (Logradouro)',
            'complemento': 'Complemento',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'uf': 'Estado (UF)',
            'cep': 'CEP',
            'valor_orcado': 'Orçamento (R$)',
            'valor_contratado': 'Valor Contratado (R$)',
            'num_visitas_tecnicas': 'Número de Visitas Técnicas',
            'num_visitas_cobradas': 'Número de Visitas Técnicas Cobradas',
            'valor_visita': 'Valor por Visita Técnica (R$)',
            'valor_total_visitas': 'Valor Total Visitas Cobradas (R$)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar formatos de data
        for field_name in ['data_orcamento', 'data_contratacao', 'data_inicio_real', 'data_previsao_termino', 'data_termino_real']:
            if field_name in self.fields:
                self.fields[field_name].input_formats = ['%Y-%m-%d']
        
        # Se tem data_orcamento no initial, garantir que seja aplicada
        if self.initial.get('data_orcamento'):
            self.fields['data_orcamento'].initial = self.initial.get('data_orcamento')
        
        # Customizar label dos orçamentos para mostrar código e cliente
        self.fields['orcamento'].queryset = Orcamento.objects.select_related('cliente').all()
        self.fields['orcamento'].label_from_instance = lambda obj: f"{obj.codigo} - {obj.cliente.nome}" if obj.cliente else obj.codigo
        
        # Se está editando (instância existe), desabilitar campo orçamento
        if self.instance and self.instance.pk:
            self.fields['orcamento'].widget.attrs['disabled'] = 'disabled'
            self.fields['orcamento'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
            self.fields['orcamento'].help_text = 'Orçamento base não pode ser alterado'
            self.fields['orcamento'].required = False
            
            # Forçar o valor inicial do orçamento para garantir que apareça
            if self.instance.orcamento:
                self.fields['orcamento'].initial = self.instance.orcamento
        
        # Filtrar vendedores para mostrar apenas pessoas com flag vendedor
        self.fields['vendedor'].queryset = Pessoa.objects.filter(
            vendedor=True, 
            ativo=True
        ).order_by('nome')
        
        # Filtrar clientes
        self.fields['cliente'].queryset = Pessoa.objects.filter(
            cliente=True,
            ativo=True
        ).order_by('nome')
        
        # Se tem orçamento (criação ou edição), desabilitar campo cliente
        tem_orcamento = self.initial.get('orcamento') or (self.instance and self.instance.pk and self.instance.orcamento)
        
        if tem_orcamento:
            self.fields['cliente'].widget.attrs['disabled'] = 'disabled'
            self.fields['cliente'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'
            self.fields['cliente'].help_text = 'Cliente vinculado ao orçamento (não pode ser alterado)'
            # Garantir que o cliente seja mantido
            self.fields['cliente'].required = False
        
        # Se tem instância (editando) ou initial com cliente, preencher endereço do cliente
        cliente = None
        if self.instance and self.instance.pk and self.instance.cliente:
            cliente = self.instance.cliente
        elif self.initial.get('cliente'):
            try:
                cliente = Pessoa.objects.get(pk=self.initial['cliente'].pk if hasattr(self.initial['cliente'], 'pk') else self.initial['cliente'])
            except (Pessoa.DoesNotExist, AttributeError):
                pass
        
        if cliente:
            # Montar endereço completo do cliente
            endereco_parts = []
            if cliente.logradouro:
                endereco_parts.append(cliente.logradouro)
            if cliente.numero:
                endereco_parts.append(f"Nº {cliente.numero}")
            if cliente.complemento:
                endereco_parts.append(cliente.complemento)
            if cliente.bairro:
                endereco_parts.append(f"Bairro: {cliente.bairro}")
            if cliente.cidade and cliente.uf:
                endereco_parts.append(f"{cliente.cidade}/{cliente.uf}")
            elif cliente.cidade:
                endereco_parts.append(cliente.cidade)
            if cliente.cep:
                endereco_parts.append(f"CEP: {cliente.cep}")
            
            self.fields['endereco_cliente'].initial = ', '.join(endereco_parts) if endereco_parts else 'Endereço não cadastrado'
            
        # Se veio de orçamento ou tem orçamento vinculado, tornar cliente e data_orcamento readonly
        orcamento = None
        if self.initial.get('orcamento'):
            orcamento = self.initial.get('orcamento')
        elif self.instance and self.instance.pk and self.instance.orcamento:
            orcamento = self.instance.orcamento
            
        if orcamento:
            self.fields['cliente'].widget.attrs['readonly'] = True
            self.fields['cliente'].widget.attrs['disabled'] = True
            self.fields['cliente'].widget.attrs['style'] = 'background-color: #e9ecef;'
            
            # Tornar data_orcamento readonly também
            self.fields['data_orcamento'].widget.attrs['readonly'] = True
            self.fields['data_orcamento'].widget.attrs['style'] = 'background-color: #e9ecef;'
            self.fields['data_orcamento'].required = False
            
            # Garantir que data_orcamento está preenchida com a data do orçamento
            data_do_orcamento = None
            if hasattr(orcamento, 'data_orcamento'):
                data_do_orcamento = orcamento.data_orcamento
            elif hasattr(orcamento, 'pk'):
                # Se orcamento é apenas um ID, buscar o objeto
                try:
                    orcamento_obj = Orcamento.objects.get(pk=orcamento.pk if hasattr(orcamento, 'pk') else orcamento)
                    data_do_orcamento = orcamento_obj.data_orcamento
                except Orcamento.DoesNotExist:
                    pass
            
            if data_do_orcamento:
                # Atualizar a instância se estiver editando e não tiver data
                if self.instance and self.instance.pk:
                    self.instance.data_orcamento = data_do_orcamento
                # Setar no initial
                self.initial['data_orcamento'] = data_do_orcamento
                # Setar diretamente no campo
                self.fields['data_orcamento'].initial = data_do_orcamento
    
    def clean_cliente(self):
        # Se o campo foi desabilitado, retornar o valor original
        if self.instance and self.instance.pk and self.instance.orcamento:
            return self.instance.cliente
        if self.initial.get('cliente') and self.initial.get('orcamento'):
            return self.initial.get('cliente')
        return self.cleaned_data.get('cliente')
    
    def clean_data_orcamento(self):
        # Se tem orçamento vinculado, sempre usar a data do orçamento
        if self.instance and self.instance.pk and self.instance.orcamento:
            return self.instance.orcamento.data_orcamento
        
        # Se está criando e tem orçamento no initial
        orcamento = self.initial.get('orcamento')
        if orcamento:
            if hasattr(orcamento, 'data_orcamento'):
                return orcamento.data_orcamento
            # Se é apenas um ID, buscar o objeto
            try:
                orcamento_obj = Orcamento.objects.get(pk=orcamento.pk if hasattr(orcamento, 'pk') else orcamento)
                return orcamento_obj.data_orcamento
            except Orcamento.DoesNotExist:
                pass
        
        # Caso contrário, usar o valor do formulário
        return self.cleaned_data.get('data_orcamento')


class VisitaTecnicaForm(forms.ModelForm):
    class Meta:
        model = VisitaTecnica
        fields = ['orcamento', 'tecnico', 'data_visita', 'hora_inicio', 'hora_fim', 'custo_visita', 'valor_cobrado', 'status', 'descricao', 'observacoes']
        widgets = {
            'orcamento': forms.Select(attrs={'class': 'form-control'}),
            'tecnico': forms.Select(attrs={'class': 'form-control'}),
            'data_visita': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'hora_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'custo_visita': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'valor_cobrado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Objetivo da visita técnica'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'orcamento': 'Orçamento',
            'tecnico': 'Técnico Responsável',
            'data_visita': 'Data da Visita',
            'hora_inicio': 'Horário Início',
            'hora_fim': 'Horário Fim',
            'custo_visita': 'Custo da Visita (R$)',
            'valor_cobrado': 'Valor Cobrado (R$)',
            'status': 'Status',
            'descricao': 'Descrição/Objetivo',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar formatos
        self.fields['data_visita'].input_formats = ['%Y-%m-%d']
        self.fields['hora_inicio'].input_formats = ['%H:%M']
        self.fields['hora_fim'].input_formats = ['%H:%M']
        
        # Filtrar técnicos (vendedores ativos)
        self.fields['tecnico'].queryset = Pessoa.objects.filter(
            vendedor=True,
            ativo=True
        ).order_by('nome')
        
        # Filtrar orçamentos (apenas pendentes e aprovados)
        self.fields['orcamento'].queryset = Orcamento.objects.filter(
            status__in=['PENDENTE', 'APROVADO']
        ).select_related('cliente').order_by('-data_orcamento')
        
        # Customizar label dos orçamentos para mostrar código e cliente
        self.fields['orcamento'].label_from_instance = lambda obj: f"{obj.codigo} - {obj.cliente.nome}"


class AlocacaoProjetoForm(forms.ModelForm):
    class Meta:
        model = AlocacaoProjeto
        fields = ['projeto', 'data_alocacao', 'tipo', 'item', 'quantidade', 'valor_unitario', 'observacoes']
        widgets = {
            'projeto': forms.Select(attrs={'class': 'form-control'}),
            'data_alocacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VendaDiretaForm(forms.ModelForm):
    class Meta:
        model = VendaDireta
        fields = ['codigo', 'cliente', 'data_venda', 'desconto', 'status', 'observacoes']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'data_venda': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class VendaDiretaItemForm(forms.ModelForm):
    class Meta:
        model = VendaDiretaItem
        fields = ['item', 'quantidade', 'valor_unitario', 'desconto']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


VendaDiretaItemFormSet = inlineformset_factory(
    VendaDireta,
    VendaDiretaItem,
    form=VendaDiretaItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class ContaCorrenteProjetoForm(forms.ModelForm):
    class Meta:
        model = ContaCorrenteProjeto
        fields = ['projeto', 'data_movimento', 'tipo', 'descricao', 'valor', 'documento', 'observacoes']
        widgets = {
            'projeto': forms.Select(attrs={'class': 'form-control'}),
            'data_movimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DiarioObraForm(forms.ModelForm):
    """Formulário para Diário da Obra"""
    class Meta:
        from .models import DiarioObra
        model = DiarioObra
        fields = [
            'data', 'periodo', 'clima', 'temperatura',
            'num_trabalhadores', 'equipe_descricao', 'equipamentos_utilizados',
            'atividades_realizadas', 'percentual_progresso',
            'materiais_recebidos', 'materiais_utilizados',
            'problemas_encontrados', 'solucoes_aplicadas', 'visitas_fiscalizacao',
            'incidentes_seguranca', 'epi_utilizado',
            'observacoes'
        ]
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periodo': forms.Select(attrs={'class': 'form-control'}),
            'clima': forms.Select(attrs={'class': 'form-control'}),
            'temperatura': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 25°C'}),
            
            'num_trabalhadores': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'equipe_descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva a equipe presente (nomes e funções)'}),
            'equipamentos_utilizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Liste os equipamentos utilizados'}),
            
            'atividades_realizadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descreva as atividades executadas no dia'}),
            'percentual_progresso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            
            'materiais_recebidos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Materiais que chegaram na obra'}),
            'materiais_utilizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Materiais consumidos no dia'}),
            
            'problemas_encontrados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva problemas ou imprevistos'}),
            'solucoes_aplicadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Como os problemas foram resolvidos'}),
            'visitas_fiscalizacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Registre visitas de fiscais, engenheiros, clientes'}),
            
            'incidentes_seguranca': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Acidentes ou questões de segurança'}),
            'epi_utilizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Outras informações relevantes'}),
        }
        labels = {
            'epi_utilizado': 'Todos utilizaram EPIs adequados?',
        }

