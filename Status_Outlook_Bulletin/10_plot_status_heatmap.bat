@echo off
echo Ingrese fecha de analisis (YYYY-MM-01): 
set /p end_date=

c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/status_heatmap.py %end_date%
pause