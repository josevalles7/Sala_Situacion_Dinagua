pause
echo Obteniendo estado hidrologico mensual
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/monthly_status.py "monthly" "./waterbalance/input/" "./waterbalance/output_csv/01_month/" "./waterbalance/output_json/01_month/"
echo Obteniendo estado hidrologico trimestral
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/quaterly_status.py "monthly" "./waterbalance/input/" "./waterbalance/output_csv/03_month/" "./waterbalance/output_json/03_month/"
echo Obteniendo estado hidrologico anual
c:/Users/DINAGUA/anaconda3/envs/HydroSOS/python.exe python_scripts/annualy_status.py "monthly" "./waterbalance/input/" "./waterbalance/output_csv/12_month/" "./waterbalance/output_json/12_month/"
pause