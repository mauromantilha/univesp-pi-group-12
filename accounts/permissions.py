from rest_framework.permissions import BasePermission, SAFE_METHODS


def usuario_pode_escrever(usuario):
    return bool(
        usuario
        and usuario.is_authenticated
        and (usuario.is_administrador() or usuario.is_advogado())
    )


class IsAdvogadoOuAdministradorWrite(BasePermission):
    message = 'Apenas advogados e administradores podem alterar dados.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return usuario_pode_escrever(request.user)
