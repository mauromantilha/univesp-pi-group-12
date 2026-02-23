from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Compromisso
from .forms import CompromissoForm


@login_required
def calendario(request):
    usuario = request.user
    hoje = timezone.now().date()
    if usuario.is_administrador():
        compromissos = Compromisso.objects.select_related('advogado', 'processo').all()
    else:
        compromissos = Compromisso.objects.filter(advogado=usuario).select_related('processo')

    # Group by date for simple display
    prazos = compromissos.filter(tipo='prazo', status='pendente').order_by('data')
    proximos = compromissos.filter(data__gte=hoje, status='pendente').order_by('data', 'hora')[:20]
    atrasados = compromissos.filter(data__lt=hoje, status='pendente').order_by('data')

    return render(request, 'agenda/calendario.html', {
        'proximos': proximos,
        'prazos': prazos,
        'atrasados': atrasados,
        'hoje': hoje,
    })


@login_required
def novo_compromisso(request):
    form = CompromissoForm(request.POST or None)
    if not request.user.is_administrador():
        form.fields['advogado'].initial = request.user
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Compromisso cadastrado com sucesso.')
        return redirect('calendario')
    return render(request, 'agenda/form_compromisso.html', {'form': form, 'titulo': 'Novo Compromisso'})


@login_required
def editar_compromisso(request, pk):
    compromisso = get_object_or_404(Compromisso, pk=pk)
    form = CompromissoForm(request.POST or None, instance=compromisso)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Compromisso atualizado.')
        return redirect('calendario')
    return render(request, 'agenda/form_compromisso.html', {'form': form, 'titulo': 'Editar Compromisso', 'objeto': compromisso})


@login_required
def excluir_compromisso(request, pk):
    compromisso = get_object_or_404(Compromisso, pk=pk)
    if request.method == 'POST':
        compromisso.delete()
        messages.success(request, 'Compromisso removido.')
    return redirect('calendario')


@login_required
def alertas(request):
    """Exibe prazos próximos nos próximos 7 dias."""
    usuario = request.user
    hoje = timezone.now().date()
    from datetime import timedelta
    limite = hoje + timedelta(days=7)
    if usuario.is_administrador():
        prazos = Compromisso.objects.filter(tipo='prazo', data__range=[hoje, limite], status='pendente').order_by('data')
    else:
        prazos = Compromisso.objects.filter(advogado=usuario, tipo='prazo', data__range=[hoje, limite], status='pendente').order_by('data')
    return render(request, 'agenda/alertas.html', {'prazos': prazos, 'hoje': hoje})
