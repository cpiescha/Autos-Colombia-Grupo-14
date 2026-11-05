import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AccountRole

_USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9._]{2,59}$")
AccountState = Literal["ACTIVA", "ANULADA"]


class OperatorCreateRequest(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    usuario: str = Field(min_length=3, max_length=60)
    clave: str = Field(min_length=8, max_length=72)

    @field_validator("nombre")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("name must contain at least 3 non-whitespace characters")
        return normalized

    @field_validator("usuario")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        username = value.strip().lower()
        if not _USERNAME_PATTERN.fullmatch(username):
            raise ValueError("invalid username format")
        return username

    @field_validator("clave")
    @classmethod
    def validate_password_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password exceeds bcrypt limit")
        return value


class OperatorStateRequest(BaseModel):
    estado: AccountState


class OperatorAccountResponse(BaseModel):
    id: int
    operador_id: int
    nombre: str
    usuario: str
    rol: AccountRole
    estado: AccountState
    creado_en: datetime
    actualizado_en: datetime
