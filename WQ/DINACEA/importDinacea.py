 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 11:21:27 2022

@author: dinagua
"""
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta
import pandas as pd

ini = datetime.now()

# El archivo run_info se puede usar para agregar una fecha de fin, pero no es obligatorio
def get_fecha_run_info(archivo):
    with open(archivo) as f:
        root = ET.parse(f)
        for child in root.iter('*'):
            # Se busca la linea con el tag startDateTime y se arma la fecha con los datos allí indicados
            if child.tag == '{http://www.wldelft.nl/fews/PI}startDateTime':
                fecha = child.attrib['date'] + ' ' + child.attrib['time']
                break
    # Se crea una fecha fin con los datos obtenidos
    fin = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    # La fecha de inicio es un año anterior a la de fin
    inicio = fin - timedelta(days = 365)
    return inicio, fin

def get_data(rio):
    # La url de donde se bajarán los archivos se arma con un número de rio, la lista de parámetros y los datos de las fechas
    url = 'https://www.ambiente.gub.uy/consultas/index.php/consultas_agua/mediciones_agua_download_csv/'\
         f'/0/0/{rio}/{id_parametros}/{inicio_dia}/{inicio_mes}/{inicio_ano}/00_00/{fin_dia}/{fin_mes}/{fin_ano}/00_00/0'
    response = requests.get(url, verify = False)
    # Se separa la respuesta en lineas y se guarda en data
    data = str(response.content).split('\\n')
    # En la primera línea vienen los nombres de los parametros, los cuales se guardan en nom_parametros
    nom_parametros = data[0].replace('"', '').replace('\\xc3\\xb3', 'ó').replace('\\xc3\\xad', 'í').replace('\\xc2\\xb5', 'µ').replace('\\xc2\\xba','º').split(',')[2:]
    # Se elimina la línea de los parámetros para trabajar en adelante solo con los datos
    return data[1:len(data)-1], nom_parametros

def get_nombres_y_unidades_parametros():
    nom_parametros, uni_parametros = [], []
    for param in parametros:
        aux = param.split(' (')
        if len(aux) == 2:
            nom_parametros += [aux[0]]
        else:
            nom_parametros += [aux[0] + ' (' + aux[1]]
        uni_parametros += [aux[len(aux)-1][:-1].replace('sin unid', '-')]
    return nom_parametros, uni_parametros

def reemplazar_valores_especiales(valor):
    com = ''
    if valor == '':
        valor = '-999'
    elif valor == '<LD' or valor == '< LD':
        com = valor
        valor = '-999'
    elif valor == '<LC' or valor == '< LC':
        com = valor
        valor = '-999'
    elif valor == 'LD < X < LC' or valor == 'LD<X<LC':
        com = valor
        valor = '-999'
    else:
        valor.replace('<', '')
    return valor, com

archivo = 'run_info.xml'
# Se verifica si el archivo existe
if os.path.exists(archivo):
    inicio, fin = get_fecha_run_info(archivo)
else:
    # Si no existe el archivo, aquí se pueden indicar fechas de inicio y fin
    ###################################
    #   Formato yyyy-mm-dd hh:mm:ss   #   
    ###################################
    inicio = ''    #
    fin = ''       #
    ###################################        
    
    # Si inicio o fin se dejaron vacías, se haya la fecha actual (fin) y un año antes (inicio)
    if inicio == '' or fin == '':
        fin = datetime.today().replace(second=0, microsecond=0)
        inicio = fin - timedelta(days = 365)

# Se parsean las fechas de inicio y fin para sacar los datos que van en la url
if type(inicio) == datetime:
    inicio_dia, inicio_mes, inicio_ano = inicio.day, inicio.month, inicio.year
    fin_dia, fin_mes, fin_ano = fin.day, fin.month, fin.year
else:
    inicio_dia, inicio_mes, inicio_ano = inicio[8:10], inicio[5:7], inicio[0:4]
    fin_dia, fin_mes, fin_ano = fin[8:10], fin[5:7], fin[0:4]

# Los elementos de parametros corresponden a los parámteros, tal como se indica abajo
id_parametros  = '2009_2017_2018_2032_2035_2090_2097_2099_2101'
#id_parametros =  cond_oDis_ ph _temp_turb_NH4 _PO4 _NO3 _NO2 
nom_archivos   = ['EC','PO4','NO2','NO3','NH4','O2','PH','WT','TURBTY']
# Los elementos de ids correponden a los identificadores de las estaciones que serán tenidas en cuenta
ids = ['RC10', 'RC20', 'RC35', 'RC40', 'RC50', 'RN0', 'RN17', 'RU0', 'RU1', 'RU2', 'RU3', 'SJ01']
rios = [3, 4, 5, 13]
nom_rios = ['Santa Lucia', 'Negro', 'Cuareim', 'Uruguay']

estaciones = []
parametros = []
i = 0

df = pd.DataFrame()

linea1 = 'STATION_ID,DATE,TIME,PARAMETER,UNIT,SMPLE_ID,VALUE,METHODOLOGY,INSTRUMENT,COMMENT'
for nom in nom_archivos:
    with open(r''f'{nom}.csv', 'a') as f:
        f.write(linea1 + '\n')
        
for rio in rios:
    data, parametros = get_data(rio)
    df = pd.DataFrame([sub.replace('"', '').split(',') for sub in data])
    df.columns = ['DATE', 'STATION_ID'] + parametros
    df[['DATE', 'TIME']] = df['DATE'].str.split(' ', expand=True)
    nom_parametros, uni_parametros = get_nombres_y_unidades_parametros()
    df = df.reindex(columns = ['STATION_ID', 'DATE', 'TIME'] + parametros)

    
    j = 0

    for nom in nom_archivos:
        with open(r''f'{nom}.csv', 'a') as f:
            for i in df.index:
                valor, comentario = reemplazar_valores_especiales(df[parametros[j]][i])
                f.write(df['STATION_ID'][i] + ',' + df['DATE'][i] + ',' + df['TIME'][i] + ',' 
                    + nom_parametros[j] + ',' + uni_parametros[j] + ',,' + valor
                    + ',,,' + comentario + '\n')
           
            
print(str(round(float((datetime.now() - ini).total_seconds()),2)) + ' s -', 'Finalizado')
            
            

    