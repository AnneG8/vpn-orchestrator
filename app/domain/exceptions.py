import uuid


class DomainError(Exception):
    pass


class ClientArchivedError(DomainError):
    def __init__(self, client_id: uuid.UUID) -> None:
        super().__init__(f'Client {client_id} is archived')
        self.client_id = client_id


class InvalidSubscriptionDurationError(DomainError):
    def __init__(self, days: int) -> None:
        super().__init__(f'Invalid subscription duration: {days}')
        self.days = days
