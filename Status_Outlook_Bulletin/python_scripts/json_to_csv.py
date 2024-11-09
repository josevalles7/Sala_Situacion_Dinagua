import argparse
import json
import csv

parser = argparse.ArgumentParser(
                    prog='Hydro SOS json_to_csv PYTHON',
                    description='Convert from single json to csv to import in the QGIS',
                    epilog='Valles Jose, 07-Nov-2024')


parser.add_argument('input_directory', help='input directory, should ONLY contain .csv monthly categorised flow status files, see GitHub for examples.')   
parser.add_argument('json_filename', help='directory files will be saved to as {date}.json')
parser.add_argument('output_directory',help='output directory for the csv file')
parser.add_argument('scale',help='01, 03 or 12 months')      

args = parser.parse_args()

# Cargar el archivo JSON
with open(f"{args.input_directory}/{args.json_filename}.json") as json_file:
    data = json.load(json_file)

# Crear el archivo CSV
csv_file_name = f"{args.output_directory}/{args.scale}_status_month.csv"
with open(csv_file_name, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    # Escribir el encabezado
    csv_writer.writerow(['category', 'stationID'])
    # Escribir los datos
    for item in data:
        csv_writer.writerow([item['category'], item['stationID']])

print(f"Archivo CSV creado exitosamente.")