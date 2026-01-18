"""
Formulários do Módulo Financeiro
"""
from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from .models import (
    Banco, ContaFinanceira, FormaPagamento, CentroCusto,
    CategoriaCustoVariabilidade, TituloFinanceiro, ParcelaFinanceira,
    BaixaFinanceira, MovimentacaoConta, TransferenciaEntreContas, PlanoConta,
    ReguaCobranca, ReguaEtapa, RegimeTributario, AliquotaImposto
)
from cadastros.models import Pessoa


class BancoForm(forms.ModelForm):
    """Formulário para cadastro de Bancos"""
    
    class Meta:
        model = Banco
        fields = ['codigo_compe', 'nome', 'ativo']
        widgets = {
            'codigo_compe': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '3'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ContaFinanceiraForm(forms.ModelForm):
    """Formulário para cadastro de Contas Financeiras"""
    
    class Meta:
        model = ContaFinanceira
        fields = ['nome', 'tipo', 'banco', 'agencia', 'conta', 'saldo_inicial', 'data_saldo_inicial', 'limite_credito', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'banco': forms.Select(attrs={'class': 'form-select'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_saldo_inicial': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'limite_credito': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FormaPagamentoForm(forms.ModelForm):
    """Formulário para cadastro de Formas de Pagamento"""
    
    class Meta:
        model = FormaPagamento
        fields = ['codigo', 'descricao', 'tipo', 'prazo_compensacao', 'taxa_percentual', 'taxa_fixa', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prazo_compensacao': forms.NumberInput(attrs={'class': 'form-control'}),
            'taxa_percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'taxa_fixa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CentroCustoForm(forms.ModelForm):
    """Formulário para cadastro de Centros de Custo"""
    
    class Meta:
        model = CentroCusto
        fields = ['codigo', 'nome', 'tipo', 'projeto', 'responsavel', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'projeto': forms.Select(attrs={'class': 'form-select'}),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PlanoContaForm(forms.ModelForm):
    """Formulário para cadastro de Plano de Contas"""
    
    class Meta:
        model = PlanoConta
        fields = ['codigo', 'nome', 'tipo', 'natureza', 'conta_pai', 'ativo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1.1.01, 3.2.01.001'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'natureza': forms.Select(attrs={'class': 'form-select'}),
            'conta_pai': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas contas sintéticas como opções de conta_pai
        self.fields['conta_pai'].queryset = PlanoConta.objects.filter(ativo=True).order_by('codigo')
        self.fields['conta_pai'].required = False


class CategoriaCustoVariabilidadeForm(forms.ModelForm):
    """Formulário para classificação de variabilidade de custos"""
    
    class Meta:
        model = CategoriaCustoVariabilidade
        fields = ['nome', 'tipo', 'percentual_variavel', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'percentual_variavel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TituloFinanceiroForm(forms.ModelForm):
    """Formulário para cadastro de Títulos Financeiros"""
    
    # Campos adicionais para configuração de régua de cobrança
    regua_cobranca = forms.ModelChoiceField(
        queryset=ReguaCobranca.objects.none(),
        required=False,
        label='Régua de Cobrança',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Régua de cobrança automática para as parcelas'
    )
    ativar_regua = forms.BooleanField(
        required=False,
        initial=False,
        label='Ativar Régua Automaticamente',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Marque para ativar a régua de cobrança nas parcelas'
    )
    
    class Meta:
        model = TituloFinanceiro
        fields = [
            'tipo', 'numero_documento', 'descricao', 'pessoa', 
            'plano_conta', 'projeto', 'centro_custo', 'conta_financeira_padrao',
            'data_emissao', 'data_primeiro_vencimento', 'valor_total', 
            'num_parcelas', 'intervalo_dias', 'intervalos_personalizados', 'observacao'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: NF-001/2025'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição do título'}),
            'pessoa': forms.Select(attrs={'class': 'form-select'}),
            'plano_conta': forms.Select(attrs={'class': 'form-select'}),
            'projeto': forms.Select(attrs={'class': 'form-select'}),
            'centro_custo': forms.Select(attrs={'class': 'form-select'}),
            'conta_financeira_padrao': forms.Select(attrs={'class': 'form-select'}),
            'data_emissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'data_primeiro_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'num_parcelas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'intervalo_dias': forms.NumberInput(attrs={'class': 'form-control', 'value': '30'}),
            'intervalos_personalizados': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 30/45/60'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Configurar formato de data para inputs type="date"
        self.fields['data_emissao'].input_formats = ['%Y-%m-%d']
        self.fields['data_primeiro_vencimento'].input_formats = ['%Y-%m-%d']
        
        # Filtrar réguas pela empresa
        if empresa:
            self.fields['regua_cobranca'].queryset = ReguaCobranca.objects.filter(
                empresa=empresa,
                ativa=True
            ).order_by('nome')
        
        # Se está editando, pegar régua da primeira parcela
        if self.instance and self.instance.pk:
            primeira_parcela = self.instance.parcelas.first()
            if primeira_parcela:
                self.initial['regua_cobranca'] = primeira_parcela.regua
                self.initial['ativar_regua'] = primeira_parcela.regua_ativa
        
        # Valores padrão quando criando novo título
        if not self.instance.pk:
            self.fields['intervalo_dias'].initial = 0
            self.fields['num_parcelas'].initial = 1
        
        # Filtrar apenas pessoas que são clientes ou fornecedores (campo opcional)
        self.fields['pessoa'].queryset = Pessoa.objects.filter(
            models.Q(cliente=True) | models.Q(fornecedor=True),
            ativo=True
        ).order_by('nome')
        self.fields['pessoa'].required = False
        self.fields['pessoa'].help_text = 'Opcional - deixe vazio para impostos e taxas'
        
        # Importar modelo Projeto
        from projetos.models import Projeto
        
        # Filtrar plano de contas - apenas analíticas ativas
        self.fields['plano_conta'].queryset = PlanoConta.objects.filter(
            aceita_lancamento=True,
            ativo=True
        ).order_by('codigo')
        self.fields['plano_conta'].required = False
        self.fields['plano_conta'].help_text = 'Classificação contábil (conta analítica)'
        self.fields['plano_conta'].label_from_instance = lambda obj: f"{obj.codigo} - {obj.nome}"
        
        # Filtrar projetos ativos (excluir cancelados e concluídos)
        self.fields['projeto'].queryset = Projeto.objects.exclude(
            status__in=['CANCELADO', 'CONCLUIDO']
        ).order_by('codigo')
        self.fields['projeto'].required = False
        self.fields['projeto'].help_text = 'Selecione o projeto/obra (opcional)'
        
        # Filtrar centros de custo ativos
        self.fields['centro_custo'].queryset = CentroCusto.objects.filter(ativo=True).select_related('projeto').order_by('nome')
        self.fields['centro_custo'].required = False
        self.fields['centro_custo'].help_text = 'Centro de custo/departamento (opcional)'
        
        # Filtrar contas financeiras ativas
        self.fields['conta_financeira_padrao'].queryset = ContaFinanceira.objects.filter(ativo=True).select_related('banco').order_by('nome')
        self.fields['conta_financeira_padrao'].required = False
        self.fields['conta_financeira_padrao'].label_from_instance = lambda obj: f"{obj.nome}{f' - {obj.banco}' if obj.banco else ''} ({obj.get_tipo_display()})"
        self.fields['conta_financeira_padrao'].help_text = 'Banco/caixa de onde sairá o pagamento (será usada como padrão nas baixas)'


class ParcelaFinanceiraForm(forms.ModelForm):
    """Formulário para edição manual de Parcelas"""
    
    class Meta:
        model = ParcelaFinanceira
        fields = ['data_vencimento', 'valor_original']
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_original': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class BaixaFinanceiraForm(forms.ModelForm):
    """Formulário para baixa de parcelas"""
    
    class Meta:
        model = BaixaFinanceira
        fields = [
            'data_pagamento', 'conta_financeira', 'forma_pagamento',
            'valor_principal', 'juros', 'multa', 'desconto', 'observacao'
        ]
        widgets = {
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'conta_financeira': forms.Select(attrs={'class': 'form-select'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'valor_principal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'juros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'value': '0'}),
            'multa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'value': '0'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'value': '0'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, parcela=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parcela = parcela
        
        # Filtrar contas financeiras ativas
        self.fields['conta_financeira'].queryset = ContaFinanceira.objects.filter(ativo=True).order_by('nome')
        self.fields['forma_pagamento'].queryset = FormaPagamento.objects.filter(ativo=True).order_by('descricao')
        
        # Se tiver parcela, preencher valor padrão
        if parcela:
            self.fields['valor_principal'].initial = parcela.saldo_aberto
    
    def clean_valor_principal(self):
        """Valida se o valor não excede o saldo em aberto"""
        valor = self.cleaned_data.get('valor_principal')
        
        if self.parcela and valor > self.parcela.saldo_aberto:
            raise ValidationError(
                f'Valor não pode exceder o saldo em aberto: R$ {self.parcela.saldo_aberto:.2f}'
            )
        
        return valor


class TransferenciaEntreContasForm(forms.ModelForm):
    """Formulário para transferências entre contas"""
    
    class Meta:
        model = TransferenciaEntreContas
        fields = ['data_transferencia', 'conta_origem', 'conta_destino', 'valor', 'descricao']
        widgets = {
            'data_transferencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'conta_origem': forms.Select(attrs={'class': 'form-select'}),
            'conta_destino': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar contas ativas
        self.fields['conta_origem'].queryset = ContaFinanceira.objects.filter(ativo=True).order_by('nome')
        self.fields['conta_destino'].queryset = ContaFinanceira.objects.filter(ativo=True).order_by('nome')
    
    def clean(self):
        cleaned_data = super().clean()
        conta_origem = cleaned_data.get('conta_origem')
        conta_destino = cleaned_data.get('conta_destino')
        
        if conta_origem and conta_destino and conta_origem == conta_destino:
            raise ValidationError('Conta de origem e destino não podem ser iguais.')
        
        return cleaned_data


class MovimentacaoContaForm(forms.ModelForm):
    """Formulário para lançamentos manuais em contas"""
    
    class Meta:
        model = MovimentacaoConta
        fields = ['conta_financeira', 'tipo', 'data_movimentacao', 'valor', 'descricao']
        widgets = {
            'conta_financeira': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'data_movimentacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição da movimentação'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['conta_financeira'].queryset = ContaFinanceira.objects.filter(ativo=True).order_by('nome')


# Formulários de Filtro para Relatórios

class FiltroRelatorioForm(forms.Form):
    """Formulário base para filtros de relatórios"""
    
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Início'
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Fim'
    )
    centro_custo = forms.ModelChoiceField(
        queryset=CentroCusto.objects.filter(ativo=True).order_by('nome'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Centro de Custo',
        empty_label='Todos'
    )


class FiltroContasPagarReceberForm(FiltroRelatorioForm):
    """Filtro para relatórios de contas a pagar/receber"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('ABERTO', 'Em Aberto'),
        ('PARCIAL', 'Parcialmente Pago'),
        ('QUITADO', 'Quitado'),
        ('VENCIDO', 'Vencido'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Status'
    )
    pessoa = forms.ModelChoiceField(
        queryset=Pessoa.objects.filter(ativo=True).order_by('nome'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cliente/Fornecedor',
        empty_label='Todos'
    )


class FiltroFluxoCaixaForm(forms.Form):
    """Filtro para relatório de fluxo de caixa"""
    
    data_inicio = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Início'
    )
    data_fim = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Data Fim'
    )
    conta_financeira = forms.ModelChoiceField(
        queryset=ContaFinanceira.objects.filter(ativo=True).order_by('nome'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Conta Financeira',
        empty_label='Todas'
    )
    incluir_previsao = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir Previsão'
    )


class FiltroCalendarioForm(forms.Form):
    """Filtro para calendário financeiro"""
    
    mes = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'}),
        label='Mês'
    )
    ano = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2100'}),
        label='Ano'
    )
    tipo = forms.ChoiceField(
        choices=[('', 'Todos'), ('PAGAR', 'A Pagar'), ('RECEBER', 'A Receber')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo'
    )


# ============================================
# FORMULÁRIOS RÉGUA DE COBRANÇA
# ============================================

class ReguaCobrancaForm(forms.ModelForm):
    """Formulário para cadastro de Régua de Cobrança"""
    
    class Meta:
        model = ReguaCobranca
        fields = ['nome', 'descricao', 'empresa', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Régua Padrão - Cobrança Progressiva'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o objetivo desta régua de cobrança...'
            }),
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReguaEtapaForm(forms.ModelForm):
    """Formulário para cadastro de Etapas da Régua"""
    
    class Meta:
        model = ReguaEtapa
        fields = [
            'ordem', 'nome', 'offset_dias', 'enviar_email',
            'assunto_email', 'template_email', 'ativo'
        ]
        widgets = {
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '1'
            }),
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lembrete Pré-Vencimento'
            }),
            'offset_dias': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: -3 (antes), 0 (no dia), +7 (depois)'
            }),
            'enviar_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'assunto_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lembrete: Parcela vence em 3 dias'
            }),
            'template_email': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 8,
                'placeholder': 'Use variáveis: {cliente_nome}, {parcela_valor}, {data_vencimento}, etc.'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'ordem': 'Ordem de Execução',
            'nome': 'Nome da Etapa',
            'offset_dias': 'Dias em Relação ao Vencimento',
            'enviar_email': 'Enviar E-mail',
            'assunto_email': 'Assunto do E-mail',
            'template_email': 'Mensagem do E-mail',
            'ativo': 'Etapa Ativa',
        }
        help_texts = {
            'offset_dias': 'Número negativo para antes do vencimento, 0 para o dia, positivo para depois',
            'template_email': 'Use as variáveis disponíveis para personalizar a mensagem',
        }


# Formset para múltiplas etapas
ReguaEtapaFormSet = forms.inlineformset_factory(
    ReguaCobranca,
    ReguaEtapa,
    form=ReguaEtapaForm,
    extra=5,  # 5 etapas em branco por padrão
    can_delete=True,
    min_num=1,
    validate_min=True,
)


# ============================================================================
# FORMS - REGIME TRIBUTÁRIO
# ============================================================================

class RegimeTributarioForm(forms.ModelForm):
    """Formulário para cadastro de Regime Tributário"""
    
    class Meta:
        model = RegimeTributario
        fields = ['nome', 'descricao', 'ativo']
        widgets = {
            'nome': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome': 'Regime Tributário',
            'descricao': 'Descrição',
            'ativo': 'Ativo',
        }


class AliquotaImpostoForm(forms.ModelForm):
    """Formulário para cadastro de Alíquotas de Impostos"""
    
    class Meta:
        model = AliquotaImposto
        fields = ['regime_tributario', 'tipo_imposto', 'aliquota_percentual', 'base_calculo', 'observacao', 'ativo']
        widgets = {
            'regime_tributario': forms.Select(attrs={'class': 'form-control'}),
            'tipo_imposto': forms.Select(attrs={'class': 'form-control'}),
            'aliquota_percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'base_calculo': forms.Select(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'regime_tributario': 'Regime Tributário',
            'tipo_imposto': 'Tipo de Imposto',
            'aliquota_percentual': 'Alíquota (%)',
            'base_calculo': 'Base de Cálculo',
            'observacao': 'Observação',
            'ativo': 'Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            self.instance.empresa = empresa


class CategoriaCustoForm(forms.ModelForm):
    """Formulário para cadastro de Categorias de Custo"""
    
    class Meta:
        model = CategoriaCustoVariabilidade
        fields = ['nome', 'tipo', 'percentual_variavel', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'percentual_variavel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nome': 'Nome da Categoria',
            'tipo': 'Tipo de Custo',
            'percentual_variavel': 'Percentual Variável (%)',
            'observacao': 'Observação',
        }
        help_texts = {
            'percentual_variavel': 'Para custos mistos: percentual que é variável (0 a 100%)',
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            self.instance.empresa = empresa
        
        # Adicionar lógica para mostrar/esconder campo percentual_variavel
        self.fields['percentual_variavel'].widget.attrs['data-tipo-field'] = 'percentual_variavel'
