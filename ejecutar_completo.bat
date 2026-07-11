@echo off
title Simulador de Trafico Cusco - Sistema Completo con ML/IA

echo.
echo ======================================================================
echo        SIMULADOR DE TRAFICO CUSCO - SISTEMA COMPLETO
echo    Backend FastAPI + Dashboard React + Motor ML (RF + DQN)
echo ======================================================================
echo.

:: Verificar Python
set PYTHON_WORKS=0
for /f "tokens=*" %%i in ('py -3.11 -c "print('OK')" 2^>^&1') do (
    if "%%i"=="OK" set PYTHON_WORKS=1
)
if %PYTHON_WORKS%==0 (
    echo [ERROR] Python 3.11 no encontrado. Ejecute instalar_dependencias.bat primero.
    pause
    exit /b 1
)

:: Verificar Node
node --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js no encontrado. Instala Node.js 18+
    pause
    exit /b 1
)

:: Verificar si los modelos ML existen, si no, entrenarlos
echo [0/4] Verificando modelos de Machine Learning...
if not exist "%~dp0backend\ml_models\predictor_congestion.pkl" (
    echo      -> Modelos no encontrados. Entrenando desde el dataset...
    py -3.11 "%~dp0backend\train_models.py"
    if errorlevel 1 (
        echo [ADVERTENCIA] El entrenamiento fallo. La IA usara modo heuristico.
    ) else (
        echo      -> Modelos entrenados y guardados correctamente.
    )
) else (
    echo      -> Modelos ML encontrados. RandomForest + DQN listos.
)
echo.

echo [1/4] Iniciando backend FastAPI en http://localhost:8000 ...
start "Backend FastAPI - Simulador Cusco" cmd /k "cd /d "%~dp0" && py -3.11 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Esperar para que el backend arranque y cargue los modelos ML
timeout /t 6 /nobreak > nul

echo [2/4] Verificando que el backend este respondiendo...
py -3.11 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > nul 2>&1
if errorlevel 1 (
    echo      [ADVERTENCIA] Backend aun arrancando, esperando 5 segundos mas...
    timeout /t 5 /nobreak > nul
) else (
    echo      -> Backend OK.
)
echo.

echo [3/4] Iniciando dashboard React en http://localhost:5173 ...
start "Dashboard React - Simulador Cusco" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Esperar para que el frontend arranque
timeout /t 5 /nobreak > nul

echo [4/4] Abriendo navegador...
start "" "http://localhost:5173"

echo.
echo ======================================================================
echo   Sistema iniciado correctamente.
echo.
echo   Dashboard:   http://localhost:5173
echo   API REST:    http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo.
echo   MOTOR ML ACTIVO:
echo     - Random Forest (Scikit-learn): prediccion de congestion
echo     - Random Forest Classifier: clasificacion de nivel de trafico
echo     - DQN (PyTorch): optimizacion adaptativa de semaforos
echo.
echo   El agente RL aprende en tiempo real durante la simulacion.
echo   Los pesos se actualizan cada 50 pasos de simulacion.
echo.
echo   Cierra las ventanas de consola para detener el sistema.
echo ======================================================================
echo.
pause
