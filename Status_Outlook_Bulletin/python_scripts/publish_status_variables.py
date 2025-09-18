import requests
import json
import os
import argparse
import sys

#---------------------------------------------------------------------------------------
#--------------------------------Configurar bat-----------------------------------------
parser = argparse.ArgumentParser(
    prog='publish runoff and precip jsons',
    description='Publish escorrentia and precipitacion JSONs to Dinagua WS',
    epilog='Tiago Pohren, DINAGUA, 02092025'
)
parser.add_argument('input_json_directory', help='provide the input json directory')
parser.add_argument('filename_json', help='input the month number (e.g., 2025-04)')
args = parser.parse_args()

#---------------------------------------------------------------------------------------
#--------------------------------Obtener Json-------------------------------------------
json_file = os.path.join(args.input_json_directory, args.filename_json + '.json')
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

fecha = args.filename_json 

"""Si es necesario dividir el json entre escorrentia y precipitación descomentar esta parte
escorrentia_list = []
precip_list = []
for idx, item in enumerate(data, start=1):
    escorrentia_list.append({
        "id": idx,
        "escorrentia": item.get("runoff", 0),
        "units": "%",
        "fecha": fecha,
        "stationID": item.get("codigo")
    })
    precip_list.append({
        "id": idx,
        "precip": item.get("precip_val", 0),
        "units": "mm",
        "fecha": fecha,
        "stationID": item.get("codigo")
    })"""

#---------------------------------------------------------------------------------------
#-----------------------------Acceder al webservice-------------------------------------
# ----> Acceder a producción
url_base = 'https://www.ambiente.gub.uy/dinaguaws/'
user_dinagua = {"user":"FEWS-Uruguay","password":"4MEzOeKFgp0pj9lATSIF"}
"""# ----> Acceder a testing
url_base = 'http://172.28.0.165:8080/dinaguaws/'
user_dinagua = {"user":"saladesituacion","password":"Rondeau1921"}
"""

#---------------------------------------------------------------------------------------
#---------------------------------Generar token-----------------------------------------
try:
    response_token = requests.post(url=url_base + "gettoken", json=user_dinagua, verify=False)
    response_token.raise_for_status()
    token = response_token.text.strip()
    headers = {"Authorization": "Bearer " + token}
    print("Token obtenido con éxito.")
except requests.RequestException as e:
    print("Error al obtener el token:", e)
    sys.exit(1)

#---------------------------------------------------------------------------------------
#--------------------------------Publicar el json---------------------------------------
json_body = data

post_estado = requests.post(
    url=f"{url_base}estadohidro/escorrentia?fecha={fecha}",
    headers=headers,
    json=json_body,
    verify=False
)
if post_estado.status_code != 200:
    print("Error al publicar el estado:", post_estado.text)
    sys.exit(1)
post_estado.close()
print(post_estado.text)

