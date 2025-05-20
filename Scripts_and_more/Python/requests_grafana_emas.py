import requests
from datetime import datetime, timezone
import time
import random
import pandas as pd
import os


# Crear una sesión para mantener las cookies
session = requests.Session()

# URL de login
url_login = "https://sistemas.inumet.gub.uy/login"

# Datos de login
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
# Una pequeña pausa no sospechosa
time.sleep(random.uniform(5, 8)) 
#---------------------------------------------------------------------------------------------------------------

# === Lista de estaciones ===
nombres_estaciones = [
    "Lavalleja G3"
]

# === Elegir fechas y convertir a milisegundos y segundos epoch ===

fecha_inicio_str = "2025-03-01 00:00:00"
fecha_fin_str = "2025-05-15 00:00:00"

fmt = "%Y-%m-%d %H:%M:%S"
epoch_from = int(datetime.strptime(fecha_inicio_str, fmt).timestamp() * 1000)
epoch_to = int(datetime.strptime(fecha_fin_str, fmt).timestamp() * 1000)

epoch_from_s = epoch_from // 1000
epoch_to_s = epoch_to // 1000

# Bucle de consulta 

for nombre_estacion in nombres_estaciones:
    # === Armar SQL personalizado ===
    raw_sql = f"""
    SELECT d.fecha AS 'time', d.valorCorregido AS '5 minutal'
    FROM d_precip5min AS d
    INNER JOIN estaciones AS e ON d.idEstacion=e.id
    WHERE e.NombreEstacion='{nombre_estacion}'
    AND d.fecha BETWEEN FROM_UNIXTIME({epoch_from_s}) + INTERVAL 3 HOUR
    AND FROM_UNIXTIME({epoch_to_s}) + INTERVAL 3 HOUR;
    """

    # === Payload para el query de datos ===
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
                "intervalMs": 300000,
                "maxDataPoints": 335
            }
        ],
        "from": str(epoch_from),
        "to": str(epoch_to)
    }

    # === Enviar request a /api/ds/query ===
    url_datos = "https://sistemas.inumet.gub.uy/api/ds/query?ds_type=mysql&requestId=Q104"
    
    response_datos = session.post(url_datos, json=query_payload, headers=headers)

    print(f"Query status para {nombre_estacion}:", response_datos.status_code)

    if response_datos.status_code == 200:
        data = response_datos.json()
        try:
            timestamps = data["results"]["A"]["frames"][0]["data"]["values"][0]
            valores = data["results"]["A"]["frames"][0]["data"]["values"][1]
            fechas = [datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d") for ts in timestamps]
            df = pd.DataFrame({
                "fecha": fechas,
                "valor": valores
            })
            nombre_archivo = "ema_" + nombre_estacion.replace(" ", "_") + ".csv"
            # === Alterar ruta de salida ===
            ruta_salida = os.path.join(r"C:\Tiago\3_Series_Hitoricas\Estaciones_Santa_Lucia\03-2025_05-2025\EMA", nombre_archivo)
            df.to_csv(ruta_salida, index=False, encoding="utf-8")
            print(f"CSV guardado en: {ruta_salida}")
        except Exception as e:
            print(f"Error procesando datos para {nombre_estacion}: {e}")
    else:
        print(f"Error en la consulta para {nombre_estacion}")
    
    # Pausa entre estaciones para evitar bloqueos
    time.sleep(random.uniform(5, 10))