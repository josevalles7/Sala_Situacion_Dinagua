#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 19 11:24:27 2022

@author: fernando.penades
"""

import requests
import json
from datetime import datetime, timedelta
import sys

def acomodarFecha(ts):
# Quita 3 ceros al final y convierte de timestap a datetime
    dt = datetime.fromtimestamp(ts/1000).replace(second=0)
    return dt

# URL donde se realiza el login para obtener una cookie
url_login = 'https://sistemas.inumet.gub.uy/login'
# URL de donde se consulta la información sobre Convencionales y EMAs
url = "https://sistemas.inumet.gub.uy/api/tsdb/query"

# Datos que se enviarán en el request de login
payload = {"user":"******","email":"","password":"******"}
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}

# Se realiza el login y se obtine la cookie "grafana_session"
print("Realizando login...\n")
response = requests.request("POST", url_login, headers=headers, data=payload)
if response.ok:
    print("Login exitoso")
else:
    print("Login incorrecto: " + response.text.replace('"}', '')[12:])
    sys.exit()

# headers con la cookie para realizar las consultas
headers = {
  'Cookie': f"grafana_session={response.cookies.get('grafana_session')}",
  'Content-Type': 'application/json',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
}

############################################
#   PERÍODO DE PRECIPITACIONES             #
#   Fechas yyyy-mm-dd hh:mm                #
#   tipoEstacion convencional, ema, tp     #
############################################
fecha_inicio = '1980-01-01 00:00'    
fecha_fin = '2022-12-31 00:00'
tipoEstacion = 'convencional'
estacion = ''
############################################
# Si se deja vacío el nombre de la estación, se desplegará una lista de todas las estaciones disponibles
# para la categoría seleccionada y se pedirá que seleccione el número de la estación deseada

# En el caso de "estación" esté vacío, se realiza un procedimiento para listar las estaciones y perimitir seleccionar una
if estacion == '':
    # El valor de "automática" se usara en el payload para indicar cuales estaciones se listarán
    # Las automáticas son las tp y las ema, mientras que no automáticas son las convecionales
    automatica = tipoEstacion.lower() != 'convencional' and tipoEstacion.lower() != 'convencionales'
    payload = json.dumps({
        "queries": [
            {
                "refId": "r3",
                "datasourceId": 28,
                "rawSql": f"SELECT e.NombreEstacion FROM estaciones AS e WHERE e.activa=1 AND e.automatica={automatica} AND e.tipoExterna=0",
                "format": "table"
            }
        ],
        "from": "1577847600000",
        "to": "1580525940000"
    })
    
    # Se realiza la consulta para obtener la lista de estaciones 
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    # Se parsea el JSON de respuesta para sacar los datos de las estaciones
    lista = data.get('results').get('r3').get('tables')[0].get('rows')    
    lista.sort()
    i = 0
    estaciones = []
    num_str = []
    # Se imprimen los nombres de las estaciones con un número correlativo
    for l in lista:
        estaciones += l
    
    # resp = ''
    # print('Ingrese el número correspondiente a la estación deseada:')
    # # Se solicita al usuario ingresar el número correspondiente a la estación deseada
    # while not resp in num_str:
    #     resp = input()
    #     # Minetras no se ingrese un número correcto, se sigue solicitando
    #     if not resp in num_str:
    #         print(f'Debe ingresar un número entero entre 1 y {len(estaciones)}')
    # num_est = int(resp)
    # # Se guarda el nombre de la estación seleccionada
    # estacion = estaciones[num_est-1][1]
    # print(f'\nUsted seleccionó la estación {estacion}\n')
for estacion in estaciones:
    if estacion == 'Laguna del Sauce - Aeropuerto Internacional C/C Carlos A. Curbelo':
        estacion = 'Laguna del Sauce - Aeropuerto Internacional Carlos Curbelo'
    print('Estación actual: ' + estacion)
    # Se obtine el timestamp de inicio para enivar en el post
    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d %H:%M')
    tsInicio = str(int(datetime.timestamp(inicio)*1000))
    # Las primeras lineas que se escribiran en el archivo de salida
    linea1 = 'Location Names,' + estacion
    linea2 = 'Location Ids,' + estacion
    linea3 = 'Time,Precipitaciones'
    
    # La fuente y la forma de obtener lo datos es difernte si el tipo de estación es telepluviómetro
    if tipoEstacion.lower() == 'tp' or tipoEstacion.lower() == 'tps':
        # URL de donde se obtienen los datos de telepluviómetros
        url = "https://sistemas.inumet.gub.uy/api/datasources/proxy/56/_msearch?max_concurrent_shard_requests=256"
        carpeta = 'TPs'
        # Se elimina el " (TP)" que viene en el nombre
        est = estacion.replace(' (TP)', '').replace(' ', '\\\\ ')
        # Los datos se van tomando de a 30 días porque el servidor no devuelve más de 10.000 datos
        fin = inicio + timedelta(days = 30)
        tsFin = str(int(datetime.timestamp(fin)*1000))
        # Se abre un archivo con el nombre de la estación en la carpeta "TPs"
        with open(f'{carpeta}/'f'{estacion}.csv', 'w') as f:
            # Se imprimen las tres primeras líneas del archivo
            f.write(linea1 + '\n')
            f.write(linea2 + '\n')
            f.write(linea3 + '\n')
            # Se repite el procedimiento de obtener 30 días de datos hasta que se llegue a la fecha actual
            while inicio < datetime.now():
                # Se forma el payload que se enviará en la consulta
                # Se usan los timestamp de incio y fin, así como el nombre de la estación
                parte1 = {"search_type":"query_then_fetch","ignore_unavailable":True,"index":"*iot*"}
                parte2 = {"size":10000,"query":{"bool":{"filter":[{"range":{"timestamp":{"gte":f"{tsInicio}","lte":f"{tsFin}","format":"epoch_millis"}}},
                          {"query_string":{"analyze_wildcard":True,"query":f"locality.keyword :{est}"" AND (_exists_:rtuRain AND (rtuRain:[0 TO 0.001} OR rtuRain:{0.005 TO 15]))"}}]}},
                          "sort":{"timestamp":{"order":"desc","unmapped_type":"boolean"}},"script_fields":{},"docvalue_fields":["timestamp"]}
                
                payload1 = json.dumps(parte1)
                payload2 = json.dumps(parte2)
                payload = payload1 + "\n" + payload2 + "\n"
                
                # Se realiza la consulta
                print('Consultando datos desde el ' + str(inicio.strftime('%Y-%m-%d')) + ' hasta el ' + str(fin.strftime('%Y-%m-%d')) + "...")
                response = requests.request("POST", url, headers=headers, data=payload)
                data = response.json()
                # Se parsea el JSON de respuesta para sacar los datos de precipitaciones
                datos = data.get('responses')[0].get('hits').get('hits')
                
                # Se voltea el orden de la lista, porque viene ordenada por fecha de mayor a menor
                lista = []
                for d in datos:
                    lista.insert(0, d)
                
                # Se recorre la lista de fechas y su valor de precipitaciones
                for l in lista:
                    # Se obtiene la fecha y se parsea
                    tiempo = l.get('_source').get('rtuTimestamp')
                    tiempo = tiempo[0:10] + ' ' + tiempo[11:19]
                    # Se obtine el valor de precipitaciones 
                    prec = l.get('_source').get('rtuRain')
                    # Se imprime una línea en el archivo con la fecha y su valor de precipitación correspondiente
                    f.write(tiempo + ',' + str(prec) + '\n')
                # Para la siguiente iteración, se mira 5 minutos después de la última fecha de fin y 30 días para adelante
                inicio = fin + timedelta(minutes = 5)
                fin = inicio + timedelta(days = 30)
                tsInicio = str(int(datetime.timestamp(inicio)*1000))
                tsFin = str(int(datetime.timestamp(fin)*1000))
    # La fuente y la forma de obtener lo datos es difernte si el tipo de estación es convencional o EMA
    else:
        # En este caso los datos se consultarán de una sola vez, por lo cual se usa como fecha de fin la ingresada por el usuario
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d %H:%M')
        tsFin = str(int(datetime.timestamp(fin)*1000))
        # Si bien convencionales y EMAs tienen en común que los datos se obtienen de una vez y desde la misma fuente,
        # varían en el payload que se deberá enviar para realizar la consulta
        if tipoEstacion.lower() == 'convencional' or tipoEstacion.lower() == 'convencionales':
            # Se crea el payload, usando los timestamp de inicio y fin y el nombre de la estación
            payload = json.dumps({
                "from": f"{tsInicio}",
                "to": f"{tsFin}",
                "queries": [
                    {
                        "refId": "A",
                        "intervalMs": 10800000,
                        "maxDataPoints": 200,
                        "datasourceId": 28,
                        "rawSql": "SELECT d.fecha + INTERVAL 10 HOUR AS 'time', d.valorCorregido AS 'r3'\nFROM d_r3 AS d\nINNER JOIN "\
                        f"estaciones AS e ON d.idEstacion=e.id\n WHERE e.NombreEstacion='{estacion}' AND d.fecha BETWEEN $__timeFrom() + INTERVAL 3 HOUR AND $__timeTo() + INTERVAL 3 HOUR",
                        "format": "time_series"
                    }
                ]
            })
            linea3 = 'Time,Precipitaciones - Acumulado diario'
            carpeta = 'Convencionales'
        elif tipoEstacion.lower() == 'ema' or tipoEstacion.lower() == 'emas':
            # Se crea el payload, usando los timestamp de inicio y fin y el nombre de la estación
            payload = json.dumps({
                "from": f"{tsInicio}",
                "to": f"{tsFin}",
                "queries": [
                    {
                        "refId": "A",
                        "intervalMs": 10800000,
                        "maxDataPoints": 211,
                        "datasourceId": 28,
                        "rawSql": "SELECT d.fecha AS 'time', d.valorCorregido AS '5 minutal'\nFROM d_precip5min AS d\nINNER JOIN estaciones AS "\
                        f"e ON d.idEstacion=e.id\nWHERE e.NombreEstacion='{estacion}' AND d.fecha BETWEEN $__timeFrom() + INTERVAL 3 HOUR AND $__timeTo() + INTERVAL 3 HOUR;",
                        "format": "time_series"
                    }
                ]
            })
            linea3 = 'Time,Precipitaciones'
            carpeta = 'EMAs'
        # Se imprime una línea en el archivo con la fecha y su valor de precipitación correspondiente
        # Se realiza la consulta    
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        # Se parsea el JSON de respuesta para sacar los datos de precipitaciones
        print("Consultando datos...")
        if (data.get('results').get('A').get('series') != None):
            datos = data.get('results').get('A').get('series')[0].get('points')
            
            linea1 = 'Location Names,' + estacion
            linea2 = 'Location Ids,' + estacion
            
            # Se abre un archivo con el nombre de la estación en la carpeta "Convencionales" o "EMAs", según correspondiente
            with open(f'{carpeta}/'f'{estacion}.csv', 'w') as f:
                print("Imprimiendo datos en el archivo...")
                f.write(linea1 + '\n')
                f.write(linea2 + '\n')
                f.write(linea3 + '\n')
                for d in datos:
                    tiempo = str(acomodarFecha(d[1]))
                    # Se imprime una línea en el archivo con la fecha y su valor de precipitación correspondiente
                    f.write(tiempo + ',' + str(d[0]) + '\n')
    print("\nFinalizado")


















