from django import forms
from .models import Compromisso

WIDGET_ATTRS = {'class': 'form-control'}
SELECT_ATTRS = {'class': 'form-select'}


class CompromissoForm(forms.ModelForm):
    class Meta:
        model = Compromisso
        fields = ['titulo', 'tipo', 'data', 'hora', 'advogado', 'processo', 'descricao', 'status']
        widgets = {
            'titulo': forms.TextInput(attrs=WIDGET_ATTRS),
            'tipo': forms.Select(attrs=SELECT_ATTRS),
            'data': forms.DateInput(attrs={**WIDGET_ATTRS, 'type': 'date'}),
            'hora': forms.TimeInput(attrs={**WIDGET_ATTRS, 'type': 'time'}),
            'advogado': forms.Select(attrs=SELECT_ATTRS),
            'processo': forms.Select(attrs=SELECT_ATTRS),
            'descricao': forms.Textarea(attrs={**WIDGET_ATTRS, 'rows': 3}),
            'status': forms.Select(attrs=SELECT_ATTRS),
        }
