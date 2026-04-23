@echo off

echo Ingrese el codigo cuenca nivel 2 que desea graficar: 
set /p codcuenca_n2=

echo Ingrese fecha de analisis (YYYY-MM-01): 
set /p end_date=

echo Ingrese el tiempo de pronostico (1,2 o 3 meses): 
set /p leadtime=

echo Generating plots for hydrological outlook
echo ===============================================================================
echo Step 1 - bars tercile plot for cuenca_nivel2 %codcuenca_n2% ...
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/plot_esp_codcuenca_n2.py %codcuenca_n2% %end_date% %leadtime%
echo ===============================================================================

echo Step 2 - stacked bars tercile plot for cuenca_nivel2 %codcuenca_n2% ...
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/compute_esp_terciles.py %end_date% %codcuenca_n2% %leadtime%
echo ===============================================================================
echo End of process - Goodbye - 
pause