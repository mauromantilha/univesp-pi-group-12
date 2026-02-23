from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Documento
from .forms import DocumentoForm


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
    form = DocumentoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.adicionado_por = request.user
        doc.save()
        messages.success(request, 'Documento adicionado ao repositório.')
        return redirect('lista_documentos')
    return render(request, 'jurisprudencia/form_documento.html', {'form': form, 'titulo': 'Novo Documento'})


@login_required
def editar_documento(request, pk):
    doc = get_object_or_404(Documento, pk=pk)
    form = DocumentoForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Documento atualizado.')
        return redirect('detalhe_documento', pk=pk)
    return render(request, 'jurisprudencia/form_documento.html', {'form': form, 'titulo': 'Editar Documento', 'objeto': doc})
