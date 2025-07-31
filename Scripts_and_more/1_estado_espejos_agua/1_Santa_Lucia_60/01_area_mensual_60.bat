@echo off
echo Ingrese el mes de analisis (YYYY-MM):
set /p FECHA= 

CALL C:\Anaconda\Scripts\activate.bat GEE
echo Entorno GEE activado

python C:\Dinagua\1_estado_espejos_agua\1_Santa_Lucia_60\python\estado_mensual_60.py %FECHA%
echo Script ejecutado

pause