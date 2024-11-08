@echo off

echo Ingrese el mes de analisis (MM): 
set /p month_analysis=

echo Ingrese el ano de analisis (YYYY): 
set /p year_analysis=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/export_modelling_results_n2.py %month_analysis% %year_analysis%
pause