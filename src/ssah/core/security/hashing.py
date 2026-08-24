from pwdlib import PasswordHash

from ssah.auth.ports.outgoing.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        try:
            return self._hasher.verify(password, hashed_password)
        except (ValueError, TypeError):
            return False