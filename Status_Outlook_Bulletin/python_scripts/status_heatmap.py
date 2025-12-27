# %% [markdown]
# # HydroSOS Streamflow Status Product Methodology
# #### Jose Valles (jose.valles.leon@gmail.com)

# %% [markdown]
# ## One month status product
# 
# ### Importing the data and finding missing dates

# %%
# Importing the libraries
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
    def __init__(self, station_name,values,flow_cat):
        self.station_name = station_name
        self.values = values
        self.flow_cat = flow_cat
        self.DISCHARGE_MONTHLY = None

    def cargar_datos(self):
        self.DISCHARGE_MONTHLY = pd.read_csv(f'./waterbalance/input/{self.station_name}.csv',parse_dates=['Fecha'],index_col="Fecha",dayfirst=True,na_values="NA")
        self.DISCHARGE_MONTHLY['year'] = self.DISCHARGE_MONTHLY.index.year
        self.DISCHARGE_MONTHLY['month'] = self.DISCHARGE_MONTHLY.index.month
        self.DISCHARGE_MONTHLY['water_year'] = self.DISCHARGE_MONTHLY.index.year.where(self.DISCHARGE_MONTHLY.index.month < 4, self.DISCHARGE_MONTHLY.index.year + 1)
        self.DISCHARGE_MONTHLY.index = self.DISCHARGE_MONTHLY.index.map(lambda t: t.replace(day=1))
        return self.DISCHARGE_MONTHLY

    def estado_mensual(self):
        # Climatologia
        DISCHARGE_SELECTION = self.DISCHARGE_MONTHLY[(self.DISCHARGE_MONTHLY['year'] >= 1981) & (self.DISCHARGE_MONTHLY['year'] <= 2010)]
        DISCHARGE_AVERAGE = DISCHARGE_SELECTION.groupby(DISCHARGE_SELECTION.month).mean()
        DISCHARGE_AVERAGE = DISCHARGE_AVERAGE.reindex(columns=['Caudal'])
        # Calcular indicadores
        self.DISCHARGE_MONTHLY['average_percentage'] = np.nan
        self.DISCHARGE_MONTHLY['rank_average'] = np.nan
        self.DISCHARGE_MONTHLY['non_missing'] = np.nan

        for i in range(len(self.DISCHARGE_MONTHLY)):
            # Extract the current month 
            m = self.DISCHARGE_MONTHLY.month[i]
            # Extract the current year
            y = self.DISCHARGE_MONTHLY.year[i]
            self.DISCHARGE_MONTHLY.loc[self.DISCHARGE_MONTHLY.eval('month==@m & year==@y'),'rank_average']  = self.DISCHARGE_MONTHLY.query('month==@m')['Caudal'].rank()
            self.DISCHARGE_MONTHLY.loc[self.DISCHARGE_MONTHLY.eval('month==@m & year==@y'),'non_missing']  = self.DISCHARGE_MONTHLY.query('month==@m')["Caudal"].notnull().sum()
            self.DISCHARGE_MONTHLY.loc[self.DISCHARGE_MONTHLY.eval('month==@m & year==@y'),'average_percentage'] = (self.DISCHARGE_MONTHLY['Caudal'][i] - DISCHARGE_AVERAGE.query('month == @m')["Caudal"].item()) / DISCHARGE_AVERAGE.query('month == @m')["Caudal"].item()

        self.DISCHARGE_MONTHLY['percentile'] = self.DISCHARGE_MONTHLY['rank_average']/(self.DISCHARGE_MONTHLY['non_missing']+1)

        criteria = [self.DISCHARGE_MONTHLY['percentile'].between(0.90,1.00),
            self.DISCHARGE_MONTHLY['percentile'].between(0.75,0.90),
            self.DISCHARGE_MONTHLY['percentile'].between(0.25,0.75),
            self.DISCHARGE_MONTHLY['percentile'].between(0.10,0.25),
            self.DISCHARGE_MONTHLY['percentile'].between(0.00,0.10)]

        self.DISCHARGE_MONTHLY['percentile_range'] = np.select(criteria,self.values,None)
        self.DISCHARGE_MONTHLY['flowcat'] = np.select(criteria,self.flow_cat,pd.NA)

        return self.DISCHARGE_MONTHLY
    
    def estado_trimestral(self):
        # Agregar caudales
        DISCHARGE_THREE_MONTHS = pd.DataFrame(self.DISCHARGE_MONTHLY['Caudal'].rolling(3).apply(lambda x: x.mean() if x.isnull().sum()*100/len(x) < 0.5 else np.nan))
        # Agregar columnas
        DISCHARGE_THREE_MONTHS['startMonth'] = (DISCHARGE_THREE_MONTHS.index - pd.DateOffset(months=2)).month
        DISCHARGE_THREE_MONTHS['endMonth'] = DISCHARGE_THREE_MONTHS.index.month
        DISCHARGE_THREE_MONTHS['year'] = DISCHARGE_THREE_MONTHS.index.year
        DISCHARGE_THREE_MONTHS.index = DISCHARGE_THREE_MONTHS.index.map(lambda t: t.replace(day=1))
        # Climatologia
        DISCHARGE_SELECTION_THREE_MONTH = DISCHARGE_THREE_MONTHS[(DISCHARGE_THREE_MONTHS['year'] >= 1981) & (DISCHARGE_THREE_MONTHS['year'] < 2010)]
        DISCHARGE_AVERAGE_THREE_MONTH = DISCHARGE_SELECTION_THREE_MONTH.groupby(DISCHARGE_SELECTION_THREE_MONTH.startMonth).mean()
        DISCHARGE_AVERAGE_THREE_MONTH = DISCHARGE_AVERAGE_THREE_MONTH.reindex(columns=['Caudal'])
        # Calcular indicadores
        DISCHARGE_THREE_MONTHS['average_percentage'] = np.nan
        DISCHARGE_THREE_MONTHS['rank_average'] = np.nan
        DISCHARGE_THREE_MONTHS['non_missing'] = np.nan

        for i in range(len(DISCHARGE_THREE_MONTHS)):
            # Extract the current month 
            m = DISCHARGE_THREE_MONTHS.startMonth[i]
            # Extract the current year
            y = DISCHARGE_THREE_MONTHS.year[i]
            DISCHARGE_THREE_MONTHS.loc[DISCHARGE_THREE_MONTHS.eval('startMonth==@m & year==@y'),'rank_average']  = DISCHARGE_THREE_MONTHS.query('startMonth==@m')['Caudal'].rank()
            DISCHARGE_THREE_MONTHS.loc[DISCHARGE_THREE_MONTHS.eval('startMonth==@m & year==@y'),'non_missing']  = DISCHARGE_THREE_MONTHS.query('startMonth==@m')["Caudal"].notnull().sum()
            DISCHARGE_THREE_MONTHS.loc[DISCHARGE_THREE_MONTHS.eval('startMonth==@m & year==@y'),'average_percentage'] = (DISCHARGE_THREE_MONTHS['Caudal'][i] - DISCHARGE_AVERAGE_THREE_MONTH.query('startMonth == @m')["Caudal"].item()) / DISCHARGE_AVERAGE_THREE_MONTH.query('startMonth == @m')["Caudal"].item()

        DISCHARGE_THREE_MONTHS['percentile'] = DISCHARGE_THREE_MONTHS['rank_average']/(DISCHARGE_THREE_MONTHS['non_missing']+1)

        criteria_three_months = [DISCHARGE_THREE_MONTHS['percentile'].between(0.90,1.00),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.75,0.90),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.25,0.75),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.10,0.25),
            DISCHARGE_THREE_MONTHS['percentile'].between(0.00,0.10)]

        DISCHARGE_THREE_MONTHS['percentile_range'] = np.select(criteria_three_months,self.values,None)
        DISCHARGE_THREE_MONTHS['flowcat'] = np.select(criteria_three_months,self.flow_cat,pd.NA)

        row_labels = {1:'JFM',
             2:'FMA',
             3:'MAM',
             4:'AMJ',
             5:'MJJ',
             6:'JJA',
             7:'JAS',
             8:'ASO',
             9:'SON',
             10:'OND',
             11:'NDE',
             12:'DEF'}
        
        DISCHARGE_THREE_MONTHS['period'] = DISCHARGE_THREE_MONTHS['startMonth'].replace(row_labels) 
        return DISCHARGE_THREE_MONTHS
    
    def estado_anual(self):
        # Agrgar caudales
        DISCHARGE_TWELVE_MONTHS = pd.DataFrame(self.DISCHARGE_MONTHLY['Caudal'].rolling(12).apply(lambda x: x.mean() if x.isnull().sum()*100/len(x) < 0.5 else np.nan))
        DISCHARGE_TWELVE_MONTHS['startMonth'] = (DISCHARGE_TWELVE_MONTHS.index - pd.DateOffset(months=2)).month
        DISCHARGE_TWELVE_MONTHS['endMonth'] = DISCHARGE_TWELVE_MONTHS.index.month
        DISCHARGE_TWELVE_MONTHS['year'] = DISCHARGE_TWELVE_MONTHS.index.year
        DISCHARGE_TWELVE_MONTHS.index = DISCHARGE_TWELVE_MONTHS.index.map(lambda t: t.replace(day=1))
        # Climatologia
        DISCHARGE_SELECTION_TWELVE_MONTH = DISCHARGE_TWELVE_MONTHS[(DISCHARGE_TWELVE_MONTHS['year'] >= 1981) & (DISCHARGE_TWELVE_MONTHS['year'] < 2010)]
        DISCHARGE_AVERAGE_TWELVE_MONTH = DISCHARGE_SELECTION_TWELVE_MONTH.groupby(DISCHARGE_SELECTION_TWELVE_MONTH.startMonth).mean()
        DISCHARGE_AVERAGE_TWELVE_MONTH = DISCHARGE_AVERAGE_TWELVE_MONTH.reindex(columns=['Caudal'])
        # Calcular indice
        DISCHARGE_TWELVE_MONTHS['average_percentage'] = np.nan
        DISCHARGE_TWELVE_MONTHS['rank_average'] = np.nan
        DISCHARGE_TWELVE_MONTHS['non_missing'] = np.nan

        for i in range(len(DISCHARGE_TWELVE_MONTHS)):
            # Extract the current month 
            m = DISCHARGE_TWELVE_MONTHS.startMonth[i]
            # Extract the current year
            y = DISCHARGE_TWELVE_MONTHS.year[i]
            DISCHARGE_TWELVE_MONTHS.loc[DISCHARGE_TWELVE_MONTHS.eval('startMonth==@m & year==@y'),'rank_average']  = DISCHARGE_TWELVE_MONTHS.query('startMonth==@m')['Caudal'].rank()
            DISCHARGE_TWELVE_MONTHS.loc[DISCHARGE_TWELVE_MONTHS.eval('startMonth==@m & year==@y'),'non_missing']  = DISCHARGE_TWELVE_MONTHS.query('startMonth==@m')["Caudal"].notnull().sum()
            DISCHARGE_TWELVE_MONTHS.loc[DISCHARGE_TWELVE_MONTHS.eval('startMonth==@m & year==@y'),'average_percentage'] = (DISCHARGE_TWELVE_MONTHS['Caudal'][i] - DISCHARGE_AVERAGE_TWELVE_MONTH.query('startMonth == @m')["Caudal"].item()) / DISCHARGE_AVERAGE_TWELVE_MONTH.query('startMonth == @m')["Caudal"].item()
    
        DISCHARGE_TWELVE_MONTHS['percentile'] = DISCHARGE_TWELVE_MONTHS['rank_average']/(DISCHARGE_TWELVE_MONTHS['non_missing']+1)

        criteria_twelve_months = [DISCHARGE_TWELVE_MONTHS['percentile'].between(0.90,1.00),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.75,0.90),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.25,0.75),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.10,0.25),
            DISCHARGE_TWELVE_MONTHS['percentile'].between(0.00,0.10)]

        DISCHARGE_TWELVE_MONTHS['percentile_range'] = np.select(criteria_twelve_months,self.values,None)
        DISCHARGE_TWELVE_MONTHS['flowcat'] = np.select(criteria_twelve_months,self.flow_cat,pd.NA)
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
for columna, datos in ALL_BASIN.iteritems():
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

# %%
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm 
import locale

locale.setlocale(locale.LC_TIME, "es_ES")



# Definir colores discretos para cada categoría
colors = ['#CD233F', '#FFA885', '#E7E2BC', '#8ECEEE', '#2C7DCD']
cmap = ListedColormap(colors)

bounds = [1, 2, 3, 4, 5, 6]
my_norm = BoundaryNorm(bounds, ncolors=len(colors))

font_size = 12
factor_delta = 2

# Crear el heatmap
fig, ax = plt.subplots(figsize=(28,14))
ax = sns.heatmap(piv, 
                 square=True, 
                 cmap=cmap, 
                 vmin=1, 
                 vmax=5,
                 annot = False,
                 norm=my_norm,
                 linewidths=1,
                 linecolor='black', 
                 ax=ax, 
                 annot_kws={'fontsize': font_size, 'fontweight':'bold',},
                 cbar_kws={'label': '','orientation':'vertical','shrink': 0.3})

ax.set_title('Estado Hidrológico en Uruguay', pad=20, loc='center',size=18)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)

ax.set_xlabel('Fecha',rotation=0, labelpad=10,size=font_size+factor_delta)
ax.set_xticklabels(df_cat_float['FECHA'].dt.strftime('%b-%y'),fontsize=font_size+factor_delta)

ax.set_ylabel('Subcuenca Hidrográfica', rotation=90, labelpad=10, fontsize=font_size+factor_delta)
ax.tick_params(axis='y', labelsize=font_size+factor_delta)

ax.set_yticklabels(allbasins_n2.nombre,rotation=0)

colorbar = ax.collections[0].colorbar
colorbar.set_ticks([(b0+b1)/2 for b0, b1 in zip(bounds[:-1], bounds[1:])])
colorbar.set_ticklabels(['Flujo bajo', 'Por debajo de lo normal', 'Normal', 'Por encima de lo normal', 'Flujo alto'])

colorbar.ax.tick_params(labelsize=font_size)
colorbar.ax.yaxis.set_tick_params(rotation=0)
colorbar.ax.yaxis.set_label_position('left')
ax.figure.axes[-1].yaxis.label.set_size(font_size)

plt.rcParams.update({'font.family':'Arial'})
sns.set(font_scale=1.4)
plt.tight_layout()
plt.savefig(f"./waterbalance/output_png/07_status_heatmap.png", dpi=300, bbox_inches='tight')
plt.close()



