@echo off
cls
echo ==========================================================
echo      INSTALACION FORZADA Y LIMPIA DE MONGODB
echo ==========================================================
echo.

REM -----------------------------------------------------------
REM 1) DETENER Y BORRAR SERVICIO SI EXISTE
REM -----------------------------------------------------------
echo [INFO] Comprobando servicio MongoDB existente...

sc query MongoDB >nul 2>&1
IF %ERRORLEVEL%==0 (
    echo [INFO] Deteniendo servicio MongoDB...
    net stop MongoDB >nul 2>&1

    echo [INFO] Eliminando servicio MongoDB...
    sc delete MongoDB >nul 2>&1
    echo [OK] Servicio MongoDB eliminado.
) ELSE (
    echo [OK] No existía servicio MongoDB previo.
)

echo.

REM -----------------------------------------------------------
REM 2) ELIMINAR INSTALACIONES ANTERIORES
REM -----------------------------------------------------------
echo [INFO] Eliminando instalaciones previas de MongoDB...

rmdir /s /q "C:\Program Files\MongoDB" >nul 2>&1
rmdir /s /q "C:\data" >nul 2>&1

echo [OK] Instalaciones previas eliminadas.
echo.

REM -----------------------------------------------------------
REM 3) DESCARGAR INSTALADOR
REM -----------------------------------------------------------
set MONGO_URL=https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-7.0.2-signed.msi
set MONGO_MSI=mongo.msi

echo [INFO] Descargando MongoDB Community Server 7.0...
powershell -command "(New-Object Net.WebClient).DownloadFile('%MONGO_URL%', '%MONGO_MSI%')"

IF NOT EXIST "%MONGO_MSI%" (
    echo [ERROR] No se pudo descargar MongoDB.
    pause
    exit /B
)

echo [OK] Descarga completa.
echo.

REM -----------------------------------------------------------
REM 4) INSTALAR MONGODB DESDE CERO
REM -----------------------------------------------------------
echo [INFO] Instalando MongoDB desde cero...

msiexec /qn /i "%MONGO_MSI%" INSTALLLOCATION="C:\Program Files\MongoDB\Server\7.0\" ADDLOCAL="all"

echo [OK] Instalación completada.
echo.

REM -----------------------------------------------------------
REM 5) CREAR CARPETA DATA/DB
REM -----------------------------------------------------------
echo [INFO] Creando rutas de base de datos...
mkdir "C:\data\db" >nul 2>&1
echo [OK] Rutas creadas.
echo.

REM -----------------------------------------------------------
REM 6) CREAR SERVICIO NUEVO
REM -----------------------------------------------------------
echo [INFO] Creando servicio MongoDB limpio...

sc create MongoDB binPath= "\"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe\" --dbpath=\"C:\data\db\" --logpath=\"C:\data\log.txt\"" start= auto

net start MongoDB
echo [OK] Servicio creado e iniciado.
echo.

REM -----------------------------------------------------------
REM 7) AGREGAR MONGO AL PATH
REM -----------------------------------------------------------
echo [INFO] Agregando MongoDB al PATH...
setx PATH "%PATH%;C:\Program Files\MongoDB\Server\7.0\bin" >nul
echo [OK] PATH actualizado.
echo.

REM -----------------------------------------------------------
REM 8) VERIFICAR INSTALACION
REM -----------------------------------------------------------
echo [INFO] Verificando instalación...

where mongod >nul 2>&1
IF %ERRORLEVEL%==0 (
    echo.
    echo [OK] MongoDB instalado correctamente.
    mongod --version
) ELSE (
    echo.
    echo [ERROR] La instalación falló.
)

echo [INFO] Creando base de datos 'escaneo_facturas' y colección 'facturas'...

REM --- crear archivo temporal JS ---
echo use escaneo_facturas > init_mongo.js
echo db.createCollection("facturas") >> init_mongo.js
echo db.facturas.insertOne({ factura_inicial: true, fecha: new Date() }) >> init_mongo.js

REM --- ejecutarlo con mongosh ---
"C:\Program Files\MongoDB\Server\7.0\bin\mongosh.exe" init_mongo.js

del init_mongo.js >nul

echo [OK] Base de datos y colección creadas automaticamente.
echo.





pause
exit
