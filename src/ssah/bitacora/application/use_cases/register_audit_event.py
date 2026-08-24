class RegisterAuditEvent:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, action: str, description: str, user_id: str | None = None):
        event = {
            "action": action,
            "description": description,
            "user_id": user_id,
        }
        return self.repository.add(event)
