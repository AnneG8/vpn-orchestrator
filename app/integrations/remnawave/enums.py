import enum


class RWUserStatus(str, enum.Enum):
    ACTIVE = 'ACTIVE'
    DISABLED = 'DISABLED'
