import enum


class ClientStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'
    BLOCKED = 'BLOCKED'


class OperationAction(str, enum.Enum):
    CREATE_CLIENT = 'create_client'
    EXTEND_SUBSCRIPTION = 'extend_subscription'
    BLOCK = 'block'
    UNBLOCK = 'unblock'
    ROTATE_CONFIG = 'rotate_config'
    GET_CONFIG = 'get_config'
    AUTO_DEACTIVATE = 'auto_deactivate'


class OperationResult(str, enum.Enum):
    SUCCESS = 'success'
    FAIL = 'fail'
