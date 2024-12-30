# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:03:38 2024

@author: tiago
"""
from joblib import Parallel, delayed
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step  # Importar la función one_step previamente creada

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

# --- 4. Inicializar población centrada ---
def inicializar_poblacion_centrada(manual, bl, bu, n_poblacion, perturbacion=0.2):
    bl = np.array(bl, dtype=np.float64)
    bu = np.array(bu, dtype=np.float64)
    manual = np.array(manual, dtype=np.float64)
    n_parametros = len(manual)
    poblacion = np.zeros((n_poblacion, n_parametros))
    
    # Perturbación adaptativa basada en el rango de cada parámetro
    rango = bu - bl
    for i in range(n_poblacion):
        variacion = np.random.uniform(low=-perturbacion, high=perturbacion, size=n_parametros)
        poblacion[i] = manual + variacion * rango  # Perturbación proporcional al rango
        poblacion[i] = np.clip(poblacion[i], bl, bu)  # Garantizar que esté dentro de los límites
    
    return poblacion

# --- 5. Implementación de SCE-UA ---
def sceua_set_parametros_iniciales(func_objetivo, bl, bu, extra, manual, n_poblacion=400, max_iter=45, kstop=12, peps=1e-5):
    poblacion = inicializar_poblacion_centrada(manual, bl, bu, n_poblacion)
    historico_mejor = []

    for iteracion in range(max_iter):
        errores = np.array(Parallel(n_jobs=-1)(delayed(func_objetivo)(individuo, extra) for individuo in poblacion))
        indices_ordenados = np.argsort(errores)
        poblacion = poblacion[indices_ordenados]
        errores = errores[indices_ordenados]
        mejor_parametro = poblacion[0]
        mejor_error = errores[0]
        historico_mejor.append((mejor_parametro, mejor_error))

        # Criterio de convergencia
        if len(historico_mejor) > kstop:
            cambios = [abs(historico_mejor[-i][1] - historico_mejor[-i-1][1]) for i in range(1, kstop+1)]
            if all(cambio < peps for cambio in cambios):
                print(f"Convergencia alcanzada en la iteración {iteracion}.")
                break

        # Evolución: Pequeñas perturbaciones
        for i in range(1, n_poblacion):
            for j in range(len(bl)):
                poblacion[i, j] += np.random.uniform(-0.15, 0.15) * (bu[j] - bl[j])
                poblacion[i, j] = np.clip(poblacion[i, j], bl[j], bu[j])

    return mejor_parametro, mejor_error, historico_mejor

# --- 6. Función Objetivo ---
def funcion_objetivo(parametros_vector, extra):
    nombres_parametros = [
        'uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 
        'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 
        'lzsk', 'lzpk', 'pfree', 'side', 'rserv'
    ]
    parametros = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_vector)}
    caudales_simulados = simular_sacramento(parametros, extra['estados'], extra['datos'], extra['parametros_cuenca'])
    nse = calcular_nse(extra['datos']['QM'].values, caudales_simulados)
    return -nse

if __name__ == "__main__":
    # Cargar datos
    df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados.csv')

    # Dividir en calentamiento y calibración
    fecha_inicio_calibracion = "2001-01-01"
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df_calentamiento = df[df['Fecha'] < fecha_inicio_calibracion]
    df_calibracion = df[df['Fecha'] >= fecha_inicio_calibracion]

    # Ajustar estados iniciales con calentamiento
    estados_iniciales = {
        'uztwc': 31.2, 'uzfwc': 18.0, 'lztwc': 240.0, 
        'lzfsc': 121.2, 'lzfpc': 366.0, 'adimc': 271.2
    }
    parametros_manual = [128.0957, 65.4602, 0.2963, 0.0246, 0.3764, 10.0000, 4.6567, 355.6461, 31.1920, 700.1640, 0.4650, 0.0289, 0.0169, 0.5000, 0.1502]
    

    # Convertir parametros_manual a un diccionario
    nombres_parametros = [
        'uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 
        'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 
        'lzsk', 'lzpk', 'pfree', 'side', 'rserv'
    ]
    parametros_dict = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_manual)}

    for _, fila in df_calentamiento.iterrows():
        estados_iniciales, _, *_ = one_step(estados_iniciales, fila["Precip"], fila["PET"], parametros_dict)

    # Definir límites de parámetros
    bl = [10, 5, 0.1, 0.0, 0.0, 10, 1, 50, 10, 100, 0.01, 0.001, 0.0, 0.0, 0.0]  # Límites inferiores
    bu = [150, 150, 0.7, 0.1, 0.4, 500, 5, 500, 500, 1000, 0.5, 0.05, 0.6, 0.5, 0.3]  # Límites superiores

    # Usar estados ajustados para calibración
    with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
        parametros_cuenca = json.load(file)
    extra = {'estados': estados_iniciales, 'datos': df_calibracion, 'parametros_cuenca': parametros_cuenca}

    # Ejecutar calibración
    mejor_parametro, mejor_error, historico = sceua_set_parametros_iniciales(
        funcion_objetivo, bl, bu, extra, parametros_manual
    )

    print("Mejor conjunto de parámetros:", mejor_parametro)
    print("Mejor NSE obtenido:", -mejor_error)

