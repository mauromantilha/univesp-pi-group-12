from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


def _jwt_cookie_secure():
    return bool(getattr(settings, 'JWT_COOKIE_SECURE', not settings.DEBUG))


def _jwt_cookie_samesite():
    return getattr(settings, 'JWT_COOKIE_SAMESITE', 'Lax')


def _access_cookie_name():
    return getattr(settings, 'JWT_ACCESS_COOKIE_NAME', 'access_token')


def _refresh_cookie_name():
    return getattr(settings, 'JWT_REFRESH_COOKIE_NAME', 'refresh_token')


def set_jwt_cookies(response, access_token, refresh_token=None):
    access_ttl = getattr(settings, 'SIMPLE_JWT', {}).get('ACCESS_TOKEN_LIFETIME', timedelta(minutes=45))
    refresh_ttl = getattr(settings, 'SIMPLE_JWT', {}).get('REFRESH_TOKEN_LIFETIME', timedelta(days=7))

    response.set_cookie(
        _access_cookie_name(),
        str(access_token),
        max_age=int(access_ttl.total_seconds()),
        httponly=True,
        secure=_jwt_cookie_secure(),
        samesite=_jwt_cookie_samesite(),
        path='/',
    )

    if refresh_token:
        response.set_cookie(
            _refresh_cookie_name(),
            str(refresh_token),
            max_age=int(refresh_ttl.total_seconds()),
            httponly=True,
            secure=_jwt_cookie_secure(),
            samesite=_jwt_cookie_samesite(),
            path='/',
        )

    return response


def clear_jwt_cookies(response):
    response.delete_cookie(
        _access_cookie_name(),
        path='/',
        samesite=_jwt_cookie_samesite(),
    )
    response.delete_cookie(
        _refresh_cookie_name(),
        path='/',
        samesite=_jwt_cookie_samesite(),
    )
    return response


class CookieJWTAuthentication(JWTAuthentication):
    """
    Prioriza o header Authorization (Bearer) e, na ausência dele,
    utiliza o token JWT armazenado em cookie httpOnly.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
        else:
            raw_token = request.COOKIES.get(_access_cookie_name())
            if not raw_token:
                return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
