from django import forms
from .models import Documento

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['titulo', 'categoria', 'tribunal', 'processo_referencia', 'conteudo', 'arquivo', 'tags', 'data_decisao']
        widgets = {
            'titulo': forms.TextInput(attrs=WIDGET_ATTRS),
            'categoria': forms.Select(attrs=SELECT_ATTRS),
            'tribunal': forms.TextInput(attrs=WIDGET_ATTRS),
            'processo_referencia': forms.Select(attrs=SELECT_ATTRS),
            'conteudo': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 8}),
            'tags': forms.TextInput(attrs={**WIDGET_ATTRS, 'placeholder': 'ex: trabalhista, rescisão, FGTS'}),
            'data_decisao': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
        }
