from datetime import datetime
from models.users import acciones
from config.db import conn

def registro(accion: str, userId: int):
    fecha = datetime.now()
    result = conn.execute(acciones.insert().values(
        hizo = accion,
        quien = userId,
        fechaHora = fecha
    ))

    print("Execution has taken place")