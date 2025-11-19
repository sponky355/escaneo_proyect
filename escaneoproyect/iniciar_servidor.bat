@echo off
title Iniciar servidor Flask
chcp 65001 >nul

echo ==================================================
echo [INFO] Iniciando entorno y servidor Flask
echo ==================================================

setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No existe el entorno virtual.
    echo Ejecuta primero "crear_entorno.bat"
    pause
    exit /b
)

:: Activar entorno virtual
echo [INFO] Activando entorno virtual...
call venv\Scripts\activate.bat

:: Mostrar ubicación actual de Python
where python

:: Comprobación del archivo principal
if not exist "app.py" (
    echo [ERROR] No se encontró app.py en esta carpeta.
    pause
    exit /b
)

echo.
echo [INFO] Iniciando servidor Flask y mostrando salida...
echo ==================================================
echo (Presiona CTRL + C para detener el servidor)
echo ==================================================
echo.

:: Ejecutar Flask directamente para mostrar logs en vivo
python app.py

echo.
echo [INFO] Servidor finalizado.
pause
