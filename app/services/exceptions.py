import uuid

from app.db.models.enums import ClientStatus


class ClientNotFoundError(Exception):
    def __init__(self, client_id: uuid.UUID) -> None:
        super().__init__(f'Client {client_id} not found')
        self.client_id = client_id


class UnsupportedClientStatusError(Exception):
    def __init__(self, status: ClientStatus) -> None:
        super().__init__(f'Unsupported client status: {status}')
        self.status = status
