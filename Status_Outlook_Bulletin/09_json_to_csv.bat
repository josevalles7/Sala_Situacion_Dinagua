pause
echo Convirtiendo json a csv 01-Mes
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/01_month" "2024-10" "D:/Documentos/Python Scripts/Balance Hidrico/forplotting" "01"
echo Convirtiendo json a csv 03-Meses
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/03_month" "2024-10" "D:/Documentos/Python Scripts/Balance Hidrico/forplotting" "03"
echo Convirtiendo json a csv 12-Meses
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/12_month" "2024-10" "D:/Documentos/Python Scripts/Balance Hidrico/forplotting" "12"
pause