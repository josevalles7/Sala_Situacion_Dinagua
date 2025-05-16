import requests
from datetime import datetime
import time
import random
import pandas as pd
import os


# Crear una sesión para mantener las cookies
session = requests.Session()

# URL de login
url_login = "https://sistemas.inumet.gub.uy/login"

# Datos de login (rellená con tus credenciales)
payload_login = {
    "user": "telepluvio",
    "password": "telepluvio"
}

# Cabeceras necesarias
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://sistemas.inumet.gub.uy",
    "Referer": "https://sistemas.inumet.gub.uy/login",
    "Accept": "application/json, text/plain, */*"
}


response_login = session.post(url_login, json=payload_login, headers=headers)
print("Login status:", response_login.status_code)

#---------------------------------------------------------------------------------------------------------------
#una pequeña pausa no sospechosa
time.sleep(random.uniform(5, 8)) 
#---------------------------------------------------------------------------------------------------------------

# === 2. Lista de estaciones ===
nombres_estaciones = [
    "18 de Julio",
    "Prado",
    "Cerrillos"
]


fecha_inicio = "2024-12-01"
fecha_fin = "2025-01-31"

# === 3. Convertir fechas a milisegundos y segundos epoch ===
def fecha_a_epoch_ms(fecha_str):
    dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

epoch_from = fecha_a_epoch_ms(fecha_inicio)
epoch_to = fecha_a_epoch_ms(fecha_fin)
epoch_from_s = epoch_from // 1000
epoch_to_s = epoch_to // 1000

for nombre_estacion in nombres_estaciones:
    # === 4. Armar SQL personalizado ===
    raw_sql = f"""
    SELECT d.fecha + INTERVAL 10 HOUR AS 'time',
           d.valorCorregido AS 'R3'
    FROM d_r3 AS d
    INNER JOIN estaciones AS e ON d.idEstacion = e.id
    WHERE e.NombreEstacion = '{nombre_estacion}'
      AND d.fecha BETWEEN FROM_UNIXTIME({epoch_from_s}) + INTERVAL 3 HOUR
                       AND FROM_UNIXTIME({epoch_to_s}) + INTERVAL 3 HOUR
    """

    # === 5. Payload para el query de datos ===
    query_payload = {
        "queries": [
            {
                "refId": "A",
                "datasource": {
                    "type": "mysql",
                    "uid": "000000028"
                },
                "rawSql": raw_sql,
                "format": "time_series",
                "datasourceId": 28,
                "intervalMs": 43200000,
                "maxDataPoints": 275
            }
        ],
        "from": str(epoch_from),
        "to": str(epoch_to)
    }

    # === 6. Enviar request a /api/ds/query ===
    url_datos = "https://sistemas.inumet.gub.uy/api/ds/query?ds_type=mysql&requestId=Q100"
    response_datos = session.post(url_datos, json=query_payload, headers=headers)

    print(f"Query status para {nombre_estacion}:", response_datos.status_code)

    if response_datos.status_code == 200:
        data = response_datos.json()
        try:
            timestamps = data["results"]["A"]["frames"][0]["data"]["values"][0]
            valores = data["results"]["A"]["frames"][0]["data"]["values"][1]
            fechas = [datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d") for ts in timestamps]
            df = pd.DataFrame({
                "fecha": fechas,
                "valor": valores
            })
            nombre_archivo = nombre_estacion.replace(" ", "_") + ".csv"
            ruta_salida = os.path.join(r"C:\Tiago\3_Series_Hitoricas", nombre_archivo)
            df.to_csv(ruta_salida, index=False, encoding="utf-8")
            print(f"CSV guardado en: {ruta_salida}")
        except Exception as e:
            print(f"Error procesando datos para {nombre_estacion}: {e}")
    else:
        print(f"Error en la consulta para {nombre_estacion}")
    
    # Pausa entre estaciones para evitar bloqueos
    time.sleep(random.uniform(2, 5))