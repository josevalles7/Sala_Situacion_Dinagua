import requests
from datetime import datetime
import time
import random
import pandas as pd
import os

# Crear sesión
session = requests.Session()

# Login
url_login = "https://sistemas.inumet.gub.uy/login"
payload_login = {
    "user": "telepluvio",
    "password": "telepluvio"
}
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
time.sleep(random.uniform(8, 15)) 
#---------------------------------------------------------------------------------------------------------------

# Elegir fechas
fecha_inicio_str = "2025-03-01 00:00:00"
fecha_fin_str = "2025-05-15 00:00:00"

# Convertir a epoch en milisegundos
fmt = "%Y-%m-%d %H:%M:%S"
epoch_from = int(datetime.strptime(fecha_inicio_str, fmt).timestamp() * 1000)
epoch_to = int(datetime.strptime(fecha_fin_str, fmt).timestamp() * 1000)

# Estaciones
nombres_estaciones = [
    "Chacra Policial"
]
for nombre_estacion in nombres_estaciones:

    # Payload JSON para la consulta
    payload = {
        "queries": [
            {
                "alias": "5 minutal",
                "bucketAggs": [
                    {
                        "field": "timestamp",
                        "id": "2",
                        "settings": {"interval": "5m", "min_doc_count": 0, "trimEdges": 0},
                        "type": "date_histogram"
                    }
                ],
                "datasource": {"type": "elasticsearch", "uid": "000000056"},
                "metrics": [
                    {
                        "field": "rtuRain",
                        "id": "1",
                        "meta": {},
                        "settings": {},
                        "type": "sum"
                    }
                ],
                "query": f"locality.keyword :{nombre_estacion} AND (_exists_:rtuRain AND (rtuRain:[0 TO 0.001] OR rtuRain:{{0.005 TO 15}}))",
                "refId": "A",
                "timeField": "timestamp",
                "datasourceId": 56,
                "intervalMs": 300000,
                "maxDataPoints": 1000
            }
        ],
        "from": str(epoch_from),
        "to": str(epoch_to)
    }

    url_query = "https://sistemas.inumet.gub.uy/api/ds/query?ds_type=elasticsearch&requestId=Q105"

    headers_query = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://sistemas.inumet.gub.uy",
        "Referer": "https://sistemas.inumet.gub.uy",
    }

    response = session.post(url_query, json=payload, headers=headers_query)

    if response.ok:
        data = response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")

    # Extraer listas de fecha y precip
    valores_tiempo = data['results']['A']['frames'][0]['data']['values'][0]
    valores_lluvia = data['results']['A']['frames'][0]['data']['values'][1]

    # Convertir timestamps (milisegundos) a datetime en formato yyyy-mm-dd HH:mm
    fechas = [datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M') for ts in valores_tiempo]

    # Crear DataFrame
    df = pd.DataFrame({
        'fecha': fechas,
        'valor': pd.Series(valores_lluvia).round(2) # Redondear los valores
    })

    # Guardar a CSV
    ruta_salida = os.path.join(r"C:\Tiago\3_Series_Hitoricas\Estaciones_Santa_Lucia\03-2025_05-2025\Telepluv", nombre_estacion + ".csv")
    df.to_csv(ruta_salida, index=False, encoding="utf-8")

    print("CSV creado con éxito para estación:", nombre_estacion)
    # Pausa entre estaciones para evitar bloqueos
    time.sleep(random.uniform(8, 15))