from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import AccountRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: AccountRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: CurrentUserResponse
