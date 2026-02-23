from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Usuario
from .forms import LoginForm, UsuarioCreationForm, UsuarioChangeForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    from processos.models import Processo
    from agenda.models import Compromisso
    from django.utils import timezone

    hoje = timezone.now().date()
    usuario = request.user

    if usuario.is_administrador():
        processos_ativos = Processo.objects.filter(status='em_andamento').count()
        compromissos_hoje = Compromisso.objects.filter(data=hoje).count()
        prazos_urgentes = Compromisso.objects.filter(data=hoje, tipo='prazo').count()
        todos_processos = Processo.objects.order_by('-criado_em')[:5]
    else:
        processos_ativos = Processo.objects.filter(advogado=usuario, status='em_andamento').count()
        compromissos_hoje = Compromisso.objects.filter(advogado=usuario, data=hoje).count()
        prazos_urgentes = Compromisso.objects.filter(advogado=usuario, data=hoje, tipo='prazo').count()
        todos_processos = Processo.objects.filter(advogado=usuario).order_by('-criado_em')[:5]

    return render(request, 'accounts/dashboard.html', {
        'processos_ativos': processos_ativos,
        'compromissos_hoje': compromissos_hoje,
        'prazos_urgentes': prazos_urgentes,
        'processos_recentes': todos_processos,
        'hoje': hoje,
    })


@login_required
def lista_usuarios(request):
    if not request.user.is_administrador():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    usuarios = Usuario.objects.all().order_by('first_name')
    return render(request, 'accounts/lista_usuarios.html', {'usuarios': usuarios})


@login_required
def novo_usuario(request):
    if not request.user.is_administrador():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    form = UsuarioCreationForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário criado com sucesso.')
        return redirect('lista_usuarios')
    return render(request, 'accounts/form_usuario.html', {'form': form, 'titulo': 'Novo Usuário'})


@login_required
def editar_usuario(request, pk):
    if not request.user.is_administrador():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioChangeForm(request.POST or None, request.FILES or None, instance=usuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuário atualizado com sucesso.')
        return redirect('lista_usuarios')
    return render(request, 'accounts/form_usuario.html', {'form': form, 'titulo': 'Editar Usuário', 'objeto': usuario})


@login_required
def perfil(request):
    form = UsuarioChangeForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil atualizado com sucesso.')
        return redirect('perfil')
    return render(request, 'accounts/perfil.html', {'form': form})
