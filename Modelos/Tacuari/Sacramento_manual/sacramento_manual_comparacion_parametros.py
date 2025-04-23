import pandas as pd
import numpy as np
import HydroErr as he
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step  # Importar la función one_step previamente creada


###definiciones iniciales:
#0
parametros = {
    'uztwm': 104.19393, 'uzfwm': 5.0, 'uzk': 0.541117334, 'pctim': 0.0,
    'adimp': 0.4, 'zperc': 160.56391, 'rexp': 5.0, 'lztwm': 184.794858,
    'lzfsm': 40.0773827, 'lzfpm': 100.0, 'lzsk': 0.5, 'lzpk': 0.0097500564,
    'pfree': 0.150733005, 'side': 0.5, 'rserv': 0.0
}

parametros2 = {
    'uztwm': 97.8271, 'uzfwm': 5.0, 'uzk': 0.6618, 'pctim': 0.0,
    'adimp': 0.3984, 'zperc': 39.1498, 'rexp': 5.0, 'lztwm': 313.5992,
    'lzfsm': 39.1387, 'lzfpm': 100.0063, 'lzsk': 0.3579, 'lzpk': 0.0336,
    'pfree': 0.6, 'side': 0.5, 'rserv': 0.1087
}

parametros3 = None  # Eliminar el set de parámetros 3


estados_iniciales = {
    'uztwc': 85, 'uzfwc': 60, 'lztwc': 110,
    'lzfsc': 100, 'lzfpc': 140, 'adimc': 110
}

### Definir funciones para correr el modelo
#1.1 Propagar hidrograma

def propagar_hidrograma(precip_ef, hu):
    """
    Propaga el hidrograma unitario para convertir precipitación efectiva en caudal.
    """
    precip_ef = np.array(precip_ef, dtype=np.float64)
    hu = np.array(hu, dtype=np.float64)
    L = len(hu)
    Q = np.zeros(len(precip_ef) + L - 1)
    for i in range(len(precip_ef)):
        Q[i:i+L] += precip_ef[i] * hu
    return Q[:len(precip_ef)]

#1.2 Correr el modelo sacramento
def simular_sacramento(parametros, estados, datos, parametros_cuenca):
    hu = parametros_cuenca["hu"]
    precip_efectiva = []

    for _, fila in datos.iterrows():
        # Ejecutar modelo y obtener precipitación efectiva
        estados, tlci, *_ = one_step(estados, fila["Precip"], fila["PET"], parametros)
        precip_efectiva.append(tlci)

    # Propagar el hidrograma con la HU
    caudales_simulados = propagar_hidrograma(precip_efectiva, hu)
    return caudales_simulados

### Definir metricas.
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
    e_v = np.sum(q_obs - q_sim) / np.sum(q_obs)
    return e_v

    """    rve = he.ve(q_sim, q_obs)
    return 1-rve"""

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

#4 Cargar y guardar datos
with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
    parametros_cuenca = json.load(file)

df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados_completos.csv')

def exportar_caudal_simulado(fechas, caudales_simulados, filepath):
    df_resultados = pd.DataFrame({
        'Fecha': fechas,
        'Caudal Simulado': caudales_simulados
    })
    df_resultados.to_csv(filepath, index=False)

#5 Ejecución
if __name__ == "__main__":
    # Convertir 'Fecha' a formato datetime y filtrar el DataFrame
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df_filtrado = df[(df['Fecha'] >= '2000-06-01') & (df['Fecha'] <= '2025-01-31')]

    # Simular caudales con los dos conjuntos de parámetros
    caudales_simulados_set1 = simular_sacramento(parametros, estados_iniciales, df, parametros_cuenca)
    caudales_simulados_set2 = simular_sacramento(parametros2, estados_iniciales, df, parametros_cuenca)

    # Filtrar resultados para el período específico
    caudal_simulado_filtrado_set1 = caudales_simulados_set1[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_simulado_filtrado_set2 = caudales_simulados_set2[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_observado_filtrado = df_filtrado['QM'].values

    # Calcular métricas para cada conjunto de parámetros
    nse_set1 = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado_set1)
    nse_set2 = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado_set2)
    rve_set1 = calcular_error_volumetrico(caudal_observado_filtrado, caudal_simulado_filtrado_set1)
    rve_set2 = calcular_error_volumetrico(caudal_observado_filtrado, caudal_simulado_filtrado_set2)
    nrmse_set1 = calcular_nrmse(caudal_observado_filtrado, caudal_simulado_filtrado_set1)
    nrmse_set2 = calcular_nrmse(caudal_observado_filtrado, caudal_simulado_filtrado_set2)

    # Crear gráfico comparativo
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Eje principal: Caudal observado y simulado para cada set de parámetros
    ax1.plot(df_filtrado['Fecha'], caudal_observado_filtrado, label='Caudal Observado', color='blue', linewidth=1.2)
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set1, label=f'Set 1 (NSE={nse_set1:.2f})', color='red')
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set2, label=f'Set 2 (NSE={nse_set2:.2f})', color='orange')

    ax1.set_xlabel('Fecha')
    ax1.set_ylabel('Caudal (m³/s)', color='black')
    ax1.legend(loc='upper left')

    # Eje secundario: Precipitación
    ax2 = ax1.twinx()
    precip_filtrada = df_filtrado['Precip'].values
    ax2.bar(df_filtrado['Fecha'], precip_filtrada, width=1, color='gray', alpha=0.5)
    ax2.set_ylabel('Precipitación (mm)', color='gray')

    plt.title('Comparación de Caudal Observado y Simulado para Diferentes Calibraciones')
    plt.show()

    # Exportar resultados a CSV
    resultados = pd.DataFrame({
        'Fecha': df['Fecha'],
        'Caudal Observado': df['QM'],
        'Simulado Set 1': caudales_simulados_set1,
        'Simulado Set 2': caudales_simulados_set2,
    })
    resultados.to_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\resultados_simulados_todos.csv', index=False)

    # Imprimir métricas
    print("Set 1 - NSE:", nse_set1, "RVE:", rve_set1, "NRMSE:", nrmse_set1)
    print("Set 2 - NSE:", nse_set2, "RVE:", rve_set2, "NRMSE:", nrmse_set2)
