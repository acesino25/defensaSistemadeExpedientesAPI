# En este archivo vamos a configurar las respuestas de solicitudes a
# GET, POST, DELETE y las restantes


from fastapi import APIRouter, Response, status
from fastapi import Response    # Importamos para dar respuestas HTML en consultas como delete
from starlette.status import HTTP_204_NO_CONTENT    # Importamos desde una librería la respuesta que queremos dar

from sqlalchemy import and_

from fastapi import status      # Esto lo usaremos a la hora de indicar el modelo de respuesta
                                # que cada consulta recibirá
import bcrypt   # Usaremos Bcrypt en lugar de Fernet

from utils.registro import registro # importamos una funcion que carga los movimientos de los usuarios

# YA CREDA LA CONEXIÓN con la DB en
# config.db y models.user
# importamos lo creado:
from config.db import conn  
# Nos permitirá interactuar, 
# pero nos falta el esquema:
from models.users import users, acciones
# Importamos la función 'users'

from schemas.user import User, Perfil, Login

# Para PASSWORD importamos un módulo para encriptar
from cryptography.fernet import Fernet

### PARA LA PASSWORD ########
# 1 Generamos una key única de cifrado
key = Fernet.generate_key()
# 2 A esa key se la pasamos a Fernet
# nos devuelve una función que guardamos
# en f
f = Fernet(key)

user = APIRouter() # Esto devuelve una respuesta y la guardamos



# En lugar the FERNET usaremos Bcrypt que es mejor para passwords
def hash_password(password: str):
    salt = bcrypt.gensalt()
    password_bytes = password.encode("utf-8")
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password

def check_password(password: str, hashed_password: bytes):
    password_bytes = password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password_bytes)


    '''
    MODO DE USO:

    # Example usage
    password = "secret password"
    hashed_password = hash_password(password)
    print(hashed_password)

    is_password_correct = check_password(password, hashed_password)
    print(is_password_correct) # True

    incorrect_password = "incorrect password"
    is_password_correct = check_password(incorrect_password, hashed_password)
    print(is_password_correct) # False
    
    '''





# Los CRUD tienen 5 rutas típicas:
# LISTAR, CREAR, ELIMINAR, ACTUALIZAR (hay una que no recuerdo)
# GET,  POST,   DELETE, PUT



# SALTAMOS A OTRO ARCHIVO:
# Ahora nos vamos a crear nuestra base de datos para tener a los usuarios
# en la carpeta 'config'


# Aquí en response_model indicamos el modelo de dato
# que devolverá como respuesta
# En este caso: Una lista con datos tipo User
@user.get("/users", response_model = list[User], tags=['users'])     #Interceptamos la ruta a la que están intentando acceder
def get_users():            # Esta es la manera en la que definimos un funcion en python
    return conn.execute(users.select()).fetchall() 
    # Acá esperamos a que el método 'select' termine.
    # Y recién hacemos 'fetch'


@user.post("/users", response_model=Perfil, tags=['users'])     #Interceptamos la ruta a la que están intentando acceder
def create_user(user: User): # Recibe como argumento (user) un tipo de dato User, ese tipo de dato lo crearemos en la carpeta 'schemas'

    if(user.password == user.passwordConfirm):
        # Es más práctico tener los datos como un DICCIONARIO, un tipo de dato de python.
        # Para ello lo convertiremos en un diccionario. Semejante a un Objeto en Javascript.
        new_user = {"name": user.name, "email": user.mail, "permiso": user.permiso,
                    "puntos": 0}
        new_user['password'] =  hash_password(user.password)    # Creamos una propiedad extra de esta forma, y asignamos una contraseña
                                                                            # La contraseña recibida con POST NO está cifrada, lo haremos.
        
        # Chequeamos que el mail no esté ya registrado:
        registrado = conn.execute(users.select().where(users.c.email == user.mail)).fetchone()

        if(not registrado):
            # Intentamos guardar en la base de datos ahora
            result = conn.execute(users.insert().values(new_user))
            ultimoid = result.lastrowid

            # Ahora retornaremos la creación:
            # con lastrowid accedemos al id del último elemento agregado en la consulta 'result'
            respuesta = conn.execute(users.select().where(users.c.id == ultimoid)).first()
            perfil = {
                "id": respuesta.id,
                "name": respuesta.name,
                "mail": respuesta.email,
                "puntos": respuesta.puntos,
                "permiso": respuesta.permiso
            }
            return perfil

            # 'users.c.id' -> users es la tabla, 'c' indica la columna, y el 'id' es el nombre de la columna
            # Le pedimos con .first() que de lo devuelto como lista, que nos devuelva solo el primer elemento
    return Response(status_code=status.HTTP_400_BAD_REQUEST) 


@user.get("/users/{id}", response_model=User, tags=['users'])    # Interceptamos la dirección a la que accedemos
def get_user(id: str):      # Diferente a lo anterior, no usaremos nada del Schemas
    return conn.execute(users.select().where(users.c.id == id)).first()
    #   De la conexión actual ejecuta: 
    #   en la tabla 'users"
    #   la seleción de elementos
    #   donde en users columna id sea igual al 'id' que recibo como argumento del get
    #   De los resultados, devolveme el primero first()

@user.post("/users/login/", tags=['users'])    # Interceptamos la dirección a la que accedemos
def log_in(login: Login):      # Diferente a lo anterior, no usaremos nada del Schemas
    print(login)

    result = conn.execute(users.select().where(users.c.email == login.mail)).first()

    print(result)
    if(check_password(login.password, result.password)):    # Mando a encode ambos parametros que son string
        perfil = {
            "id": result.id,
            "name": result.name,
            "mail": result.email,
            "puntos": result.puntos,
            "permiso": result.permiso
        }
        return perfil
    else:
        return Response(status_code=HTTP_204_NO_CONTENT)


# Aquí el modelo cambia
# Indicamos que pasamos un 'status_code' en lugar de
# un response_model
@user.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=['users'])
def delete_user(id: str):
    conn.execute(users.delete().where(users.c.id == id))   # Ya no usamos first() porque es propio de select
    return Response(status_code=HTTP_204_NO_CONTENT)
    # Devolvemos una respuesta 204 en formato HTML que
    # el frontend deberá procesar como que todo fue bien, pero no devolvió nada
    # Response : es obtenido de la biblioteca de fastapi
    # HTTP_204_NO_CONTENT : es importado de la biblioteca starlett.status, que supuestamente ya está en fastapi


@user.put("/users/{id}", response_model=User, tags=['users'])
def update_user(id: str, user: User):    # La función recibe un id, y recibe un argumento user de tipo User, declarado en el archivo schemas
    conn.execute(users.update().values(name=user.name,
    email=user.email,
    password=f.encrypt(user.password.encode('utf-8'))).where(users.c.id == id))
    return conn.execute(users.select().where(users.c.id==id)).first()   #   Tras la ejecución devolvemos el elemento para que se muestre lo actualizado



# TRAS TERMINAR:

# Para que se vea mejor en tu /docs
# agruparemos las rutas que tengan relación,
# en este caso todas a users
# para ello ponemos tags = ["nombre que queremos dar al grupo"]

# Agregaremos la modificación de /docs a nuestra 'app.py'
# Agregaremos texto, descripción, título y más