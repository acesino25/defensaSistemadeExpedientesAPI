from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: Optional[str]
    name: str
    email: str
    password: str
    passwordConfirm: Optional[str]
    pregunta: Optional[str]
    puntos: str
    permiso: str

class Perfil(BaseModel):
    id: Optional[str]
    name: Optional[str]
    mail: Optional[str]
    puntos: Optional[str]
    permiso: Optional[str]

class Login(BaseModel):
    mail: str
    password: str