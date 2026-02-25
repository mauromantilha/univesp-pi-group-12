from .models import UsuarioAtividadeLog


def _ip_do_request(request):
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_atividade(
    *,
    acao,
    request=None,
    usuario=None,
    autor=None,
    detalhes='',
    dados_extra=None,
):
    if autor is None and request is not None and getattr(request, 'user', None) and request.user.is_authenticated:
        autor = request.user
    if usuario is None:
        usuario = autor

    UsuarioAtividadeLog.objects.create(
        usuario=usuario,
        autor=autor,
        acao=acao,
        detalhes=detalhes,
        rota=(request.path if request is not None else ''),
        ip_endereco=_ip_do_request(request),
        dados_extra=dados_extra,
    )
