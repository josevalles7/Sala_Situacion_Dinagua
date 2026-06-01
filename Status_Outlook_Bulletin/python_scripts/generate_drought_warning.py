# %%
import geopandas as gpd
from rasterstats import zonal_stats
import pandas as pd
import argparse
import os
import numpy as np

# This script generates drought warnings for sub-basins based on the SPI (Standardized Precipitation Index) and IEH (Hydrological Drought Index) values. It classifies the drought status into categories such as NORMALIDAD, MODERADO, SEVERO, and EXTREMO based on predefined criteria. The results are saved in a shapefile for use in QGIS.
# Define arguments 
parser = argparse.ArgumentParser(
                    prog='generate_drought_warning.py',
                    description='generate drought warning',
                    epilog='Jose Valles, DINAGUA, 08Abr2026')

# 
parser.add_argument('ano', help='provide year of analysis')
parser.add_argument('mes', help='provide month of analysis')

args = parser.parse_args()

'''
args = argparse.Namespace(
    ano='2026',
    mes='03',
)
'''
print('Good morning! Starting the drought warning generation process...')
# %%
# 1. Cargar las subcuencas
cuencas = gpd.read_file('./qgis_status_outlook/shapefiles/Cuencas_n2.shp')
# from cuencas, extract cod_n2, nombrec2, area and create a dataframe
cuencas_df = cuencas[['cod_n2', 'nombrec2', 'area']].copy()
cuencas_df.rename(columns={'cod_n2': 'cod_n2', 'nombrec2': 'nombrec2', 'area': 'area'}, inplace=True)
cuencas_df.head().style.hide(axis='index')

# %%
# 2. Definir los archivos raster de SPI
# De la carpeta ../qgis_status_outlook/IPE/ extraer los archivos raster de SPI para los periodos 1, 3, 6 y 12 meses. 
# Los nombres de archivo contienen el periodo de tiempo, por ejemplo: YYYY_MM_IPE_01meses, YYYY_MM_IPE_03meses, YYYY_MM_IPE_06meses, YYYY_MM_IPE_12meses. Donde YYYY es el año y MM es el mes.
ano = args.ano
mes = args.mes

raster_files = {
    '1_mes': f'qgis_status_outlook/IPE/{ano}_{mes}_IPE_01meses.tif',
    '3_meses': f'qgis_status_outlook/IPE/{ano}_{mes}_IPE_03meses.tif',
    '6_meses': f'qgis_status_outlook/IPE/{ano}_{mes}_IPE_06meses.tif',
    '12_meses': f'qgis_status_outlook/IPE/{ano}_{mes}_IPE_12meses.tif'
}

# %%
# 3. Iterar sobre cada raster y calcular el promedio
for col_name, raster_path in raster_files.items():
    print(f"Procesando: {col_name} - {raster_path}")
    
    # Verificar que el archivo existe
    if not os.path.exists(raster_path):
        print(f"Archivo no encontrado: {raster_path}")
        cuencas[col_name] = None
        continue
    
    # zonal_stats devuelve una lista de diccionarios
    # Asegurar que ambos tienen el mismo CRS y usar all_touched=True para capturar valores
    # Usar band=2 para especificar la banda 2
    stats = zonal_stats(
        cuencas.to_crs(epsg=32721),  # Asegurar CRS común
        raster_path, 
        stats="mean",
        all_touched=True,
        nodata=-999,
        band=1  # Usar la banda 1 del raster
    )
    
    # Extraemos el valor 'mean' y lo asignamos a la columna cod_n2 de el dataframe cuencas_df
    cuencas_df[col_name] = [x['mean'] if x['mean'] is not None else float('nan') for x in stats]
    
    # Mostrar resumen
    valid_values = sum(1 for x in stats if x['mean'] is not None)
    print(f"Valores válidos: {valid_values}/{len(stats)}")

# %%
# import 01_status_month.csv, 03_status_month.csv
status_1_mes = pd.read_csv('qgis_status_outlook/csvtables/01_status_month.csv')
status_3_meses = pd.read_csv('qgis_status_outlook/csvtables/03_status_month.csv')


# %%
# 4. asignar el status_1_mes y status_3_meses a cuencas_df usando cod_n2 como clave
cuencas_df = cuencas_df.merge(
    status_1_mes.rename(columns={'stationID': 'cod_n2', 'category': 'IEH_1'}),
    on='cod_n2', how='left'
)
cuencas_df = cuencas_df.merge(
    status_3_meses.rename(columns={'stationID': 'cod_n2', 'category': 'IEH_3'}),
    on='cod_n2', how='left'
)


# %%
def clasificar_ipe(valor):
    if np.isnan(valor):
        return np.nan
    if valor >= -0.5:
        return 0
    elif valor >= -1.0:
        return 1
    elif valor >= -1.5:
        return 2
    elif valor >= -2.0:
        return 3
    else:
        return 4

cuencas_df['IPE_1'] = cuencas_df['1_mes'].apply(clasificar_ipe)
cuencas_df['IPE_3'] = cuencas_df['3_meses'].apply(clasificar_ipe)
cuencas_df['IPE_6'] = cuencas_df['6_meses'].apply(clasificar_ipe)
cuencas_df['IPE_12'] = cuencas_df['12_meses'].apply(clasificar_ipe)


# drop columns 1_mes, 3_meses, 6_meses, 12_meses
# cuencas_df.drop(columns=['1_mes', '3_meses', '6_meses', '12_meses'], inplace=True)

# %%
# 6. Evaluar criterios de alerta de sequía por fila

# Normalidad: IEH_1 > 2, IEH_3 >= 3, IPE_3 <= 2, IPE_6 <= 2 → cumple 3 de 4 → 1
cuencas_df['NORMALIDAD'] = (
    (cuencas_df['IEH_1'] > 2).astype(int) +
    (cuencas_df['IEH_3'] >= 3).astype(int) +
    (cuencas_df['IPE_3'] <= 2).astype(int) +
    (cuencas_df['IPE_6'] <= 2).astype(int)
>= 3).astype(int)


# %%
cuencas_df['MODERADO'] = ((
    (cuencas_df['IEH_1'] <= 2).astype(int) +
    (cuencas_df['IEH_3'] <= 2).astype(int) +
    (cuencas_df['IPE_3'] >= 3).astype(int) +
    (cuencas_df['IPE_6'] >= 2).astype(int)
>= 2).astype(int) * 2)

# %%
cuencas_df['SEVERO'] = ((
    (cuencas_df['IEH_1'] <= 1).astype(int) +
    (cuencas_df['IEH_3'] <= 2).astype(int) +
    (cuencas_df['IPE_6'] >= 3).astype(int) +
    (cuencas_df['IPE_12'] >= 2).astype(int)
>= 3).astype(int) * 3)

# %%
cuencas_df['EXTREMO'] = ((
    (cuencas_df['IEH_1'] == 1).astype(int) +
    (cuencas_df['IEH_3'] == 1).astype(int) +
    (cuencas_df['IPE_6'] >= 4).astype(int) +
    (cuencas_df['IPE_12'] >= 3).astype(int)
>= 4).astype(int) * 4)

# %%
# 7. Asignar code_advertencia como el valor máximo entre NORMALIDAD, MODERADO, SEVERO, EXTREMO
cuencas_df['code_advertencia'] = cuencas_df[['NORMALIDAD', 'MODERADO', 'SEVERO', 'EXTREMO']].max(axis=1)
# %%
# 8. Crear columna ESTADO_ACTUAL y colorear según code_advertencia
estado_map = {1: 'NORMALIDAD', 2: 'MODERADO', 3: 'SEVERO', 4: 'EXTREMO'}
color_map = {'NORMALIDAD': '#D9D9D9', 'MODERADO': '#FAD463', 'SEVERO': '#F5B183', 'EXTREMO': '#EE4565'}

cuencas_df['ESTADO_ACTUAL'] = cuencas_df['code_advertencia'].map(estado_map).fillna('')

def colorear_estado(val):
    color = color_map.get(val, '')
    return f'background-color: {color}' if color else ''
# %%
# replace advertenci column from cuencas using the column ESTADO_ACTUAL from cuencas_df
cuencas = cuencas.merge(cuencas_df[['cod_n2', 'ESTADO_ACTUAL']], on='cod_n2', how='left')
# drop advertenci column from cuencas
cuencas.drop(columns=['advertenci'], inplace=True)
# rename ESTADO_ACTUAL to warning
cuencas.rename(columns={'ESTADO_ACTUAL': 'ADVER'}, inplace=True)

# %%
# Save cuencas to shapefile. Use in the file name the ano-mes of the data used to calculate the advertencia
cuencas.to_file(f'qgis_status_outlook/shapefiles/Advertencia_{ano}-{mes}.shp')