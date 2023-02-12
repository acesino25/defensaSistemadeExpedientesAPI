from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class Datos(BaseModel):
    idEspecial: Optional[str]
    nombres: str
    apellido: str
    direccion: str
    localidad: str
    telefono: str
    dni: str
    fechaAudiencia: datetime
    detalles: Optional[str]
    empresas: str
    hipervulnerable: bool
    actuacion: bool
    creador: str

    # 'fechaAudiencia: datetime'

    # si lo declaramos de esta forma, a la hora de asignar el valor
    # deberemos hacerlo de la siguiente manera:
    # fechaAudiencia= datetime.strptime('2022-01-01', '%Y-%m-%d')

    # la alternativa es declararlo de esta manera:
    # fechaAudiencia: datetime.date
    # fechaAudiencia=datetime.date(2022, 1, 1)

class Estado(BaseModel):
    id: Optional[str]
    idEspecial: str
    estado: str
    descripcion: str

class Temporizador(BaseModel):
    id: Optional[str]
    idEspecial: Optional[str]
    titulo: str
    fechaInicio: datetime
    fechaFin: datetime

class File(BaseModel):
    id: Optional[str]
    idEspecial: str
    datos: Datos
    estados: Optional[List[Estado]]
    temporizador: Temporizador
    archivado: Optional[bool]



