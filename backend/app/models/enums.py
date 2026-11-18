import enum


class VehicleType(str, enum.Enum):
    MOTO = "MOTO"
    CARRO = "CARRO"
    CAMIONETA = "CAMIONETA"


class SpotCategory(str, enum.Enum):
    MOTO = "MOTO"
    AUTOMOVIL = "AUTOMOVIL"


class AccountRole(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERADOR = "OPERADOR"


class ClientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class PaymentMethod(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    QR = "QR"


class PaymentStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    ANNULLED = "ANNULLED"
