from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q, Sum
from datetime import timedelta
from .models import Usuario
from .forms import LoginForm, UsuarioCreationForm, UsuarioChangeForm, PerfilForm


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
            next_url = request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('dashboard')
        messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    from processos.models import Processo, Cliente
    from agenda.models import Compromisso
    from django.utils import timezone

    hoje = timezone.now().date()
    limite = hoje + timedelta(days=7)
    usuario = request.user

    if usuario.is_administrador():
        processos_qs = Processo.objects.select_related('cliente', 'advogado', 'tipo').all()
        clientes_qs = Cliente.objects.all()
        compromissos_qs = Compromisso.objects.select_related('advogado', 'processo').all()
    else:
        processos_qs = Processo.objects.select_related('cliente', 'advogado', 'tipo').filter(advogado=usuario)
        clientes_qs = Cliente.objects.filter(processos__advogado=usuario).distinct()
        compromissos_qs = Compromisso.objects.select_related('advogado', 'processo').filter(advogado=usuario)

    total_processos = processos_qs.count()
    total_clientes = clientes_qs.count()
    eventos_hoje = compromissos_qs.filter(
        data=hoje,
        status='pendente',
    ).exclude(tipo='prazo').count()
    prazos_proximos = compromissos_qs.filter(
        tipo='prazo',
        status='pendente',
        data__gte=hoje,
        data__lte=limite,
    ).count()

    return render(request, 'accounts/dashboard.html', {
        # O frontend mantém o card com o rótulo "Processos Ativos", mas o usuário
        # solicitou explicitamente que traga o total de processos cadastrados.
        'processos_ativos': total_processos,
        'total_processos': total_processos,
        'total_clientes': total_clientes,
        'eventos_hoje': eventos_hoje,
        'prazos_proximos': prazos_proximos,
        # chaves legadas para compatibilidade com templates existentes
        'compromissos_hoje': eventos_hoje,
        'prazos_urgentes': prazos_proximos,
        'processos_recentes': processos_qs.order_by('-criado_em')[:5],
        'eventos_prazos_proximos': compromissos_qs.filter(
            status='pendente',
            data__gte=hoje,
        ).order_by('data', 'hora')[:8],
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
    form = PerfilForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil atualizado com sucesso.')
        return redirect('perfil')
    return render(request, 'accounts/perfil.html', {'form': form})


def _contexto_portal(usuario_alvo=None):
    from processos.models import Processo
    from agenda.models import Compromisso
    from financeiro.models import Lancamento
    from django.utils import timezone
    from datetime import timedelta

    hoje = timezone.now().date()

    if usuario_alvo is None:
        processos_qs = Processo.objects.select_related('cliente', 'advogado', 'tipo').all()
        compromissos_qs = Compromisso.objects.select_related('advogado', 'processo').all()
        lancamentos_qs = Lancamento.objects.select_related('cliente', 'processo', 'criado_por').all()
        titulo = 'Portal Administrativo'
        subtitulo = 'Visão consolidada do escritório'
    else:
        processos_qs = Processo.objects.select_related('cliente', 'advogado', 'tipo').filter(advogado=usuario_alvo)
        compromissos_qs = Compromisso.objects.select_related('advogado', 'processo').filter(advogado=usuario_alvo)
        lancamentos_qs = Lancamento.objects.select_related('cliente', 'processo', 'criado_por').filter(
            Q(criado_por=usuario_alvo) | Q(processo__advogado=usuario_alvo)
        ).distinct()
        nome = usuario_alvo.get_full_name() or usuario_alvo.username
        titulo = f'Portal de {nome}'
        subtitulo = 'Visão individual do advogado'

    totais_financeiro = lancamentos_qs.aggregate(
        pendente=Sum('valor', filter=Q(status='pendente')),
        atrasado=Sum('valor', filter=Q(status='atrasado')),
        pago=Sum('valor', filter=Q(status='pago')),
    )

    return {
        'titulo_portal': titulo,
        'subtitulo_portal': subtitulo,
        'usuario_alvo': usuario_alvo,
        'processos_ativos': processos_qs.filter(status='em_andamento').count(),
        'total_processos': processos_qs.count(),
        'compromissos_hoje': compromissos_qs.filter(data=hoje, status='pendente').count(),
        'prazos_7_dias': compromissos_qs.filter(
            data__gte=hoje,
            data__lte=hoje + timedelta(days=7),
            tipo='prazo',
            status='pendente',
        ).count(),
        'financeiro_pendente': totais_financeiro['pendente'] or 0,
        'financeiro_atrasado': totais_financeiro['atrasado'] or 0,
        'financeiro_pago': totais_financeiro['pago'] or 0,
        'processos_recentes': processos_qs.order_by('-criado_em')[:8],
        'compromissos_proximos': compromissos_qs.filter(data__gte=hoje).order_by('data', 'hora')[:8],
        'lancamentos_recentes': lancamentos_qs.order_by('-criado_em')[:8],
        'advogados_portal': Usuario.objects.filter(papel='advogado').order_by('first_name', 'username'),
    }


@login_required
def meu_portal(request):
    if request.user.is_administrador():
        contexto = _contexto_portal(usuario_alvo=None)
    else:
        contexto = _contexto_portal(usuario_alvo=request.user)
    return render(request, 'accounts/portal_usuario.html', contexto)


@login_required
def portal_usuario(request, pk):
    usuario_alvo = get_object_or_404(Usuario, pk=pk)
    if not request.user.is_administrador() and request.user.pk != usuario_alvo.pk:
        messages.error(request, 'Você não pode acessar o portal de outro usuário.')
        return redirect('meu_portal')
    contexto = _contexto_portal(usuario_alvo=usuario_alvo)
    return render(request, 'accounts/portal_usuario.html', contexto)
