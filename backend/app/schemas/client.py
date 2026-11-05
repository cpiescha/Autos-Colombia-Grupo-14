from pydantic import BaseModel


class ClientResponse(BaseModel):
    id: int
    nombre: str
