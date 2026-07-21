@echo off

echo Ingrese fecha de inicio (YYYY-MM-DD): 
set /p fecha_inicio=

echo Ingrese fecha de fin (YYYY-MM-DD): 
set /p fecha_fin=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/requests_forcing_bulletin.py %fecha_inicio% %fecha_fin%
pause