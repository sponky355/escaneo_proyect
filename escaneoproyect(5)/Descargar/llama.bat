@echo off
title Descarga automática del modelo Llama3 para Ollama
chcp 65001 >nul

echo ==============================================
echo [INFO] Verificando instalación de Ollama...
echo ==============================================

:: Verificar que Ollama está instalado
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama no está instalado o no está en PATH.
    echo Descárgalo desde: https://ollama.com/download
    pause
    exit /b
)

echo [OK] Ollama detectado.
echo.

echo ==============================================
echo [INFO] Verificando si el modelo Llama3 ya está instalado...
echo ==============================================

set "HAS_LLAMA3="

for /f "tokens=* delims=" %%M in ('ollama list ^| findstr /i "llama3"') do (
    set "HAS_LLAMA3=1"
)

if defined HAS_LLAMA3 (
    echo [OK] El modelo Llama3 ya está instalado.
    echo.
    echo Modelos instalados:
    ollama list
    echo.
    pause
    exit /b
)

echo [INFO] Modelo Llama3 no encontrado. Iniciando descarga...
echo.

ollama pull llama3

if %errorlevel% neq 0 (
    echo [ERROR] Ocurrió un error al descargar Llama3.
    echo Revisa tu conexión a Internet.
    pause
    exit /b
)

echo.
echo ==============================================
echo [OK] Descarga de Llama3 completada con éxito.
echo Puedes comprobarlo ejecutando:
echo --> ollama list
echo ==============================================
echo.

pause
exit /b
