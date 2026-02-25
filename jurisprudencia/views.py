from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.permissions import usuario_pode_escrever
from .models import Documento
from .forms import DocumentoForm


def _pode_editar_documento(usuario, documento):
    return usuario.is_administrador() or documento.adicionado_por_id == usuario.id


def _somente_escrita_permitida(request):
    if usuario_pode_escrever(request.user):
        return None
    messages.error(request, 'Somente advogados e administradores podem alterar dados.')
    return redirect('lista_documentos')


@login_required
def lista_documentos(request):
    q = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    docs = Documento.objects.select_related('adicionado_por', 'processo_referencia')
    if q:
        docs = docs.filter(
            Q(titulo__icontains=q) |
            Q(conteudo__icontains=q) |
            Q(tags__icontains=q) |
            Q(tribunal__icontains=q)
        )
    if categoria:
        docs = docs.filter(categoria=categoria)
    return render(request, 'jurisprudencia/lista_documentos.html', {
        'documentos': docs,
        'q': q,
        'categoria_filtro': categoria,
        'categorias': Documento.CATEGORIA_CHOICES,
    })


@login_required
def detalhe_documento(request, pk):
    doc = get_object_or_404(Documento, pk=pk)
    return render(request, 'jurisprudencia/detalhe_documento.html', {'doc': doc})


@login_required
def novo_documento(request):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    form = DocumentoForm(request.POST or None, request.FILES or None)
    if not request.user.is_administrador():
        form.fields['processo_referencia'].queryset = form.fields['processo_referencia'].queryset.filter(
            advogado=request.user
        )
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.adicionado_por = request.user
        doc.save()
        messages.success(request, 'Documento adicionado ao repositório.')
        return redirect('lista_documentos')
    return render(request, 'jurisprudencia/form_documento.html', {'form': form, 'titulo': 'Novo Documento'})


@login_required
def editar_documento(request, pk):
    bloqueio = _somente_escrita_permitida(request)
    if bloqueio:
        return bloqueio
    doc = get_object_or_404(Documento, pk=pk)
    if not _pode_editar_documento(request.user, doc):
        messages.error(request, 'Acesso negado.')
        return redirect('detalhe_documento', pk=pk)
    form = DocumentoForm(request.POST or None, request.FILES or None, instance=doc)
    if not request.user.is_administrador():
        form.fields['processo_referencia'].queryset = form.fields['processo_referencia'].queryset.filter(
            advogado=request.user
        )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Documento atualizado.')
        return redirect('detalhe_documento', pk=pk)
    return render(request, 'jurisprudencia/form_documento.html', {'form': form, 'titulo': 'Editar Documento', 'objeto': doc})
