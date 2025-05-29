"""
Punto de entrada principal para el Binance RedPacket Bot.

Este script inicia el bot de Telegram para monitorear y reclamar sobres rojos de Binance.
"""
import asyncio
import sys
from pathlib import Path

# Configurar el path para importaciones
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Configuración de consola y logging
from core.utils import setup_console, setup_logging, logger
from core.config import config

# Configurar consola y logging
setup_console()
logger = setup_logging(config.LOG_LEVEL)

# Importar después de configurar el logging
from core.telegram import BaseClient

def print_banner():
    """Muestra el banner de la aplicación."""
    banner = """
╔══════════════════════════════════════════╗
║    ██████╗░██╗███╗░░██╗░█████╗░███╗░░██╗  ║
║    ██╔══██╗██║████╗░██║██╔══██╗████╗░██║  ║
║    ██████╔╝██║██╔██╗██║███████║██╔██╗██║  ║
║    ██╔══██╗██║██║╚████║██╔══██║██║╚████║  ║
║    ██████╔╝██║██║░╚███║██║░░██║██║░╚███║  ║
║    ╚═════╝░╚═╝╚═╝░░╚══╝╚═╝░░╚═╝╚═╝░░╚══╝  ║
║                                            ║
║    ██████╗░███████╗██████╗░██████╗░░█████╗╗
║    ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██║
║    ██████╔╝█████╗░░██║░░██║██████╔╝███████║
║    ██╔══██╗██╔══╝░░██║░░██║██╔═══╝░██╔══██║
║    ██║░░██║███████╗██████╔╝██║░░░░░██║░░██║
║    ╚═╝░░╚═╝╚══════╝╚═════╝░╚═╝░░░░░╚═╝░░╚═╝
║                                            ║
║    ██╗░░░██╗░█████╗░████████╗░█████╗░██╗  ║
║    ╚██╗░██╔╝██╔══██╗╚══██╔══╝██╔══██╗██║  ║
║    ░╚████╔╝░██║░░██║░░░██║░░░███████║██║  ║
║    ░░╚██╔╝░░██║░░██║░░░██║░░░██╔══██║╚═╝  ║
║    ░░░██║░░░╚█████╔╝░░░██║░░░██║░░██║██╗  ║
║    ░░░╚═╝░░░░╚════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝  ║
║                                            ║
║    by: Binance RedPacket Team              ║
╚══════════════════════════════════════════╝
"""
    print(banner)

async def main_async():
    try:
        # Limpiar la consola
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Mostrar banner
        print_banner()
        
        # Validar configuración
        if not config.API_ID or not config.API_HASH:
            logger.error("API_ID o API_HASH no están configurados. Por favor, configura el archivo .env")
            return
        
        # Inicializar cliente de Telegram
        logger.info("Inicializando cliente de Telegram...")
        client = BaseClient()
        
        # Iniciar el cliente
        await client.start()
        
        # Obtener información del usuario
        me = await client.get_me()
        logger.success(f"Sesión iniciada como: {me.first_name} (@{me.username or 'sin_usuario'})")
        
        # Mostrar chats monitoreados
        logger.info("\nMonitoreando los siguientes chats:")
        for chat_id in config.CHATS:
            try:
                entity = await client.get_entity(chat_id)
                logger.info(f"- {entity.title} (ID: {chat_id})")
            except Exception as e:
                logger.warning(f"No se pudo obtener información del chat {chat_id}: {e}")
        
        logger.info("\nEl bot está en ejecución. Presiona Ctrl+C para salir.")
        
        # Mantener el bot en ejecución
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Deteniendo el bot...")
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        raise
    finally:
        # Asegurarse de que el cliente se detenga correctamente
        if 'client' in locals() and client.is_connected():
            await client.disconnect()
            logger.info("Sesión finalizada correctamente.")

def main():
    """Función principal de entrada."""
    try:
        # Configurar el bucle de eventos para Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        # Ejecutar el bot
        asyncio.run(main_async())
        
    except KeyboardInterrupt:
        logger.info("Aplicación detenida por el usuario.")
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        return 1
    finally:
        logger.info("¡Hasta luego!")
    
    return 0

if __name__ == "__main__":
    main()
