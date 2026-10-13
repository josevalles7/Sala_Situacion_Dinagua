# %% [markdown]
# # HydroSOS Streamflow Status Product Methodology
# #### Jose Valles (jose.valles.leon@gmail.com)

# %% [markdown]
# ## One month status product
# 
# ### Importing the data and finding missing dates

# %%
# Importing the libraries
from unittest import result

import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import argparse 
plt.style.use('classic')

sns.set()

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='calculate_hydrological_status',
                    description='Plot ESP outlook from codcuenca n2',
                    epilog='Jose Valles, DINAGUA, 26082024')

# 
parser.add_argument('end_date', help='end date for the discharge plot in format YYYY-MM-DD')      

args = parser.parse_args()

# %%
class EstadoHidrologico:
    def __init__(self, station_name, values, flow_cat):
        self.station_name = station_name
        self.values = values
        self.flow_cat = flow_cat
        self.DISCHARGE_MONTHLY = None

    def cargar_datos(self):
        self.DISCHARGE_MONTHLY = pd.read_csv(
            f'./waterbalance/input/{self.station_name}.csv',
            parse_dates=['Fecha'],
            index_col="Fecha",
            dayfirst=True,
            na_values="NA"
        )
        self.DISCHARGE_MONTHLY['year'] = self.DISCHARGE_MONTHLY.index.year
        self.DISCHARGE_MONTHLY['month'] = self.DISCHARGE_MONTHLY.index.month
        self.DISCHARGE_MONTHLY['water_year'] = self.DISCHARGE_MONTHLY.index.year.where(
            self.DISCHARGE_MONTHLY.index.month < 4, self.DISCHARGE_MONTHLY.index.year + 1
        )
        self.DISCHARGE_MONTHLY.index = self.DISCHARGE_MONTHLY.index.map(lambda t: t.replace(day=1))
        return self.DISCHARGE_MONTHLY

    def estado_mensual(self):
        # Climatologia 1981-2010
        ref_mask = (self.DISCHARGE_MONTHLY['year'] >= 1981) & (self.DISCHARGE_MONTHLY['year'] <= 2010)
        clim_mean = self.DISCHARGE_MONTHLY.loc[ref_mask].groupby('month')['Caudal'].mean()

        # Vectorizacion por mes
        self.DISCHARGE_MONTHLY['rank_average'] = self.DISCHARGE_MONTHLY.groupby('month')['Caudal'].rank()
        self.DISCHARGE_MONTHLY['non_missing'] = self.DISCHARGE_MONTHLY.groupby('month')['Caudal'].transform(lambda s: s.notna().sum())
        
        # Mapeo de la media climatológica y cálculo de anomalía porcentual
        self.DISCHARGE_MONTHLY['mean'] = self.DISCHARGE_MONTHLY['month'].map(clim_mean)
        self.DISCHARGE_MONTHLY['average_percentage'] = (self.DISCHARGE_MONTHLY['Caudal'] - self.DISCHARGE_MONTHLY['mean']) / self.DISCHARGE_MONTHLY['mean']

        # Formula de Cunnane (alphap = 0.4, betap = 0.4)
        alphap, betap = 0.4, 0.4
        self.DISCHARGE_MONTHLY['percentile'] = (self.DISCHARGE_MONTHLY['rank_average'] - alphap) / (self.DISCHARGE_MONTHLY['non_missing'] + 1 - alphap - betap)

        criteria = [
            self.DISCHARGE_MONTHLY['percentile'].between(0.90, 1.00),
            self.DISCHARGE_MONTHLY['percentile'].between(0.75, 0.90),
            self.DISCHARGE_MONTHLY['percentile'].between(0.25, 0.75),
            self.DISCHARGE_MONTHLY['percentile'].between(0.10, 0.25),
            self.DISCHARGE_MONTHLY['percentile'].between(0.00, 0.10)
        ]

        self.DISCHARGE_MONTHLY['percentile_range'] = np.select(criteria, self.values, default=None)
        self.DISCHARGE_MONTHLY['flowcat'] = np.select(criteria, self.flow_cat, default=np.nan)

        return self.DISCHARGE_MONTHLY

    def estado_trimestral(self):
        # Media móvil de 3 meses
        DISCHARGE_THREE_MONTHS = pd.DataFrame(
            self.DISCHARGE_MONTHLY['Caudal'].rolling(3).apply(lambda x: x.mean() if x.isnull().sum() * 100 / len(x) < 0.5 else np.nan),
            index=self.DISCHARGE_MONTHLY.index
        )
        DISCHARGE_THREE_MONTHS['startMonth'] = (DISCHARGE_THREE_MONTHS.index - pd.DateOffset(months=2)).month
        DISCHARGE_THREE_MONTHS['endMonth'] = DISCHARGE_THREE_MONTHS.index.month
        DISCHARGE_THREE_MONTHS['year'] = DISCHARGE_THREE_MONTHS.index.year

        ref_mask = (DISCHARGE_THREE_MONTHS['year'] >= 1981) & (DISCHARGE_THREE_MONTHS['year'] <= 2010)
        clim_mean = DISCHARGE_THREE_MONTHS.loc[ref_mask].groupby('startMonth')['Caudal'].mean()

        DISCHARGE_THREE_MONTHS['rank_average'] = DISCHARGE_THREE_MONTHS.groupby('startMonth')['Caudal'].rank()
        DISCHARGE_THREE_MONTHS['non_missing'] = DISCHARGE_THREE_MONTHS.groupby('startMonth')['Caudal'].transform(lambda s: s.notna().sum())
        DISCHARGE_THREE_MONTHS['mean'] = DISCHARGE_THREE_MONTHS['startMonth'].map(clim_mean)
        DISCHARGE_THREE_MONTHS['average_percentage'] = (DISCHARGE_THREE_MONTHS['Caudal'] - DISCHARGE_THREE_MONTHS['mean']) / DISCHARGE_THREE_MONTHS['mean']

        alphap, betap = 0.4, 0.4
        DISCHARGE_THREE_MONTHS['percentile'] = (DISCHARGE_THREE_MONTHS['rank_average'] - alphap) / (DISCHARGE_THREE_MONTHS['non_missing'] + 1 - alphap - betap)

        criteria_three_months = [
            DISCHARGE_THREE_MONTHS['percentile'].between(0.90, 1.00),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.75, 0.90),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.25, 0.75),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.10, 0.25),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.00, 0.10)
        ]

        DISCHARGE_THREE_MONTHS['percentile_range'] = np.select(criteria_three_months, self.values, default=None)
        DISCHARGE_THREE_MONTHS['flowcat'] = np.select(criteria_three_months, self.flow_cat, default=np.nan)

        row_labels = {1:'JFM', 2:'FMA', 3:'MAM', 4:'AMJ', 5:'MJJ', 6:'JJA',
                      7:'JAS', 8:'ASO', 9:'SON', 10:'OND', 11:'NDE', 12:'DEF'}
        DISCHARGE_THREE_MONTHS['period'] = DISCHARGE_THREE_MONTHS['startMonth'].map(row_labels)
        return DISCHARGE_THREE_MONTHS

    def estado_anual(self):
        DISCHARGE_TWELVE_MONTHS = pd.DataFrame(
            self.DISCHARGE_MONTHLY['Caudal'].rolling(12).apply(lambda x: x.mean() if x.isnull().sum() * 100 / len(x) < 0.5 else np.nan),
            index=self.DISCHARGE_MONTHLY.index
        )
        DISCHARGE_TWELVE_MONTHS['startMonth'] = (DISCHARGE_TWELVE_MONTHS.index - pd.DateOffset(months=11)).month
        DISCHARGE_TWELVE_MONTHS['endMonth'] = DISCHARGE_TWELVE_MONTHS.index.month
        DISCHARGE_TWELVE_MONTHS['year'] = DISCHARGE_TWELVE_MONTHS.index.year

        ref_mask = (DISCHARGE_TWELVE_MONTHS['year'] >= 1981) & (DISCHARGE_TWELVE_MONTHS['year'] <= 2010)
        clim_mean = DISCHARGE_TWELVE_MONTHS.loc[ref_mask].groupby('startMonth')['Caudal'].mean()

        DISCHARGE_TWELVE_MONTHS['rank_average'] = DISCHARGE_TWELVE_MONTHS.groupby('startMonth')['Caudal'].rank()
        DISCHARGE_TWELVE_MONTHS['non_missing'] = DISCHARGE_TWELVE_MONTHS.groupby('startMonth')['Caudal'].transform(lambda s: s.notna().sum())
        DISCHARGE_TWELVE_MONTHS['mean'] = DISCHARGE_TWELVE_MONTHS['startMonth'].map(clim_mean)
        DISCHARGE_TWELVE_MONTHS['average_percentage'] = (DISCHARGE_TWELVE_MONTHS['Caudal'] - DISCHARGE_TWELVE_MONTHS['mean']) / DISCHARGE_TWELVE_MONTHS['mean']

        alphap, betap = 0.4, 0.4
        DISCHARGE_TWELVE_MONTHS['percentile'] = (DISCHARGE_TWELVE_MONTHS['rank_average'] - alphap) / (DISCHARGE_TWELVE_MONTHS['non_missing'] + 1 - alphap - betap)

        criteria_twelve_months = [
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.90, 1.00),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.75, 0.90),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.25, 0.75),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.10, 0.25),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.00, 0.10)
        ]

        DISCHARGE_TWELVE_MONTHS['percentile_range'] = np.select(criteria_twelve_months, self.values, default=None)
        DISCHARGE_TWELVE_MONTHS['flowcat'] = np.select(criteria_twelve_months, self.flow_cat, default=np.nan)
        return DISCHARGE_TWELVE_MONTHS

# %%
# Definir la fecha de finalización para el HeatMap
fecha_fin = args.end_date
back_months = 18

# Generar la secuencia de fechas de los X meses anteriores, incluyendo el mes de la fecha de finalización
fechas = pd.date_range(end=fecha_fin, periods=back_months, freq='MS')
# Crear un DataFrame vacío con las fechas como índice
df_cat = pd.DataFrame(index=fechas)
df_cat.index.name = 'FECHA'

# Importar nombre de subcuencas
ALL_BASIN = pd.read_csv(f'./waterbalance/cuenca_nivel2.csv',index_col="Codigo")
allbasins_n2 = pd.read_csv(f'./waterbalance/cuencas_nombres.csv')

# %%
values = ['High flow','Above normal','Normal range','Below normal','Low flow']
flow_cat = [5,4,3,2,1]
for columna, datos in ALL_BASIN.items():
    # print(columna)
    # Create model instance 
    hydro_status = EstadoHidrologico(station_name = columna,values=values,flow_cat=flow_cat)
    DISCHARGE_MONTHLY = hydro_status.cargar_datos()
    STATUS_ONE_MONTH = hydro_status.estado_mensual()
    STATUS_ONE_MONTH = STATUS_ONE_MONTH.rename_axis('date')
    # Extract categories from the last back_months variable
    df_cat[columna] = STATUS_ONE_MONTH.loc[fechas]['flowcat']
    

# %%
# Hoursecleaning 
df_cat_float = df_cat.astype(float)
df_cat_float = df_cat_float.reset_index()
piv = pd.pivot_table(df_cat_float,columns=["FECHA"])

# %% [markdown]
# ### Plot the HeatMap

# %% Funciones para generar heatmaps de estado hidrológico

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm 
import locale
import numpy as np

locale.setlocale(locale.LC_TIME, "es_ES")


def plot_heatmap_status_simple(piv_df, df_dates, allbasins_df, output_file=None):
    """
    Genera un heatmap simple del estado hidrológico sin agrupación de cuencas.
    
    Parameters:
    -----------
    piv_df : pd.DataFrame
        Dataframe pivotado (cuencas como rows, fechas como columns)
    df_dates : pd.DataFrame
        Dataframe con columna FECHA
    allbasins_df : pd.DataFrame
        Dataframe con información de cuencas (columna 'nombre')
    output_file : str, optional
        Ruta para guardar la figura. Si es None, no guarda.
    
    Returns:
    --------
    fig, ax : matplotlib.figure.Figure, matplotlib.axes.Axes
    """
    # Definir colores y normalización
    colors = ['#CD233F', '#FFA885', '#E7E2BC', '#8ECEEE', '#2C7DCD']
    cmap = ListedColormap(colors)
    bounds = [1, 2, 3, 4, 5, 6]
    my_norm = BoundaryNorm(bounds, ncolors=len(colors))
    
    font_size = 12
    factor_delta = 2
    
    # Crear el heatmap
    fig, ax = plt.subplots(figsize=(28, 14))
    ax = sns.heatmap(piv_df, 
                     square=True, 
                     cmap=cmap, 
                     vmin=1, 
                     vmax=5,
                     annot=False,
                     norm=my_norm,
                     linewidths=1,
                     linecolor='black', 
                     ax=ax, 
                     annot_kws={'fontsize': font_size, 'fontweight': 'bold'},
                     cbar_kws={'label': '', 'orientation': 'vertical', 'shrink': 0.3})
    
    ax.set_title('Estado Hidrológico en Uruguay', pad=20, loc='center', size=18)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)
    
    ax.set_xlabel('Fecha', rotation=0, labelpad=10, size=font_size + factor_delta)
    ax.set_xticklabels(df_dates['FECHA'].dt.strftime('%b-%y'), fontsize=font_size + factor_delta)
    
    ax.set_ylabel('Subcuenca Hidrográfica', rotation=90, labelpad=10, fontsize=font_size + factor_delta)
    ax.tick_params(axis='y', labelsize=font_size + factor_delta)
    
    ax.set_yticklabels(allbasins_df.nombre, rotation=0)
    
    # Configurar colorbar
    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks([(b0 + b1) / 2 for b0, b1 in zip(bounds[:-1], bounds[1:])])
    colorbar.set_ticklabels(['Flujo bajo', 'Por debajo de lo normal', 'Normal', 
                             'Por encima de lo normal', 'Flujo alto'])
    colorbar.ax.tick_params(labelsize=font_size)
    colorbar.ax.yaxis.set_tick_params(rotation=0)
    colorbar.ax.yaxis.set_label_position('left')
    ax.figure.axes[-1].yaxis.label.set_size(font_size)
    
    plt.rcParams.update({'font.family': 'Arial'})
    sns.set(font_scale=1.4)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax


def plot_heatmap_status_grouped(piv_df, df_dates, allbasins_df, output_file=None):
    """
    Genera un heatmap del estado hidrológico con agrupación por cuencas principales.
    
    Parameters:
    -----------
    piv_df : pd.DataFrame
        Dataframe pivotado (cuencas como rows, fechas como columns)
    df_dates : pd.DataFrame
        Dataframe con columna FECHA
    allbasins_df : pd.DataFrame
        Dataframe con información de cuencas (columna 'nombre')
    output_file : str, optional
        Ruta para guardar la figura. Si es None, no guarda.
    
    Returns:
    --------
    fig, ax : matplotlib.figure.Figure, matplotlib.axes.Axes
    """
    # Definir colores y normalización
    colors = ['#CD233F', '#FFA885', '#E7E2BC', '#8ECEEE', '#2C7DCD']
    cmap = ListedColormap(colors)
    bounds = [1, 2, 3, 4, 5, 6]
    my_norm = BoundaryNorm(bounds, ncolors=len(colors))
    
    font_size = 12
    factor_delta = 2
    ancho_linea = 2
    
    # Mapeo de grupos de cuencas
    group_map = {
        '1': 'Río Uruguay',
        '2': 'Río de la Plata',
        '3': 'Océano Atlántico',
        '4': 'Laguna Merín',
        '5': 'Río Negro',
        '6': 'Río Santa Lucia'
    }
    
    # Obtener grupos para cada fila
    basin_groups = [group_map.get(str(code)[0], "Otro") for code in piv_df.index]
    change_indices = np.where(np.array(basin_groups)[:-1] != np.array(basin_groups)[1:])[0]
    
    # Crear heatmap
    fig, ax = plt.subplots(figsize=(28, 14))
    plt.subplots_adjust(left=0.3)
    
    sns.heatmap(piv_df, square=True, cmap=cmap, norm=my_norm, linewidths=1,
                linecolor='black', ax=ax, cbar_kws={'shrink': 0.3})
    
    # Agregar etiquetas de grupo y bordes
    last_idx = 0
    x_lim_left = -1.7
    
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
    
    # Líneas verticales
    ax.vlines(x=x_lim_left, ymin=0, ymax=len(piv_df), transform=ax.get_yaxis_transform(),
              color='black', linewidth=ancho_linea, clip_on=False)
    
    ax.vlines(x=x_lim_left + 0.5, ymin=0, ymax=len(piv_df), transform=ax.get_yaxis_transform(),
              color='black', linewidth=ancho_linea, clip_on=False)
    
    # Formateo de etiquetas
    ax.set_yticklabels(allbasins_df.nombre, rotation=0, fontsize=font_size + factor_delta)
    ax.set_xticklabels(df_dates['FECHA'].dt.strftime('%b-%y').str.upper(), fontsize=font_size + factor_delta)
    
    # Configurar colorbar
    colorbar = ax.collections[0].colorbar
    colorbar.set_ticks([(b0 + b1) / 2 for b0, b1 in zip(bounds[:-1], bounds[1:])])
    colorbar.set_ticklabels(['Flujo bajo', 'Por debajo de lo normal', 'Normal',
                             'Por encima de lo normal', 'Flujo alto'])
    colorbar.ax.tick_params(labelsize=font_size)
    colorbar.ax.yaxis.set_tick_params(rotation=0)
    colorbar.ax.yaxis.set_label_position('left')
    ax.figure.axes[-1].yaxis.label.set_size(font_size)
    
    plt.rcParams.update({'font.family': 'Arial'})
    sns.set(font_scale=1.4)
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    
    return fig, ax


# %% Ejecutar los gráficos

# Gráfico 1: Heatmap simple
# fig1, ax1 = plot_heatmap_status_simple(piv, df_cat_float, allbasins_n2, output_file="./waterbalance/output_png/07_status_heatmap_simple.png")
# plt.close(fig1)

# Gráfico 2: Heatmap con agrupación
fig2, ax2 = plot_heatmap_status_grouped(piv, df_cat_float, allbasins_n2,
                                        output_file="./waterbalance/output_png/07_status_heatmap.png")
plt.close(fig2)