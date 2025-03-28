### Script para calibrar el modelo sacramento con el algoritmo PSO a partir de un set de parámetros pré-establecido.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from joblib import Parallel, delayed
from one_step_chat import one_step

###definiciones iniciales:
#0
nombres_parametros = ['uztwm', 'uzfwm', 'uzk', 'pctim', 'adimp', 'zperc', 'rexp', 'lztwm', 'lzfsm', 'lzfpm', 'lzsk', 'lzpk', 'pfree', 'side', 'rserv']
parametros_manual = [
    131.701385, 18.5176017, 0.689227679, 0.0, 0.0647055147, 160.432494, 
    4.70064136, 248.31675, 10.0, 100.0, 0.388247181, 0.0287144287, 
    0.403956199, 0.5, 0.101568064
]
bl = [10, 5, 0.1, 0.0, 0.0, 10, 1, 50, 10, 100, 0.01, 0.001, 0.0, 0.0, 0.0]
bu = [150, 150, 0.7, 0.1, 0.4, 500, 5, 500, 500, 1000, 0.5, 0.05, 0.6, 0.5, 0.3]
estados_iniciales = {'uztwc': 31.2, 'uzfwc': 18.0, 'lztwc': 240.0, 'lzfsc': 121.2, 'lzfpc': 366.0, 'adimc': 271.2}

### Definir funciones para correr el modelo
#1.1 Propagar hidrograma

def propagar_hidrograma(precip_ef, hu):
    precip_ef = np.array(precip_ef, dtype=np.float64)
    hu = np.array(hu, dtype=np.float64)
    L = len(hu)
    Q = np.zeros(len(precip_ef)+L-1)
    for i in range(len(precip_ef)):
        Q[i:i+L] += precip_ef[i]*hu
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
    mask = ~np.isnan(q_obs)
    q_sim = q_sim[mask]
    q_obs = q_obs[mask]
    numerador = np.sum((q_obs - q_sim)**2)
    denominador = np.sum((q_obs - np.mean(q_obs))**2)
    return 1 - numerador/denominador

#2.2 Calcular el error cuadrático medio normalizado 
def calcular_nrmse(q_obs, q_sim):
    mask = ~np.isnan(q_obs) & ~np.isnan(q_sim)
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    mse = np.mean((q_obs - q_sim)**2)  # Error cuadrático medio
    rmse = np.sqrt(mse)  # Raíz del error cuadrático medio
    sigma_obs = np.std(q_obs)  # Desviación estándar de los valores observados
    return rmse / sigma_obs

#2.3 Calcular error volumetrico
def calcular_error_volumetrico(q_obs, q_sim):
    mask = ~np.isnan(q_obs)
    q_sim = q_sim[mask]
    q_obs = q_obs[mask]
    e_v = np.sum(np.abs(q_obs - q_sim)) / np.sum(q_obs)
    return e_v

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
    #e_c = calcular_error_cuadratico(q_obs_calibración, q_sim_calibración)

    w1, w2 = 0.7, 0.3
    return w1*(-nse) + w2*e_v

### Algoritmo de calibración
#3.1 Inicial articulas
def inicializar_particulas(bl, bu, n_particulas):

    bl = np.array(bl, dtype=np.float64)
    bu = np.array(bu, dtype=np.float64)
    n_parametros = len(bl)
    
    particulas = np.random.uniform(bl, bu, (n_particulas, n_parametros))
    velocidades = np.random.uniform(-0.1, 0.1, (n_particulas, n_parametros))
    
    return particulas, velocidades

#3.2 Definir algoritmo de optimización
def pso(func_objetivo, bl, bu, extra, n_particulas=220, max_iter=20, c1=2.2, c2=2.2, w=0.4):
    particulas, velocidades = inicializar_particulas(bl, bu, n_particulas)
    n_parametros = len(bl)

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
        print(f"Iteración {iteracion+1}/{max_iter} - Mejor Error: {mejor_error_global} - Mejor parametro: {mejor_global}")

    return mejor_global, mejor_error_global, historico_mejor

### Correr el modelo
if __name__ == "__main__":
#4.1 Leer datos
    df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados_calibracion.csv')
    parametros_dict = {nombre: valor for nombre, valor in zip(nombres_parametros, parametros_manual)}
    for _, fila in df.iterrows():
        estados_iniciales, _, *_ = one_step(estados_iniciales, fila["Precip"], fila["PET"], parametros_dict)
    with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
        parametros_cuenca = json.load(file)
    extra = {'estados': estados_iniciales, 'datos': df, 'parametros_cuenca': parametros_cuenca}

#4.2 Correr el algoritmo de optimización
    mejor_parametro, mejor_error, historico = pso(funcion_objetivo, bl, bu, extra)
    
    print("Mejor conjunto de parámetros:", mejor_parametro)
    print("Mejor error obtenido:", mejor_error)