pause
echo ========================= publicando 01-Mes ===========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" "2024-10.json" 1 "Modelos"
echo ========================= publicando 03-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" "2024-10.json" 3 "Modelos"
echo ========================= publicando 12-Meses =========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_status_product.py "./waterbalance/output_json/01_month/" "2024-10.json" 12 "Modelos"
pause