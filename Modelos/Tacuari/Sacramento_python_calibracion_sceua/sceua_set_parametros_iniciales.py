import numpy as np

def inicializar_poblacion_centrada(manual, bl, bu, n_poblacion, perturbacion=0.1):
    """
    Genera una población inicial centrada en los parámetros manuales.
    """
    # Convertir listas a arrays de NumPy
    bl = np.array(bl, dtype=np.float64)
    bu = np.array(bu, dtype=np.float64)
    manual = np.array(manual, dtype=np.float64)

    n_parametros = len(manual)
    poblacion = np.zeros((n_poblacion, n_parametros))
    
    for i in range(n_poblacion):
        poblacion[i] = manual + np.random.uniform(
            low=-perturbacion, high=perturbacion, size=n_parametros
        ) * (bu - bl)
        poblacion[i] = np.clip(poblacion[i], bl, bu)  # Asegurar valores dentro de límites
    
    return poblacion


# Implementación del algoritmo SCE-UA
def sceua(func_objetivo, bl, bu, extra, manual, n_poblacion=10, max_iter=100, kstop=10, peps=1e-5):
    poblacion = inicializar_poblacion_centrada(manual, bl, bu, n_poblacion)
    historico_mejor = []
    
    for iteracion in range(max_iter):
        # Evaluar función objetivo
        errores = np.array([func_objetivo(individuo, extra) for individuo in poblacion])
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
        
        # Evolución: Perturbaciones adaptativas
        perturbacion_actual = 0.1 * (1 - iteracion / max_iter)  # Perturbación decreciente
        for i in range(1, n_poblacion):  # No perturbar al mejor individuo
            variacion = np.random.uniform(
                low=-perturbacion_actual, high=perturbacion_actual, size=len(bl)
            )
            poblacion[i] += variacion * (bu - bl)
            poblacion[i] = np.clip(poblacion[i], bl, bu)  # Garantizar límites

    return mejor_parametro, mejor_error, historico_mejor
