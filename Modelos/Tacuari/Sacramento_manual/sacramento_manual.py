import pandas as pd
import numpy as np
import HydroErr as he
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step  # Importar la función one_step previamente creada


###definiciones iniciales:
#0
parametros = {
    'uztwm': 150.0, 'uzfwm': 20.9559768, 'uzk': 0.283341939, 'pctim': 0.0,
    'adimp': 0.293981356, 'zperc': 20.7918414, 'rexp': 3.08570481, 'lztwm': 192.495023,
    'lzfsm': 13.3088764, 'lzfpm': 100.0, 'lzsk': 0.5, 'lzpk': 0.0141780381,
    'pfree': 0.6, 'side': 0.5, 'rserv': 0.248041281
}
"""{
    'uztwm': 97.8271, 'uzfwm': 5.0, 'uzk': 0.6618, 'pctim': 0.0,
    'adimp': 0.3984, 'zperc': 39.1498, 'rexp': 5.0, 'lztwm': 313.5992,
    'lzfsm': 39.1387, 'lzfpm': 100.0063, 'lzsk': 0.3579, 'lzpk': 0.0336,
    'pfree': 0.6, 'side': 0.5, 'rserv': 0.1087
}"""


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
    df_filtrado = df[(df['Fecha'] >= '2019-01-01') & (df['Fecha'] <= '2025-01-31')]

    caudales_simulados = simular_sacramento(parametros, estados_iniciales, df, parametros_cuenca)

    # Filtrar resultados para el período específico
    caudal_simulado_filtrado = caudales_simulados[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_observado_filtrado = df_filtrado['QM'].values

    resultados = pd.DataFrame({
        'Fecha': df['Fecha'],
        'Caudal Observado': df['QM'],
        'Simulado Set 2': caudales_simulados,
    })

    # Exportar resultados a CSV
    resultados.to_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\resultados_simulados_2.csv', index=False)

    # Exportar resultados de caudal simulado a CSV
    exportar_caudal_simulado(df['Fecha'], caudales_simulados, r'C:\Tiago\1_Cuenca_Tacuari\4_python\resultados_caudal_simulado.csv')

    # Calcular metricas
    nse = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado)
    rve = calcular_error_volumetrico(caudal_observado_filtrado, caudal_simulado_filtrado)
    nrmse = calcular_nrmse(caudal_observado_filtrado, caudal_simulado_filtrado)

    # Crear gráfico comparativo
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Eje principal: Caudal observado y simulado para cada set de parámetros
    ax1.plot(df_filtrado['Fecha'], caudal_observado_filtrado, label='Caudal Observado', color='blue', linewidth=1.2)
    #ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set1, label=f'Set 1 (NSE={nse_set1:.2f})', color='red')
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado, label=f'Caudal Simulado (NSE={nse:.2f})', color='orange')
    #ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set3, label=f'Set 3 (NSE={nse_set3:.2f})', color='green')

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

    print("NSE:",nse, "RVE:",rve, "NRMSE:",nrmse)
