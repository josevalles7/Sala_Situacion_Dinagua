# -*- coding: utf-8 -*-
"""
Created on Fri Dec 15 15:39:32 2023

@author: dinagua.pronostico01
"""

import numpy as np
import pandas as pd
from TemezRegional import TemezRegional
import os 

def pronostico_esp_balance(AD, codigos, fechas, P1, ETP1):
    # Cargar datos
    fechas_original = fechas.copy()
    mes_fin = fechas[-1, 1] + 1

    if mes_fin == 13:
        mes_fin=1
    ano_fin = fechas[-1, 0]
    rows = np.where(fechas[:, 1] == mes_fin)[0]
    
    for j in range(len(rows)):
        f = fechas[rows[j]:rows[j]+6, :].copy()
        dif = ano_fin - f[0, 0]
        f[:, 0] = f[:, 0] + dif
        f_merge = np.vstack((fechas_original, f))
        fechas = fechas_original

        P_fcst = P1[rows[j]:rows[j]+6, :].copy()
        P_merge = np.concatenate((P1, P_fcst), axis=0)

        E_fcst = ETP1[rows[j]:rows[j]+6, :].copy()
        E_merge = np.concatenate((ETP1, E_fcst), axis=0)

        ETR1 = np.zeros((len(P_merge), len(AD)))
        QC1 = np.zeros((len(P_merge), len(AD)))
        H = np.zeros((len(P_merge), len(AD)))
        Asup = np.zeros((len(P_merge), len(AD)))
        Asub = np.zeros((len(P_merge), len(AD)))
 
            
        for i, ad_val in enumerate(AD):
            ETR1[:, i], QC1[:, i], I, H[:, i], V, Asup[:, i], Asub[:, i] = TemezRegional(ad_val, P_merge[:, i], E_merge[:, i])
        
        # Convertir 'codigos' a cadena sin decimales
        codigos_str = codigos.astype(int).astype(str)
        
        # Convertir 'fechas' a cadena sin decimales
        f_merge_str = f_merge.astype(int).astype(str)

        ETR1 = np.concatenate((codigos_str.reshape(1, -1), np.hstack((f_merge_str, np.round(ETR1, 3)))), axis=0)
        QC1 = np.concatenate((codigos_str.reshape(1, -1), np.hstack((f_merge_str, np.round(QC1, 3)))), axis=0)
        H = np.concatenate((codigos_str.reshape(1, -1), np.hstack((f_merge_str, np.round(H, 3)))), axis=0)
        Asup = np.concatenate((codigos_str.reshape(1, -1), np.hstack((f_merge_str, np.round(Asup, 3)))), axis=0)
        Asub = np.concatenate((codigos_str.reshape(1, -1), np.hstack((f_merge_str, np.round(Asub, 3)))), axis=0)
    
        ETR1 = pd.DataFrame(ETR1)
        QC1 = pd.DataFrame(QC1)
        H = pd.DataFrame(H)
        Asup = pd.DataFrame(Asup)
        Asub = pd.DataFrame(Asub)
        
        # Crear el directorio si no existe
        output_directory = 'output_modelo/esp'
        os.makedirs(output_directory, exist_ok=True)
        
        # Guardar en archivos CSV
        anio = int(fechas[rows[j], 0])

        output_filename = 'Escorrentia_'+str(anio)+'.csv'
        QC1.to_csv('output_modelo/esp/'+output_filename, index=False, header=False)
        
        # Limpiar variables
        del f, P_fcst, P_merge, E_fcst, E_merge, ETR1, QC1, H


