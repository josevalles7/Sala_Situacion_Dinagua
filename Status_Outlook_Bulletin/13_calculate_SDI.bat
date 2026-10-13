@echo off
set "CONDA_ENV=HydroSOS"
set "SCRIPT_NAME=python_scripts\SDI.py"

cd /d "%~dp0"

:: 1. Mensaje de bienvenida dinamico
echo ========================================================
echo        CALCULO DE SDI (STREAMFLOW DROUGHT INDEX)
echo                       HYDROSOS
echo ========================================================
echo   Entorno Conda : %CONDA_ENV%
echo   Script Python : %SCRIPT_NAME%
echo ========================================================
echo.
echo Presiona cualquier tecla para iniciar el calculo de SDI...
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

:: 3. Ejecucion del script
echo ========================= Calculando SDI ===========================
python "%SCRIPT_NAME%"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo el calculo de SDI.
    pause
    exit /b %errorlevel%
)

:: 4. Mensaje de finalizacion
echo.
echo ========================================================
echo                 PROCESO FINALIZADO
echo ========================================================
pause