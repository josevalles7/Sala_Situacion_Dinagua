# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 12:48:32 2024

@author: tiago
"""

import pandas as pd
import numpy as np
import datetime
from netCDF4 import Dataset

# Abre el archivo NetCDF
archivo_nc = r'C:\Tiago\2_FEWS\FEWS-UY\trunk\FEWS-UY\Uruguay\Modules\wflow\wflow_sbm_SantaLucia_diario\inmaps.nc'
dataset = Dataset(archivo_nc, 'r')  # 'r' es para abrirlo en modo de solo lectura
# Mostrar las variables disponibles en el archivo
#print(dataset.variables.keys())

# Accede a la variable de precipitación y tiempo
precip = dataset.variables['precip']
time = dataset.variables['time']
#print(precip.dimensions)
#print(time.dimensions)

# Imprime algunos metadatos
#print(precip.units)
#print(time.ncattrs())
print(time.units)#OBSERVAR LA FECHA DE TIME.UNITS

# Convertir minutos desde la fecha base a datetime
start_date = datetime.datetime(1970, 1, 1, 0, 0, 0)#UTILIZAR LA FECHA DE TIME.UNITS
fechas = [start_date + datetime.timedelta(minutes=float(m)) for m in time[:]]#USAR EL PASO DE TIEMPO DE TIME.UNITS

# Extrae los datos de precipitación
datos_precip = precip[:]

# Calcular el promedio espacial para cada paso de tiempo
promedio_espacial = np.mean(datos_precip, axis=(1, 2))

# Crear un DataFrame con fechas como índice
df_promedio = pd.DataFrame(data=promedio_espacial, index=fechas, columns=['precip_promedio'])

# Identificar las fechas sin datos (donde 'precip_promedio' es NaN)
fechas_sin_datos = df_promedio[df_promedio['precip_promedio'].isna()].index

# Si hay fechas sin datos, identificar los intervalos
if not fechas_sin_datos.empty:
    intervalos = []
    inicio_intervalo = fechas_sin_datos[0]

    for i in range(1, len(fechas_sin_datos)):
        # Si la fecha actual no es consecutiva con la anterior, cerramos el intervalo
        if fechas_sin_datos[i] != fechas_sin_datos[i - 1] + pd.Timedelta(days=1):
            fin_intervalo = fechas_sin_datos[i - 1]
            intervalos.append((inicio_intervalo, fin_intervalo))
            inicio_intervalo = fechas_sin_datos[i]

    # Añadir el último intervalo
    intervalos.append((inicio_intervalo, fechas_sin_datos[-1]))

    # Printar los intervalos sin datos
    for intervalo in intervalos:
        print(f"Faltan datos desde {intervalo[0]} hasta {intervalo[1]}")
else:
    print("No hay fechas sin datos.")
