@echo off

echo Fecha_inicio en formato YYYY-MM-DD: 
set /p user_start_date=

echo Fecha_fin en formato YYYY-MM-DD: 
set /p user_end_date=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/daily_rainfall_n2.py %user_start_date% %user_end_date%
pause