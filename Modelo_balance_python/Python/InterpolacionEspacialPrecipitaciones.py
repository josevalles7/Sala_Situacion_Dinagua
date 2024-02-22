import numpy as np
import pandas as pd
import time

def funcion_interpolacion_precipitaciones():
    # Registra el tiempo de inicio
    inicio = time.time()
    
    # Cargar datos desde archivos
    ncuen = np.loadtxt('Cuencas.txt')
    cuenca = np.loadtxt('CuencasOrden3.txt')
    datos = np.loadtxt('Pluviometros.txt')

    # Definir variables
    xll, yll, delta = 255265, 6130196, 3000

    # Calcular número de días y de pluviómetros
    ndias = len(datos[:, 0]) - 3
    npluvs = len(datos[1, :]) - 3

    # Obtener coordenadas, códigos y matriz de datos
    coord = datos[0:2, 3:(npluvs + 3)]
    codigos = datos[2, 3:(npluvs + 3)]
    yll = yll + delta * (len(cuenca) - 1)
    M = datos[3:(ndias + 3), 3:npluvs + 3]

    # Inicializar matrices
    nrows, ncols = cuenca.shape
    MAT = np.zeros((ndias + 3, nrows * ncols))
    MATCAL = np.zeros((ndias + 3, nrows * ncols))

    # Procesar cada celda de la cuenca
    cont = 0
    for i in range(1, nrows + 1):
        for j in range(1, ncols + 1):
            if cuenca[i - 1, j - 1] > 0:
                corx = xll + j * delta
                cory = yll - i * delta

                cx = (coord[0, :] - corx) ** 2
                cy = (coord[1, :] - cory) ** 2
                c = cx + cy

                dist = np.column_stack((codigos, c))
                MAT[0, cont] = cuenca[i - 1, j - 1]
                MAT[1, cont] = corx
                MAT[2, cont] = cory

                for k in range(ndias):
                    y = np.column_stack((dist, M[k, :]))
                    y = y[y[:, 2] != -1, :]
                    y = y[y[:, 1].argsort()]

                    MAT[k + 3, cont] = np.sum(y[:3, 2] / y[:3, 1]) / np.sum(1 / y[:3, 1])
                    MATCAL[k + 3, cont] = np.sqrt(y[0, 1])

                cont += 1

    cont2 = 1
    MATCAL[0:3, :] = MAT[0:3, :]

    Pcuen_data = []

    for t in range(len(ncuen)):
        # Seleccionar columnas donde la condición se cumple
        M2 = MAT[3:, MAT[0, :] == ncuen[t]]
        
        # Verificar si M2 tiene al menos una columna
        if M2.shape[1] > 0:
            mean_values = np.round(np.mean(M2, axis=1), 3)
            Pcuen_data.append(mean_values)

    # Transponer la lista para que las listas internas representen las columnas
    Pcuen_data_transposed = np.array(Pcuen_data).T

    # Agregar filas de ncuen al principio de Pcuen_data_transposed
    #Pcuen_data_transposed = np.vstack((ncuen.astype(int), Pcuen_data_transposed))

    # Obtener las primeras dos columnas de datos (desde la fila 3 hasta el final)
    primeras_dos_columnas_datos = datos[3:, :2].astype(int)

    # Agregar las columnas de Pcuen_data_transposed al principio de las primeras dos columnas de datos
    Pcuen = np.column_stack((primeras_dos_columnas_datos.astype(str), Pcuen_data_transposed.astype(float)))

    nombres_columnas = list(datos[0, :2].astype(int)) + list(ncuen.astype(int))
    # Crear DataFrame de pandas con nombres de columnas
    Pcuen_df = pd.DataFrame(Pcuen, columns=nombres_columnas)

    # Formatear las columnas flotantes con 3 decimales
    columnas_float = Pcuen_df.select_dtypes(include='float64').columns
    Pcuen_df[columnas_float] = Pcuen_df[columnas_float].round(3)

    # Guardar resultados en un archivo CSV con formato específico
    Pcuen_df.to_csv('Pmedias.csv', index=False, header=True)
    
    # Registra el tiempo de finalización
    fin = time.time()

    # Calcula y muestra el tiempo de ejecución
    tiempo_ejecucion = fin - inicio
    print(f"Tiempo de ejecución interpolacion P: {tiempo_ejecucion} segundos")
