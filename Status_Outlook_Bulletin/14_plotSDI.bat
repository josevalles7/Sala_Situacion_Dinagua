@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\plotting_SDI.py"

cd /d "%~dp0"

:: 1. Activacion previa de Conda (solo se ejecuta una vez antes del bucle)
call conda activate %CONDA_ENV% 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Buscando instalacion local de Conda...
    if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\anaconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
        call "%USERPROFILE%\miniconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else if exist "%ProgramData%\anaconda3\Scripts\activate.bat" (
        call "%ProgramData%\anaconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else if exist "%ProgramData%\miniconda3\Scripts\activate.bat" (
        call "%ProgramData%\miniconda3\Scripts\activate.bat" %CONDA_ENV%
    ) else (
        echo [ERROR] No se encontro Conda ni en PATH ni en las rutas estandar.
        pause
        exit /b 1
    )
)

:inicio
cls
echo ========================================================
echo       PROCESAMIENTO DE INDICADORES DE SEQUIA (SDI)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura del codigo de estacion
set /p "codcuenca=Ingrese el codigo de la estacion que desee graficar: "
echo.

:: 3. Ejecucion del script con argumentos protegidos
echo [INFO] Procesando estacion: %codcuenca%...
python "%SCRIPT_NAME%" "%codcuenca%"
if %errorlevel% neq 0 (
    echo [ERROR] Ocurrio un problema al graficar la estacion %codcuenca%.
)
echo.

:: 4. Bucle interactivo para continuar o salir
echo --------------------------------------------------------
set /p "respuesta=Desea graficar otra estacion? (S/N): "

if /i "%respuesta%"=="S" goto inicio

echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
echo Saliendo del programa...
pause
exit /b 0