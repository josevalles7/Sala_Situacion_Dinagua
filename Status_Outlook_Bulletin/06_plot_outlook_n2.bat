@echo off

echo Ingrese el codigo cuenca nivel 2 que desea graficar: 
set /p codcuenca_n2=

echo Ingrese fecha de analisis (YYYY-MM-01): 
set /p end_date=

echo Generating plots for hydrological outlook
echo ===============================================================================
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/compute_esp_terciles.py %end_date% %codcuenca_n2%
echo End of process - Goodbye - 
pause