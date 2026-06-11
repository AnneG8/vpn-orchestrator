from app.db.models import Client
from app.domain.client import ClientEntity


class ClientMapper:
    @staticmethod
    def to_domain(model: Client) -> ClientEntity:
        return ClientEntity(
            id=model.id,
            remnawave_uuid=model.remnawave_uuid,
            status=model.status,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def update_model(model: Client, entity: ClientEntity) -> None:
        model.status = entity.status
        model.expires_at = entity.expires_at
