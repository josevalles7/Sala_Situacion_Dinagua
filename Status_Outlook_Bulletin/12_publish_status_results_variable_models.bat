@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\publish_model_variables.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo     PUBLICACION DE VARIABLES DE MODELO (WATERBALANCE)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo   Directorio    : ./waterbalance/output_json/output_variables/
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

:: 4. Ejecucion del script
echo ========================= Publicando variables ===========================
python "%SCRIPT_NAME%" "./waterbalance/output_json/output_variables/" "%filename_json%"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo la publicacion de las variables del modelo.
    pause
    exit /b %errorlevel%
)

:: 5. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
echo Periodo publicado : %filename_json%
echo ========================================================
pause