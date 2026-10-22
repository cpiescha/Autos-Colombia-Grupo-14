import enum


class VehicleType(str, enum.Enum):
    MOTO = "MOTO"
    CARRO = "CARRO"
    CAMIONETA = "CAMIONETA"


class SpotCategory(str, enum.Enum):
    MOTO = "MOTO"
    AUTOMOVIL = "AUTOMOVIL"
