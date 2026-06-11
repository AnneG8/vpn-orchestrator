import uuid


class ClientNotFoundError(Exception):
    def __init__(self, client_id: uuid.UUID) -> None:
        super().__init__(f'Client {client_id} not found')
        self.client_id = client_id
