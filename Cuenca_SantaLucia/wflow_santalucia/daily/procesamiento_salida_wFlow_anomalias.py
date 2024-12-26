#@author: tiago

"""etapa1: selecciona un archivo NetCDF de salida del modelo wflow, estpa 2:extrae la variable q_river, estapa 3:acumula los valores diarios a mensuales,
etapa 4:calcula las anomalias mensuales y estapa 5: exporta la anomalia mensual a un raster.tiff"""

import matplotlib.pyplot as plt
from netCDF4 import Dataset, num2date, date2num
from datetime import datetime, timedelta
import numpy as np
import os
import rasterio
from rasterio.transform import from_origin

### ETAPA 1: EXTRAE Q_RIVER DEL ARCHIVO DE SALIDA DE WFLOW ###
# Abre el archivo NetCDF ----------------CAMBIAR RUTA----------------
archivo_nc = r'C:\Tiago\2_FEWS\FEWS-UY\trunk\FEWS-UY\Uruguay\Modules\wflow\wflow_sbm_SantaLucia_diario\run_default\output.nc'
dataset = Dataset(archivo_nc, 'r')  # 'r' es para abrirlo en modo de solo lectura
# Mostrar las variables disponibles en el archivo
#print(dataset.variables.keys())
#print("\n")

# Selecciona la variable 'q_river'
var = dataset.variables['q_river']

#Seleccionar rango de tiempo de la variable (si queres elegir 01-12-2024 - 31-12-2024 utilizar 2-12-2024 - 02-01-2025)
time_var = dataset.variables['time']
fecha_base = datetime(1900, 1, 1, 7, 0, 0)
fecha_inicio = datetime(2020, 11, 2)
fecha_fin = datetime(2024, 12, 2)

dias_inicio = (fecha_inicio - fecha_base).days
dias_fin = (fecha_fin - fecha_base).days

idx_inicio = (time_var[:] >= dias_inicio).argmax()
idx_fin = (time_var[:] <= dias_fin).argmin()

# Selecciona el rango de tiempo en la variable 'q_river'
q_river_periodo = var[idx_inicio:idx_fin, :, :]
"""
print("Forma de q_river_periodo:", q_river_periodo.shape)
print("Tipo de q_river_periodo:", type(q_river_periodo))
print("Primeros valores de q_river_periodo:\n", q_river_periodo[1000, :, :])
"""
# donde guardar el archivo de salida ----------------CAMBIAR RUTA----------------
directorio = r"C:\Tiago\1_Cuenca_Santa_Lucia\3_Estados_WFLOW\1_q_river_aislada"
nombre_archivo = f"q_river_{fecha_inicio.year}_{fecha_fin.year}.nc"
ruta_archivo = os.path.join(directorio, nombre_archivo)

nc_salida = Dataset(ruta_archivo, 'w', format='NETCDF4')

# Crea las dimensiones (tiempo, latitud, longitud) basadas en las dimensiones de q_river_periodo
nc_salida.createDimension('time', q_river_periodo.shape[0])
nc_salida.createDimension('lat', q_river_periodo.shape[1])
nc_salida.createDimension('lon', q_river_periodo.shape[2])

# Crea las variables para tiempo, latitud y longitud, y luego las rellena
times = nc_salida.createVariable('time', 'f4', ('time',))
lats = nc_salida.createVariable('lat', 'f4', ('lat',))
lons = nc_salida.createVariable('lon', 'f4', ('lon',))

# Ayustar la ubicación
lats[:] = dataset.variables['lat'][:] * -1 - 69.6875 #ayste para proyetar la cuenca
lons[:] = dataset.variables['lon'][:]

# Rellena la variable de tiempo
times[:] = time_var[idx_inicio:idx_fin]

# Crea la variable para q_river_periodo
q_river_var = nc_salida.createVariable('q_river', 'f4', ('time', 'lat', 'lon'), zlib=True)
q_river_var[:, :, :] = q_river_periodo  # Guarda los datos en la nueva variable

# Agrega atributos a las variables (opcional)
q_river_var.units = 'm3/s'
lats.units = 'degrees_north'
lons.units = 'degrees_east'
times.units = 'days since 1900-01-01 07:00:00'

# Cierra el archivo NetCDF
nc_salida.close()

### ETAPA 2: EMPIEZA PROCESO DE ACUMULACION MENSUAL DE Q_RIVER ###

# Abre el archivo NetCDF con q_river aislada
dataset = Dataset(ruta_archivo, 'r')  # 'r' es para abrirlo en modo de solo lectura

q_river = dataset.variables['q_river'][:] 
time = dataset.variables['time'][:]
time_units = dataset.variables['time'].units
time_calendar = dataset.variables['time'].calendar if hasattr(dataset.variables['time'], 'calendar') else 'standard'
lat = dataset.variables['lat'][:]
lon = dataset.variables['lon'][:]

# Convierte las fechas de la variable 'time' a formato datetime
fechas = num2date(time, units=time_units, calendar=time_calendar)
#print(fechas)

# Crear un diccionario para almacenar los promedios mensuales por lat-lon
promedios_mensuales = {}

# Iterar sobre las fechas y datos de 'q_river'
for i, fecha in enumerate(fechas):
    anio_mes = (fecha.year, fecha.month)
    
    # Si el año-mes no está en el diccionario, lo inicializamos
    if anio_mes not in promedios_mensuales:
        promedios_mensuales[anio_mes] = []
    
    # Añadimos el valor de 'q_river' para este tiempo (lat, lon) a la lista correspondiente
    promedios_mensuales[anio_mes].append(q_river[i, :, :])

# Calcular el promedio mensual por lat-lon para cada mes
promedios_mensuales_final = {}
for anio_mes, valores in promedios_mensuales.items():
    # Convertir la lista de arrays (diarios) a un array numpy y calcular el promedio mensual para cada lat-lon
    valores_np = np.array(valores)
    promedio_mensual = np.mean(valores_np, axis=0)
    promedios_mensuales_final[anio_mes] = promedio_mensual

# Crear el nuevo archivo NetCDF con promedios mensuales ----------------CAMBIAR RUTA----------------
archivo_mensual = r"C:\Tiago\1_Cuenca_Santa_Lucia\3_Estados_WFLOW\q_river_promedio_mensual_2020_2024.nc"

with Dataset(archivo_mensual, 'w') as nc_mensual:
    # Crea las dimensiones
    nc_mensual.createDimension('time', len(promedios_mensuales_final))
    nc_mensual.createDimension('lat', len(lat))
    nc_mensual.createDimension('lon', len(lon))
    
    # Crea las variables
    times = nc_mensual.createVariable('time', 'f4', ('time',))
    lats = nc_mensual.createVariable('lat', 'f4', ('lat',))
    lons = nc_mensual.createVariable('lon', 'f4', ('lon',))
    q_river_var = nc_mensual.createVariable('q_river', 'f4', ('time', 'lat', 'lon'))

    # Escribe las coordenadas espaciales
    lats[:] = lat
    lons[:] = lon
    print("Meses incluidos:", list(promedios_mensuales_final.keys()))
    # Convierte las fechas a números (en formato 'days since ...') para el nuevo archivo NetCDF
    fechas_mensuales = [datetime(anio, mes, 15) for (anio, mes) in promedios_mensuales_final.keys()]
    times[:] = date2num(fechas_mensuales, units=time_units, calendar=time_calendar)
    print("Fechas mensuales generadas:", fechas_mensuales)
    # Escribe los datos del promedio mensual en el archivo
    for i, (anio_mes, promedio_mensual) in enumerate(promedios_mensuales_final.items()):
        print(f"Escribiendo datos de {anio_mes} en índice {i} -> Fecha: {fechas_mensuales[i]}")
        q_river_var[i, :, :] = promedio_mensual

    # Añade atributos de tiempo
    times.units = time_units
    times.calendar = time_calendar

#print(f"Archivo con promedios mensuales creado: {archivo_mensual}")

### ETAPA 3: DIVIDIR LOS PROMEDIOS MENSUALES POR EL PROMEDIO MENSUAL HISTÓRICO Y OBETENER NOMLIAS ###

# ----------------CAMBIAR RUTA----------------
archivo_promedio_por_mes = r"C:\Tiago\1_Cuenca_Santa_Lucia\3_Estados_WFLOW\q_river_promedio_mensual_1991_2020.nc" #archivo de promedio mensual histórico para q_river, está en el github 
archivo_anomalia = r"C:\Tiago\1_Cuenca_Santa_Lucia\3_Estados_WFLOW\3_seguimineto_estados2024\q_river_division_mensual_por_promedio.nc"

# Abre ambos archivos NetCDF
with Dataset(archivo_mensual, 'r') as nc_mensual, Dataset(archivo_promedio_por_mes, 'r') as nc_historico:
    # Leer las variables necesarias de ambos archivos
    q_river_mensual = nc_mensual.variables['q_river'][:] 
    time_mensual = nc_mensual.variables['time'][:]
    time_units_original = nc_mensual.variables['time'].units
    time_calendar = nc_mensual.variables['time'].calendar if hasattr(nc_mensual.variables['time'], 'calendar') else 'standard'
    lat_mensual = nc_mensual.variables['lat'][:]
    lon_mensual = nc_mensual.variables['lon'][:]
    q_river_por_mes = nc_historico.variables['q_river'][:] 

    # Cambiar la referencia de tiempo al día 15 del mes
    time_units_adjusted = "days since 1900-01-15 00:00:00" #se adelanta la fecha base para que coincidan los valores de promedio mensual con las fechas correspondentes
    fechas_mensuales = num2date(time_mensual, units=time_units_adjusted, calendar=time_calendar)

        # Crear un nuevo archivo NetCDF para guardar los resultados
    with Dataset(archivo_anomalia, 'w') as nc_anomalia:
        # Crear dimensiones
        nc_anomalia.createDimension('time', len(time_mensual))
        nc_anomalia.createDimension('lat', len(lat_mensual))
        nc_anomalia.createDimension('lon', len(lon_mensual))

        # Crear variables
        times = nc_anomalia.createVariable('time', 'f4', ('time',))
        lats = nc_anomalia.createVariable('lat', 'f4', ('lat',))
        lons = nc_anomalia.createVariable('lon', 'f4', ('lon',))
        q_river_div = nc_anomalia.createVariable('q_river', 'f4', ('time', 'lat', 'lon'))

        # Escribir coordenadas
        lats[:] = lat_mensual
        lons[:] = lon_mensual
        times[:] = time_mensual 
        times.units = time_units_adjusted  # Aplicar la nueva referencia
        if hasattr(nc_anomalia.variables['time'], 'calendar'):
            times.calendar = nc_anomalia.variables['time'].calendar

        # Iterar sobre los tiempos y dividir los valores mensuales por el promedio correspondiente
        for i, fecha_actual in enumerate(fechas_mensuales):
            mes_actual = fecha_actual.month  # Extraer el mes ajustado
            q_river_div[i, :, :] = q_river_mensual[i, :, :] / q_river_por_mes[mes_actual - 1, :, :]

        print(f"Archivo de salida generado: {archivo_anomalia}")

###ETAPA 5: EXPORTAR ANOMALIAS MENSUALES A ARCHIVOS RASTER.TIFF ##

dataset = Dataset(archivo_anomalia, 'r') 

# Obtener la variable de tiempo y convertirla a fechas legibles
time_var = dataset.variables['time']
time_units = time_var.units  # Unidades de la variable de tiempo
time_calendar = time_var.calendar if hasattr(time_var, 'calendar') else 'standard'

# Convertir los valores de tiempo a fechas
fechas = num2date(time_var[:], units=time_units, calendar=time_calendar)

num_tiempos = len(time_var)
#print(f"Número de pasos de tiempo disponibles: {num_tiempos}")

# Selecciona la variable 'q_river'
var1 = dataset.variables['q_river']
name = "q_river"

# Obtener las dimensiones espaciales (latitud y longitud)
latitudes = dataset.variables['lat'][:]
longitudes = dataset.variables['lon'][:]

# Definir la resolución y la transformación (puede necesitar ajustes según tus datos)
resolucion_x = (longitudes[-1] - longitudes[0]) / len(longitudes)
resolucion_y = (latitudes[-1] - latitudes[0]) / len(latitudes)
transform = from_origin(longitudes[0], latitudes[0], resolucion_x, resolucion_y)

# Bucle para exportar un archivo TIFF para cada paso de tiempo
for dia_especifico in range(num_tiempos):
    # Extraer la fecha correspondiente al día seleccionado
    fecha_seleccionada = fechas[dia_especifico]
    fecha_str = fecha_seleccionada.strftime('%Y-%m')  # Formato deseado para el nombre de archivo
    print(f"Exportando el GeoTIFF correspondiente a la fecha: {fecha_str}")
    
    # Extrae los datos para el día seleccionado
    datos_var1 = var1[dia_especifico, :, :]
    
    # Reemplazar valores mayores a 1000000 por NaN, asumiendo que representan datos nulos
    datos_var1 = np.where(datos_var1 > 1000000, np.nan, datos_var1)
    
    # Elegir local de guardado ----------------CAMBIAR RUTA----------------
    ruta_salida = fr'C:\Tiago\1_Cuenca_Santa_Lucia\3_Estados_WFLOW\3_seguimineto_estados2024\Estados_tiff\SL_estado_hidrologico_{fecha_str}.tif'
    
    # Escribir el archivo TIFF
    with rasterio.open(
        ruta_salida,
        'w',
        driver='GTiff',
        height=datos_var1.shape[0],
        width=datos_var1.shape[1],
        count=1,
        dtype=datos_var1.dtype,
        crs='+proj=latlong',
        transform=transform,
        nodata=np.nan,  # Definir el valor 'nodata' para el archivo TIFF
    ) as dst:
        dst.write(datos_var1, 1)
    
    #print(f"Exportación completada para: {ruta_salida}")

print("Exportación de todos los archivos GeoTIFF completada.")
