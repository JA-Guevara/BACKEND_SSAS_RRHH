from pwdlib import PasswordHash

from ssas.auth.ports.outgoing.password_hasher import PasswordHasher

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return _password_hash.verify(password, hashed_password)
    except (ValueError, TypeError):
        return False


class Argon2PasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return hash_password(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        return verify_password(password, hashed_password)
