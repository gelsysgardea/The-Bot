@echo off
cls
title Binance RedPacket Bot - Iniciando...

echo ==============================================
echo  Iniciando Configuración de Binance RedPacket Bot
echo ==============================================
echo.

echo [PASO 1/4] Verificando Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python no está instalado o no está en el PATH.
    echo Por favor, instala Python 3.7 o superior desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [PASO 2/4] Actualizando pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo actualizar pip. Verifica tu conexión a Internet.
    pause
    exit /b 1
)

echo.
echo [PASO 3/4] Instalando dependencias...
python -m pip install python-dotenv telethon httpx
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudieron instalar las dependencias.
    echo Por favor, verifica tu conexión a Internet e inténtalo de nuevo.
    pause
    exit /b 1
)

echo.
echo [PASO 4/4] Iniciando Binance RedPacket Bot...
echo ==============================================
echo  ¡Todo listo! Iniciando el bot...
echo ==============================================
echo.

:start_bot
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==============================================
    echo  El bot se ha detenido con un código de error: %ERRORLEVEL%
    echo  ¿Deseas reiniciar el bot? (S/N)
    echo ==============================================
    set /p choice=Respuesta: 
    if /i "!choice!"=="s" (
        echo.
        echo Reiniciando el bot...
        timeout /t 2 >nul
        goto start_bot
    )
)

echo.
echo ==============================================
echo  El bot ha terminado. Presiona cualquier tecla para salir...
echo ==============================================
pause >nul
