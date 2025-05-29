@echo off
set LOG_FILE=bot_debug.log
echo Iniciando depuracion... > %LOG_FILE%

echo Verificando Python...
python --version >> %LOG_FILE% 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python no esta instalado o no esta en el PATH. >> %LOG_FILE%
    echo Error: Python no esta instalado o no esta en el PATH.
    pause
    exit /b 1
)

echo Instalando dependencias...
python -m pip install --upgrade pip >> %LOG_FILE% 2>&1
pip install python-dotenv telethon >> %LOG_FILE% 2>&1

echo Iniciando bot...
python -c "
import os
import sys
import asyncio
import traceback

print('Iniciando depuracion...')
try:
    from core.telegram import BaseClient
    print('Modulos importados correctamente')
    
    async def main():
        try:
            print('Creando cliente...')
            client = BaseClient()
            print('Iniciando cliente...')
            if await client.start():
                print('✅ Bot iniciado correctamente')
                await client.client.run_until_disconnected()
            else:
                print('❌ No se pudo iniciar el cliente')
        except Exception as e:
            print(f'❌ Error en main(): {str(e)}')
            print('Detalles del error:')
            traceback.print_exc()
    
    print('Ejecutando bucle de eventos...')
    asyncio.run(main())
    
except Exception as e:
    print(f'❌ Error al importar modulos: {str(e)}')
    print('Detalles del error:')
    traceback.print_exc()
    
input('\nPresiona Enter para salir...')
" >> %LOG_FILE% 2>&1

type %LOG_FILE%
echo.
echo Revisa el archivo %LOG_FILE% para mas detalles.
pause
