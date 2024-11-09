# %% [markdown]
# # Calculate the percentage of anomaly
# #### Jose Valles (jose.valles.leon@gmail.com)
# 
# ### Importing Libraries

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('classic')
import numpy as np
import calendar
import sys
import argparse

sns.set()

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='calculate_hydrological_status',
                    description='Calculates monthly hydrological status from observation point',
                    epilog='Jose Valles, DINAGUA, 26082024')

# 
parser.add_argument('month_analysis', help='provide the input time series frequency (daily or monthly)')
parser.add_argument('year_analysis', help='input directory, should ONLY contain .csv daily flow timeseries')        


args = parser.parse_args()

# %% [markdown]
# Import basin level code 2 and 3

# %%
BASIN_LEVEL3 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel3.csv',index_col="Codigo")
BASIN_LEVEL2 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',index_col="Codigo")

# %%
def importmodelvariable(model_variable):
    df = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/{model_variable}.csv')
    df = df.rename(columns={'-1': 'year','-1.1':'month'})
    df['date'] = pd.to_datetime(dict(year=df['year'],month=df['month'],day=1))
    df = df.set_index('date')
    df['days_in_month'] = df.index.days_in_month
    return df

def convertRunoff2Discharge(df_runoff):
    df_runoff_selected = df_runoff.drop(['year','month','days_in_month'],axis=1)
    df_discharge = pd.DataFrame(df_runoff_selected.values*1000*BASIN_LEVEL3.values,columns=df_runoff_selected.columns)
    df_discharge['days_in_month'] = df_runoff['days_in_month'].values
    df_discharge = df_discharge.loc[:, df_discharge.columns != 'days_in_month'].divide(df_discharge["days_in_month"]*24*3600, axis="index")
    df_discharge['date'] = df_runoff.index.values
    df_discharge = df_discharge.set_index('date')
    df_discharge['year'] = df_runoff['year'].values
    df_discharge['month'] = df_runoff['month'].values
    return df_discharge

def defineHydroSOScategory(VARIABLE_MENSUAL,VARIABLE_AVERAGE,VARIABLE):
    # create empty columns in the dataframe
    VARIABLE_MENSUAL['mean'] = np.nan
    VARIABLE_MENSUAL['average_percentage'] = np.nan
    VARIABLE_MENSUAL['rank_average'] = np.nan
    VARIABLE_MENSUAL['non_missing'] = np.nan


    for i in range(len(VARIABLE_MENSUAL)):
        # Extract the current month 
        m = VARIABLE_MENSUAL.month[i]
        # Extract the current year
        y = VARIABLE_MENSUAL.year[i]
        VARIABLE_MENSUAL.loc[VARIABLE_MENSUAL.eval('month==@m & year==@y'),'rank_average']  = VARIABLE_MENSUAL.query('month==@m')[VARIABLE].rank()
        VARIABLE_MENSUAL.loc[VARIABLE_MENSUAL.eval('month==@m & year==@y'),'non_missing']  = VARIABLE_MENSUAL.query('month==@m')[VARIABLE].notnull().sum()
        VARIABLE_MENSUAL.loc[VARIABLE_MENSUAL.eval('month==@m & year==@y'),'mean'] = VARIABLE_AVERAGE.query('month == @m')[VARIABLE].item()
        VARIABLE_MENSUAL.loc[VARIABLE_MENSUAL.eval('month==@m & year==@y'),'average_percentage'] = (VARIABLE_MENSUAL[VARIABLE][i] - VARIABLE_AVERAGE.query('month == @m')[VARIABLE].item()) / VARIABLE_AVERAGE.query('month == @m')[VARIABLE].item()

    VARIABLE_MENSUAL['percentile'] = VARIABLE_MENSUAL['rank_average']/(VARIABLE_MENSUAL['non_missing']+1)
    criteria = [VARIABLE_MENSUAL['percentile'].between(0.90,1.00),
            VARIABLE_MENSUAL['percentile'].between(0.75,0.90),
            VARIABLE_MENSUAL['percentile'].between(0.25,0.75),
            VARIABLE_MENSUAL['percentile'].between(0.10,0.25),
            VARIABLE_MENSUAL['percentile'].between(0.00,0.10)]

    values = ['High flow','Above normal','Normal range','Below normal','Low flow']

    VARIABLE_MENSUAL['percentile_range'] = np.select(criteria,values,None)
    return VARIABLE_MENSUAL

# %%
hydrological_variable = ['Escorrentia_total','Escorrentia_sup','Escorrentia_sub','Pmedias','ETR','HumedadSuelo']

for hydro in hydrological_variable:
    if hydro == "Escorrentia_total":
        RUNOFF_total = importmodelvariable(hydro)
    elif hydro == "Pmedias":
        PRECIP = importmodelvariable(hydro)
    elif hydro == "ETR":
        ETR = importmodelvariable(hydro)
    elif hydro == "HumedadSuelo":
        SM = importmodelvariable(hydro)
    elif hydro == 'Escorrentia_sup':
        RUNOFF_sup = importmodelvariable(hydro)
    elif hydro == 'Escorrentia_sub':
        RUNOFF_sub = importmodelvariable(hydro)


# %%
DISCHARGE = convertRunoff2Discharge(RUNOFF_total)

# %%
# Select the runoff type 
RUNOFF = RUNOFF_total

# %%
year_start = 1981
year_end = 2010
# Caudal
SELECTED_REF_DISCHARGE= DISCHARGE[(DISCHARGE['year'] >= year_start) & (DISCHARGE['year'] <= year_end)]
# Escorrentia total
SELECTED_REF_RUNOFF = RUNOFF[(RUNOFF['year'] >= year_start) & (RUNOFF['year'] <= year_end)]
# Precip
SELECTED_REF_PRECIP = PRECIP[(PRECIP['year'] >= year_start) & (PRECIP['year'] <= year_end)]

# %% [markdown]
# ## Calculate the percentage of anomaly for each basin code level 2 and a specific month and year

# %%
#-- OJO: Cambiar fecha
month_analyis = int(args.month_analysis)
year_analysis = int(args.year_analysis)

AVERAGE_PERCENTAGE = pd.DataFrame()
AVERAGE_PERCENTAGE['codigo'] = BASIN_LEVEL2.columns
AVERAGE_PERCENTAGE['discharge'] = np.nan
AVERAGE_PERCENTAGE['runoff'] = np.nan
AVERAGE_PERCENTAGE['precip'] = np.nan

for basin in BASIN_LEVEL2.columns:
    # filter the basin code bas
    filter_col = [col for col in DISCHARGE if col.startswith(str(basin))]
    # Select basins level 3 that belongs to level 2 basin
    # Discharge
    DISCHARGE_FILTER = DISCHARGE[filter_col]
    DISCHARGE_SELECTED = pd.DataFrame()
    DISCHARGE_SELECTED['year'] = DISCHARGE['year']
    DISCHARGE_SELECTED['month'] = DISCHARGE['month']    
    DISCHARGE_SELECTED['discharge'] = DISCHARGE_FILTER.sum(axis=1)
    DISCHARGE_REF = DISCHARGE_SELECTED[(DISCHARGE_SELECTED['year'] >= year_start) & (DISCHARGE_SELECTED['year'] <= year_end)]
    # Runoff
    RUNOFF_FILTER = RUNOFF[filter_col]
    RUNOFF_SELECTED = pd.DataFrame()
    RUNOFF_SELECTED['year'] = RUNOFF['year']
    RUNOFF_SELECTED['month'] = RUNOFF['month']    
    RUNOFF_SELECTED['runoff'] = RUNOFF_FILTER.mean(axis=1)
    RUNOFF_REF = RUNOFF_SELECTED[(RUNOFF_SELECTED['year'] >= year_start) & (RUNOFF_SELECTED['year'] <= year_end)]
    # Precip
    PRECIP_FILTER = PRECIP[filter_col]
    PRECIP_SELECTED = pd.DataFrame()
    PRECIP_SELECTED['year'] = PRECIP['year']
    PRECIP_SELECTED['month'] = PRECIP['month']    
    PRECIP_SELECTED['precip'] = PRECIP_FILTER.mean(axis=1)
    PRECIP_REF = PRECIP_SELECTED[(PRECIP_SELECTED['year'] >= year_start) & (PRECIP_SELECTED['year'] <= year_end)]
    # CALCULATE CLIMATOLOGICAL NORMALS
    # Discharge
    DISCHARGE_AVERAGE = DISCHARGE_REF.groupby(DISCHARGE_REF.month).mean()
    # Runoff
    RUNOFF_AVERAGE = RUNOFF_REF.groupby(RUNOFF_REF.month).mean()
    # Precip
    PRECIP_AVERAGE = PRECIP_REF.groupby(PRECIP_REF.month).mean()
    # HydroSOS Category
    hydroSOS = defineHydroSOScategory(DISCHARGE_SELECTED,DISCHARGE_AVERAGE,'discharge')
    # Calculate the anomaly
    AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'discharge'] = (DISCHARGE_SELECTED.query('month == @month_analyis & year == @year_analysis')['discharge'].item() - DISCHARGE_AVERAGE.query('month == @month_analyis')['discharge'].item()) / DISCHARGE_AVERAGE.query('month == @month_analyis')['discharge'].item()
    AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'runoff'] = (RUNOFF_SELECTED.query('month == @month_analyis & year == @year_analysis')['runoff'].item()- RUNOFF_AVERAGE.query('month == @month_analyis')['runoff'].item()) / RUNOFF_AVERAGE.query('month == @month_analyis')['runoff'].item()
    AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'precip'] = (PRECIP_SELECTED.query('month == @month_analyis & year == @year_analysis')['precip'].item() - PRECIP_AVERAGE.query('month == @month_analyis')['precip'].item()) / PRECIP_AVERAGE.query('month == @month_analyis')['precip'].item()
    AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'precip_val'] = PRECIP_SELECTED.query('month == @month_analyis & year == @year_analysis')['precip'].item()
    AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'hydroSOS_category'] = hydroSOS.query('month == @month_analyis & year == @year_analysis')['percentile_range'].item()
    #AVERAGE_PERCENTAGE.loc[AVERAGE_PERCENTAGE.eval('codigo==@basin'),'percentile'] = hydroSOS.query('month == @month_analyis & year == @year_analysis')['percentile'].item()

# %%
AVERAGE_PERCENTAGE.to_csv('./qgis_status_outlook/csvtables/modelling_result_codcuenca_2.csv',index=False)

# %%
# Contar las ocurrencias de cada categoría
category_counts = AVERAGE_PERCENTAGE['hydroSOS_category'].value_counts()

# %%
# Definir los colores para cada categoría basados en el estado hidrológico
colors = [
    '#2C7DCD' if category == 'High flow' else
    '#8ECEEE' if category == 'Above normal' else
    '#E7E2BC' if category == 'Normal range' else
    '#FFA885' if category == 'Below normal' else
    '#CD233F'  # Low flow
    for category in category_counts.index
]

# Crear el gráfico de doughnut
fig, ax = plt.subplots()
ax.pie(category_counts, labels=None, autopct='%1.1f%%', startangle=90, wedgeprops={'width': 0.3}, colors=colors)

# Asegurar que el gráfico sea un círculo
ax.axis('equal')

# Añadir leyenda con los nombres de las categorías
plt.legend(category_counts.index, title="HydroSOS Category", loc="center left", bbox_to_anchor=(1, 0.5))

# Título del gráfico
plt.title('Distribución de HydroSOS Category')

# Mostrar el gráfico
plt.show()


