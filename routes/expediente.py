from fastapi import APIRouter, Response, status
from schemas.file import File, Datos, Estado, Temporizador

from datetime import datetime, timedelta

from config.db import conn
from models.expediente import expedientes, estados, temporizador, fechas

from fastapi.responses import JSONResponse

from sqlalchemy import and_, or_

from utils.registro import registro # importamos una funcion que carga los movimientos de los usuarios

expediente = APIRouter()

# esta nos sirve para el panel de admin
@expediente.get("/fechasDisponibles/{desde},{hasta}")
def get_fechaNuevaAudiencia(desde: datetime, hasta: datetime):

    result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora >= desde, and_(fechas.c.fechaHora <= hasta)))).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5173"
    return response
#esta nos sirve para actualizar el estado de una fecha a no disponible o disponible
@expediente.get("/inhabilitarFecha/{idFecha}, {userId}")
def get_fechaNuevaAudiencia(idFecha: int, userId: int):
    result = conn.execute(fechas.select().where(fechas.c.id == idFecha))
    if(result.rowcount>0):
        disponible = not result.fetchone().disponible

    result2 = conn.execute(fechas.update().values(
        disponible = disponible
    ).where(fechas.c.id == idFecha))

    respuesta = JSONResponse(content=disponible)
    respuesta.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5173"
    print(result.fetchone())

    # REGISTRO #
    registro('Modificación de fecha: ' + str(idFecha) , userId)
    return respuesta

@expediente.get("/nuevaAudiencia")
def get_fechaNuevaAudiencia():
    def business_days_ahead(n):
        today = datetime.now().date()
        business_days = 0
        while business_days < n:
            today += timedelta(days=1)
            if today.weekday() < 5: # 0-4 are weekdays, 5 and 6 are weekends
                business_days += 1
        return today

    result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora > business_days_ahead(10), fechas.c.disponible == True)).limit(30)).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:5173"
    return response

@expediente.get("/cargarfechas")
def get_fechas():
    result = conn.execute(fechas.select())

    def loop_ten_years():
        current_year = datetime.now().year
        end_year = current_year + 10
        current_date = datetime(current_year, 1, 1, 5, 0)

        while current_date.year < end_year:
            if current_date.weekday() >= 5:  # 5 is the index of Saturday and 6 is the index of Sunday
                current_date += timedelta(days=1)
                continue

            end_of_day = current_date + timedelta(hours=12)
            while current_date < end_of_day:
                i = 0
                while i < 2:
                    conn.execute(fechas.insert().values(
                        fechaHora = current_date,
                        disponible = True
                    ))
                    i += 1
                current_date += timedelta(hours=1)
            current_date = current_date.replace(hour=5)
            current_date += timedelta(days=1)

    if(result.rowcount <= 0):
        loop_ten_years()
        result = conn.execute(fechas.select())
    
    return result.fetchall()
    



@expediente.get("/expedientes")
def get_expedientes():

    arrayRespuesta = []
    result = conn.execute(expedientes.select()).fetchall()



    for element in result:

        resultEstados = conn.execute(estados.select().where(estados.c.idEspecial == element["idEspecial"]))
        resultTemporizador = conn.execute(temporizador.select().where(temporizador.c.idEspecial == element["idEspecial"]))

        arrayEstados = []
        objTemporizador = {}

        if(resultEstados.rowcount > 0):
            for elementEstados in resultEstados:
                new_object_estado = {
                    "id":   elementEstados["id"],
                    "idEspecial":   elementEstados["idEspecial"],
                    "estado": elementEstados["estado"],
                    "descripcion": elementEstados["descripcion"]
                }
                arrayEstados.append(new_object_estado)


        if(resultTemporizador.rowcount > 0):
           objTemporizador["titulo"] = resultTemporizador["titulo"]
           objTemporizador["fechaInicio"] = resultTemporizador["fechaInicio"]
           objTemporizador["fechaFin"] = resultTemporizador["fechaFin"]

                

        expediente = {
            "id": element["id"],
            "idEspecial": element["idEspecial"],
            "datos": {
                "nombres": element["nombres"],
                "apellido": element["apellido"],
                "direccion": element["direccion"],
                "localidad": element["localidad"],
                "telefono": element["telefono"],
                "dni": element["dni"],
                "fechaAudiencia": element["fechaAudiencia"],
                "detalles": element["detalles"],
                "empresas": element["empresas"],
                "hipervulnerable": element["hipervulnerable"],
                "actuacion": element["actuacion"],
                "creador": element["creador"]
            },
            "estados": arrayEstados,
            "temporizador":
                objTemporizador
            ,
            "archivado": element["archivado"]
        }
        
        arrayRespuesta.append(expediente)
    

    return  arrayRespuesta


# OBTENER LOS ÚLTIMOS 10

@expediente.get("/expedientes/{limit}")
def get_expedientes_upto(limit: str = 10):

    arrayRespuesta = []
    result = conn.execute(expedientes.select().order_by(expedientes.c.id.desc()).limit(limit)).fetchall()



    for element in result:

        resultEstados = conn.execute(estados.select().where(estados.c.idEspecial == element["idEspecial"]))
        resultTemporizador = conn.execute(temporizador.select().where(temporizador.c.idEspecial == element["idEspecial"]))

        arrayEstados = []
        objTemporizador = {}

        if(resultEstados.rowcount > 0):
            for elementEstados in resultEstados:
                new_object_estado = {
                    "id":   elementEstados["id"],
                    "idEspecial":   elementEstados["idEspecial"],
                    "estado": elementEstados["estado"],
                    "descripcion": elementEstados["descripcion"]
                }
                arrayEstados.append(new_object_estado)


        if(resultTemporizador.rowcount > 0):
           objTemporizador["titulo"] = resultTemporizador["titulo"]
           objTemporizador["fechaInicio"] = resultTemporizador["fechaInicio"]
           objTemporizador["fechaFin"] = resultTemporizador["fechaFin"]

                

        expediente = {
            "id": element["id"],
            "idEspecial": element["idEspecial"],
            "datos": {
                "nombres": element["nombres"],
                "apellido": element["apellido"],
                "direccion": element["direccion"],
                "localidad": element["localidad"],
                "telefono": element["telefono"],
                "dni": element["dni"],
                "fechaAudiencia": element["fechaAudiencia"],
                "detalles": element["detalles"],
                "empresas": element["empresas"],
                "hipervulnerable": element["hipervulnerable"],
                "actuacion": element["actuacion"],
                "creador": element["creador"]
            },
            "estados": arrayEstados,
            "temporizador":
                objTemporizador
            ,
            "archivado": element["archivado"]
        }
        
        arrayRespuesta.append(expediente)
    

    return  arrayRespuesta

@expediente.get("/buscar/{DNIIdIdespecial}, {userId}")
def buscar_expediente(DNIIdIdespecial:str, userId: int):

    result = conn.execute(
        expedientes.select().where(or_(
            expedientes.c.idEspecial==DNIIdIdespecial,
            expedientes.c.id == DNIIdIdespecial,
            expedientes.c.dni == DNIIdIdespecial))).fetchall()

    if(not result):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)    # Le avisamos al usuario que lo que nos pasó no es correcto

    # REGISTRO #
    registro('Realizó una búsqueda contra la base de datos: '+DNIIdIdespecial, userId)
    return  result

@expediente.get("/expediente/{idEspecial}")
def get_expedientes(idEspecial:str):

    result = conn.execute(expedientes.select().where(expedientes.c.idEspecial==idEspecial)).first()
    if(not result):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)    # Le avisamos al usuario que lo que nos pasó no es correcto


    # NO PODES no usar first() si vas a usar result["nombreCol"], porque te va a tirar un error del legacy. Después averigua bien en la documentación
    resultEstados = conn.execute(estados.select().where(estados.c.idEspecial == idEspecial))
    resultTemporizador = conn.execute(temporizador.select().where(temporizador.c.idEspecial == idEspecial))

    arrayEstados = []
    objTemporizador = {}

    if(resultEstados.rowcount > 0):
        for elementEstados in resultEstados:
            new_object_estado = {
                "id":   elementEstados["id"],
                "idEspecial":   elementEstados["idEspecial"],
                "estado": elementEstados["estado"],
                "descripcion": elementEstados["descripcion"]
            }
            arrayEstados.append(new_object_estado)


    if(resultTemporizador.rowcount > 0):
        objTemporizador["titulo"] = resultTemporizador["titulo"]
        objTemporizador["fechaInicio"] = resultTemporizador["fechaInicio"]
        objTemporizador["fechaFin"] = resultTemporizador["fechaFin"]

                

    expediente = {
        "id": result["id"],
        "idEspecial": result["idEspecial"],
        "datos": {
            "nombres": result["nombres"],
            "apellido": result["apellido"],
            "direccion": result["direccion"],
            "localidad": result["localidad"],
            "telefono": result["telefono"],
            "dni": result["dni"],
            "fechaAudiencia": result["fechaAudiencia"],
            "detalles": result["detalles"],
            "empresas": result["empresas"],
            "hipervulnerable": result["hipervulnerable"],
            "actuacion": result["actuacion"],
            "creador": result["creador"]
        },
        "estados": arrayEstados,
        "temporizador":
            objTemporizador
        ,
        "archivado": result["archivado"]
    }
    

    return  expediente

@expediente.get("/expediente/estados/{idEspecial}, {userId}") #id de sistema
def get_estados_expediente(idEspecial:str, userId: int):
    result = conn.execute(estados.select().where(estados.c.idEspecial==idEspecial)).fetchall() #id de sistema
    if(not result):
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    # REGISTRO #
    registro('Realizó una consulta sobre el expediente: '+idEspecial, userId)

    return result


@expediente.post("/expediente")
def create_expediente(expediente: Datos):
    print(expediente) # Recibimos

    new_expediente = {                             # Convertimos lo recibido en un nuevo diccionario
        "nombres": expediente.nombres,
        "apellido": expediente.apellido,
        "direccion": expediente.direccion,
        "localidad": expediente.localidad,
        "telefono": expediente.telefono,
        "dni": expediente.dni,
        "fechaAudiencia": expediente.fechaAudiencia,
        "detalles": expediente.detalles,
        "empresas": expediente.empresas,
        "hipervulnerable": expediente.hipervulnerable,
        "actuacion": expediente.actuacion,
        "creador": expediente.creador
    }

    print(new_expediente)                         # Imprimimos para ver el nuevo diccionario

    # Intentamos guardar en la base de datos ahora
    result = conn.execute(expedientes.insert().values(new_expediente))
    print(result)   # Imprimimos el resultado de la consulta a la base de datos
                    # Te devuelve un cursor
    estado = {
        "idEspecial": result.lastrowid, # ID DE SISTEMA es lo que usamos con estados
        "estado": "Creación del expediente",
        "fecha": datetime.now()
    }

    reloj = {
        "idEspecial": result.lastrowid,
        "fechaInicio": datetime.now(),
        "fechaFin": expediente.fechaAudiencia
    }

    # Obtengo el que coincida con fecha y hora.
    # Si coincide obtengo el id
    resultSelectFechaAudiencia = conn.execute(fechas.select().where(fechas.c.fechaHora == expediente.fechaAudiencia).limit(1)).fetchone()
    idInicial = resultSelectFechaAudiencia.id

    # Ahora de ese id, le pregunto si tiene disponible
    resultFechaAudiencia = conn.execute(fechas.update().values(
        idExpediente = result.lastrowid,
        disponible = 0
    ).where(and_(fechas.c.fechaHora == expediente.fechaAudiencia, fechas.c.disponible == True, fechas.c.id == idInicial)))
    
    # Si no lo tiene disponible haceme un while hasta encontrar el siguiente disponible
    if(resultFechaAudiencia.rowcount <= 0):
        i = 1
        while i == 1:
            idInicial += 1
            resultUpdated = conn.execute(fechas.update().values(
                idExpediente = result.lastrowid,
                disponible = 0
            ).where(and_(fechas.c.id == idInicial, fechas.c.disponible == True)))

            if(resultUpdated.rowcount > 0):
                i = 0

    result2 = conn.execute(estados.insert().values(estado))
    result3 = conn.execute(temporizador.insert().values(reloj))
    userId = expediente.creador
    # REGISTRO #
    registro('Creó un nuevo expediente con id de sistema: '+ str(result.lastrowid), userId)
    return  conn.execute(estados.select().where(estados.c.idEspecial == result.lastrowid)).first() # Devuelve el ID del sistema

        # 'users.c.id' -> users es la tabla, 'c' indica la columna, y el 'id' es el nombre de la columna
        # Le pedimos con .first() que de lo devuelto como lista, que nos devuelva solo el primer elemento

@expediente.post("/estado/{userId}")
def create_estado(estado: Estado, userId: int):
    result = conn.execute(estados.insert().values(idEspecial = estado.idEspecial, estado=estado.estado, descripcion=estado.descripcion))
    # REGISTRO #
    registro('Cargó un nuevo estado: ' + estado.estado + 'sobre el id de sistema: ' + estado.idEspecial, userId)
    return conn.execute(estados.select().where(estados.c.id == result.lastrowid)).first()

@expediente.post("/temporizador")
def create_temporizador(settemporizador: Temporizador):
    result = conn.execute(temporizador.select().where(temporizador.c.idEspecial==settemporizador.idEspecial))

    if(result.rowcount < 0 ):
        result_temporizador = conn.execute(temporizador.insert().values(
            idEspecial = settemporizador.idEspecial,
            titulo = settemporizador.titulo,
            fechaInicio = settemporizador.fechaInicio,
            fechaFin = settemporizador.fechaFin
        ))
        return conn.execute(temporizador.select().where(temporizador.c.id==result_temporizador.lastrowid))
    else:
        result_temporizador = conn.execute(temporizador.update().values(
            idEspecial = settemporizador.idEspecial,
            titulo = settemporizador.titulo,
            fechaInicio = settemporizador.fechaInicio,
            fechaFin = settemporizador.fechaFin).where(temporizador.c.idEspecial==settemporizador.idEspecial))
        return conn.execute(temporizador.select().where(temporizador.c.idEspecial==settemporizador.idEspecial)).first()

    

@expediente.put("/expediente/datos/{id},{userId}")
def update_expediente(id: str, setexpediente: Datos, userId: int):
        conn.execute(expedientes.update().values(
            idEspecial = setexpediente.idEspecial if setexpediente.idEspecial else expedientes.c.idEspecial,
            nombres = setexpediente.nombres,
            apellido = setexpediente.apellido,
            direccion = setexpediente.direccion,
            localidad = setexpediente.localidad,
            telefono = setexpediente.telefono,
            dni = setexpediente.dni,
            fechaAudiencia = setexpediente.fechaAudiencia,
            detalles = setexpediente.detalles,
            empresas = setexpediente.empresas,
            hipervulnerable = setexpediente.hipervulnerable,
            actuacion = setexpediente.actuacion,
            creador = setexpediente.creador

        ).where(expedientes.c.id == id))

        # REGISTRO #
        registro('Actualizó el expediente con id de sistema: ' + id, userId)

        return conn.execute(expedientes.select().where(expedientes.c.id==id)).first()

@expediente.put("/expediente/estados/{id},{userId}")
def update_estado(id: str, estado: Estado, userId: int):
        conn.execute(estados.update().values(
            idEspecial = estado.idEspecial,
            estado = estado.estado,
            descripcion = estado.descripcion

        ).where(estados.c.id == id))

        # REGISTRO #
        registro('Actualizó un estado a: ' + estado.estado, userId)

        return conn.execute(estados.select().where(estados.c.id == id)).first()