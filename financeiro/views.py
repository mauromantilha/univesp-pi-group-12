from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from accounts.permissions import usuario_pode_escrever
from .models import Lancamento, LancamentoArquivo
from .forms import LancamentoForm, LancamentoArquivoUploadForm
from processos.models import Processo


def _lancamentos_usuario(usuario):
    if usuario.is_administrador():
        return Lancamento.objects.select_related('cliente', 'processo', 'criado_por')
    return Lancamento.objects.select_related('cliente', 'processo', 'criado_por').filter(
        Q(criado_por=usuario) | Q(processo__advogado=usuario)
    ).distinct()


def _somente_escrita_permitida(request):
    if usuario_pode_escrever(request.user):
        return None
    messages.error(request, 'Somente advogados e administradores podem alterar dados.')
    return redirect('lista_lancamentos')


def _salvar_arquivos_lancamento(lancamento, arquivos, usuario):
    for arquivo in arquivos:
        LancamentoArquivo.objects.create(
            lancamento=lancamento,
            arquivo=arquivo,
            nome_original=arquivo.name,
            enviado_por=usuario,
        )


@login_required
def lista_lancamentos(request):
    qs = _lancamentos_usuario(request.user)

    q = request.GET.get('q', '')
    status_filtro = request.GET.get('status', '')
    tipo_filtro = request.GET.get('tipo', '')

    if q:
        qs = qs.filter(
            Q(descricao__icontains=q) |
            Q(cliente__nome__icontains=q)
        )
    if status_filtro:
        qs = qs.filter(status=status_filtro)
    if tipo_filtro:
        qs = qs.filter(tipo=tipo_filtro)

    # Totalizadores
    totais = qs.aggregate(
        total_pendente=Sum('valor', filter=Q(status='pendente')),
        total_pago=Sum('valor', filter=Q(status='pago')),
        total_atrasado=Sum('valor', filter=Q(status='atrasado')),
    )

    # Marcar atrasados automaticamente
    hoje = timezone.now().date()
    ids_atrasados = list(qs.filter(status='pendente', data_vencimento__lt=hoje).values_list('id', flat=True))
    if ids_atrasados:
        Lancamento.objects.filter(id__in=ids_atrasados).update(status='atrasado')
        qs = _lancamentos_usuario(request.user)

    return render(request, 'financeiro/lista_lancamentos.html', {
        'lancamentos': qs,
        'q': q,
        'status_filtro': status_filtro,
        'tipo_filtro': tipo_filtro,
        'status_choices': Lancamento.STATUS_CHOICES,
        'tipo_choices': Lancamento.TIPO_CHOICES,
        'totais': totais,
    })


@login_required
def novo_lancamento(request):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    form = LancamentoForm(request.POST or None, request.FILES or None)
    if not request.user.is_administrador():
        processos_usuario = Processo.objects.filter(advogado=request.user).select_related('cliente')
        form.fields['processo'].queryset = processos_usuario
        form.fields['cliente'].queryset = form.fields['cliente'].queryset.filter(processos__advogado=request.user).distinct()
    if request.method == 'POST' and form.is_valid():
        lancamento = form.save(commit=False)
        if (
            not request.user.is_administrador()
            and lancamento.processo
            and lancamento.processo.advogado_id != request.user.id
        ):
            messages.error(request, 'Processo inválido para o seu perfil.')
            return render(request, 'financeiro/form_lancamento.html', {'form': form, 'titulo': 'Novo Lançamento'})
        lancamento.criado_por = request.user
        lancamento.save()
        _salvar_arquivos_lancamento(
            lancamento=lancamento,
            arquivos=form.cleaned_data.get('arquivos', []),
            usuario=request.user,
        )
        return redirect('lista_lancamentos')
    return render(request, 'financeiro/form_lancamento.html', {'form': form, 'titulo': 'Novo Lançamento'})


@login_required
def editar_lancamento(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    lancamento = get_object_or_404(_lancamentos_usuario(request.user), pk=pk)
    form = LancamentoForm(request.POST or None, request.FILES or None, instance=lancamento)
    if not request.user.is_administrador():
        processos_usuario = Processo.objects.filter(advogado=request.user).select_related('cliente')
        form.fields['processo'].queryset = processos_usuario
        form.fields['cliente'].queryset = form.fields['cliente'].queryset.filter(processos__advogado=request.user).distinct()
    if request.method == 'POST' and form.is_valid():
        lancamento_editado = form.save(commit=False)
        if (
            not request.user.is_administrador()
            and lancamento_editado.processo
            and lancamento_editado.processo.advogado_id != request.user.id
        ):
            messages.error(request, 'Processo inválido para o seu perfil.')
            return render(request, 'financeiro/form_lancamento.html', {'form': form, 'titulo': 'Editar Lançamento', 'lancamento': lancamento})
        lancamento_editado.save()
        _salvar_arquivos_lancamento(
            lancamento=lancamento_editado,
            arquivos=form.cleaned_data.get('arquivos', []),
            usuario=request.user,
        )
        return redirect('detalhe_lancamento', pk=lancamento.pk)
    return render(request, 'financeiro/form_lancamento.html', {'form': form, 'titulo': 'Editar Lançamento', 'lancamento': lancamento})


@login_required
def detalhe_lancamento(request, pk):
    lancamento = get_object_or_404(_lancamentos_usuario(request.user), pk=pk)
    arquivos = lancamento.arquivos.select_related('enviado_por').all()
    form_arquivos = LancamentoArquivoUploadForm()
    return render(request, 'financeiro/detalhe_lancamento.html', {
        'lancamento': lancamento,
        'arquivos': arquivos,
        'form_arquivos': form_arquivos,
    })


@login_required
def api_cliente_do_processo(request, processo_pk):
    """Retorna JSON com o ID e nome do cliente de um processo (usado via JS no formulário)."""
    processos_qs = Processo.objects.select_related('cliente')
    if not request.user.is_administrador():
        processos_qs = processos_qs.filter(advogado=request.user)
    processo = get_object_or_404(processos_qs, pk=processo_pk)
    return JsonResponse({'cliente_id': processo.cliente.pk, 'cliente_nome': processo.cliente.nome})


@login_required
def upload_arquivos_lancamento(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio

    lancamento = get_object_or_404(_lancamentos_usuario(request.user), pk=pk)
    if request.method != 'POST':
        return redirect('detalhe_lancamento', pk=pk)

    form = LancamentoArquivoUploadForm(request.POST, request.FILES)
    if form.is_valid():
        arquivos = form.cleaned_data.get('arquivos', [])
        _salvar_arquivos_lancamento(
            lancamento=lancamento,
            arquivos=arquivos,
            usuario=request.user,
        )
        messages.success(request, f'{len(arquivos)} arquivo(s) enviado(s) com sucesso.')
    else:
        messages.error(request, 'Selecione ao menos um arquivo válido para upload.')

    return redirect('detalhe_lancamento', pk=pk)
