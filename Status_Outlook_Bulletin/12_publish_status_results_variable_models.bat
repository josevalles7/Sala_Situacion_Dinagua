@echo off

echo Ingrese el nombre archivo json (YYYY-MM): 
set /p filename_json=
echo ========================= publicando vriables ===========================
C:\Users\Usuario\anaconda3\envs\hydroSOS\python.exe python_scripts/publish_status_variables.py "./waterbalance/output_json/output_variables/" %filename_json%
pause