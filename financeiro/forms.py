from django import forms
from .models import Lancamento
from processos.models import Cliente, Processo


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    widget = MultiFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if data in self.empty_values:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class LancamentoForm(forms.ModelForm):
    arquivos = MultiFileField(
        required=False,
        label='Anexos',
        widget=MultiFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Lancamento
        fields = [
            'cliente', 'processo', 'tipo', 'descricao',
            'valor', 'data_vencimento', 'data_pagamento', 'status', 'observacoes',
        ]
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'processo': forms.Select(attrs={'class': 'form-select', 'id': 'id_processo'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['processo'].queryset = Processo.objects.select_related('cliente').all()
        self.fields['processo'].required = False
        self.fields['data_pagamento'].required = False
        self.fields['observacoes'].required = False
        # Label com nome do cliente em cada opção de processo
        self.fields['processo'].label_from_instance = lambda p: f'{p.numero} – {p.cliente.nome}'


class LancamentoArquivoUploadForm(forms.Form):
    arquivos = MultiFileField(
        required=True,
        label='Anexar Arquivos',
        widget=MultiFileInput(attrs={'class': 'form-control'}),
    )
