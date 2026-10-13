@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPTS_DIR=python_scripts"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       CALCULO DE ESTADO HIDROLOGICO - HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Procesos      : Mensual, Trimestral y Anual
echo ========================================================
echo.
echo Presiona cualquier tecla para iniciar el procesamiento en cadena...
pause >nul
echo.

:: 2. Activacion de Conda (PATH o busqueda local portable)
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
echo.

:: 3. Ejecucion de la cadena de scripts
echo [1/3] Obteniendo estado hidrologico mensual...
python "%SCRIPTS_DIR%\monthly_status.py" "monthly" "./waterbalance/input/" "./waterbalance/output_csv/01_month/" "./waterbalance/output_json/01_month/"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo mensual.
    pause
    exit /b %errorlevel%
)
echo.

echo [2/3] Obteniendo estado hidrologico trimestral...
python "%SCRIPTS_DIR%\quaterly_status.py" "monthly" "./waterbalance/input/" "./waterbalance/output_csv/03_month/" "./waterbalance/output_json/03_month/"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo trimestral.
    pause
    exit /b %errorlevel%
)
echo.

echo [3/3] Obteniendo estado hidrologico anual...
python "%SCRIPTS_DIR%\annualy_status.py" "monthly" "./waterbalance/input/" "./waterbalance/output_csv/12_month/" "./waterbalance/output_json/12_month/"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo anual.
    pause
    exit /b %errorlevel%
)

:: 4. Mensaje de finalizacion
echo.
echo ========================================================
echo        TODOS LOS ESTADOS SE PROCESARON CON EXITO
echo ========================================================
echo Archivos generados en: ./waterbalance/
pause