@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\ESP_outlook_tertiles.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       PRONOSTICO POR TERCILOS (ESP OUTLOOK)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "forecast_leadtime=Ingrese el tiempo de pronostico (1, 2 o 3 meses): "
echo.
set /p "end_date=Ingrese fecha de analisis (YYYY-MM-01): "
echo.

:: 3. Activacion de Conda (PATH o busqueda local portable)
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

echo [OK] Entorno "%CONDA_ENV%" activado.
echo [INFO] Ejecutando pronostico ESP (Lead time: %forecast_leadtime%m, Fecha: %end_date%)...
echo.

:: 4. Ejecucion del script con argumentos protegidos
python "%SCRIPT_NAME%" "%forecast_leadtime%" "%end_date%"

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
pause