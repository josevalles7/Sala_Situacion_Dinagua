"""
PUBLISH RESULTS IN DINAGUA WS
JOSE VALLES  26-08-2024 
"""

import requests
import json
import sys
import os
import argparse

# Define arguments 
parser = argparse.ArgumentParser(
                    prog='publish results from hydrosos',
                    description='Publish the result of hydrological status in Dinagua WS',
                    epilog='Jose Valles, DINAGUA, 26082024')

# 
parser.add_argument('input_json_directory', help='provide the input json directory')
parser.add_argument('filename_json', help='input the month number')
parser.add_argument('scale', help='provide the status category scale (1,3,12)')        
parser.add_argument('ts_type', help='provide the time series type (Estaciones, Modelos)') 

args = parser.parse_args()

# ------------------------------------------------------------------------------
# Obtain Token
# ------------------------------------------------------------------------------

url_base = 'https://www.ambiente.gub.uy/dinaguaws/'
# Username and password
user_dinagua = {"user":"FEWS-Uruguay","password":"4MEzOeKFgp0pj9lATSIF"}
# Get the token from DINAGUA WS
response_token = requests.post(url=url_base + "gettoken", json=user_dinagua, verify=False);
response_token.close()
# Extract token and assign it to a variable
token = response_token.text
# Add the token to a bearer authorization
headers = {"Authorization" : "Bearer " + token}

# ------------------------------------------------------------------------------
# POST Method for creating the filter Id
# ------------------------------------------------------------------------------

# Locate the corresponding json file
json_directory = args.input_json_directory
filename = args.filename_json
json_file = os.path.join(json_directory, filename)
# Define Parameters
date_name = json_file.split('/')[-1].split('.')[0]

cat_scale = int(args.scale)
ts = args.ts_type

# create the json dictonary
dataFiltro = {"fecha": date_name,"temporalidad": cat_scale,"serietemporal": ts}

# POST Save Filter
post_filtro = requests.post(url=url_base + "estadohidro/datoscat/guardarFiltro", headers = headers, json=dataFiltro, verify=False)
post_filtro.close()
print(post_filtro.text)

# ------------------------------------------------------------------------------
# GET Method for extracting the FilterID
# ------------------------------------------------------------------------------

# Create the json dictonary
params_filtros = {"fecha" : date_name, "temporalidad" : cat_scale, "serietemporal" : ts}
# Send requests
get_filtro_id = requests.get(url = url_base + "estadohidro/filtros",headers=headers, params=params_filtros, verify=False)
get_filtro_id.close()
# print id
id = json.loads(get_filtro_id.content.decode('utf-8'))
id = id[0]["id"]
print(id)

# ------------------------------------------------------------------------------
# POST HydroSOS Status for the corresponding Month/Year
# ------------------------------------------------------------------------------

# Creating the Request Body
datosCat = {"filtrosId": {id}}
# importing the json file from the output directory
json_body = open(json_file)
json_body = json.load(json_body)
# POST HydroSOS status 
post_estado = requests.post(url=url_base+"estadohidro/datoscat/guardarDatosCat",headers=headers,params=datosCat,json=json_body,verify=False)
post_estado.close()
print(post_estado.text)

print('========================================================================')
