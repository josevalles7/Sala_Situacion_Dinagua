# main.py
import numpy as np
import pandas as pd
import time

from InterpolacionEspacialETP import funcion_interpolacion_etp
from InterpolacionEspacialPrecipitaciones import funcion_interpolacion_precipitaciones
from TemezRegional import TemezRegional
from funciones import cargar_archivos
from funciones import importar_librerias
from pronostico_esp_balance import pronostico_esp_balance


def CalculoBalance(AD, codigos, fechas, P1, ETP1):
    inicio = time.time()
    
    ETR1 = np.zeros((len(P1), len(AD)))
    QC1 = np.zeros((len(P1), len(AD)))
    H = np.zeros((len(P1), len(AD)))
    Asup = np.zeros((len(P1), len(AD)))
    Asub = np.zeros((len(P1), len(AD)))

    for i, ad_val in enumerate(AD):
        ETR1[:, i], QC1[:, i], I, H[:, i], V, Asup[:, i], Asub[:, i] = TemezRegional(ad_val, P1[:, i], ETP1[:, i])
    
    # Convertir 'codigos' a cadena sin decimales
    codigos_str = codigos.astype(int).astype(str)
    
    # Convertir 'fechas' a cadena sin decimales
    fechas_str = fechas.astype(int).astype(str)
    
    ETR1 = np.concatenate((codigos_str.reshape(1, -1), np.hstack((fechas_str, np.round(ETR1, 3)))), axis=0)
    QC1 = np.concatenate((codigos_str.reshape(1, -1), np.hstack((fechas_str, np.round(QC1, 3)))), axis=0)
    H = np.concatenate((codigos_str.reshape(1, -1), np.hstack((fechas_str, np.round(H, 3)))), axis=0)
    Asup = np.concatenate((codigos_str.reshape(1, -1), np.hstack((fechas_str, np.round(Asup, 3)))), axis=0)
    Asub = np.concatenate((codigos_str.reshape(1, -1), np.hstack((fechas_str, np.round(Asub, 3)))), axis=0)

    ETR1 = pd.DataFrame(ETR1)
    QC1 = pd.DataFrame(QC1)
    H = pd.DataFrame(H)
    Asup = pd.DataFrame(Asup)
    Asub = pd.DataFrame(Asub)

    ETR1.to_csv('ETR.csv', index=False, header=False)
    QC1.to_csv('Escorrentia_total.csv', index=False, header=False)
    H.to_csv('HumedadSuelo.csv', index=False, header=False)
    Asup.to_csv('Escorrentia_sup.csv', index=False, header=False)
    Asub.to_csv('Escorrentia_sub.csv', index=False, header=False)
    
    fin = time.time()
    tiempo_ejecucion = fin - inicio
    print(f"Tiempo de ejecución de calculo balance: {tiempo_ejecucion} segundos")


    
if __name__ == "__main__":
    inicio_total = time.time()
    importar_librerias()
    #funcion_interpolacion_etp()
    #funcion_interpolacion_precipitaciones()
    
    # Ingresar los nombres de los archivos como argumentos a cargar_archivos()
    agua_disponible = 'AguaDisponible.txt'
    archivo_pmedias = 'Pmedias.csv'
    archivo_etpmedias = 'ETPmedias.csv'

    AD, codigos, fechas, P1, ETP1 = cargar_archivos(agua_disponible, archivo_pmedias, archivo_etpmedias)
    
    CalculoBalance(AD, codigos, fechas, P1, ETP1)
    
    pronostico_esp_balance(AD, codigos, fechas, P1, ETP1)
    
    fin_total = time.time()
    tiempo_ejecucion_total = fin_total - inicio_total
    print(f"Tiempo total de ejecución: {tiempo_ejecucion_total} segundos")
