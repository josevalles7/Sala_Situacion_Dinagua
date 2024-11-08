@echo off

echo Ingrese el nombre archivo json (YYYY-MM): 
set /p filename_json=
echo ========================= publicando 01-Mes ===========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" %filename_json% 1 "Modelos"
echo ========================= publicando 03-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" %filename_json% 3 "Modelos"
echo ========================= publicando 12-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" %filename_json% 12 "Modelos"
pause