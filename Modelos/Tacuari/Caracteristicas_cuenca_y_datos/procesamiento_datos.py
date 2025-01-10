# -*- coding: utf-8 -*-
"""
Created on Wed Nov 20 14:47:23 2024

@author: tiago
"""

import pandas as pd
import json

# Leer el CSV con datos hidrometeorológicos
df = pd.read_csv(r'C:\Tiago\1_Cuenca_Tacuari\1_Datos\datos_python.csv')  # Cambia el nombre si tu CSV es diferente

# Convertir la columna 'Fecha' a formato datetime si no lo está
df['Fecha'] = pd.to_datetime(df['Fecha'])

# Extraer día y mes para agrupar por fecha en la climatología
df['mes_dia'] = df['Fecha'].dt.strftime('%m-%d')

# Crear la climatología: promedio diario para cada día del año
climatologia_etp = df.groupby('mes_dia')['PET'].mean()

# Rellenar valores faltantes de PET usando la climatología
def rellenar_pet(fila):
    if pd.isnull(fila['PET']):
        return climatologia_etp[fila['mes_dia']]
    return fila['PET']

df['PET'] = df.apply(rellenar_pet, axis=1)

# Verificar si PET aún tiene valores faltantes
print("Valores faltantes en PET después del relleno:", df['PET'].isnull().sum())

# Eliminar filas con valores faltantes en QM
df_clean = df.dropna(subset=['QM'])

# Verificar el nuevo tamaño del DataFrame
print("Tamaño final del DataFrame después de procesar QM:", df_clean.shape)

# Identificar valores faltantes en QM
df['QM_faltante'] = df['QM'].isnull()

# Identificar bloques de datos faltantes consecutivos
df['grupo_faltante'] = (df['QM_faltante'] != df['QM_faltante'].shift()).cumsum()

# Contar el tamaño de cada grupo de valores faltantes
tamano_bloques = df[df['QM_faltante']].groupby('grupo_faltante').size()

# Rellenar los bloques de menos de 4 días por interpolación lineal
bloques_pequenos = tamano_bloques[tamano_bloques <= 3].index
df.loc[df['grupo_faltante'].isin(bloques_pequenos), 'QM'] = df['QM'].interpolate(method='linear')

# Eliminar los bloques de más de 3 días
bloques_grandes = tamano_bloques[tamano_bloques > 3].index
df = df[~df['grupo_faltante'].isin(bloques_grandes)]

# Limpiar las columnas temporales
df = df.drop(columns=['QM_faltante', 'grupo_faltante'])
# Revisar si las fechas son continuas
diffs = df['Fecha'].diff().dt.days
print("Lagunas mayores a 1 día después del procesamiento:", diffs[diffs > 1])

# Verificar si quedan valores faltantes
print("Valores faltantes finales:\n", df.isnull().sum())

df.to_csv(r'C:\Tiago\1_Cuenca_Tacuari\4_python\datos\datos_procesados.csv', index=False)

print("Archivo CSV guardado exitosamente como 'datos_procesados.csv'")