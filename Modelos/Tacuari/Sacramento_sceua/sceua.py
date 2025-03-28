# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 16:52:35 2024

@author: tiago
"""

import numpy as np

# Función para inicializar la población
def inicializar_poblacion(bl, bu, n_poblacion):
    n_parametros = len(bl)
    return np.random.uniform(low=bl, high=bu, size=(n_poblacion, n_parametros))

# Función para dividir la población en complejos
def dividir_en_complejos(poblacion, n_complex):
    np.random.shuffle(poblacion)  # Mezclar la población de manera aleatoria
    complejos = [poblacion[i::n_complex] for i in range(n_complex)]
    return complejos

# Evolución dentro de un complejo usando el método de simplex
def evolucionar_complejo(complejo, func_objetivo, bl, bu, extra, n_evol):
    bl = np.array(bl)  # Convertir bl a array de NumPy
    bu = np.array(bu)  # Convertir bu a array de NumPy
    n_parametros = len(bl)
    for _ in range(n_evol):
        # Ordenar el complejo según la función objetivo
        errores = np.array([func_objetivo(individuo, extra) for individuo in complejo])
        indices_ordenados = np.argsort(errores)
        complejo = complejo[indices_ordenados]
        
        # Crear un nuevo punto mediante combinaciones lineales (simplex)
        mejor = complejo[0]
        peor = complejo[-1]
        centroide = np.mean(complejo[:10], axis=0)
        
        
        rango = (bu - bl) * 0.6  # Usar el 10% del rango de cada parámetro
        nuevo_punto = centroide + np.random.uniform(-rango, rango, size=n_parametros)
        nuevo_punto = np.clip(nuevo_punto, bl, bu)  # Asegurar que está dentro de los límites
    
        # Evaluar el nuevo punto
        error_nuevo = func_objetivo(nuevo_punto, extra)
        error_peor = func_objetivo(peor, extra)
        
        # Reemplazar si el nuevo punto es mejor que el peor
        if error_nuevo < error_peor:
            complejo[-1] = nuevo_punto
    
    return complejo
# --- 5. Implementación de SCE-UA ---
def sceua(func_objetivo, bl, bu, extra, n_poblacion, n_complex, n_evol, max_iter, kstop, peps):
    poblacion = inicializar_poblacion(bl, bu, n_poblacion)
    historico_mejor = []

    for iteracion in range(max_iter):
        # Evaluar función objetivo
        errores = np.array([func_objetivo(individuo, extra) for individuo in poblacion])
        
        # Ordenar población según los errores
        indices_ordenados = np.argsort(errores)
        poblacion = poblacion[indices_ordenados]
        errores = errores[indices_ordenados]
        mejor_parametro = poblacion[0]
        mejor_error = errores[0]
        historico_mejor.append((mejor_parametro, mejor_error))
        
        print(f"Iteración {iteracion}: Mejor error = {mejor_error}, parámetros: {mejor_parametro}")
        # Criterio de convergencia
        if len(historico_mejor) > kstop:
            cambios = [abs(historico_mejor[-i][1] - historico_mejor[-i-1][1]) for i in range(1, kstop+1)]
            if all(cambio < peps for cambio in cambios):
                print(f"Convergencia alcanzada en la iteración {iteracion}.")
                break

        # Dividir población en complejos
        complejos = dividir_en_complejos(poblacion, n_complex)
        
        # Evolucionar cada complejo de manera independiente
        nuevos_complejos = []
        for complejo in complejos:
            evolucionado = evolucionar_complejo(complejo, func_objetivo, bl, bu, extra, n_evol)
            nuevos_complejos.append(evolucionado)
        
        # Remezclar población
        poblacion = np.vstack(nuevos_complejos)
        np.random.shuffle(poblacion)

    return mejor_parametro, mejor_error, historico_mejor