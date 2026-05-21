@echo off

echo Ingrese el caudal erogado represa Salto Grande (XXXX y XXXX): 
set /p Q_EROGADO_SG=

echo Ingrese el caudal erogado represa Rincon del Bonete (XXXX y XXXX): 
set /p Q_EROGADO_BONETE=

echo Ingrese el caudal erogado represa Palmar (XXXX y XXXX): 
set /p Q_EROGADO_PALMAR=

echo Importando datos al archivo database_report.xlsx
"c:\Users\DINAGUA\anaconda3\envs\floodreport\python.exe" "d:\GitHub\Sala_Situacion_Dinagua\automatic docx\get_data4report.py" "%Q_EROGADO_SG%" "%Q_EROGADO_BONETE%" "%Q_EROGADO_PALMAR%"
echo fin de la tarea. Ir al archivo database_report.xlsx y verificar que todo esta correcto.
echo si todo esta correcto, entonces ejecutar el bat automatic_floodreport.bat
echo fin!
pause