import base64
import hashlib
import hmac
import os
from typing import Optional

from django.conf import settings
from rest_framework import serializers

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - fallback sem dependência externa
    Fernet = None

    class InvalidToken(Exception):
        pass

DEFAULT_ALLOWED_UPLOAD_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.rtf',
    '.png', '.jpg', '.jpeg',
    '.csv', '.xls', '.xlsx',
}
DEFAULT_ALLOWED_UPLOAD_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf',
    'text/rtf',
    'image/png',
    'image/jpeg',
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def get_allowed_upload_extensions():
    raw = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', None)
    if raw:
        return {str(ext).lower() if str(ext).startswith('.') else f".{str(ext).lower()}" for ext in raw}
    return DEFAULT_ALLOWED_UPLOAD_EXTENSIONS


def get_max_upload_bytes():
    return int(getattr(settings, 'MAX_UPLOAD_FILE_BYTES', DEFAULT_MAX_UPLOAD_BYTES))


def get_allowed_upload_mime_types():
    raw = getattr(settings, 'ALLOWED_UPLOAD_MIME_TYPES', None)
    if raw:
        return {str(m).strip().lower() for m in raw if str(m).strip()}
    return DEFAULT_ALLOWED_UPLOAD_MIME_TYPES


def validate_upload_file(uploaded_file):
    if uploaded_file is None:
        raise serializers.ValidationError('Arquivo inválido.')

    name = str(getattr(uploaded_file, 'name', '') or '')
    ext = os.path.splitext(name)[1].lower()
    allowed_ext = get_allowed_upload_extensions()
    if ext not in allowed_ext:
        raise serializers.ValidationError(
            f'Tipo de arquivo não permitido ({ext or "sem extensão"}). '
            f'Permitidos: {", ".join(sorted(allowed_ext))}.'
        )

    size = int(getattr(uploaded_file, 'size', 0) or 0)
    max_size = get_max_upload_bytes()
    if size > max_size:
        raise serializers.ValidationError(
            f'Arquivo excede o limite de {max_size // (1024 * 1024)}MB.'
        )

    content_type = str(getattr(uploaded_file, 'content_type', '') or '').split(';')[0].strip().lower()
    if content_type:
        allowed_mimes = get_allowed_upload_mime_types()
        if content_type not in allowed_mimes:
            raise serializers.ValidationError(
                f'Tipo MIME não permitido ({content_type}).'
            )

    return uploaded_file


def _pii_encryption_key():
    env_key = os.environ.get('PII_ENCRYPTION_KEY', '').strip()
    if env_key:
        key = env_key.encode()
        if len(key) == 44:
            return key

    secret = (settings.SECRET_KEY or 'fallback-secret').encode()
    digest = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet():
    if Fernet is None:
        return None
    return Fernet(_pii_encryption_key())


def _xor_stream_crypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(data):
        counter_bytes = counter.to_bytes(4, 'big')
        block = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
        output.extend(block)
        counter += 1
    return bytes(d ^ s for d, s in zip(data, output[:len(data)]))


def encrypt_pii(value: Optional[str]) -> Optional[str]:
    if value in (None, ''):
        return value
    text = str(value)
    if text.startswith('enc::'):
        return text
    cipher = _get_fernet()
    if cipher is not None:
        token = cipher.encrypt(text.encode('utf-8')).decode('utf-8')
        return f'enc::{token}'

    key = hashlib.sha256(_pii_encryption_key()).digest()
    nonce = os.urandom(16)
    encrypted = _xor_stream_crypt(text.encode('utf-8'), key, nonce)
    payload = base64.urlsafe_b64encode(nonce + encrypted).decode('utf-8')
    return f'enc::{payload}'


def decrypt_pii(value: Optional[str]) -> Optional[str]:
    if value in (None, ''):
        return value
    text = str(value)
    if not text.startswith('enc::'):
        return text
    raw = text.split('enc::', 1)[1]
    cipher = _get_fernet()
    if cipher is not None:
        try:
            return cipher.decrypt(raw.encode('utf-8')).decode('utf-8')
        except (InvalidToken, ValueError, TypeError):
            return value

    try:
        payload = base64.urlsafe_b64decode(raw.encode('utf-8'))
        nonce = payload[:16]
        encrypted = payload[16:]
        key = hashlib.sha256(_pii_encryption_key()).digest()
        plain = _xor_stream_crypt(encrypted, key, nonce)
        return plain.decode('utf-8')
    except Exception:
        return value
