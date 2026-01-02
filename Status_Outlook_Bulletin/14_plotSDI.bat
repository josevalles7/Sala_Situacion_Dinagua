@echo off
:inicio
cls
echo ====================================================
echo   PROCESAMIENTO DE INDICADORES DE SEQUIA (SDI)
echo ====================================================
echo.

:: Solicitar el código de la cuenca
set /p codcuenca="Ingrese el codigo de la estacion que desee graficar: "

:: Ejecutar el script de Python con el argumento
echo.
echo Procesando estacion %codcuenca%...
c:\Users\DINAGUA\anaconda3\envs\HydroSOS\python.exe python_scripts/plotting_SDI.py %codcuenca%
echo.

:: Preguntar si desea continuar
echo ----------------------------------------------------
set /p respuesta="¿Desea graficar otra estacion? (S/N): "

if /i "%respuesta%"=="S" goto inicio

echo.
echo Saliendo del programa...
pause
exit