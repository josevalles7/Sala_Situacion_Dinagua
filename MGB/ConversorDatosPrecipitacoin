#este script converte los datos de precipitacion de UTE en el formato de entrada de los datos de precipitacion del MGB

import datetime

# Ruta al archivo local
archivo = 'C:/Users/tiago/OneDrive/Área de Trabalho/Dinagua/MGB/Yi2/Precipitacion/teste.txt'

# Lista para almacenar los resultados
resultados = []

# Leer el archivo línea por línea
with open(archivo, 'r') as file:
    for linea in file:
        linea = linea.strip()  # Eliminar espacios en blanco al inicio y final de la línea

        # Dividir la línea en módulos separados por el carácter ';'
        modulos = linea.split(';')

        # Verificar si la línea tiene suficientes módulos antes de acceder al sexto módulo
        if len(modulos) >= 6:
            # Extraer la fecha al principio de la línea
            fecha = modulos[0]

            # Extraer el valor de precipitación del sexto módulo y verificar si es válido
            precipitacion = modulos[6].strip()  # Eliminar espacios en blanco alrededor del valor
            if precipitacion.isnumeric():
                precipitacion = int(precipitacion)
            else:
                precipitacion = -1  # Valor por defecto si no es numérico

            # Agregar los resultados a la lista
            resultados.append((fecha, precipitacion))
        else:
            resultados.append((None, -1))  # Valores por defecto si la línea no tiene suficientes módulos

# Procesar los resultados
output_resultados = []

for fecha, precipitacion in resultados:
    if fecha is not None:
        try:
            date_obj = datetime.datetime.strptime(fecha, '%d/%m/%Y')
            day = str(date_obj.day)
            month = str(date_obj.month)
            year = str(date_obj.year)
            output_resultados.append(f"{day.rjust(6)} {month.rjust(5)} {year.rjust(5)} {str(precipitacion).rjust(8)}.00")

        except ValueError:
            print(f"Error: Ignorando línea con formato incorrecto: {fecha};{precipitacion}")

# Imprimir los resultados
#for resultado in output_resultados:
#    print(resultado)

# Opcionalmente, guardar los resultados en un archivo
archivo_salida = 'C:/Users/tiago/OneDrive/Área de Trabalho/Dinagua/MGB/Yi2/Precipitacion/teste2.txt'
with open(archivo_salida, 'w') as file_salida:
    for resultado in output_resultados:
        file_salida.write(resultado + '\n')

print("Datos reorganizados con éxito.")
