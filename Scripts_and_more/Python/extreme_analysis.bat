@echo off

echo Ingresa el nombre del archivo csv: 
set /p station=

c:\Users\DINAGUA\anaconda3\envs\hydromt-wflow\python.exe Return_period/extreme_value_analysis.py %station%
pause