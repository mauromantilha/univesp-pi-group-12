import logging
import os

from consulta_tribunais.services.groq_service import GroqService

logger = logging.getLogger(__name__)


class _SyncResult:
    def __init__(self, value):
        self.value = value

    def get(self, timeout=None):
        return self.value


try:
    from celery import shared_task
except Exception:  # pragma: no cover - fallback quando Celery não está instalado
    def shared_task(*task_args, **task_kwargs):  # type: ignore
        def _decorate(func):
            func.delay = lambda *args, **kwargs: _SyncResult(func(*args, **kwargs))
            func.apply_async = lambda args=None, kwargs=None, **opts: _SyncResult(
                func(*(args or ()), **(kwargs or {}))
            )
            func.run = func
            return func

        if task_args and callable(task_args[0]) and len(task_args) == 1 and not task_kwargs:
            return _decorate(task_args[0])
        return _decorate


def _chamar_groq(messages, temperature=0.2, max_tokens=1200):
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return ''

    groq = GroqService(groq_api_key)
    completion = groq.client.chat.completions.create(
        messages=messages,
        model=groq.model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return completion.choices[0].message.content or ''


@shared_task(name='ia_preditiva.gerar_resposta_ia')
def gerar_resposta_ia(messages, temperature=0.2, max_tokens=1200):
    try:
        return _chamar_groq(messages=messages, temperature=temperature, max_tokens=max_tokens)
    except Exception as exc:
        logger.warning('Falha na task gerar_resposta_ia: %s', exc)
        return ''
