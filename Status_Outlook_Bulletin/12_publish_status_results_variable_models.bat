@echo off

echo Ingrese el nombre archivo json (YYYY-MM): 
set /p filename_json=
echo ========================= publicando vriables ===========================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/publish_model_variables.py "./waterbalance/output_json/output_variables/" %filename_json%

pause
