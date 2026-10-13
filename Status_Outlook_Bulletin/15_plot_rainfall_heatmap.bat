@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\daily_rainfall_n2.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       CALCULO DE PRECIPITACION DIARIA (NIVEL 2)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "user_start_date=Fecha_inicio en formato YYYY-MM-DD: "
echo.
set /p "user_end_date=Fecha_fin en formato YYYY-MM-DD: "
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
echo [INFO] Procesando precipitacion del %user_start_date% al %user_end_date%...
echo.

:: 4. Ejecucion del script con argumentos protegidos
python "%SCRIPT_NAME%" "%user_start_date%" "%user_end_date%"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo de precipitacion diaria.
    pause
    exit /b %errorlevel%
)

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
pause