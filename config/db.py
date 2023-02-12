# Para la base de datos necesitamos a 
# sqlalchemy y a PyMysql, este último
# lo necesita sqlalchemy

from sqlalchemy import create_engine, MetaData

# Esta es una solicitud de conexión a la base de datos
# Utilizaremos XAMPP como proveedor de base de datos
# El puerto de la base de datos te lo da en el panel xampp
# Por defecto es localhost:3306
# la parte del principio "mysql+pymysql" es para indicar
# que leeremos una Mysql utilizando pymysql
# la barra "/" indica la tabla a la que accederemos

#create_engine("mysql+pymysql://(user)root:password@localhost:3306/basededatosaconectar")


engine = create_engine("mysql+pymysql://root:@localhost:3306/def")

meta = MetaData() # Esto nos da acceso a las propiedades que usaremos en la carpeta MODELS

# Almacenamos la respuesta de conexión, almacenamos lo devuelto por 
# el método aplicado a engine, que es "connect"
conn = engine.connect()

# Hecho esto prepararemos la reación de las tablas
# en caso de que no existan.
# NOS VAMOS A LA CARPETA 'MODELS'