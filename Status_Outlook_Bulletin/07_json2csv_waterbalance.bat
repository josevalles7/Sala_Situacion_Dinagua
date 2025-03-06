pause
echo Convirtiendo json a csv 01-Mes
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/01_month" "2025-02" "qgis_status_outlook/csvtables" "01"
echo Convirtiendo json a csv 03-Meses
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/03_month" "2025-02" "qgis_status_outlook/csvtables" "03"
echo Convirtiendo json a csv 12-Meses
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/json_to_csv.py "./waterbalance/output_json/12_month" "2025-02" "qgis_status_outlook/csvtables" "12"
pause