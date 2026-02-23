from django import forms
from .models import Cliente, Processo, Movimentacao, Comarca, Vara, TipoProcesso

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        exclude = ['criado_em']
        widgets = {
            'tipo': forms.Select(attrs=SELECT_ATTRS),
            'nome': forms.TextInput(attrs=WIDGET_ATTRS),
            'cpf_cnpj': forms.TextInput(attrs=WIDGET_ATTRS),
            'email': forms.EmailInput(attrs=WIDGET_ATTRS),
            'telefone': forms.TextInput(attrs=WIDGET_ATTRS),
            'endereco': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 2}),
            'observacoes': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
        }


class ProcessoForm(forms.ModelForm):
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
