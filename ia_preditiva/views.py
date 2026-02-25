from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from accounts.permissions import usuario_pode_escrever
from processos.models import Processo
from jurisprudencia.models import Documento
from .models import AnaliseRisco


def _calcular_probabilidade(processo):
    """
    Cálculo simples de risco baseado no histórico do banco.
    Retorna (probabilidade_exito, similares_total, similares_vitorias, justificativa)
    """
    similares = Processo.objects.filter(
        tipo=processo.tipo,
        vara=processo.vara,
        status='finalizado',
    ).exclude(pk=processo.pk)

    total = similares.count()
    if total == 0:
        return None, 0, 0, 'Não há processos similares finalizados nesta vara para calcular a probabilidade.'

    # Considera "vitória" processos cujas movimentações mencionem "procedente" ou "ganho"
    vitorias = similares.filter(
        movimentacoes__descricao__icontains='procedente'
    ).distinct().count()

    prob = round((vitorias / total) * 100, 1)
    justificativa = (
        f'Análise baseada em {total} processo(s) similar(es) finalizado(s) '
        f'no mesmo tipo e vara. '
        f'{vitorias} resultaram favoravelmente.'
    )
    return prob, total, vitorias, justificativa


@login_required
def analise_risco(request, processo_pk):
    if not usuario_pode_escrever(request.user):
        messages.error(request, 'Somente advogados e administradores podem executar análise de risco.')
        return redirect('dashboard')

    processos_qs = Processo.objects.all()
    if not request.user.is_administrador():
        processos_qs = processos_qs.filter(advogado=request.user)
    processo = get_object_or_404(processos_qs, pk=processo_pk)

    analise, _ = AnaliseRisco.objects.get_or_create(processo=processo)

    if request.method == 'POST' or analise.atualizado_em is None:
        prob, total, vitorias, justificativa = _calcular_probabilidade(processo)
        analise.probabilidade_exito = prob
        analise.processos_similares = total
        analise.vitorias_similares = vitorias
        analise.justificativa = justificativa
        analise.save()

    # Sugestões de jurisprudência
    sugestoes = []
    if processo.tipo:
        sugestoes = Documento.objects.filter(
            Q(conteudo__icontains=processo.tipo.nome) |
            Q(tags__icontains=processo.tipo.nome)
        )[:5]

    return render(request, 'ia_preditiva/analise_risco.html', {
        'processo': processo,
        'analise': analise,
        'sugestoes': sugestoes,
    })


@login_required
def sugestoes_jurisprudencia(request):
    """Sugere documentos com base em busca livre."""
    q = request.GET.get('q', '')
    sugestoes = []
    if q:
        sugestoes = Documento.objects.filter(
            Q(titulo__icontains=q) |
            Q(conteudo__icontains=q) |
            Q(tags__icontains=q)
        )[:10]
    return render(request, 'ia_preditiva/sugestoes.html', {'sugestoes': sugestoes, 'q': q})
