from django import forms
from .models import Cliente, Processo, ProcessoArquivo, Movimentacao, Comarca, Vara, TipoProcesso

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


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


class ClienteForm(forms.ModelForm):
    documentos = MultiFileField(
        required=False,
        label='Documentos do Cliente',
        widget=MultiFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Cliente
        fields = [
            'tipo',
            'nome',
            'responsavel',
            'cpf_cnpj',
            'email',
            'telefone',
            'endereco',
            'demanda',
            'processos_possiveis',
            'observacoes',
        ]
        widgets = {
            'tipo': forms.Select(attrs=SELECT_ATTRS),
            'nome': forms.TextInput(attrs=WIDGET_ATTRS),
            'responsavel': forms.Select(attrs=SELECT_ATTRS),
            'cpf_cnpj': forms.TextInput(attrs=WIDGET_ATTRS),
            'email': forms.EmailInput(attrs=WIDGET_ATTRS),
            'telefone': forms.TextInput(attrs=WIDGET_ATTRS),
            'endereco': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
            'demanda': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
            'processos_possiveis': forms.SelectMultiple(attrs={**SELECT_ATTRS, 'size': 8}),
            'observacoes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['processos_possiveis'].queryset = TipoProcesso.objects.order_by('nome')
        self.fields['processos_possiveis'].help_text = 'Selecione um ou mais tipos de processo relacionados à demanda.'


class ProcessoForm(forms.ModelForm):
    arquivos = MultiFileField(
        required=False,
        label='Arquivos do Processo',
        widget=MultiFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Processo
        fields = ['numero', 'cliente', 'advogado', 'tipo', 'vara', 'status', 'valor_causa', 'objeto']
        widgets = {
            'numero': forms.TextInput(attrs=WIDGET_ATTRS),
            'cliente': forms.Select(attrs=SELECT_ATTRS),
            'advogado': forms.Select(attrs=SELECT_ATTRS),
            'tipo': forms.Select(attrs=SELECT_ATTRS),
            'vara': forms.Select(attrs=SELECT_ATTRS),
            'status': forms.Select(attrs=SELECT_ATTRS),
            'valor_causa': forms.NumberInput(attrs=WIDGET_ATTRS),
            'objeto': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 4}),
        }


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['data', 'titulo', 'descricao', 'documento']
        widgets = {
            'data': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'titulo': forms.TextInput(attrs=WIDGET_ATTRS),
            'descricao': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 4}),
        }


class ComarcaForm(forms.ModelForm):
    class Meta:
        model = Comarca
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs=WIDGET_ATTRS),
            'estado': forms.TextInput(attrs=WIDGET_ATTRS),
        }


class VaraForm(forms.ModelForm):
    class Meta:
        model = Vara
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs=WIDGET_ATTRS),
            'comarca': forms.Select(attrs=SELECT_ATTRS),
        }


class TipoProcessoForm(forms.ModelForm):
    class Meta:
        model = TipoProcesso
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs=WIDGET_ATTRS),
            'descricao': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
        }


class ProcessoArquivoUploadForm(forms.Form):
    arquivos = MultiFileField(
        required=True,
        label='Anexar Arquivos',
        widget=MultiFileInput(attrs={'class': 'form-control'}),
    )
