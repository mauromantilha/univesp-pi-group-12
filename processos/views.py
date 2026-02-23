from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Cliente, Processo, Movimentacao, Comarca, Vara, TipoProcesso
from .forms import ClienteForm, ProcessoForm, MovimentacaoForm, ComarcaForm, VaraForm, TipoProcessoForm


# ─── Clientes ────────────────────────────────────────────────────────────────

@login_required
def lista_clientes(request):
    q = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nome__icontains=q) if q else Cliente.objects.all()
    return render(request, 'processos/lista_clientes.html', {'clientes': clientes, 'q': q})


@login_required
def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'processos/detalhe_cliente.html', {'cliente': cliente})


@login_required
def novo_cliente(request):
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente cadastrado com sucesso.')
        return redirect('lista_clientes')
    return render(request, 'processos/form_cliente.html', {'form': form, 'titulo': 'Novo Cliente'})


@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente atualizado com sucesso.')
        return redirect('detalhe_cliente', pk=pk)
    return render(request, 'processos/form_cliente.html', {'form': form, 'titulo': 'Editar Cliente', 'objeto': cliente})


# ─── Processos ───────────────────────────────────────────────────────────────

@login_required
def lista_processos(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    usuario = request.user
    processos = Processo.objects.select_related('cliente', 'advogado', 'tipo', 'vara')
    if not usuario.is_administrador():
        processos = processos.filter(advogado=usuario)
    if q:
        processos = processos.filter(Q(numero__icontains=q) | Q(cliente__nome__icontains=q))
    if status:
        processos = processos.filter(status=status)
    return render(request, 'processos/lista_processos.html', {
        'processos': processos,
        'q': q,
        'status_filtro': status,
        'status_choices': Processo.STATUS_CHOICES,
    })


@login_required
def detalhe_processo(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    movimentacoes = processo.movimentacoes.all()
    form_mov = MovimentacaoForm()
    return render(request, 'processos/detalhe_processo.html', {
        'processo': processo,
        'movimentacoes': movimentacoes,
        'form_mov': form_mov,
    })


@login_required
def novo_processo(request):
    form = ProcessoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Processo cadastrado com sucesso.')
        return redirect('lista_processos')
    return render(request, 'processos/form_processo.html', {'form': form, 'titulo': 'Novo Processo'})


@login_required
def editar_processo(request, pk):
    processo = get_object_or_404(Processo, pk=pk)
    form = ProcessoForm(request.POST or None, instance=processo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Processo atualizado com sucesso.')
        return redirect('detalhe_processo', pk=pk)
    return render(request, 'processos/form_processo.html', {'form': form, 'titulo': 'Editar Processo', 'objeto': processo})


@login_required
def nova_movimentacao(request, processo_pk):
    processo = get_object_or_404(Processo, pk=processo_pk)
    form = MovimentacaoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        mov = form.save(commit=False)
        mov.processo = processo
        mov.autor = request.user
        mov.save()
        messages.success(request, 'Movimentação registrada.')
        return redirect('detalhe_processo', pk=processo_pk)
    return render(request, 'processos/form_movimentacao.html', {'form': form, 'processo': processo})


# ─── Carga de trabalho ───────────────────────────────────────────────────────

@login_required
def carga_trabalho(request):
    from accounts.models import Usuario
    advogados = Usuario.objects.filter(papel__in=['advogado', 'administrador'])
    dados = []
    for adv in advogados:
        dados.append({
            'advogado': adv,
            'total': adv.processos.count(),
            'em_andamento': adv.processos.filter(status='em_andamento').count(),
        })
    return render(request, 'processos/carga_trabalho.html', {'dados': dados})


# ─── Entidades legais (Comarca, Vara, Tipo) ───────────────────────────────────

@login_required
def lista_comarcas(request):
    comarcas = Comarca.objects.all()
    return render(request, 'processos/lista_comarcas.html', {'comarcas': comarcas})


@login_required
def nova_comarca(request):
    form = ComarcaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Comarca cadastrada.')
        return redirect('lista_comarcas')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Nova Comarca', 'voltar': 'lista_comarcas'})


@login_required
def lista_varas(request):
    varas = Vara.objects.select_related('comarca').all()
    return render(request, 'processos/lista_varas.html', {'varas': varas})


@login_required
def nova_vara(request):
    form = VaraForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vara cadastrada.')
        return redirect('lista_varas')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Nova Vara', 'voltar': 'lista_varas'})


@login_required
def lista_tipos(request):
    tipos = TipoProcesso.objects.all()
    return render(request, 'processos/lista_tipos.html', {'tipos': tipos})


@login_required
def novo_tipo(request):
    form = TipoProcessoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de processo cadastrado.')
        return redirect('lista_tipos')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Novo Tipo de Processo', 'voltar': 'lista_tipos'})
