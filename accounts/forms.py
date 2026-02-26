from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Usuario


class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'papel', 'responsavel_advogado', 'oab', 'telefone', 'foto')


class UsuarioChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'papel', 'responsavel_advogado', 'oab', 'telefone', 'foto')


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'oab', 'telefone', 'foto')


class LoginForm(forms.Form):
    username = forms.CharField(label='Usuário', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'}))
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}))
