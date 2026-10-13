@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\export_modelling_results_n2.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo     EXPORTACION DE RESULTADOS DE MODELACION (N2)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "month_analysis=Ingrese el mes de analisis (MM): "
echo.
set /p "year_analysis=Ingrese el ano de analisis (YYYY): "
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
echo [INFO] Exportando resultados para el periodo: %month_analysis%/%year_analysis%...
echo.

:: 4. Ejecucion del script con argumentos protegidos
python "%SCRIPT_NAME%" "%month_analysis%" "%year_analysis%"

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
pause