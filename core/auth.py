"""Autenticação — hash de palavras-passe com PBKDF2 (biblioteca padrão, sem dependências)."""
import binascii
import hashlib
import hmac
import os

_ITERACOES = 200_000


def criar_hash(password: str) -> tuple[str, str]:
    """Devolve (hash_hex, salt_hex) para guardar na base de dados."""
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACOES)
    return binascii.hexlify(h).decode(), binascii.hexlify(salt).decode()


def verificar(password: str, hash_hex: str, salt_hex: str) -> bool:
    """True se a palavra-passe corresponde ao hash guardado (comparação segura)."""
    if not hash_hex or not salt_hex:
        return False
    salt = binascii.unhexlify(salt_hex)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERACOES)
    return hmac.compare_digest(binascii.hexlify(h).decode(), hash_hex)
