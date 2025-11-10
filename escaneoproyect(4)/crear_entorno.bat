@echo off
title Crear entorno virtual Flask (forzado)
chcp 65001 >nul
echo ==================================================
echo [INFO] Iniciando creación forzada del entorno virtual
echo ==================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: limpiar variable
set "PYTHON_PATH="

echo [INFO] Buscando Python real (ignorando alias de Microsoft Store)...

:: Buscar en unidades comunes y ubicaciones típicas
for %%V in (C D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%V:\Python39\python.exe" set "PYTHON_PATH=%%V:\Python39\python.exe"
    if exist "%%V:\Python310\python.exe" set "PYTHON_PATH=%%V:\Python310\python.exe"
    if exist "%%V:\Python311\python.exe" set "PYTHON_PATH=%%V:\Python311\python.exe"
    if exist "%%V:\Python312\python.exe" set "PYTHON_PATH=%%V:\Python312\python.exe"
    if exist "%%V:\Program Files\Python311\python.exe" set "PYTHON_PATH=%%V:\Program Files\Python311\python.exe"
    if exist "%%V:\Program Files (x86)\Python311\python.exe" set "PYTHON_PATH=%%V:\Program Files (x86)\Python311\python.exe"
    if exist "%%V:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe" set "PYTHON_PATH=%%V:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe"
)

:: Probar where python (y filtrar alias de WindowsApps)
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
    :: probar lanzador py
    where py >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_PATH=py"
    )
)

if not defined PYTHON_PATH (
    echo [ERROR] No se encontró una instalación válida de Python.
    echo Instala Python desde:
    echo https://www.python.org/downloads/
    echo Marca "Add Python to PATH" al instalar.
    pause
    exit /b
)

echo [INFO] Python detectado en: %PYTHON_PATH%
echo [INFO] Forzando recreación de venv...

if exist venv (
    echo [INFO] Eliminando venv previo...
    rmdir /s /q venv
)

:: Crear venv
%PYTHON_PATH% -m venv venv
if errorlevel 1 (
    echo [WARN] Creación con %PYTHON_PATH% falló. Intentando con 'py'...
    py -m venv venv
)

if not exist venv\Scripts\python.exe (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b
)

echo [INFO] Activando venv e instalando dependencias...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install --upgrade pip

echo [INFO] Instalando Flask y dependencias principales...
venv\Scripts\pip install flask

echo [INFO] Instalando dependencias para IA (Llama/Ollama)...
venv\Scripts\pip install ollama requests

echo [INFO] Instalando dependencias adicionales para desarrollo...
venv\Scripts\pip install python-dotenv blinker

echo [INFO] Verificando instalación...
venv\Scripts\pip list

deactivate

echo ==================================================
echo [OK] Entorno virtual listo con todas las dependencias
echo.
echo [INFO] Dependencias instaladas:
echo   - Flask
echo   - Ollama (para IA/Llama)
echo   - Requests
echo   - Python-dotenv
echo   - Blinker
echo.
echo [NEXT] Ahora instala Ollama desde:
echo        https://ollama.ai/download
echo.
echo [NEXT] Luego ejecuta en CMD:
echo        ollama pull llama2
echo ==================================================
pause