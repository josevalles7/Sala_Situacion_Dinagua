@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPTS_DIR=python_scripts"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo     PUBLICACION DE PRODUCTOS DE ESTADO (ESTACIONES)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Tipo          : Estaciones
echo   Ventanas      : 01, 03 y 12 meses
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "filename_json=Ingrese el nombre archivo json (YYYY-MM): "
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

:: 4. Ejecucion de la cadena de publicacion
echo ========================= publicando 01-Mes ===========================
python "%SCRIPTS_DIR%\publish_status_product.py" "./stations/output_json/01_month/" "%filename_json%" 1 "Estaciones"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la publicacion de 01 mes (Estaciones).
    pause
    exit /b %errorlevel%
)
echo.

echo ========================= publicando 03-Meses =========================
python "%SCRIPTS_DIR%\publish_status_product.py" "./stations/output_json/03_month/" "%filename_json%" 3 "Estaciones"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la publicacion de 03 meses (Estaciones).
    pause
    exit /b %errorlevel%
)
echo.

echo ========================= publicando 12-Meses =========================
python "%SCRIPTS_DIR%\publish_status_product.py" "./stations/output_json/12_month/" "%filename_json%" 12 "Estaciones"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la publicacion de 12 meses (Estaciones).
    pause
    exit /b %errorlevel%
)

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo        TODAS LAS PUBLICACIONES FINALIZARON CON EXITO
echo ========================================================
echo Periodo publicado : %filename_json%
echo Tipo de producto  : Estaciones
echo ========================================================
pause