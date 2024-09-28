import random
from datetime import datetime, timedelta

import psycopg2

# Configuración de la conexión a la base de datos
conn = psycopg2.connect(
    dbname="postgres", user="admin", password="psw", host="localhost", port="5432"
)

# Crear un cursor
cur = conn.cursor()

# Generar 100 lecturas de temperatura
for i in range(100):
    sensor_id = 127
    value = round(random.uniform(20.0, 30.0), 1)  # Temperatura entre 20.0 y 30.0 °C
    units = "°C"
    timestamp = datetime.now() - timedelta(
        minutes=i
    )  # Lecturas en los últimos 100 minutos

    # Insertar la lectura en la base de datos
    cur.execute(
        "INSERT INTO lecturas (sensor_id, value, units, timestamp) VALUES (%s, %s, %s, %s)",
        (sensor_id, value, units, timestamp),
    )

# Confirmar los cambios y cerrar la conexión
conn.commit()
cur.close()
conn.close()

print("Se han insertado 100 lecturas de temperatura en la base de datos.")
