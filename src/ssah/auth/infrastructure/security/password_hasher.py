from ssah.core.security.hashing import Argon2PasswordHasher

BcryptPasswordHasher = Argon2PasswordHasher

__all__ = ["Argon2PasswordHasher", "BcryptPasswordHasher"]