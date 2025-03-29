# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:03:38 2024

@author: tiago
"""

import pandas as pd
import numpy as np
import HydroErr as he
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step # Importar función one_step del modelo Sacramento
from sceua import dividir_en_complejos, evolucionar_complejo, inicializar_poblacion, sceua # Importar funciones de SCE-UA

###definiciones iniciales:
#0
nombres_parametros = ['uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 'lzsk', 'lzpk', 'pfree', 'side', 'rserv']
estados_iniciales = {'uztwc': 85, 'uzfwc': 60, 'lztwc': 110,'lzfsc': 100, 'lzfpc': 140, 'adimc': 110}
bl = [10, 5, 0.1, 0.0, 0.0, 10, 1, 50, 10, 100, 0.01, 0.001, 0.0, 0.0, 0.0]  
bu = [150, 150, 0.7, 0.1, 0.4, 500, 5, 500, 500, 1000, 0.5, 0.05, 0.6, 0.5, 0.3]  

### Definir funciones para correr el modelo
#1.1 Propagar hidrograma
def propagar_hidrograma(precip_ef, hu):
    precip_ef = np.array(precip_ef, dtype=np.float64)
    hu = np.array(hu, dtype=np.float64)
    L = len(hu)
    Q = np.zeros(len(precip_ef) + L - 1)
    for i in range(len(precip_ef)):
        Q[i:i+L] += precip_ef[i] * hu
    return Q[:len(precip_ef)]

#1.2 Correr el modelo sacramento
def simular_sacramento(parametros, estados, datos, parametros_cuenca):
    hu = parametros_cuenca['hu']
    precip_efectiva = []

    for _, fila in datos.iterrows():
        estados, tlci, *_ = one_step(estados, fila['Precip'], fila["PET"], parametros)
        precip_efectiva.append(tlci)
    
    caudales_simulados = propagar_hidrograma(precip_efectiva, hu)

    return caudales_simulados

### Definir funcion objectivo.
#2.1 Calcular metrica NSE
def calcular_nse(q_obs, q_sim):
    mask = ~np.isnan(q_obs)& ~np.isnan(q_sim)
    q_sim = q_sim[mask]
    q_obs = q_obs[mask]
    nse = he.nse(q_sim, q_obs)
    return nse
    """mask = ~np.isnan(q_obs)
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    numerador = np.sum((q_obs - q_sim)**2)
    denominador = np.sum((q_obs - np.mean(q_obs))**2)
    return 1 - (numerador / denominador)"""

#2.2 Calcular error volumetrico
def calcular_error_volumetrico(q_obs, q_sim):

    mask = ~np.isnan(q_obs)& ~np.isnan(q_sim)
    q_sim = q_sim[mask]
    q_obs = q_obs[mask]
    rve = he.ve(q_sim, q_obs)
    return 1-rve
    """e_v = np.sum(q_obs - q_sim) / np.sum(q_obs)
    return e_v"""

#2.3 Calcular el error cuadrático medio normalizado 
def calcular_nrmse(q_obs, q_sim):
    mask = ~np.isnan(q_obs)& ~np.isnan(q_sim)
    q_sim = q_sim[mask]
    q_obs = q_obs[mask]
    nrmse = he.nrmse_range(q_sim, q_obs)
    return nrmse
    
    """mask = ~np.isnan(q_obs) & ~np.isnan(q_sim)
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    mse = np.mean((q_obs - q_sim)**2)  # Error cuadrático medio
    rmse = np.sqrt(mse)  # Raíz del error cuadrático medio
    sigma_obs = np.std(q_obs)  # Desviación estándar de los valores observados
    return rmse / sigma_obs"""

#2.4 Definir funcion objetivo
def funcion_objetivo(parametros_vector, extra):
    parametros = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_vector)}

    caudales_simulados = simular_sacramento(parametros, extra['estados'], extra['datos'], extra['parametros_cuenca'])
    q_obs = extra['datos']['QM'].values

    #calentamento:
    periodo_calentamiento = 730
    datos_calibración = extra['datos'].iloc[periodo_calentamiento:]
    q_obs_calibración = q_obs[periodo_calentamiento:]
    q_sim_calibración = caudales_simulados[periodo_calentamiento:]

    #calculo de metricas
    nse = calcular_nse(q_obs_calibración, q_sim_calibración)
    e_v = calcular_error_volumetrico(q_obs_calibración, q_sim_calibración)
    #e_c = calcular_nrmse(q_obs_calibración, q_sim_calibración)

    w1, w2 = 0.6, 0.4
    return w1*(-nse) + w2*e_v

### Algoritmo de calibración
#3.1 Inicial articulas
def inicializar_poblacion(bl, bu, n_poblacion):
    n_parametros = len(bl)
    return np.random.uniform(low=bl, high=bu, size=(n_poblacion, n_parametros))

### Correr el modelo
if __name__ == "__main__":
#4.1 Leer datos
    with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
        parametros_cuenca = json.load(file)
    df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados_calibracion.csv')
    extra = {'estados': estados_iniciales, 'datos': df, 'parametros_cuenca': parametros_cuenca}

    #4.2 Correr el algoritmo de optimización
    mejor_parametro, mejor_error, historico = sceua(        
        funcion_objetivo, bl, bu, extra=extra,
        n_poblacion=600, n_complex=10, n_evol=6, max_iter=50, kstop=30, peps=1e-7)

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
