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

"""def calibracion_sa(func_objetivo, bl, bu, extra, manual, temp=1.0, alpha=0.85, temp_min=0.5, max_iter=5):
    params = np.array(manual, dtype=np.float64)
    best_params = params.copy()
    best_cost = func_objetivo(params, extra)
    current_cost = best_cost

    while temp > temp_min:
        for _ in range(max_iter):
            new_params = params + np.random.uniform(-0.05, 0.05, size=params.shape) * (np.array(bu) - np.array(bl))
            new_params = np.clip(new_params, bl, bu)
            
            new_cost = func_objetivo(new_params, extra)
            delta_cost = new_cost - current_cost

            if delta_cost < 0 or np.random.rand() < np.exp(-delta_cost / temp):
                params = new_params
                current_cost = new_cost
                if new_cost < best_cost:
                    best_params = new_params
                    best_cost = new_cost

        temp *= alpha

        # Convergencia temprana
        if abs(current_cost - best_cost) < 1e-3:
            break

    return best_params, best_cost"""

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

#  --- 3. Calcular Error Cuadrático ---
def calcular_error_cuadratico(q_obs, q_sim):
    mask = ~np.isnan(q_obs)
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    error_cuadratico = np.sum((q_obs - q_sim)**2) / len(q_obs)  # Normalización
    raiz_error_cuadratico = error_cuadratico ** 0.5  # Error cuadrático normalizado
    return raiz_error_cuadratico

# --- 4. Inicializar población centrada ---
def inicializar_particulas(bl, bu, n_particulas):
    """
    Inicializa las partículas y sus velocidades.
    """
    parametros_iniciales = [150, 5, 0.1, 0, 0.4, 10, 1, 500,
                             10, 100, 0.5, 0.03287888, 0, 0.5, 0]

    nombres_parametros = ['uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 'lzsk', 'lzpk', 'pfree', 'side', 'rserv']

    bl = np.array(bl, dtype=np.float64)
    bu = np.array(bu, dtype=np.float64)
    n_parametros = len(bl)
    
    particulas = np.random.uniform(bl, bu, (n_particulas, n_parametros))
    velocidades = np.random.uniform(-0.1, 0.1, (n_particulas, n_parametros))
    
    return particulas, velocidades

def pso(func_objetivo, bl, bu, extra, n_particulas=220, max_iter=20, c1=2.2, c2=2.2, w=0.4):
    """
    Implementación del algoritmo de optimización por enjambre de partículas (PSO).
    
    Parámetros:
    - func_objetivo: Función objetivo a minimizar.
    - bl: Límites inferiores para los parámetros.
    - bu: Límites superiores para los parámetros.
    - extra: Información adicional para la función objetivo.
    - n_particulas: Número de partículas en el enjambre.
    - max_iter: Número máximo de iteraciones.
    - c1, c2: Coeficientes de atracción hacia la mejor posición local y global.
    - w: Factor de inercia para las velocidades.

    Retorna:
    - mejor_parametro: El mejor conjunto de parámetros encontrado.
    - mejor_error: El error asociado al mejor conjunto de parámetros.
    - historico_mejor: Histórico de los mejores resultados por iteración.
    """
    particulas, velocidades = inicializar_particulas(bl, bu, n_particulas)
    n_parametros = len(bl)

    # Inicialización de valores
    errores = np.array([func_objetivo(p, extra) for p in particulas])
    mejores_locales = particulas.copy()
    errores_locales = errores.copy()

    mejor_global = particulas[np.argmin(errores)]
    mejor_error_global = np.min(errores)

    historico_mejor = [(mejor_global, mejor_error_global)]

    for iteracion in range(max_iter):
        for i in range(n_particulas):
            # Actualización de velocidades
            r1 = np.random.random(n_parametros)
            r2 = np.random.random(n_parametros)

            velocidades[i] = (
                w * velocidades[i] +
                c1 * r1 * (mejores_locales[i] - particulas[i]) +
                c2 * r2 * (mejor_global - particulas[i])
            )

            # Actualización de posiciones
            particulas[i] += velocidades[i]
            particulas[i] = np.clip(particulas[i], bl, bu)

            # Evaluación de función objetivo
            error = func_objetivo(particulas[i], extra)

            # Actualización de mejor posición local
            if error < errores_locales[i]:
                errores_locales[i] = error
                mejores_locales[i] = particulas[i].copy()

            # Actualización de mejor posición global
            if error < mejor_error_global:
                mejor_error_global = error
                mejor_global = particulas[i].copy()

        historico_mejor.append((mejor_global, mejor_error_global))

        # Mostrar progreso
        print(f"Iteración {iteracion+1}/{max_iter} - Mejor Error: {mejor_error_global}")

    return mejor_global, mejor_error_global, historico_mejor

# --- 6. Función Objetivo ---
def funcion_objetivo(parametros_vector, extra):
    nombres_parametros = [
        'uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 
        'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 
        'lzsk', 'lzpk', 'pfree', 'side', 'rserv'
    ]
    parametros = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_vector)}
    caudales_simulados = simular_sacramento(parametros, extra['estados'], extra['datos'], extra['parametros_cuenca'])
    nse = calcular_error_cuadratico(extra['datos']['QM'].values, caudales_simulados)

        # Imprimir parámetros y NSE
    #if nse > 0.92:
     #           print(f"Mejor NSE: {nse}, Parámetros: {parametros}")

    return -nse

# Uso del algoritmo PSO
if __name__ == "__main__":
    # Cargar datos y definir límites como en el código anterior
    df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados_calibracion.csv')

    fecha_inicio_calibracion = "2000-06-01"
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df_calentamiento = df[df['Fecha'] < fecha_inicio_calibracion]
    df_calibracion = df[df['Fecha'] >= fecha_inicio_calibracion]

    estados_iniciales = {
        'uztwc': 31.2, 'uzfwc': 18.0, 'lztwc': 240.0, 
        'lzfsc': 121.2, 'lzfpc': 366.0, 'adimc': 271.2
    }


    parametros_dict = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_manual)}
    for _, fila in df_calentamiento.iterrows():
        estados_iniciales, _, *_ = one_step(estados_iniciales, fila["Precip"], fila["PET"], parametros_dict)

    bl = [10, 5, 0.1, 0.0, 0.0, 10, 1, 50, 10, 100, 0.01, 0.001, 0.0, 0.0, 0.0]
    bu = [150, 150, 0.7, 0.1, 0.4, 500, 5, 500, 500, 1000, 0.5, 0.05, 0.6, 0.5, 0.3]

    with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
        parametros_cuenca = json.load(file)

    extra = {'estados': estados_iniciales, 'datos': df_calibracion, 'parametros_cuenca': parametros_cuenca}

    mejor_parametro, mejor_error, historico = pso(funcion_objetivo, bl, bu, extra)

    print("Mejor conjunto de parámetros:", mejor_parametro)
    print("Mejor NSE obtenido:", -mejor_error)
        