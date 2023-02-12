from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime
from config.db import meta, engine

# Creamos una tabla dentro de la base de datos
# Llamamos a la función "Table"
# que recibe los argumentos:
# 1 Nombre de la base de datos
# 2 Propiedades de la base de datos (meta), que traemos desde config.db
# 3 Las Columns que deseemos insertar

# Las columns reciben argumentos:
# 1 Nombre de la columna
# 2 Tipo de dato 
    # Tenemos los tipos de datos en 'sqlalchemy.sql.sqltypes'
    # los llamamos y llamamos cada tipo de dato para usar.
    # además los tipos de datos reciben argumentos para indicar
    # límites

# 3 Opcional - si es primary u otros argumentos que se le puedan pasar
# Leer la documentación

users = Table('users', meta, Column(
    "id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("email", String(255)),
    Column("password", String(255)),
    Column("pregunta", String(255)),
    Column("puntos", String(255)),
    Column("permiso", String(255))
    )

acciones = Table('acciones', meta,
    Column("id", Integer, primary_key=True),
    Column("hizo", String(255)),
    Column("quien", String(255)),
    Column("fechaHora", DateTime)
)

# 'meta' almacena o linkea la creación de una tabla
# finalmente la ejecutamos con el método "create_all"
# y le pasamos la conexión 'engine' que viene del archivo
# db.py en config
meta.create_all(engine)


# TERMINADO DE CREAR LA TABLA
# VAMOS A LA CARPETA 'ROUTES'