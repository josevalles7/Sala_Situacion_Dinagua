# %%
import requests
from datetime import datetime, timezone, timedelta
import time
import random
import pandas as pd
import os
import argparse

# %%
# from the current folder, import convencionales_ids.csv
estaciones_ids = pd.read_csv("./stations/ids/convencionales_ids.csv", encoding='utf-8')
# from the N_OFICIAL row remove the prefix INUMET-
estaciones_ids['N_OFICIAL'] = estaciones_ids['N_OFICIAL'].str.replace('INUMET-', '', regex=False)   
# CREATE A SUBSET OF THE DATAFRAME WITH ONLY BOLETINES TRUE
estaciones_sel = estaciones_ids[estaciones_ids['BOLETINES'] == True]
# create a dict from estaciones N_OFICIAL AND NOMBRE_GRAFANA 
estaciones = dict(zip(estaciones_sel['N_OFICIAL'], estaciones_sel['NOMBRE_GRAFANA']))

# %%
# Define arguments

parser = argparse.ArgumentParser(
                    prog='download forcing data for bulletin',
                    description='Downloads forcing data for bulletin',
                    epilog='Jose Valles, DINAGUA, 15062026')

#
parser.add_argument('fecha_inicio', help='provide the start date for the data in YYYY-MM-DD format')
parser.add_argument('fecha_fin', help='provide the end date for the data in YYYY-MM-DD format')

args = parser.parse_args()
'''

args = argparse.Namespace(
    fecha_inicio ='2026-05-01',
    fecha_fin ='2026-05-31'
)
'''

# %%
fecha_inicio = (datetime.strptime(args.fecha_inicio, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')  # Subtract one day from the start date
fecha_fin = args.fecha_fin

# %%
# Crear una sesión para mantener las cookies
session = requests.Session()

# %%
# URL de login
url_login = "https://sistemas.inumet.gub.uy/login"

# %%
# Datos de login (rellená con tus credenciales)
payload_login = {
    "user": "telepluvio",
    "password": "telepluvio"
}

# %%
# Cabeceras necesarias
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://sistemas.inumet.gub.uy",
    "Referer": "https://sistemas.inumet.gub.uy/login",
    "Accept": "application/json, text/plain, */*"
}

# %%
response_login = session.post(url_login, json=payload_login, headers=headers)
print("Login status:", response_login.status_code)

# %%
nombres_estaciones = list(estaciones.values())

# %%
# === 3. Convertir fechas a milisegundos y segundos epoch ===
def fecha_a_epoch_ms(fecha_str):
    dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

# %%
epoch_from = fecha_a_epoch_ms(fecha_inicio)
epoch_to = fecha_a_epoch_ms(fecha_fin)
epoch_from_s = epoch_from // 1000
epoch_to_s = epoch_to // 1000

# %%
nombre_a_id = {v: k for k, v in estaciones.items()}

resultados = []

for nombre_estacion in nombres_estaciones:
    id = nombre_a_id[nombre_estacion]  # Obtener el código
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
            fechas = [datetime.fromtimestamp(ts / 1000, timezone.utc).date() for ts in timestamps]

            df = pd.DataFrame({
                "fecha": fechas,
                "valor": valores
            })
            df = df.dropna(subset=["valor"])

            dias_con_datos = df["fecha"].nunique()
            acumulado = df["valor"].sum()
            start_date = df["fecha"].min() if not df.empty else None
            end_date = df["fecha"].max() if not df.empty else None

            resultados.append({
                "Estacion": nombre_estacion,
                "StartDate": start_date,
                "EndDate": end_date,
                "Dias con datos": dias_con_datos,
                "Precipitacion acumulada (mm)": round(acumulado, 2)
            })

        except Exception as e:
            print(f"Error procesando datos para {nombre_estacion}: {e}")
    else:
        print(f"Error en la consulta para {nombre_estacion}")

    # Pausa entre estaciones para evitar bloqueos
    time.sleep(random.uniform(2, 5))

df_resultado = pd.DataFrame(resultados)


# %%
# Obtain EMA for Bulletin
nombres_estaciones = [
    "Paso de los Toros G3",
    "Young G3"
]

# %%
# === Elegir fechas y convertir a milisegundos y segundos epoch ===

fecha_inicio_str = (datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d") + " 07:00:00"
fecha_fin_str = (datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=0)).strftime("%Y-%m-%d") + " 07:00:00"

fmt = "%Y-%m-%d %H:%M:%S"
epoch_from = int(datetime.strptime(fecha_inicio_str, fmt).timestamp() * 1000)
epoch_to = int(datetime.strptime(fecha_fin_str, fmt).timestamp() * 1000)

epoch_from_s = epoch_from // 1000
epoch_to_s = epoch_to // 1000

# %%
resultados_ema = []

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
            fechas = [datetime.fromtimestamp(ts / 1000, timezone.utc).date() for ts in timestamps]

            df = pd.DataFrame({
                "fecha": fechas,
                "valor": valores
            })
            df = df.dropna(subset=["valor"])

            # Aggregate 5-minute data to daily totals
            df_daily = df.groupby("fecha")["valor"].sum().reset_index()

            dias_con_datos = df_daily["fecha"].nunique()
            acumulado = round(df_daily["valor"].sum(), 2)
            start_date_val = df_daily["fecha"].min() if not df_daily.empty else None
            end_date_val = df_daily["fecha"].max() if not df_daily.empty else None

            resultados_ema.append({
                "Estacion": nombre_estacion,
                "StartDate": start_date_val,
                "EndDate": end_date_val,
                "Dias con datos": dias_con_datos,
                "Precipitacion acumulada (mm)": acumulado
            })

        except Exception as e:
            print(f"Error procesando datos para {nombre_estacion}: {e}")
    else:
        print(f"Error en la consulta para {nombre_estacion}")

    # Pausa entre estaciones para evitar bloqueos
    time.sleep(random.uniform(5, 10))

df_ema = pd.DataFrame(resultados_ema)


# %%
# Cerrar sesión al finalizar todo el trabajo
session.close()
print("Sesión cerrada correctamente.")


# %%
# Get INIA Stations
URL_BASE = 'https://gras.inia.uy/gras/es/api/'
URL_ESTACIONES = os.path.join(URL_BASE, 'estaciones')
URL_DIARIAS = os.path.join(URL_BASE, 'observaciones-diarias')
URL_VARIABLE_DIARIAS = os.path.join(URL_BASE, 'variables-diarias')

def get_estaciones():
    """Realiza una petición GET a /estaciones."""
    print(f"Consultando: {URL_ESTACIONES}")
    try:
        response = requests.get(URL_ESTACIONES)
        response.raise_for_status()

        print("Estaciones obtenidas con éxito:")
        response.close()
        return pd.DataFrame(response.json())

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error de Conexión: {e}")
    return None


def datos_diarios(estacion: str = None, variable: int = None, start_date: str = None, end_date: str = None):
    """
    Realiza una petición POST a /observaciones-diarias para obtener datos diarios.

    Args:
        estacion (str): Código de la estación.
        variable (int): Código de la variable.
        start_date (str): Fecha de inicio en formato 'YYYY-MM-DD'.
        end_date (str): Fecha de fin en formato 'YYYY-MM-DD'.

    Returns:
        list or None: Lista de observaciones diarias o None si hay un error.
    """
    json_request = {
        "estacion": estacion,
        "variable": variable,
        "fecha_inicial": start_date,
        "fecha_final": end_date
    }

    print(f'Descargando datos diarios para estación: {estacion}, variable: {variable}')
    try:
        # Usamos json=payload para enviar los datos como JSON y setear el Content-Type.
        response = requests.post(URL_DIARIAS, json=json_request)
        response.raise_for_status()  # Lanza una excepción para códigos de error 4xx/5xx

        print("Datos Diarios obtenidos con éxito.")
        print("-" * 45)
        response.close()
        return pd.DataFrame(response.json())

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP ({response.status_code}): No se pudo obtener datos diarios.")
        print(f"Mensaje del servidor: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error de Conexión: {e}")
    return None

def get_variables_diarias():
    """Realiza una petición GET a /variables-diarias."""
    print(f"Consultando: {URL_VARIABLE_DIARIAS}")
    try:
        response = requests.get(URL_VARIABLE_DIARIAS)
        response.raise_for_status()  # Lanza una excepción para códigos de error 4xx/5xx

        print("Variables Diarias obtenidas con éxito:")
        response.close()
        return pd.DataFrame(response.json())

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error de Conexión: {e}")
    return None

# %%
# Consultar las variables_id diarias
variables_diarias = get_variables_diarias()
# Consultar las estaciones
estaciones = get_estaciones()
variables_diarias_importar = variables_diarias[variables_diarias['id_variable'].isin([51, 85])]

# %%
resultados_p = []  # variable 51 - Precipitacion
resultados_e = []  # variable 85 - Evapotranspiracion

for _, estacion_row in estaciones.iterrows():
    station_id = estacion_row['id_zona']
    station_name = estacion_row['nombre'] if 'nombre' in estacion_row.index else station_id

    for _, variable_row in variables_diarias_importar.iterrows():
        variable_id = variable_row['id_variable']

        datos_dia = datos_diarios(
            estacion=station_id,
            variable=variable_id,
            # add one day to start_date to ensure we get all data for the first day
            start_date=(datetime.strptime(fecha_inicio, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
            end_date=fecha_fin
        )
        time.sleep(2)

        if datos_dia is None or datos_dia.empty:
            print(f"-> Sin datos para estación {station_name} variable {variable_id}")
            continue

        # Normalizar columna fecha
        if 'fecha' in datos_dia.columns:
            datos_dia['fecha'] = pd.to_datetime(datos_dia['fecha']).dt.date
        elif 'date' in datos_dia.columns:
            datos_dia = datos_dia.rename(columns={'date': 'fecha'})
            datos_dia['fecha'] = pd.to_datetime(datos_dia['fecha']).dt.date

        # Detectar columna de valor
        value_cols = [c for c in datos_dia.columns if c.lower() not in
                      ('fecha', 'date', 'estacion', 'variable', 'id_estacion', 'id_variable', 'id_zona')]
        if not value_cols:
            print(f"-> No se encontró columna de valor para var {variable_id}")
            continue
        val_col = value_cols[0]

        datos_dia = datos_dia[['fecha', val_col]].dropna(subset=[val_col])

        dias_con_datos = datos_dia['fecha'].nunique()
        total = round(datos_dia[val_col].sum(), 2)
        start_date_val = datos_dia['fecha'].min() if not datos_dia.empty else None
        end_date_val = datos_dia['fecha'].max() if not datos_dia.empty else None

        row = {
            "Estacion": station_name,
            "StartDate": start_date_val,
            "EndDate": end_date_val,
            "Dias con datos": dias_con_datos,
        }

        if variable_id == 51:
            row["Precipitacion total (mm)"] = total
            resultados_p.append(row)
        elif variable_id == 85:
            row["Evapotranspiracion (mm)"] = total
            resultados_e.append(row)

df_inia_p = pd.DataFrame(resultados_p)
df_inia_e = pd.DataFrame(resultados_e)


# %%
# Align column name before concatenating
df_inia_p_renamed = df_inia_p.rename(columns={"Precipitacion total (mm)": "Precipitacion acumulada (mm)"})

# Stack both sources into a single dataframe
df_final = pd.concat([df_resultado, df_inia_p_renamed, df_ema], ignore_index=True)


# %%
df_final.to_csv("PRECIP_Mensuales_boletines.csv", index=False)
df_inia_e.to_csv("EVAPOTRANSPIRACION_Mensuales_boletines.csv", index=False)


