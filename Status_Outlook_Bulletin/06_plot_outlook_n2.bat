@echo off

echo Ingrese el codigo cuenca nivel 2 que desea graficar: 
set /p codcuenca_n2=

echo Ingrese fecha de analisis (YYYY-MM-01): 
set /p end_date=

echo Ingrese el tiempo de pronostico (1,2 o 3 meses): 
set /p leadtime=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/plot_esp_codcuenca_n2.py %codcuenca_n2% %end_date% %leadtime%
pause