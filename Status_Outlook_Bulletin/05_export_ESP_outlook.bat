@echo off

echo Ingrese el tiempo de pronostico (1,2 o 3 meses): 
set /p forecast_leadtime=

echo Ingrese fecha de analisis (YYYY-MM-01): 
set /p end_date=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/ESP_outlook_quintiles.py %forecast_leadtime% %end_date%
pause