# %% [markdown]
# ## Exportación caudales modelos balance hídrico 

# %%
import pandas as pd
import numpy as np
import calendar

# %% [markdown]
# ### Generar clase WaterBalanceModel

# %%
class WaterBalanceModel:
    def __init__(self, codcuenca_n2, model_variable):
        self.codcuenca_n2 = codcuenca_n2
        self.model_variable = model_variable

    def importmodelvariable(self):
        df_runoff = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/{self.model_variable}.csv', usecols=lambda col: col.startswith((str(self.codcuenca_n2), '-1')))
        df_runoff = df_runoff.rename(columns={'-1': 'year', '-1.1':'month'})
        df_runoff['date'] = pd.to_datetime(dict(year=df_runoff['year'], month=df_runoff['month'], day=1))
        df_runoff = df_runoff.set_index('date')
        df_runoff['days_in_month'] = df_runoff.index.days_in_month
        return df_runoff

    def convertRunoff2Discharge(self, df_runoff):
        basin_level3 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel3.csv',usecols=lambda col: col.startswith(str(self.codcuenca_n2)))
        basin_level2 = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',usecols=lambda col: col.startswith(str(self.codcuenca_n2)))
        df_runoff_selected = df_runoff.drop(['year', 'month', 'days_in_month'], axis=1)
        df_discharge = pd.DataFrame(df_runoff_selected.values * 1000 * basin_level3.values, columns=df_runoff_selected.columns)
        df_discharge['days_in_month'] = df_runoff['days_in_month'].values
        df_discharge = df_discharge.loc[:, df_discharge.columns != 'days_in_month'].divide(df_discharge["days_in_month"] * 24 * 3600, axis="index")
        df_discharge['date'] = df_runoff.index.values
        df_discharge = df_discharge.set_index('date')
        df_discharge['year'] = df_runoff['year'].values
        df_discharge['month'] = df_runoff['month'].values
        return df_discharge

    def AggregateDischarge(self, df_discharge):
        filter_col = [col for col in df_discharge if col.startswith(str(self.codcuenca_n2))]
        DISCHARGE_SELECTED = df_discharge[filter_col]
        DISCHARGE_N2 = pd.DataFrame()
        DISCHARGE_N2['year'] = df_discharge['year']
        DISCHARGE_N2['month'] = df_discharge['month']
        DISCHARGE_N2['discharge'] = DISCHARGE_SELECTED.sum(axis=1)
        DISCHARGE_N2['date'] = pd.to_datetime(dict(year=DISCHARGE_N2['year'], month=DISCHARGE_N2['month'], day=1))
        DISCHARGE_N2 = DISCHARGE_N2.set_index('date')
        return DISCHARGE_N2

# %% [markdown]
# ### Ejemplo usando todas las cuencas

# %%
ALL_BASIN = pd.read_csv(f'./waterbalance/balance_hidrico_regional/output_modelo/cuenca_nivel2.csv',index_col="Codigo")

# %%
for columna, datos in ALL_BASIN.iteritems():
    # print(columna)
    # Create model instance based on WaterBalanceModel Class
    model_instance = WaterBalanceModel(columna, 'Escorrentia_total')
    # Import variable
    df_runoff_data = model_instance.importmodelvariable()
    # Convert level 3 runoff to discharge
    df_discharge_data = model_instance.convertRunoff2Discharge(df_runoff_data)
    # Aggregate discharge from level 3 to level 2
    result = model_instance.AggregateDischarge(df_discharge_data)
    result = result.reset_index()
    result = result[['date', 'discharge']].rename(columns={'date': 'Fecha', 'discharge': 'Caudal'})
    result.to_csv(f'./waterbalance/input/{columna}.csv', index=False, date_format='%d/%m/%Y', columns=['Fecha', 'Caudal'])


