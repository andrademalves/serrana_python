"""
Formulários do módulo de usuários
"""
from django import forms
from .models import BackupConfig


class BackupConfigForm(forms.ModelForm):
    """
    Formulário para configuração de backups agendados
    """
    
    class Meta:
        model = BackupConfig
        fields = [
            'habilitado',
            'frequencia',
            'hora_execucao',
            'dia_semana',
            'dia_mes',
            'manter_ultimos_n',
            'manter_dias',
        ]
        
        widgets = {
            'habilitado': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'frequencia': forms.Select(attrs={
                'class': 'form-select',
            }),
            'hora_execucao': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'dia_semana': forms.Select(attrs={
                'class': 'form-select',
            }),
            'dia_mes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 28,
            }),
            'manter_ultimos_n': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'help_text': '0 = ilimitado',
            }),
            'manter_dias': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'help_text': '0 = ilimitado',
            }),
        }
    
    def clean_dia_mes(self):
        """Valida que o dia do mês está entre 1 e 28"""
        dia = self.cleaned_data.get('dia_mes')
        if dia and (dia < 1 or dia > 28):
            raise forms.ValidationError('O dia do mês deve estar entre 1 e 28')
        return dia
    
    def clean(self):
        """Validações personalizadas"""
        cleaned_data = super().clean()
        
        manter_ultimos_n = cleaned_data.get('manter_ultimos_n')
        manter_dias = cleaned_data.get('manter_dias')
        
        # Pelo menos uma política de retenção deve estar ativa
        if manter_ultimos_n == 0 and manter_dias == 0:
            raise forms.ValidationError(
                'Defina pelo menos uma política de retenção: '
                'quantidade de backups OU dias de retenção.'
            )
        
        return cleaned_data
