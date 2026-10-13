@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPTS_DIR=python_scripts"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       CONVERSION JSON A CSV (ESTADOS WATERBALANCE)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Destino       : qgis_status_outlook\csvtables
echo   Ventanas      : 01, 03 y 12 meses
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "filename_json=Ingrese la fecha correspondiente (YYYY-MM): "
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
echo.

:: 4. Ejecucion de la cadena de scripts
echo [1/3] Convirtiendo JSON a CSV: 01-Mes...
python "%SCRIPTS_DIR%\json_to_csv.py" "./waterbalance/output_json/01_month" "%filename_json%" "qgis_status_outlook/csvtables" "01"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la conversion de 01 mes.
    pause
    exit /b %errorlevel%
)
echo.

echo [2/3] Convirtiendo JSON a CSV: 03-Meses...
python "%SCRIPTS_DIR%\json_to_csv.py" "./waterbalance/output_json/03_month" "%filename_json%" "qgis_status_outlook/csvtables" "03"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la conversion de 03 meses.
    pause
    exit /b %errorlevel%
)
echo.

echo [3/3] Convirtiendo JSON a CSV: 12-Meses...
python "%SCRIPTS_DIR%\json_to_csv.py" "./waterbalance/output_json/12_month" "%filename_json%" "qgis_status_outlook/csvtables" "12"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la conversion de 12 meses.
    pause
    exit /b %errorlevel%
)

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo        TODAS LAS CONVERSIONES FINALIZARON CON EXITO
echo ========================================================
echo Tablas CSV listas en: qgis_status_outlook/csvtables
echo Fecha procesada     : %filename_json%
echo ========================================================
pause