from fastapi import APIRouter, Response, status
import urllib.parse
from schemas.file import File, Datos, Estado, Temporizador, TipoDeDenuncia

from data.data import server

from datetime import datetime, timedelta

from config.db import conn
from models.expediente import expedientes, estados, temporizador, fechas, contador, categorias

from fastapi.responses import JSONResponse

from sqlalchemy import and_, or_

from utils.registro import registro # importamos una funcion que carga los movimientos de los usuarios

expediente = APIRouter()


# Crearemos categorías de denuncias
@expediente.post("/cargarCategoria/", tags=['categorias'])
def post_categoria(nuevaCategoria: TipoDeDenuncia):
    categoriaInsertar = {"nombre": nuevaCategoria.nombre}
    conn.execute(categorias.insert(categoriaInsertar))

    #Registramos este cambio:
    registro('Categoria agregada: ' , nuevaCategoria.creador)
    return 'Categoría creada'

# Retornamos todas las categorías
@expediente.get("/verCategorias/", tags=['categorias'])
def get_categorias():
    return conn.execute(categorias.select()).fetchall()

# Eliminamos una categoria
@expediente.delete("/eliminarCategoria/{id}/{userid}", tags=['categorias'])
def delete_categoria(id: int, userId: str):
    # Eliminamos el registro
    conn.execute(categorias.delete().where(categorias.c.id==id))

    #Registramos este cambio:
    registro('Se ha eliminado una categoría del registro', userId)

    return 'Eliminado'
    

# Obtener las alertas máx próximas
@expediente.get("/temporizador/{cantidad}")
def get_temporizador(cantidad: int):

    # Obtenemos la fecha de hoy
    today = datetime.now()
    result = conn.execute(temporizador.select().where(temporizador.c.fechaFin >= today.date()).limit(cantidad)).fetchall()

    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = server
    return response


# Obtenemos las audiencias del día
@expediente.get("/audiencias/{dia}", tags=['audiencias'])
def get_fechaNuevaAudiencia(dia: str):
    print("Valor recibido:")
    print(dia)
    # Parse the string into a datetime.date object
    dia_date = datetime.strptime(dia, '%Y-%m-%d').date()
    # Create a datetime object with the same date and time set to midnight
    start_date = datetime.combine(dia_date, datetime.min.time())
    # Create a datetime object with the same date and time set to 23:59
    end_date = datetime.combine(dia_date, datetime.max.time())
    result = conn.execute(expedientes.select().where(expedientes.c.fechaAudiencia.between(start_date, end_date))).fetchall()
    return result

# esta nos sirve para el panel de admin
@expediente.get("/fechasDisponibles/{desde},{hasta}")
def get_fechaNuevaAudiencia(desde: datetime, hasta: datetime):

    result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora >= desde, and_(fechas.c.fechaHora <= hasta)))).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = server
    return response


# Reasignar fechasde audiencias:
@expediente.get("/diaDisponible/{desde},{hasta}")
def get_fechaDia(desde: datetime, hasta: datetime):

    result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora >= desde, and_(fechas.c.fechaHora <= hasta, and_(fechas.c.disponible == True))))).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = server
    return response


# Reasignar fechasde audiencias:
@expediente.post("/editarDisponible/")
def post_editarDisponible(idFecha: int, idEspecial: str, userId: int):
    print(idFecha, idEspecial, userId)
    #Obtengo el expediente
    print('Obtengo el expediente')
    decoded = urllib.parse.unquote(idEspecial)
    result = conn.execute(expedientes.select().where(expedientes.c.idEspecial==decoded)).first()

    idSistema = result.id
    fechaActual = result.fechaAudiencia

    # PONER CONDICIÓN PARA DETECTAR QUE AÚN SIGA DISPONIBLE LA FECHA
    print('PONER CONDICIÓN PARA DETECTAR QUE AÚN SIGA DISPONIBLE LA FECHA')
    resultDisponible = conn.execute(fechas.select().where(fechas.c.id==idFecha)).first()
    if(not resultDisponible.disponible):
        print('No podemos proceder')
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    print('se ejecutó')
    #Libero para otro la fecha usada
    print('Libero para otro la fecha usada')
    resultFechas = conn.execute(fechas.update().values(
        idExpediente = None,
        disponible = True
    ).where(fechas.c.idExpediente==idSistema))

    #Reservo la fecha para este expediente
    print('Reservo la fecha para este expediente')
    resultFecha = conn.execute(fechas.update().values(
        idExpediente = idSistema,
        disponible = False
    ).where(fechas.c.id==idFecha))

    #Obtengo el valor de dicha fecha para actualizarlo en el expediente
    print('Obtengo el valor de dicha fecha para actualizarlo en el expediente')
    resultFecha = conn.execute(fechas.select().where(fechas.c.id==idFecha)).first()
    fechaNueva = resultFecha.fechaHora

    #Actualizo dicha fecha
    print('Actualizo dicha fecha')
    result = conn.execute(expedientes.update().values(
        fechaAudiencia = fechaNueva
    ).where(expedientes.c.id==idSistema))

    #Actualizo el temporizador
    print('Actualizo el temporizador')
    resultTemporizador = conn.execute(temporizador.update().values(
        fechaFin = fechaNueva,
        titulo = 'Audiencia reprogramada'
    ).where(temporizador.c.idEspecial==idSistema))


    #Devuelvo la fecha actual del expediente:
    print('Devuelvo la fecha actual del expediente:')
    result = conn.execute(expedientes.select().where(expedientes.c.id==idSistema)).first()

    #Registramos este cambio:
    registro('Nueva fecha de audiencia sobre expediente con id de sistema: ' + str(idSistema) , userId)

    #Declaro un nuevo estado en el expediente:
    conn.execute(estados.insert().values(
        idEspecial = idSistema,
        estado = 'Nueva audiencia o reprogramada',
        fecha = datetime.now()
    ))

    return(result.fechaAudiencia)




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
    respuesta.headers["Access-Control-Allow-Origin"] = server
    print(result.fetchone())

    # REGISTRO #
    registro('Modificación de fecha: ' + str(idFecha) , userId)
    return respuesta






#DESHABILITAR FECHA POR MES



@expediente.get("/deshabilitarmes/{desde},{hasta},{idUser}")
def get_fechaNuevaAudiencia(desde: datetime, hasta: datetime, idUser: int):

    result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora >= desde, and_(fechas.c.fechaHora <= hasta)))).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    
    for fecha in result_list:
        result2 = conn.execute(fechas.update().values(
            disponible = 0
        ).where(fechas.c.id == fecha["id"]))

    return 'Deshabilitado'







# MODIFIQUÉ PARA QUE TOME 3 - 4 MESES
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

    #LIMITE
    # result = conn.execute(fechas.select().where(and_(fechas.c.fechaHora > business_days_ahead(14), fechas.c.disponible == True)).limit(50)).fetchall()

    result = conn.execute(fechas.select().where(and_(fechas.c.disponible == True, fechas.c.fechaHora < business_days_ahead(30))).limit(150)).fetchall()
    result_list = [{key: value.isoformat() if isinstance(value, datetime) else value for key, value in row.items()} for row in result] # convert the datetime objects to ISO 8601 strings
    response = JSONResponse(content=result_list)
    response.headers["Access-Control-Allow-Origin"] = server
    return response

# ESTO NOS SIRVE PARA POPULAR LA BASE DE DATOS
''' ESTO ES PARA CARGAR POR CADA 30 MINUTOS '''
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
                current_date += timedelta(minutes=30)   # Tomamos cada 30 minutos, en lugar de cada una hora
            current_date = current_date.replace(hour=5)
            current_date += timedelta(days=1)

    if(result.rowcount <= 0):
        loop_ten_years()
        result = conn.execute(fechas.select())
    
    return result.fetchall()


'''
ESTO ES POR HORAS

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
'''    



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
                "categoria": element["categoria"],
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
                "categoria": element["categoria"],
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

    decoded = urllib.parse.unquote(DNIIdIdespecial)
    result = conn.execute(
        expedientes.select().where(or_(
            expedientes.c.idEspecial==decoded,
            expedientes.c.id == decoded,
            expedientes.c.dni == decoded))).fetchall()

    if(not result):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)    # Le avisamos al usuario que lo que nos pasó no es correcto

    # REGISTRO #
    registro('Realizó una búsqueda contra la base de datos: '+DNIIdIdespecial, userId)
    return  result

@expediente.get("/expediente/{idEspecial}")
def get_expediente(idEspecial:str):

    result = conn.execute(expedientes.select().where(expedientes.c.id==idEspecial)).first()
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


    '''if(resultTemporizador.rowcount > 0):
        objTemporizador["titulo"] = resultTemporizador["titulo"]
        objTemporizador["fechaInicio"] = resultTemporizador["fechaInicio"]
        objTemporizador["fechaFin"] = resultTemporizador["fechaFin"]'''

                

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
            "categoria": result["categoria"],
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

# OBTENEMOS EL CONTADOR DE EXPEDIENTES
@expediente.get("/contador/{userId}")
def get_contador(userId: int):
    result = conn.execute(contador.select().limit(1)).first()
    if(not result):
        conn.execute(contador.insert().values(contador = 1, fechaHora=datetime.now()))

    # REGISTRO #
    registro('Consultó el contador de expedientes', userId)

    return result





# ACTUALIZAMOS O CREAMOS EL CONTADOR DE EXPEDIENTES
@expediente.post("/contador/set/{nuevoValor}, {userId}")
def set_contador(userId: int, nuevoValor: str):
    #Tomamos el primer resultado de la tabla contador
    resultContador = conn.execute(contador.select().limit(1))
    print(resultContador)
    # Si no hay resultados insertamos un nuevo contador
    if(resultContador.rowcount <= 0):
        today = datetime.now()
        yyyy = today.year
        # hacemos inserción a la base de datos
        resultContador = conn.execute(contador.insert().values(contador=nuevoValor, fechaHora = today))
    else:
        today = datetime.now()
        datos = resultContador.first()
        ultimoid = datos.id
        conn.execute(contador.update().values(contador = nuevoValor, fechaHora=today).where(contador.c.id == ultimoid))

    # REGISTRO #
    registro('Consultó el contador de expedientes', userId)

    return 'actualizado'







@expediente.post("/expediente")
def create_expediente(expediente: Datos):
    print(expediente) # Recibimos
    idEspecial = expediente.idEspecial

    # 3/3/23
    # En vista del error generado el 3 del 3 del 23
    # Donde por intentar alterar el bucle de la próxima fecha
    # el servidor cambió las fechas de todos los expedientes
    # haremos un cambio y en lugar de colocar la próxima disponible
    # vamos a enviar un error y lo manejaremos en react para que haga el cambio de fecha


    # Detectamos la hora primero

    resultIdEspecialExiste = conn.execute(expedientes.select().where(expedientes.c.idEspecial == expediente.idEspecial).limit(1))
    noExiste = False
    # Chequeamos si existe el expediente ya
    if(resultIdEspecialExiste.rowcount <= 0):
        noExiste = True

    # Obtengo el que coincida con fecha y hora.
    # Si coincide obtengo el id
    if(not idEspecial or idEspecial == None or noExiste):
        resultSelectFechaAudiencia = conn.execute(fechas.select().where(fechas.c.fechaHora == expediente.fechaAudiencia).limit(1)).fetchone()
        idInicial = resultSelectFechaAudiencia.id
        print("Fecha encontrada")
        print(idInicial)

        # Ahora de ese id, le pregunto si tiene disponible y que actualice
        # LO ACTUALIZO DE MANERA PREVENTIVA CON EL idEspecial
        print("Intentamos asignar una fecha con idEspecial de momento")
        resultFechaAudiencia = conn.execute(fechas.update().values(
            idExpediente = expediente.idEspecial,
            disponible = 0
        ).where(and_(fechas.c.fechaHora == expediente.fechaAudiencia, fechas.c.disponible == True, fechas.c.id == idInicial)))
        print(resultFechaAudiencia.rowcount)

        '''
        ORIGINAL:

        resultFechaAudiencia = conn.execute(fechas.update().values(
            idExpediente = result.lastrowid,
            disponible = 0
        ).where(and_(fechas.c.fechaHora == expediente.fechaAudiencia, fechas.c.disponible == True, fechas.c.id == idInicial)))
        '''
        
        # Si no lo tiene disponible haceme un while hasta encontrar el siguiente disponible
        # YA NO. Ahora tira error y manejalo en react
        # RETORNAMOS un error 404 indicando que la fecha que busca no ha sido encontrada
        if(resultFechaAudiencia.rowcount <= 0):

            print("Tomamos el siguiente con la misma fecha.")
            idInicial += 1
            resultUpdated = conn.execute(fechas.update().values(
                idExpediente = expediente.idEspecial,
                disponible = 0
            ).where(and_(fechas.c.id == idInicial, fechas.c.disponible == True, fechas.c.fechaHora == expediente.fechaAudiencia)))
            
            if(resultUpdated.rowcount <= 0):
                return JSONResponse(status_code=404, content={"message": "Lo intentamos, pero la fecha elegida ya ha sido tomada"})

        ###################### FIN DE NOTA ####################

    idEspecial = expediente.idEspecial
    print("este es el id")
    print(idEspecial)

    if(expediente.id):
        resultSelectMe = conn.execute(expedientes.select().where(expedientes.c.id == expediente.id)).first()
        if(resultSelectMe):
            conn.execute(expedientes.update().values(
                idEspecial = expediente.idEspecial,
                nombres = expediente.nombres,
                apellido = expediente.apellido,
                direccion = expediente.direccion,
                localidad = expediente.localidad,
                telefono = expediente.telefono,
                dni = expediente.dni,
                detalles = expediente.detalles,
                empresas = expediente.empresas,
                hipervulnerable = expediente.hipervulnerable,
                actuacion = expediente.actuacion,
                creador = expediente.creador

            ).where(expedientes.c.id == expediente.id))

            crearNuevo = False

            # REGISTRO #
            registro('Actualizó el expediente con id de sistema: ' + idEspecial, expediente.creador)

            return conn.execute(expedientes.select().where(expedientes.c.idEspecial==idEspecial)).first()
        else:
            crearNuevo = True

    if(not expediente.idEspecial or expediente.idEspecial == ''):
        #Tomamos el primer resultado de la tabla contador
        resultContador = conn.execute(contador.select().limit(1))

        # Si no hay resultados insertamos
        if(resultContador.rowcount <= 0):
            today = datetime.now()
            yyyy = today.year
            resultContador = conn.execute(contador.insert().values(contador=1))
            valor = 1
            idEspecial = str(valor) + '/' + str(yyyy)
            valor += 1
            conn.execute(contador.update().values(contador = str(valor), fechaHora=today).where(contador.c.id == resultContador.lastrowid))
        else:
            today = datetime.now()
            yyyy = today.year
            datos = resultContador.first()
            valor = datos.contador
            idEspecial = str(valor) + '/' + str(yyyy)

            fechaContador = datos.fechaHora
            #chequeamos si la última fecha cargada es del año anterior al de hoy
            if (fechaContador.year != today.year):
                # COMENTÉ ESTA CONDICIÓN: today.month >= 1) and (today.day >= 1) and (idEspecial > 1) and 
                valor = 1 
                # Si es así reiniciamos el contador
                idEspecial = str(valor) + '/' + str(yyyy)
                conn.execute(contador.update().values(contador = str(valor), fechaHora=today).where(contador.c.id == datos.id))
                print("Año actualizado")
            #Si seguimos en el mismo año, seguimos sumando:    
            else:
                valor = datos.contador
                idEspecial = str(valor) + '/' + str(yyyy)
                valor = int(valor)+1
                conn.execute(contador.update().values(contador = str(valor), fechaHora=today).where(contador.c.id == datos.id))









# CREACIÓN DEL EXPEDIENTE
    new_expediente = {       
        "idEspecial": idEspecial,                      # Convertimos lo recibido en un nuevo diccionario
        "nombres": expediente.nombres,
        "apellido": expediente.apellido,
        "direccion": expediente.direccion,
        "localidad": expediente.localidad,
        "telefono": expediente.telefono,
        "dni": expediente.dni,
        "fechaAudiencia": expediente.fechaAudiencia,
        "categoria": expediente.categoria,
        "detalles": expediente.detalles,
        "empresas": expediente.empresas,
        "hipervulnerable": expediente.hipervulnerable,
        "actuacion": expediente.actuacion,
        "creador": expediente.creador
    }

    print(new_expediente)                         # Imprimimos para ver el nuevo diccionario

    # Intentamos guardar en la base de datos ahora
    result = conn.execute(expedientes.insert().values(new_expediente))
    devolver = result
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

    # Sobre la fecha que reservamos actualizamos y ponemos el ID de sistema
    resultFechaAudiencia = conn.execute(fechas.update().values(
        idExpediente = result.lastrowid
    ).where(and_(fechas.c.disponible == False, fechas.c.idExpediente == expediente.idEspecial)))
    print("Fecha con idSistema actualizada")

    result2 = conn.execute(estados.insert().values(estado))
    result3 = conn.execute(temporizador.insert().values(reloj))
    userId = expediente.creador
    # REGISTRO #
    registro('Creó un nuevo expediente con id de sistema: '+ str(result.lastrowid), userId)
    resultPrint = conn.execute(expedientes.select().where(expedientes.c.id == devolver.lastrowid)).first()
    print(resultPrint)
    return  resultPrint

        # 'users.c.id' -> users es la tabla, 'c' indica la columna, y el 'id' es el nombre de la columna
        # Le pedimos con .first() que de lo devuelto como lista, que nos devuelva solo el primer elemento

@expediente.post("/estado/{userId}")
def create_estado(estado: Estado, userId: int):
    if(estado.estado == ''): return 'No es posible guardar un estado vacío'
    result = conn.execute(estados.insert().values(idEspecial = estado.idEspecial, estado=estado.estado, descripcion=estado.descripcion, fecha=datetime.now()))
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