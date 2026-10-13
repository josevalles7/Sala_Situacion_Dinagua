@echo off
set "CONDA_ENV=floodreport"
set "SCRIPT_NAME=get_data4report.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo       IMPORTACION DE DATOS - SALA DE SITUACION
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.

:: 2. Captura de parametros del usuario
set /p "Q_EROGADO_SG=Ingrese el caudal erogado represa Salto Grande (XXXX y XXXX): "
echo.
set /p "Q_EROGADO_BONETE=Ingrese el caudal erogado represa Rincon del Bonete (XXXX y XXXX): "
echo.
set /p "Q_EROGADO_PALMAR=Ingrese el caudal erogado represa Palmar (XXXX y XXXX): "
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
echo [INFO] Importando datos al archivo database_report.xlsx...
echo.

:: 4. Ejecucion del script con los argumentos pasados
python "%SCRIPT_NAME%" "%Q_EROGADO_SG%" "%Q_EROGADO_BONETE%" "%Q_EROGADO_PALMAR%"

:: 5. Mensaje de cierre e instrucciones siguientes
echo.
echo ========================================================
echo                 TAREA FINALIZADA
echo ========================================================
echo 1. Revisa el archivo database_report.xlsx para validar los datos.
echo 2. Genera la advertencia hidrologica usando el archivo advertencia_codcuenca_n2.xlsm
echo 3. Exporta los mapas de advertencia y el atlas de cuencas hidrograficas de QGIS
echo 4. Si todo esta correcto, ejecuta: automatic_floodreport.bat
echo ========================================================
pause