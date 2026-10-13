
@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\requests_forcing_bulletin.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       DESCARGA DE DATOS DE FORZANTES - HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "fecha_inicio=Ingrese fecha de inicio (YYYY-MM-DD): "
echo.
set /p "fecha_fin=Ingrese fecha de fin (YYYY-MM-DD): "
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
echo [INFO] Solicitando forzantes para el periodo: %fecha_inicio% al %fecha_fin%...
echo.

:: 4. Ejecucion del script con argumentos protegidos
python "%SCRIPT_NAME%" "%fecha_inicio%" "%fecha_fin%"

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
pause