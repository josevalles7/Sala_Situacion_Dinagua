@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPTS_DIR=python_scripts"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       GENERACION DE GRAFICOS Y TERCILES ESP (N2)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Procesos      : Graficos de cuenca + Calculo de terciles
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "codcuenca_n2=Ingrese el codigo cuenca nivel 2 que desea graficar: "
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
echo.

:: 4. Ejecucion de la cadena de scripts
echo [1/2] Generando graficos para el pronostico hidrologico...
python "%SCRIPTS_DIR%\plot_esp_codcuenca_n2.py" "%codcuenca_n2%" "%end_date%"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la generacion de graficos de la cuenca %codcuenca_n2%.
    pause
    exit /b %errorlevel%
)
echo.

echo [2/2] Calculando terciles ESP...
python "%SCRIPTS_DIR%\compute_esp_terciles.py" "%end_date%" "%codcuenca_n2%"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo de terciles ESP.
    pause
    exit /b %errorlevel%
)

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
echo Graficos y terciles procesados para cuenca: %codcuenca_n2%
echo Fecha de corte: %end_date%
echo ========================================================
pause