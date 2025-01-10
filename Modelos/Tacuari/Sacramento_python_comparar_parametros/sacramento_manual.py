import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from one_step_chat import one_step  # Importar la función one_step previamente creada

# --- 1. Propagación del hidrograma ---
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

# --- 2. Simulación del modelo Sacramento ---
def simular_sacramento(parametros, estados, datos, parametros_cuenca):
    """
    Simula el modelo Sacramento para un conjunto de datos hidrometeorológicos.

    Parámetros:
    - parametros: Diccionario con parámetros del modelo Sacramento.
    - estados: Estados iniciales del modelo.
    - datos: DataFrame con datos hidrometeorológicos (precipitación, PET).
    - parametros_cuenca: Diccionario con características de la cuenca y HU.

    Retorna:
    - caudales_simulados: Lista con caudales simulados.
    """
    hu = parametros_cuenca["hu"]  # Curva Unidad
    precip_efectiva = []

    for _, fila in datos.iterrows():
        # Ejecutar modelo y obtener precipitación efectiva
        estados, tlci, *_ = one_step(estados, fila["Precip"], fila["PET"], parametros)
        precip_efectiva.append(tlci)

    # Propagar el hidrograma con la HU
    caudales_simulados = propagar_hidrograma(precip_efectiva, hu)
    return caudales_simulados

# --- 3. Función para calcular NSE ---
def calcular_nse(q_obs, q_sim):
    """
    Calcula el coeficiente de eficiencia de Nash-Sutcliffe (NSE).
    """
    mask = ~np.isnan(q_obs) & ~np.isnan(q_sim)  # Asegurar valores válidos
    q_obs = q_obs[mask]
    q_sim = q_sim[mask]
    numerador = np.sum((q_obs - q_sim)**2)
    denominador = np.sum((q_obs - np.mean(q_obs))**2)
    return 1 - (numerador / denominador)

# --- 4. Parámetros del modelo ---
parametros_opcion1 = {
    'uztwm': 150.0, 'uzfwm': 65.25, 'uzk': 0.4008, 'pctim': 0.01448,
    'adimp': 0.4, 'zperc': 10.0, 'rexp': 4.104, 'lztwm': 421.45,
    'lzfsm': 10.0, 'lzfpm': 788.05, 'lzsk': 0.5, 'lzpk': 0.0231,
    'pfree': 0.01793, 'side': 0.456, 'rserv': 0.118
}

parametros_opcion2 = {
    'uztwm': 150.0, 'uzfwm': 48.99, 'uzk': 0.3072, 'pctim': 0.00667,
    'adimp': 0.4, 'zperc': 500.0, 'rexp': 5.0, 'lztwm': 500.0,
    'lzfsm': 76.39, 'lzfpm': 1000.0, 'lzsk': 0.5, 'lzpk': 0.001,
    'pfree': 0.6, 'side': 0.5, 'rserv': 0.0
}

parametros_opcion3 = {
    'uztwm': 150.0, 'uzfwm': 47.70, 'uzk': 0.4502, 'pctim': 0.0,
    'adimp': 0.4, 'zperc': 500.0, 'rexp': 5.0, 'lztwm': 500.0,
    'lzfsm': 100.12, 'lzfpm': 1000.0, 'lzsk': 0.3651, 'lzpk': 0.001,
    'pfree': 0.4238, 'side': 0.5, 'rserv': 0.3
}

# --- 5. Cargar datos y parámetros de la cuenca ---
with open(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\parametros_cuenca.json', 'r') as file:
    parametros_cuenca = json.load(file)

df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados.csv')

# --- 6. Ejecución del modelo ---
if __name__ == "__main__":
    # Inicializar estados
    estados_iniciales = {
        'uztwc': 31.2, 'uzfwc': 18.0, 'lztwc': 240.0,
        'lzfsc': 121.2, 'lzfpc': 366.0, 'adimc': 271.2
    }

    # Convertir 'Fecha' a formato datetime y filtrar el DataFrame
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    df_filtrado = df[(df['Fecha'] >= '2001-01-01') & (df['Fecha'] <= '2022-12-31')]

    # Simular caudales para cada conjunto de parámetros
    caudales_simulados_set1 = simular_sacramento(parametros_opcion1, estados_iniciales, df, parametros_cuenca)
    caudales_simulados_set2 = simular_sacramento(parametros_opcion2, estados_iniciales, df, parametros_cuenca)
    caudales_simulados_set3 = simular_sacramento(parametros_opcion3, estados_iniciales, df, parametros_cuenca)

    # Filtrar resultados para el período específico
    caudal_simulado_filtrado_set1 = caudales_simulados_set1[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_simulado_filtrado_set2 = caudales_simulados_set2[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_simulado_filtrado_set3 = caudales_simulados_set3[df_filtrado.index[0]:df_filtrado.index[-1] + 1]
    caudal_observado_filtrado = df_filtrado['QM'].values

    resultados = pd.DataFrame({
        'Fecha': df['Fecha'],
        'Caudal Observado': df['QM'],
        'Simulado Set 1': caudales_simulados_set1,
        'Simulado Set 2': caudales_simulados_set2,
        'Simulado Set 3': caudales_simulados_set3
    })

    # Exportar resultados a CSV
    resultados.to_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\resultados_simulados.csv', index=False)

    # Calcular NSE para cada calibración
    nse_set1 = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado_set1)
    nse_set2 = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado_set2)
    nse_set3 = calcular_nse(caudal_observado_filtrado, caudal_simulado_filtrado_set3)

    # Crear gráfico comparativo
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Eje principal: Caudal observado y simulado para cada set de parámetros
    ax1.plot(df_filtrado['Fecha'], caudal_observado_filtrado, label='Caudal Observado', color='blue', linewidth=1.2)
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set1, label=f'Set 1 (NSE={nse_set1:.2f})', color='red')
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set2, label=f'Set 2 (NSE={nse_set2:.2f})', color='orange')
    ax1.plot(df_filtrado['Fecha'], caudal_simulado_filtrado_set3, label=f'Set 3 (NSE={nse_set3:.2f})', color='green')

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
