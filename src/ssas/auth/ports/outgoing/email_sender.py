from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    async def send(self, recipient: str, subject: str, text: str, html: str) -> None:
        raise NotImplementedError
