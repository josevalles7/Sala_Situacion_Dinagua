# %% [markdown]
# # Generar mapa distribución lluvia registrada en cuenca nivel 2

# %% [markdown]
# ## Importar librerias

# %%
import pandas as pd
import numpy as np; np.random.seed(0)
import matplotlib.pylab as plt
import seaborn as sns
import requests
import json
import locale
locale.setlocale(locale.LC_TIME, "es_ES")

import matplotlib.font_manager as fm
import argparse


# %% [markdown]
# ## Acceder a los datos de precipitación procesadas en Delft-FEWS para Cuencas Hidrográficas Nivel 2
# 
# **Importante** Se recomienda estar conectado a la VPN de Presidencia para acceder a travez de Servicio web 
# Define arguments 
parser = argparse.ArgumentParser(
                    prog='daily_rainfall_n2.py',
                    description='Plot SDI for a specific station and time scales',
                    epilog='Jose Valles, DINAGUA, 26082024')
parser.add_argument('user_start_date', help='fecha_inicio en formato YYYY-MM-DD')      
parser.add_argument('user_end_date', help='fecha_fin en formato YYYY-MM-DD')     

args = parser.parse_args()

user_start_date = args.user_start_date
adjust_start_date = pd.to_datetime(user_start_date) + pd.Timedelta(days=1)
user_end_date = args.user_end_date
adjust_end_date = pd.to_datetime(user_end_date) + pd.Timedelta(days=1)

# %%
# URL de acceso al servicio web de producción de FEWS-Uruguay
# url_base = 'http://testterh-fssaws:8080/FewsWebServices/rest/fewspiservice/v1/timeseries?'
url_base = 'http://prodterh-fssaws:8080/FewsWebServices/rest/fewspiservice/v1/timeseries?'
headers = {'Accept':'application/json'}
# Parametros de busqueda para MAP en cuenca nivel 2
documentVersion='1.24'
documentFormat='PI_JSON'
filterid = 'CuencaNivel2'
parameterIds = 'P.cuenca'
moduleInstanceIds = 'PreprocessP'

# Fecha de inicio de busqueda y finalización. Importante brindar la fecha en UTC
# Formato requerido por FEWS: yyyy-MM-dd'T'HH:mm:ss'Z'
startTime = adjust_start_date.strftime('%Y-%m-%dT10:00:00Z')
endTime = adjust_end_date.strftime('%Y-%m-%dT10:00:00Z')

print(f"Parámetros de búsqueda:")
print(f"  Fecha inicio: {startTime}")
print(f"  Fecha fin: {endTime}")

# URL de busqueda de datos de MAP 
url = f"{url_base}filterId={filterid}&parameterIds={parameterIds}&moduleInstanceIds={moduleInstanceIds}&startTime={startTime}&endTime={endTime}&documentFormat={documentFormat}"

# %%
# Abrir consulta con parametros de busqueda
try:
    print(f"Conectando a: {url}")
    r = requests.get(url, headers=headers, timeout=30)
    
    # Validar status code
    if r.status_code != 200:
        print(f"Error: Status Code {r.status_code}")
        print(f"Respuesta: {r.text[:500]}")
        raise ValueError(f"Servicio web retornó: {r.status_code}")
    
    # Validar que la respuesta no esté vacía
    if not r.content:
        print("Error: La respuesta del servidor está vacía")
        print("Posibles causas: VPN desconectada, servicio web no disponible o rango de fechas sin datos")
        raise ValueError("Respuesta vacía del servidor")
    
    # Intentar parsear JSON
    data = json.loads(r.content.decode('utf-8'))
    print(f"✓ Datos obtenidos exitosamente: {len(data.get('timeSeries', []))} series temporales")
    
except requests.exceptions.Timeout:
    print("Error: Timeout - El servidor tardó demasiado en responder")
    raise
except requests.exceptions.ConnectionError:
    print("Error: No se puede conectar al servidor. Verificar VPN y conectividad")
    raise
except json.JSONDecodeError as e:
    print(f"Error: Respuesta inválida - No es JSON válido")
    print(f"Contenido: {r.text[:200]}")
    raise
except Exception as e:
    print(f"Error inesperado: {str(e)}")
    raise
finally:
    if 'r' in locals():
        r.close()

# %%
allbasins_n2 = pd.read_csv(f'./waterbalance/cuencas_nombres.csv')

# %%
# Extrae los datos de MAP para cada cuenca hidrografica
df = pd.DataFrame()
for x in range(len(data['timeSeries'])):
    extraer_estacion = data['timeSeries'][x]['header']['locationId']
    datos_estacion = pd.DataFrame(data['timeSeries'][x]['events'])
    df[extraer_estacion] = datos_estacion['value'].values
# Une los datos de fecha y hora
datos_estacion = datos_estacion.drop(columns=['value','flag'])
datos_estacion = pd.to_datetime(datos_estacion['date'] + ' ' + datos_estacion['time'])
datos_estacion.to_frame()
# Une los datos con las fechas de serie de tiempo
df = pd.concat([datos_estacion, df],axis=1,join='inner')
df = df.rename(columns= {0: 'FECHA'})
# Convierte la hora de UTC a UTC-0300 (hora Montevideo)
df['FECHA'] = df['FECHA'] - pd.Timedelta(hours=3)
df['FECHA'] = df['FECHA'] - pd.Timedelta(days=1)
df.set_index('FECHA')
df.sort_index(ascending=True)
df = df.filter(regex='^(?!6060)')

# %% [markdown]
# ## Utilizar si no se tiene en funcionamiento el WS de FEWS

# %%
"""
df = pd.read_csv(f'Pmonthly_backup.csv')
df['FECHA'] = pd.to_datetime(df['FECHA'])
df['FECHA'] = df['FECHA'] - pd.Timedelta(days=1)
display(df.tail(6))
"""

# %%
cols = ['FECHA','63','67','28','52','45','42','40','31','33','32','30','12','13','44','10','15','27','29','24','22','26','20','58','55','54','57','50','43','17','23','65','21','61','64','68','66','62','60','53','51','41','14','11','16','19','18','56']
df = df[cols]

# %%
piv = pd.pivot_table(df,columns=["FECHA"])
piv[piv < 0] = np.NaN

# %%
piv2 = piv.transpose()

# %%
# piv2.to_clipboard(excel=True, sep=',', index=False)

# %% [markdown]
# ## Funciones para Generar Plots

# %%
import matplotlib
from matplotlib import pyplot as plt
from cProfile import label
from matplotlib.pyplot import axis
from numpy import size, sort

def plot_heatmap_transposed(piv2_df, df_original, allbasins_df, output_file=None):
    """
    Genera un heatmap con datos transpostos (fechas en rows, cuencas en columns).
    
    Parameters:
    -----------
    piv2_df : pd.DataFrame
        Dataframe transpuesto (pivote con fechas como index)
    df_original : pd.DataFrame
        Dataframe original con columna FECHA
    allbasins_df : pd.DataFrame
        Dataframe con información de cuencas
    """
    font_size = 12
    fig, ax = plt.subplots(figsize=(28, 14))
    
    values = piv2_df.to_numpy(dtype=float)
    
    cmap = "Blues"
    
    ax = sns.heatmap(piv2_df, square=True, cmap=cmap, annot=False, vmin=0, vmax=100,
                     linewidths=1.0, linecolor='black', annot_kws={'fontsize': 8},
                     cbar_kws={"shrink": 0.5, "label": 'Precipitación [mm]'},
                     mask=values < 1, ax=ax)
    
    ax.set_title('Lluvia registrada en cuencas hidrográficas nivel 2', pad=20, loc='center', size=18)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0)
    
    ax.set_ylabel('Día-Mes-Año', rotation=90, labelpad=10, size=font_size)
    ax.set_yticklabels(df_original['FECHA'].dt.strftime('%d-%b'), fontsize=font_size)
    
    ax.set_xlabel('Codigo de cuenca hidrográfica nivel 2', rotation=0, labelpad=10, fontsize=font_size)
    ax.tick_params(axis='x', labelsize=font_size)
    
    colorbar = ax.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=font_size)
    ax.figure.axes[-1].yaxis.label.set_size(font_size)
    
    ax.set_xticklabels(allbasins_df.nombre, rotation=90)
    
    plt.rcParams.update({'font.family': 'Arial'})
    sns.set(font_scale=1.4)
    # plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_heatmap_grouped(piv_df, df_original, allbasins_df, output_file=None):
    """
    Genera un heatmap con agrupación por cuencas principales.
    
    Parameters:
    -----------
    piv_df : pd.DataFrame
        Dataframe pivotado (cuencas como rows, fechas como columns)
    df_original : pd.DataFrame
        Dataframe original con columna FECHA
    allbasins_df : pd.DataFrame
        Dataframe con información de cuencas
    """
    font_size = 12
    factor_delta = 2
    ancho_linea = 2
    
    # Definir mapeo de grupos
    group_map = {
        '1': 'Río Uruguay',
        '2': 'Río de la Plata',
        '3': 'Océano Atlántico',
        '4': 'Laguna Merín',
        '5': 'Río Negro',
        '6': 'Río Santa Lucia'
    }
    
    basin_groups = [group_map.get(str(code)[0], "Otro") for code in piv_df.index]
    change_indices = np.where(np.array(basin_groups)[:-1] != np.array(basin_groups)[1:])[0]
    
    fig, ax = plt.subplots(figsize=(28, 14))
    values = piv_df.to_numpy(dtype=float)
    
    sns.set(font_scale=1)
    plt.subplots_adjust(left=0.3)
    
    ax = sns.heatmap(piv_df, square=True, cmap="Blues", vmin=0, vmax=100,
                     annot=False, linewidths=1.0, linecolor='black',
                     annot_kws={'fontsize': 8},
                     cbar_kws={"shrink": 0.5, "label": 'Precipitación [mm]'},
                     mask=values < 3, ax=ax)
    
    # Agregar etiquetas de grupo y bordes
    last_idx = 0
    x_lim_left = -1.0
    
    for idx in list(change_indices) + [len(basin_groups) - 1]:
        mid_point = (last_idx + idx + 1) / 2
        group_name = basin_groups[last_idx]
        
        ax.annotate(group_name, xy=(x_lim_left + 0.05, mid_point),
                    xycoords=('axes fraction', 'data'),
                    ha='left', va='center', fontweight='bold', fontsize=16)
        
        ax.axhline(y=idx + 1, xmin=x_lim_left, xmax=1.0,
                   color='black', linewidth=ancho_linea, clip_on=False)
        
        if last_idx == 0:
            ax.axhline(y=0, xmin=x_lim_left, xmax=1.0,
                       color='black', linewidth=ancho_linea, clip_on=False)
        
        last_idx = idx + 1
    
    ax.vlines(x=x_lim_left, ymin=0, ymax=len(piv_df), transform=ax.get_yaxis_transform(),
              color='black', linewidth=ancho_linea, clip_on=False)
    
    ax.vlines(x=x_lim_left + 0.33, ymin=0, ymax=len(piv_df), transform=ax.get_yaxis_transform(),
              color='black', linewidth=ancho_linea, clip_on=False)
    
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
    
    ax.set_xlabel('Día-Mes', rotation=0, labelpad=10, size=font_size)
    ax.set_xticklabels(df_original['FECHA'].dt.strftime('%d-%b'), fontsize=font_size)
    
    ax.tick_params(axis='y', labelsize=font_size)
    ax.set_yticklabels(allbasins_df.nombre, rotation=0)
    
    colorbar = ax.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=font_size)
    colorbar.ax.yaxis.set_tick_params(rotation=90)
    colorbar.ax.yaxis.set_label_position('left')
    ax.figure.axes[-1].yaxis.label.set_size(font_size)
    
    plt.rcParams.update({'font.family': 'Arial'})
    sns.set(font_scale=1.4)
    # plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax


def plot_heatmap_simple(piv_df, df_original, allbasins_df, output_file=None):
    """
    Genera un heatmap simple sin agrupación.
    
    Parameters:
    -----------
    piv_df : pd.DataFrame
        Dataframe pivotado (cuencas como rows, fechas como columns)
    df_original : pd.DataFrame
        Dataframe original con columna FECHA
    allbasins_df : pd.DataFrame
        Dataframe con información de cuencas
    """
    font_size = 14
    
    fig, ax = plt.subplots(figsize=(28, 14))
    values = piv_df.to_numpy(dtype=float)
    
    myColors = ['#ffffff', '#F7FCF0', '#E0F3DB', '#CCEBC5', '#A8DDB5',
                '#7BCCC4', '#4EB3D3', '#2B8CBE', '#0868AC', '#084081']
    cmap2 = matplotlib.colors.LinearSegmentedColormap.from_list('Custom', myColors, len(myColors))
    
    sns.set(font_scale=1)
    
    ax = sns.heatmap(piv_df, square=True, cmap="Blues", vmin=0, vmax=100,
                     annot=False, linewidths=1.0, linecolor='black',
                     annot_kws={'fontsize': 8},
                     cbar_kws={"shrink": 0.5, "label": 'Precipitación [mm]'},
                     mask=values < 3, ax=ax)
    
    ax.set_title('Lluvia registrada en cuencas hidrográficas nivel 2', pad=20, loc='center', size=18)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
    
    ax.set_xlabel('Día-Mes-Año', rotation=0, labelpad=10, size=font_size)
    ax.set_xticklabels(df_original['FECHA'].dt.strftime('%d-%b'), fontsize=font_size)
    
    ax.set_ylabel('Codigo de cuenca hidrográfica nivel 2', rotation=90, labelpad=10, fontsize=font_size)
    ax.tick_params(axis='y', labelsize=font_size)
    
    ax.set_yticklabels(allbasins_df.nombre, rotation=0)
    
    colorbar = ax.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=font_size)
    colorbar.ax.yaxis.set_tick_params(rotation=90)
    colorbar.ax.yaxis.set_label_position('left')
    ax.figure.axes[-1].yaxis.label.set_size(font_size)
    
    plt.rcParams.update({'font.family': 'Arial'})
    sns.set(font_scale=1.4)
    # plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax


# %% [markdown]
# ## Ejecutar Plots

# %%
# Plot 1: Heatmap Transpuesto
# fig1, ax1 = plot_heatmap_transposed(piv2, df, allbasins_n2)

# %%
# Plot 2: Heatmap con Agrupación por Cuencas
fig2, ax2 = plot_heatmap_grouped(piv, df, allbasins_n2, output_file="./waterbalance/output_png/08_rainfall_heatmap.png")
print("Grafico generado exitosamente.")

# %%
# Plot 3: Heatmap Simple
# fig3, ax3 = plot_heatmap_simple(piv, df, allbasins_n2)


