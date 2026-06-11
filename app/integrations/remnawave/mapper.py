from app.db.models.enums import ClientStatus
from app.domain.remnawave import RWUser

from .schemas import RWClientResponse, RWUserStatus


class RWMapper:
    @staticmethod
    def to_domain(response: RWClientResponse) -> RWUser:
        return RWUser(
            uuid=response.uuid,
            username=response.username,
            status=RWMapper._map_status(response.status),
            created_at=response.created_at,
            expires_at=response.expire_at,
            updated_at=response.updated_at,
            sub_url=response.sub_url,
        )

    @staticmethod
    def _map_status(status: RWUserStatus) -> ClientStatus:
        match status:
            case RWUserStatus.ACTIVE:
                return ClientStatus.ACTIVE

            case RWUserStatus.DISABLED:
                return ClientStatus.DISABLED
