# %%
import pandas as pd
import numpy as np
from scipy import stats
import os
import glob

from IPython.display import HTML

# %%
# --- Configuración Inicial ---
k_values = [3, 6]  # Escalas temporales a procesar
m = 4  # Mes de inicio año hidrológico (Abril)
data_folder = './stations/data'

# Percentage of missing data
max_pct_missing = 50

# Obtener lista de estaciones disponibles
import glob
station_files = glob.glob(os.path.join(data_folder, '*.csv'))
stations = [os.path.basename(f).replace('.csv', '') for f in sorted(station_files)]
print(f"Estaciones encontradas: {stations}")

# %%
def load_station_data(station_name, data_folder):
    """
    Cargar datos de descarga diaria para una estación.
    
    Parameters:
    -----------
    station_name : str
        Nombre/ID de la estación
    data_folder : str
        Ruta de la carpeta con los datos
    
    Returns:
    --------
    pd.DataFrame or None
        DataFrame con datos diarios, o None si hay error
    """
    input_file = os.path.join(data_folder, f'{station_name}.csv')
    try:
        discharge_daily = pd.read_csv(
            input_file,
            parse_dates=['Fecha'],
            index_col="Fecha",
            dayfirst=True,
            na_values="NA"
        )
        return discharge_daily
    except Exception as e:
        print(f"Error cargando estación {station_name}: {e}")
        return None

def process_discharge_to_monthly(discharge_daily, max_pct_missing=50):
    """
    Convert daily discharge data to monthly discharge data.
    
    Parameters:
    -----------
    discharge_daily : pd.DataFrame
        Daily discharge dataframe with datetime index
    max_pct_missing : float
        Maximum percentage of missing data allowed (default: 50)
    
    Returns:
    --------
    pd.DataFrame
        Monthly discharge dataframe with columns: Fecha and Caudal
    """
    # Re-index to complete date range
    date_range = pd.date_range(start=discharge_daily.index[0], 
                               end=discharge_daily.index[-1], 
                               freq='D')
    discharge_daily = discharge_daily.reindex(date_range, fill_value=None)
    discharge_daily.index.name = 'Fecha'
    
    # Standardize column name
    discharge_daily.columns = ['Caudal']
    
    # Convert daily to monthly (mean with missing data threshold)
    df = discharge_daily.resample('M', closed="right").apply(
        lambda x: x.mean() if x.isnull().sum()*100/len(x) < max_pct_missing else np.nan
    )
    
    # Reset index to make Fecha a column
    df = df.reset_index()
    
    return df

def process_sdi_for_station(station_name, k, data_folder, m=4, max_pct_missing=50):
    """
    Procesar SDI para una estación y escala temporal específicas.
    
    Parameters:
    -----------
    station_name : str
        Nombre/ID de la estación
    k : int
        Escala temporal en meses
    data_folder : str
        Ruta de la carpeta con los datos
    m : int
        Mes de inicio del año hidrológico
    max_pct_missing : float
        Máximo porcentaje de datos faltantes permitido
    
    Returns:
    --------
    pd.DataFrame or None
        DataFrame con resultados SDI o None si hay error
    """
    # Cargar datos diarios
    discharge_daily = load_station_data(station_name, data_folder)
    if discharge_daily is None:
        return None
    
    # Convertir a mensual
    date_range = pd.date_range(start=discharge_daily.index[0], 
                               end=discharge_daily.index[-1], 
                               freq='D')
    discharge_daily = discharge_daily.reindex(date_range, fill_value=None)
    discharge_daily.index.name = 'Fecha'
    discharge_daily.columns = ['Caudal']
    
    df = discharge_daily.resample('M', closed="right").apply(
        lambda x: x.mean() if x.isnull().sum()*100/len(x) < max_pct_missing else np.nan
    )
    df = df.reset_index()
    
    # Preprocesamiento
    df['cumCaudal'] = df['Caudal'].rolling(window=k).sum()
    df['lnCaudal'] = np.log(df['cumCaudal'])
    
    # Etiquetas de meses
    df['StartMonth'] = (df['Fecha'] - pd.DateOffset(months=k-1)).dt.strftime('%b')
    df['EndMonth'] = df['Fecha'].dt.strftime('%b')
    df['ScaleMonth'] = df['StartMonth'] + "-" + df['EndMonth']
    
    # Inicializar columnas de resultados
    df['SDI'] = np.nan
    df['log_SDI'] = np.nan
    df['Gamma_SDI'] = np.nan
    
    # Cálculo del SDI por grupo de meses
    iterations = df['ScaleMonth'].unique()
    
    for month_group in iterations:
        mask = (df['ScaleMonth'] == month_group) & (df['cumCaudal'].notna())
        
        if not mask.any():
            continue
            
        subset = df.loc[mask, 'cumCaudal']
        subset_ln = df.loc[mask, 'lnCaudal']
        
        # 1. SDI Estándar
        df.loc[mask, 'SDI'] = (subset - subset.mean()) / subset.std()
        
        # 2. SDI Log-Normal
        df.loc[mask, 'log_SDI'] = (subset_ln - subset_ln.mean()) / subset_ln.std()
        
        # 3. SDI Gamma
        try:
            shape, loc, scale = stats.gamma.fit(subset, floc=0)
            cdf_vals = stats.gamma.cdf(subset, shape, loc, scale)
            cdf_vals = np.clip(cdf_vals, 0.0001, 0.9999)
            df.loc[mask, 'Gamma_SDI'] = stats.norm.ppf(cdf_vals)
        except:
            df.loc[mask, 'Gamma_SDI'] = np.nan
    
    # Año Hidrológico
    def get_hydro_year(date):
        return date.year if date.month >= m else date.year - 1
    
    df['WYear'] = df['Fecha'].apply(get_hydro_year)
    df['Año_hidrologico'] = df['WYear'].astype(str) + "-" + (df['WYear'] + 1).astype(str)
    
    # Preparar exportación
    data_export = df[['Fecha', 'Año_hidrologico', 'ScaleMonth', 'SDI', 'log_SDI', 'Gamma_SDI']].copy()
    data_export.columns = ["Fecha", "Año_hidrologico", "Escala", "SDI", "LogSDI", "GammaSDI"]
    data_export[['SDI', 'LogSDI', 'GammaSDI']] = data_export[['SDI', 'LogSDI', 'GammaSDI']].round(2)
    
    return data_export

# --- Procesamiento Automatizado de Todas las Estaciones y Escalas ---

# Crear carpeta de salida si no existe
output_base = './stations/output_sdi/csv'
os.makedirs(output_base, exist_ok=True)

# Procesar todas las estaciones y escalas
results_summary = []

for k in k_values:
    print(f"\n{'='*60}")
    print(f"Procesando escala k={k} meses")
    print(f"{'='*60}")
    
    for station in stations:
        print(f"  Procesando estación {station}...", end=" ")
        
        try:
            data_export = process_sdi_for_station(station, k, data_folder, m=m, max_pct_missing=max_pct_missing)
            
            if data_export is not None and len(data_export) > 0:
                # Guardar archivo
                output_path = os.path.join(output_base, f"{k}month_CompleteSDI_{station}.txt")
                data_export.to_csv(output_path, index=False, sep=",", na_rep="")
                print(f"✓ Guardado")
                results_summary.append({
                    'Estación': station,
                    'Escala': f"{k}m",
                    'Registros': len(data_export),
                    'Estado': 'OK'
                })
            else:
                print(f"✗ Sin datos válidos")
                results_summary.append({
                    'Estación': station,
                    'Escala': f"{k}m",
                    'Registros': 0,
                    'Estado': 'Sin datos'
                })
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            results_summary.append({
                'Estación': station,
                'Escala': f"{k}m",
                'Registros': 0,
                'Estado': f'Error: {str(e)[:30]}'
            })

# Mostrar resumen
print(f"\n{'='*60}")
print("RESUMEN DE PROCESAMIENTO")
print(f"{'='*60}")
summary_df = pd.DataFrame(results_summary)
print(summary_df.to_string(index=False))

# Estadísticas finales
total_exitosos = len([r for r in results_summary if r['Estado'] == 'OK'])
total_procesados = len(stations) * len(k_values)
print(f"\nTotal procesados: {total_exitosos}/{total_procesados}")
print(f"Archivos guardados en: {output_base}")


