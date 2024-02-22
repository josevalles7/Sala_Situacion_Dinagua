def importar_librerias():
    global np, pd
    import numpy as np
    import pandas as pd
	
def cargar_archivos(agua_disponible, archivo_pmedias, archivo_etpmedias):
    AD = np.loadtxt(agua_disponible)
    data_p = np.loadtxt(archivo_pmedias, delimiter=',')
    data_etp = np.loadtxt(archivo_etpmedias, delimiter=',')
    # La primera fila de `data` contiene los códigos
    codigos = data_p[0, :]
    # Las demás filas contienen fechas y P1
    fechas = data_p[1:, :2]  # Accede a todas las filas en las primeras dos columnas
    P1 = data_p[1:, 2:]     # Accede a todas las filas desde la tercera columna en adelante
    ETP1 = data_etp[1:, 2:]

    return AD, codigos, fechas, P1, ETP1