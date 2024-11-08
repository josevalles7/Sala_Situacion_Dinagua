@echo off

echo Ingrese el nombre archivo json (YYYY-MM): 
set /p filename_json=
echo ========================= publicando 01-Mes ===========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./stations/output_json/01_month/" %filename_json% 1 "Estaciones"
echo ========================= publicando 03-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./stations/output_json/03_month/" %filename_json% 3 "Estaciones"
echo ========================= publicando 12-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./stations/output_json/12_month/" %filename_json% 12 "Estaciones"
pause