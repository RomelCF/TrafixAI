@echo off
title Instalador de Dependencias - Simulador de Trafico Cusco

echo.
echo ======================================================================
echo    INSTALADOR DE DEPENDENCIAS - SIMULADOR DE TRAFICO CUSCO
echo ======================================================================
echo.

:: Verificar Python 3.11
set PYTHON_WORKS=0
for /f "tokens=*" %%i in ('py -3.11 -c "print('OK')" 2^>^&1') do (
    if "%%i"=="OK" set PYTHON_WORKS=1
)
if %PYTHON_WORKS%==0 (
    echo [INFO] Python 3.11 no fue detectado en el sistema.
    echo Iniciando la descarga e instalacion automatica de Python 3.11...
    echo Esto puede tardar unos minutos. Por favor, espere...
    
    :: Descargar instalador de Python 3.11
    curl -L -o "%temp%\python-installer.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe > nul 2>&1
    if errorlevel 1 (
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%temp%\python-installer.exe'" > nul 2>&1
    )
    
    if not exist "%temp%\python-installer.exe" (
        echo [ERROR] No se pudo descargar el instalador de Python.
        echo Por favor, descarguelo e instalelo manualmente desde: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo [INFO] Ejecutando el instalador de Python...
    echo Se abrira una ventana mostrando el progreso. Por favor, espere a que termine.
    start /wait "" "%temp%\python-installer.exe" /passive PrependPath=1 Include_test=0 Include_launcher=1 InstallLauncherAllUsers=0
    
    :: Borrar instalador temporal
    del "%temp%\python-installer.exe" > nul 2>&1
    
    echo.
    echo ======================================================================
    echo Se ha instalado Python 3.11 correctamente en su sistema.
    echo.
    echo IMPORTANTE: Por favor, cierre esta ventana y vuelva a ejecutar
    echo 'instalar_dependencias.bat' para continuar con la instalacion.
    echo ======================================================================
    echo.
    pause
    exit /b 0
)

:: Verificar Node.js
node --version > nul 2>&1
if errorlevel 1 (
    echo [INFO] Node.js no fue detectado en el sistema.
    echo Iniciando la descarga e instalacion automatica de Node.js LTS...
    echo Esto puede tardar unos minutos. Por favor, espere...
    
    :: Descargar instalador de Node.js
    curl -L -o "%temp%\node-installer.msi" https://nodejs.org/dist/v20.14.0/node-v20.14.0-x64.msi > nul 2>&1
    if errorlevel 1 (
        powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.14.0/node-v20.14.0-x64.msi' -OutFile '%temp%\node-installer.msi'" > nul 2>&1
    )
    
    if not exist "%temp%\node-installer.msi" (
        echo [ERROR] No se pudo descargar el instalador de Node.js.
        echo Por favor, descarguelo e instalelo manualmente desde: https://nodejs.org/
        pause
        exit /b 1
    )
    
    echo [INFO] Ejecutando el instalador de Node.js...
    echo Se abrira una ventana mostrando el progreso. Por favor, complete la instalacion.
    start /wait "" msiexec /i "%temp%\node-installer.msi" /passive
    
    :: Borrar instalador temporal
    del "%temp%\node-installer.msi" > nul 2>&1
    
    echo.
    echo ======================================================================
    echo Se ha instalado Node.js correctamente en su sistema.
    echo.
    echo IMPORTANTE: Por favor, cierre esta ventana y vuelva a ejecutar
    echo 'instalar_dependencias.bat' para continuar con la instalacion.
    echo ======================================================================
    echo.
    pause
    exit /b 0
)

:: Verificar e instalar pip si falta
py -3.11 -m pip --version > nul 2>&1
if errorlevel 1 (
    echo [INFO] pip no fue detectado en Python 3.11. Instalando pip...
    py -3.11 -m ensurepip --default-pip > nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar pip automaticamente.
        pause
        exit /b 1
    )
    echo [INFO] pip se instalo correctamente.
)

echo [1/2] Instalando dependencias de Python (Backend)...
py -3.11 -m pip install -r "%~dp0backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Ocurrio un error al instalar las dependencias de Python.
    pause
    exit /b 1
)
echo.

echo [2/2] Instalando dependencias de Node.js (React Frontend)...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo [ERROR] Ocurrio un error al ejecutar 'npm install' en el frontend.
    pause
    exit /b 1
)
echo.

echo ======================================================================
echo    Instalacion completada con exito.
echo    Ahora puede iniciar el sistema ejecutando 'ejecutar_completo.bat'.
echo ======================================================================
echo.
pause
