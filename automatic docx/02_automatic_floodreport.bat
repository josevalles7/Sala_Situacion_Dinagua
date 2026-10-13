@echo off
set "CONDA_ENV=floodreport"
set "SCRIPT_NAME=flood_report.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo     GENERACION DE INFORME DE SITUACION Y PRONOSTICO
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo   Fuente Datos  : database_report.xlsx e archivos PNG de folder "Imagenes"
echo ========================================================
echo.
echo Presiona cualquier tecla para generar el informe...
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
echo [INFO] Procesando datos y generando documento...
echo.

:: 3. Ejecucion del script
python "%SCRIPT_NAME%"

:: 4. Mensaje de cierre y recordatorio de revision
echo.
echo ========================================================
echo               INFORME GENERADO CON EXITO
echo ========================================================
echo Recordatorio para el elaborador:
echo - Abre el archivo Word generado y revisa el contenido.
echo - Verifica graficos, tablas y consistencia de datos.
echo ========================================================
pause