from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.permissions import usuario_pode_escrever
from .models import Cliente, Processo, ProcessoArquivo, ClienteArquivo, Movimentacao, Comarca, Vara, TipoProcesso
from .forms import (
    ClienteForm, ProcessoForm, ProcessoArquivoUploadForm, MovimentacaoForm,
    ComarcaForm, VaraForm, TipoProcessoForm
)


def _pode_acessar_processo(usuario, processo):
    return usuario.is_administrador() or processo.advogado_id == usuario.id


def _pode_acessar_cliente(usuario, cliente):
    if usuario.is_administrador():
        return True
    return cliente.processos.filter(advogado=usuario).exists() or cliente.responsavel_id == usuario.id


def _somente_administrador(request):
    if request.user.is_administrador():
        return None
    messages.error(request, 'Acesso restrito a administradores.')
    return redirect('dashboard')


def _somente_escrita_permitida(request):
    if usuario_pode_escrever(request.user):
        return None
    messages.error(request, 'Somente advogados e administradores podem alterar dados.')
    return redirect('dashboard')


def _salvar_arquivos_processo(processo, arquivos, usuario):
    for arquivo in arquivos:
        ProcessoArquivo.objects.create(
            processo=processo,
            arquivo=arquivo,
            nome_original=arquivo.name,
            enviado_por=usuario,
        )


def _salvar_arquivos_cliente(cliente, arquivos, usuario):
    for arquivo in arquivos:
        ClienteArquivo.objects.create(
            cliente=cliente,
            arquivo=arquivo,
            nome_original=arquivo.name,
            enviado_por=usuario,
        )


def _aplicar_escopo_form_cliente(form, usuario):
    if usuario.is_administrador():
        return
    form.fields.pop('responsavel', None)


# ─── Clientes ────────────────────────────────────────────────────────────────

@login_required
def lista_clientes(request):
    q = request.GET.get('q', '')
    if request.user.is_administrador():
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(
            Q(processos__advogado=request.user) | Q(responsavel=request.user)
        ).distinct()
    if q:
        clientes = clientes.filter(nome__icontains=q)
    return render(request, 'processos/lista_clientes.html', {'clientes': clientes, 'q': q})


@login_required
def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if not _pode_acessar_cliente(request.user, cliente):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_clientes')
    arquivos_cliente = cliente.arquivos.select_related('enviado_por').all()
    return render(request, 'processos/detalhe_cliente.html', {'cliente': cliente, 'arquivos_cliente': arquivos_cliente})


@login_required
def novo_cliente(request):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    form = ClienteForm(request.POST or None, request.FILES or None)
    _aplicar_escopo_form_cliente(form, request.user)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save(commit=False)
        if not request.user.is_administrador():
            cliente.responsavel = request.user
        cliente.save()
        form.save_m2m()
        _salvar_arquivos_cliente(
            cliente=cliente,
            arquivos=form.cleaned_data.get('documentos', []),
            usuario=request.user,
        )
        messages.success(request, 'Cliente cadastrado com sucesso.')
        return redirect('detalhe_cliente', pk=cliente.pk)
    return render(request, 'processos/form_cliente.html', {'form': form, 'titulo': 'Novo Cliente'})


@login_required
def editar_cliente(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    cliente = get_object_or_404(Cliente, pk=pk)
    if not _pode_acessar_cliente(request.user, cliente):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_clientes')
    form = ClienteForm(request.POST or None, request.FILES or None, instance=cliente)
    _aplicar_escopo_form_cliente(form, request.user)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save(commit=False)
        if not request.user.is_administrador() and not cliente.responsavel_id:
            cliente.responsavel = request.user
        cliente.save()
        form.save_m2m()
        _salvar_arquivos_cliente(
            cliente=cliente,
            arquivos=form.cleaned_data.get('documentos', []),
            usuario=request.user,
        )
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
    if not _pode_acessar_processo(request.user, processo):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_processos')
    movimentacoes = processo.movimentacoes.all()
    form_mov = MovimentacaoForm()
    form_arquivos = ProcessoArquivoUploadForm()
    arquivos_processo = processo.arquivos.select_related('enviado_por').all()
    return render(request, 'processos/detalhe_processo.html', {
        'processo': processo,
        'movimentacoes': movimentacoes,
        'arquivos_processo': arquivos_processo,
        'form_mov': form_mov,
        'form_arquivos': form_arquivos,
    })


@login_required
def novo_processo(request):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    form = ProcessoForm(request.POST or None, request.FILES or None)
    if not request.user.is_administrador():
        form.fields['cliente'].queryset = Cliente.objects.filter(
            Q(processos__advogado=request.user)
            | Q(processos__isnull=True, responsavel=request.user)
            | Q(responsavel=request.user)
        ).distinct()
        form.fields['advogado'].queryset = form.fields['advogado'].queryset.filter(pk=request.user.pk)
        form.fields['advogado'].initial = request.user
    if request.method == 'POST' and form.is_valid():
        processo = form.save(commit=False)
        if not request.user.is_administrador():
            processo.advogado = request.user
        processo.save()
        _salvar_arquivos_processo(
            processo=processo,
            arquivos=form.cleaned_data.get('arquivos', []),
            usuario=request.user,
        )
        messages.success(request, 'Processo cadastrado com sucesso.')
        return redirect('lista_processos')
    return render(request, 'processos/form_processo.html', {'form': form, 'titulo': 'Novo Processo'})


@login_required
def editar_processo(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    processo = get_object_or_404(Processo, pk=pk)
    if not _pode_acessar_processo(request.user, processo):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_processos')
    form = ProcessoForm(request.POST or None, request.FILES or None, instance=processo)
    if not request.user.is_administrador():
        form.fields['cliente'].queryset = Cliente.objects.filter(
            Q(processos__advogado=request.user)
            | Q(processos__isnull=True, responsavel=request.user)
            | Q(responsavel=request.user)
        ).distinct()
        form.fields['advogado'].queryset = form.fields['advogado'].queryset.filter(pk=request.user.pk)
        form.fields['advogado'].initial = request.user
    if request.method == 'POST' and form.is_valid():
        processo = form.save(commit=False)
        if not request.user.is_administrador():
            processo.advogado = request.user
        processo.save()
        _salvar_arquivos_processo(
            processo=processo,
            arquivos=form.cleaned_data.get('arquivos', []),
            usuario=request.user,
        )
        messages.success(request, 'Processo atualizado com sucesso.')
        return redirect('detalhe_processo', pk=pk)
    return render(request, 'processos/form_processo.html', {'form': form, 'titulo': 'Editar Processo', 'objeto': processo})


@login_required
def nova_movimentacao(request, processo_pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    processo = get_object_or_404(Processo, pk=processo_pk)
    if not _pode_acessar_processo(request.user, processo):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_processos')
    form = MovimentacaoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        mov = form.save(commit=False)
        mov.processo = processo
        mov.autor = request.user
        mov.save()
        messages.success(request, 'Movimentação registrada.')
        return redirect('detalhe_processo', pk=processo_pk)
    return render(request, 'processos/form_movimentacao.html', {'form': form, 'processo': processo})


@login_required
def upload_arquivos_processo(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio

    processo = get_object_or_404(Processo, pk=pk)
    if not _pode_acessar_processo(request.user, processo):
        messages.error(request, 'Acesso negado.')
        return redirect('lista_processos')

    if request.method != 'POST':
        return redirect('detalhe_processo', pk=pk)

    form = ProcessoArquivoUploadForm(request.POST, request.FILES)
    if form.is_valid():
        arquivos = form.cleaned_data.get('arquivos', [])
        _salvar_arquivos_processo(processo=processo, arquivos=arquivos, usuario=request.user)
        messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s) com sucesso.')
    else:
        messages.error(request, 'Selecione ao menos um arquivo válido para upload.')
    return redirect('detalhe_processo', pk=pk)


# ─── Carga de trabalho ───────────────────────────────────────────────────────

@login_required
def carga_trabalho(request):
    from accounts.models import Usuario
    if request.user.is_administrador():
        advogados = Usuario.objects.filter(papel__in=['advogado', 'administrador'])
    else:
        advogados = Usuario.objects.filter(pk=request.user.pk)
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
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    comarcas = Comarca.objects.all()
    return render(request, 'processos/lista_comarcas.html', {'comarcas': comarcas})


@login_required
def nova_comarca(request):
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    form = ComarcaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Comarca cadastrada.')
        return redirect('lista_comarcas')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Nova Comarca', 'voltar': 'lista_comarcas'})


@login_required
def lista_varas(request):
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    varas = Vara.objects.select_related('comarca').all()
    return render(request, 'processos/lista_varas.html', {'varas': varas})


@login_required
def nova_vara(request):
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    form = VaraForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vara cadastrada.')
        return redirect('lista_varas')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Nova Vara', 'voltar': 'lista_varas'})


@login_required
def lista_tipos(request):
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    tipos = TipoProcesso.objects.all()
    return render(request, 'processos/lista_tipos.html', {'tipos': tipos})


@login_required
def novo_tipo(request):
    bloqueio = _somente_administrador(request)
    if bloqueio:
        return bloqueio
    form = TipoProcessoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de processo cadastrado.')
        return redirect('lista_tipos')
    return render(request, 'processos/form_generic.html', {'form': form, 'titulo': 'Novo Tipo de Processo', 'voltar': 'lista_tipos'})
