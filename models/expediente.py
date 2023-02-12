from sqlalchemy import Table, Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean
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

expedientes = Table('expedientes', meta, 
    Column("id", Integer, primary_key=True),
    Column("idEspecial", String(255)),
    Column("nombres", String(255)),
    Column("apellido", String(255)),
    Column("direccion", String(255)),
    Column("localidad", String(255)),
    Column("telefono", String(255)),
    Column("dni", String(255)),
    Column("fechaAudiencia", DateTime),
    Column("detalles", String(255)),
    Column("empresas", String(1028)),
    Column("hipervulnerable", Boolean),
    Column("actuacion", Boolean),
    Column("creador", String(255)),
    Column("archivado", Boolean))

estados = Table('estados', meta, 
    Column("id", Integer, primary_key=True),
    Column("idEspecial", String(255)),
    Column("estado", String(255)),
    Column("descripcion", String(1028)),
    Column("fecha", DateTime)
)

temporizador = Table('temporizadores', meta, 
    Column("id", Integer, primary_key=True),
    Column("idEspecial", String(255)),
    Column("titulo", String(255)),
    Column("fechaInicio", DateTime),
    Column("fechaFin", DateTime)
)

fechas = Table('fechas', meta,
    Column("id", Integer, primary_key=True),
    Column("idExpediente", String(255)),
    Column("fechaHora", DateTime),
    Column("disponible", Boolean)
)

# 'meta' almacena o linkea la creación de una tabla
# finalmente la ejecutamos con el método "create_all"
# y le pasamos la conexión 'engine' que viene del archivo
# db.py en config
meta.create_all(engine)


# TERMINADO DE CREAR LA TABLA
# VAMOS A LA CARPETA 'ROUTES'