from django.db.models import Q


def usuario_eh_junior(usuario):
    return bool(
        usuario
        and getattr(usuario, 'is_authenticated', False)
        and getattr(usuario, 'papel', None) in {'estagiario', 'assistente'}
    )


def supervisor_do_usuario(usuario):
    return getattr(usuario, 'responsavel_advogado', None)


def processos_visiveis_queryset(queryset, usuario):
    if not usuario or not usuario.is_authenticated:
        return queryset.none()
    if usuario.is_administrador():
        return queryset

    if usuario_eh_junior(usuario):
        supervisor_id = getattr(usuario, 'responsavel_advogado_id', None)
        if not supervisor_id:
            return queryset.none()
        return queryset.filter(
            Q(responsaveis__usuario=usuario, responsaveis__ativo=True),
            Q(advogado_id=supervisor_id) | Q(responsaveis__usuario_id=supervisor_id, responsaveis__ativo=True),
        ).distinct()

    return queryset.filter(
        Q(advogado=usuario)
        | Q(responsaveis__usuario=usuario, responsaveis__ativo=True)
    ).distinct()


def usuario_pode_entrar_processo(processo, usuario):
    if not usuario or not usuario.is_authenticated:
        return False
    if usuario.is_administrador():
        return True
    if processo.advogado_id == usuario.id:
        return True

    usuario_vinculado = processo.responsaveis.filter(usuario=usuario, ativo=True).exists()
    if not usuario_vinculado:
        return False

    if not usuario_eh_junior(usuario):
        return True

    supervisor_id = getattr(usuario, 'responsavel_advogado_id', None)
    if not supervisor_id:
        return False
    return (
        processo.advogado_id == supervisor_id
        or processo.responsaveis.filter(usuario_id=supervisor_id, ativo=True).exists()
    )


def validar_vinculo_junior_no_processo(processo, usuario_alvo):
    if not usuario_eh_junior(usuario_alvo):
        return None
    supervisor_id = getattr(usuario_alvo, 'responsavel_advogado_id', None)
    if not supervisor_id:
        return 'Estagiário/assistente deve ter advogado responsável definido.'
    supervisor_participa = (
        processo.advogado_id == supervisor_id
        or processo.responsaveis.filter(usuario_id=supervisor_id, ativo=True).exists()
    )
    if not supervisor_participa:
        return 'Estagiário/assistente só pode acessar processos vinculados ao seu advogado responsável.'
    return None
