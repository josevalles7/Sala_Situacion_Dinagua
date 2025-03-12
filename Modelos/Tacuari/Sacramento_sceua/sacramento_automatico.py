# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:03:38 2024

@author: tiago
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step # Importar función one_step del modelo Sacramento
from sceua import dividir_en_complejos, evolucionar_complejo, inicializar_poblacion, sceua # Importar funciones de SCE-UA

# --- 1. Propagación del hidrograma ---
def propagar_hidrograma(precip_ef, hu):
    precip_ef = np.array(precip_ef, dtype=np.float64)
    hu = np.array(hu, dtype=np.float64)
    L = len(hu)
    Q = np.zeros(len(precip_ef) + L - 1)
    for i in range(len(precip_ef)):
        Q[i:i+L] += precip_ef[i] * hu
    return Q[:len(precip_ef)]

# --- 2. Simulación del modelo Sacramento ---
def simular_sacramento(parametros, estados, datos, parametros_cuenca):
    hu = parametros_cuenca["hu"]  # Curva Unidad
    precip_efectiva = []

    for _, fila in datos.iterrows():
        estados, tlci, *_ = one_step(estados, fila["Precip"], fila["PET"], parametros)
        precip_efectiva.append(tlci)

    caudales_simulados = propagar_hidrograma(precip_efectiva, hu)
    return caudales_simulados

# --- 3. Calcular NSE ---
def calcular_nse(q_obs, q_sim):
    mask = ~np.isnan(q_obs) & ~np.isnan(q_sim)
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    numerador = np.sum((q_obs - q_sim)**2)
    denominador = np.sum((q_obs - np.mean(q_obs))**2)
    return 1 - (numerador / denominador)

# --- 4. Inicializar la población ---
def inicializar_poblacion(bl, bu, n_poblacion):
    n_parametros = len(bl)
    return np.random.uniform(low=bl, high=bu, size=(n_poblacion, n_parametros))



# --- 6. Función Objetivo con período de calentamiento implícito ---
def funcion_objetivo(parametros_vector, extra):
    nombres_parametros = [
        'uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 
        'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 
        'lzsk', 'lzpk', 'pfree', 'side', 'rserv'
    ]
    parametros = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_vector)}
    
    # Simular todo el período
    caudales_simulados = simular_sacramento(parametros, extra['estados'], extra['datos'], extra['parametros_cuenca'])
    
    # Dividir los datos en dos partes: calentamiento y calibración
    periodo_calentamiento = 730  # Número de días del período de calentamiento
    datos_calibracion = extra['datos'].iloc[periodo_calentamiento:]  # Datos después del calentamiento
    caudales_calibracion = caudales_simulados[periodo_calentamiento:]  # Caudales simulados después del calentamiento
    
    # Calcular NSE solo para el período de calibración
    nse = calcular_nse(datos_calibracion['QM'].values, caudales_calibracion)
    return -nse  # Negar para la minimización

# --- 7. Ejecutar el modelo y calibrar ---
if __name__ == "__main__":
    # Cargar parámetros de la cuenca
    with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
        parametros_cuenca = json.load(file)

    # Cargar datos
    df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados_calibracion.csv')

    # Inicializar estados
    estados_iniciales = {
        'uztwc': 85, 'uzfwc': 60, 'lztwc': 110,
        'lzfsc': 100, 'lzfpc': 140, 'adimc': 110
    }

    # Definir límites de parámetros
    bl = [10, 5, 0.1, 0.0, 0.0, 10, 1, 50, 10, 100, 0.01, 0.001, 0.0, 0.0, 0.0]  # Inferiores
    bu = [150, 150, 0.7, 0.1, 0.4, 500, 5, 500, 500, 1000, 0.5, 0.05, 0.6, 0.5, 0.3]  # Superiores

    # Ejecutar SCE-UA
    extra = {'estados': estados_iniciales, 'datos': df, 'parametros_cuenca': parametros_cuenca}
    mejor_parametro, mejor_error, historico = sceua(funcion_objetivo, bl, bu, extra=extra, n_poblacion=20, max_iter=100)

    # Mostrar resultados
    print("Mejor conjunto de parámetros:", mejor_parametro)
    print("Mejor NSE obtenido:", -mejor_error)

    # Simular con parámetros calibrados
    nombres_parametros = [
        'uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 
        'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 
        'lzsk', 'lzpk', 'pfree', 'side', 'rserv'
    ]
    parametros_calibrados = {nombre: valor for nombre, valor in zip(nombres_parametros, mejor_parametro)}
    caudales_simulados = simular_sacramento(parametros_calibrados, estados_iniciales, df, parametros_cuenca)

    # Crear gráfico
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df['Fecha'], df['QM'], label='Caudal Observado', color='blue')
    ax1.plot(df['Fecha'], caudales_simulados, label='Caudal Simulado', color='red')
    ax1.set_xlabel('Fecha')
    ax1.set_ylabel('Caudal (m³/s)')
    ax1.legend()
    plt.title(f'Comparación Caudal Observado vs Simulado\nNSE: {-mejor_error:.2f}')
    plt.show()
