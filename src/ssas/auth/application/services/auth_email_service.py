from urllib.parse import urlencode

from ssas.auth.ports.outgoing.email_sender import EmailSender


class AuthEmailService:
    def __init__(self, sender: EmailSender, frontend_url: str):
        self.sender = sender
        self.frontend_url = frontend_url.rstrip("/")

    async def send_password_reset(self, email: str, token: str) -> None:
        url = f"{self.frontend_url}/restablecer-contrasena?{urlencode({'token': token})}"
        await self.sender.send(
            email,
            "Restablece tu contraseña",
            f"Usa este enlace para restablecer tu contraseña: {url}",
            f'<p>Usa el siguiente enlace para restablecer tu contraseña:</p><p><a href="{url}">Restablecer contraseña</a></p>',
        )

    async def send_email_verification(self, email: str, token: str) -> None:
        url = f"{self.frontend_url}/verificar-correo?{urlencode({'token': token})}"
        await self.sender.send(
            email,
            "Verifica tu correo electrónico",
            f"Usa este enlace para verificar tu correo: {url}",
            f'<p>Confirma tu dirección de correo:</p><p><a href="{url}">Verificar correo</a></p>',
        )
