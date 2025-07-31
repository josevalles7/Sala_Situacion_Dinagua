pause

CALL C:\Anaconda\Scripts\activate.bat GEE
echo Entorno GEE activado

python C:\Dinagua\1_estado_espejos_agua\1_Laguna_Merin\python\grafica_percentiles.py %FECHA%
echo Script ejecutado

pause