@echo off
echo Configurando el entorno...
python -c "import sys; print(f'Python {sys.version}')"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Python no est├í instalado o no est├í en el PATH.
    pause
    exit /b 1
)

echo Instalando dependencias...
python -m pip install --upgrade pip
pip install python-dotenv telethon

echo.
echo ===================================
echo  Iniciando Binance RedPacket Bot...
echo ===================================
echo.

python -c "
import os
import sys
import asyncio
from core.telegram import BaseClient

async def main():
    try:
        print('Iniciando bot...')
        client = BaseClient()
        if await client.start():
            print('Bot iniciado correctamente. Presiona Ctrl+C para salir.')
            await client.client.run_until_disconnected()
        else:
            print('No se pudo iniciar el bot.')
            input('Presiona Enter para salir...')
    except Exception as e:
        print(f'Error: {str(e)}')
        input('Presiona Enter para salir...')

if __name__ == '__main__':
    asyncio.run(main())
"

pause
