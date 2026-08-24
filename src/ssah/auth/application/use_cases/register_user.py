from uuid import uuid4

from ssah.auth.domain.entities.user import User
from ssah.auth.domain.exceptions import UserAlreadyExistsError


class RegisterUser:
    def __init__(self, user_repository, password_hasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    async def execute(self, name: str, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if await self.user_repository.get_by_email(normalized_email):
            raise UserAlreadyExistsError("El usuario ya existe")

        hashed_password = self.password_hasher.hash(password)
        user = User(
            id=str(uuid4()),
            name=name.strip(),
            email=normalized_email,
            hashed_password=hashed_password,
        )
        return await self.user_repository.create(user)
