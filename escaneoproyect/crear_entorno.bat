@echo off
title Crear entorno virtual Flask + Instalación Ollama
chcp 65001 >nul
echo ==================================================
echo [INFO] Iniciando creación forzada del entorno virtual
echo ==================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: limpiar variable
set "PYTHON_PATH="

echo [INFO] Buscando Python real (ignorando alias MS Store)...

:: Buscar Python en rutas posibles
for %%V in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%V:\Python39\python.exe" set "PYTHON_PATH=%%V:\Python39\python.exe"
    if exist "%%V:\Python310\python.exe" set "PYTHON_PATH=%%V:\Python310\python.exe"
    if exist "%%V:\Python311\python.exe" set "PYTHON_PATH=%%V:\Python311\python.exe"
    if exist "%%V:\Python312\python.exe" set "PYTHON_PATH=%%V:\Python312\python.exe"
    if exist "%%V:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe" set "PYTHON_PATH=%%V:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe"
    if exist "%%V:\Program Files\Python311\python.exe" set "PYTHON_PATH=%%V:\Program Files\Python311\python.exe"
    if exist "%%V:\Program Files (x86)\Python311\python.exe" set "PYTHON_PATH=%%V:\Program Files (x86)\Python311\python.exe"
)

:: Probar where python (evita alias MS Store)
if not defined PYTHON_PATH (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if /i not "%%~fP"=="%LocalAppData%\Microsoft\WindowsApps\python.exe" (
            set "PYTHON_PATH=%%~fP"
            goto :found_python
        )
    )
)

:found_python
if not defined PYTHON_PATH (
    where py >nul 2>nul
    if %errorlevel%==0 set "PYTHON_PATH=py"
)

if not defined PYTHON_PATH (
    echo [ERROR] No se encontró una instalación válida de Python.
    echo Descarga desde: https://www.python.org/downloads/
    echo Asegúrate de marcar "Add Python to PATH".
    pause
    exit /b
)

echo [INFO] Python detectado en: %PYTHON_PATH%
echo [INFO] Forzando recreación de entorno virtual...

if exist venv (
    echo [INFO] Eliminando venv previo...
    rmdir /s /q venv
)

:: Crear venv
%PYTHON_PATH% -m venv venv
if errorlevel 1 (
    echo [WARN] Falló creación con Python directo. Probando con py...
    py -m venv venv
)

if not exist venv\Scripts\python.exe (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b
)

echo [INFO] Activando venv e instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

:: DEPENDENCIAS NORMALES
pip install flask
pip install ollama
pip install requests
pip install python-dotenv
pip install blinker

:: DEPENDENCIAS PARA FACTURAS
pip install pandas
pip install openpyxl

:: DEPENDENCIAS MONGO DB (LAS CORRECTAS)
pip install pymongo
pip install dnspython

deactivate

echo ==================================================
echo [OK] Entorno virtual listo con dependencias:
echo  - Flask
echo  - Ollama
echo  - Requests
echo  - Dotenv
echo  - Blinker
echo  - Pandas + Openpyxl (Excel)
echo  - MongoDB: pymongo + dnspython
echo ==================================================


echo.
echo ==============================================
echo [INFO] Verificando instalador de Ollama local
echo ==============================================

set "OLLAMA_SETUP_PATH=%~dp0Descargar\OllamaSetup(1).exe"

if exist "%OLLAMA_SETUP_PATH%" (
    echo [OK] Instalador Ollama encontrado:
    echo      %OLLAMA_SETUP_PATH%
    echo.
    echo [INFO] Iniciando instalación de Ollama...
    start "" "%OLLAMA_SETUP_PATH%"
    echo.
    echo [NEXT] Luego de instalar, corre en CMD manualmente:
    echo        ollama serve
) else (
    echo [WARN] No se encontró OllamaSetup(1).exe en carpeta /Descargar
    echo        Descarga desde: https://ollama.com/download
)

echo ==============================================
echo.
pause
