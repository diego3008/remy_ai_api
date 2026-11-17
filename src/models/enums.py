import enum

from sqlalchemy import Enum as SAEnum


def _enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Store the enum's values (not member names) in a named DB enum type."""
    return SAEnum(
        enum_cls, name=name, values_callable=lambda e: [m.value for m in e]
    )


class Channel(str, enum.Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    PHONE = "phone"


class Fulfillment(str, enum.Enum):
    DELIVERY = "delivery"
    PICKUP = "pickup"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
