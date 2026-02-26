try:
    from .celery import app as celery_app
except Exception:  # pragma: no cover - fallback quando Celery não está instalado
    celery_app = None

__all__ = ('celery_app',)
