"""
Punto de entrada principal para el Binance RedPacket Bot.

Este script inicia el bot de Telegram para monitorear y reclamar sobres rojos de Binance.
Versión mejorada con integración de dashboard y sistema anti-ban avanzado.
"""
import asyncio
import sys
import os
import signal
import argparse
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
from dashboard_integration import dashboard_integration

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
    """Función principal asíncrona mejorada con dashboard y modo headless."""
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Enhanced Binance RedPacket Bot')
        parser.add_argument('--headless', action='store_true', help='Run in headless mode (no dashboard)')
        parser.add_argument('--dashboard', action='store_true', help='Start dashboard')
        parser.add_argument('--adb-fallback', action='store_true', help='Enable ADB fallback')
        args = parser.parse_args()

        # Limpiar la consola
        os.system('cls' if os.name == 'nt' else 'clear')

        # Mostrar banner
        print_banner()

        # Validar configuración
        if not config.API_ID or not config.API_HASH:
            logger.error("API_ID o API_HASH no están configurados. Por favor, configura el archivo .env")
            return 1

        # Start dashboard integration
        dashboard_tasks = []
        if not args.headless or args.dashboard:
            logger.info("Starting dashboard integration...")
            await dashboard_integration.start()

            if args.dashboard:
                logger.info(f"🚀 Dashboard disponible en: http://localhost:8501")
                # Start dashboard in a separate process or thread
                # For now, we'll just show the URL
                dashboard_url = dashboard_integration.get_dashboard_url()
                logger.info(f"📊 Access dashboard at: {dashboard_url}")

        # Inicializar cliente de Telegram mejorado
        logger.info("Inicializando cliente de Telegram mejorado...")
        client = BaseClient()

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Iniciar el cliente
        await client.start()

        # Obtener información del usuario
        me = await client.get_me()
        logger.success(f"✅ Sesión iniciada como: {me.first_name} (@{me.username or 'sin_usuario'})")

        # Mostrar chats monitoreados
        logger.info("📱 Monitoreando los siguientes chats:")
        for chat_id in config.CHATS:
            try:
                entity = await client.get_entity(chat_id)
                logger.info(f"  - {entity.title} (ID: {chat_id})")
            except Exception as e:
                logger.warning(f"No se pudo obtener información del chat {chat_id}: {e}")

        # Show system information
        logger.info("🔧 Sistema configurado:")
        logger.info(f"  - Anti-ban: ✅ Activado")
        logger.info(f"  - TLS Fingerprinting: ✅ {['curl_cffi' if 'curl_cffi' in str(config.USER_AGENT_ROTATION[0]) else 'httpx']}")
        logger.info(f"  - Header Rotation: ✅ Cada {config.ANTI_BAN_SETTINGS['header_rotation_interval']} claims")
        logger.info(f"  - Risk-based Delays: ✅ {config.ANTI_BAN_SETTINGS['base_delay_range']}s base")
        logger.info(f"  - ADB Fallback: {'✅' if args.adb_fallback else '❌'} {'Activado' if args.adb_fallback else 'Desactivado'}")
        logger.info(f"  - Emergency Mode: ✅ MODO SIERPE disponible")
        logger.info(f"  - Dashboard: {'✅' if not args.headless else '❌'} {'Activado' if not args.headless else 'Desactivado'}")

        logger.info("🚀 El bot está en ejecución. Presiona Ctrl+C para salir.")

        # Mantener el bot en ejecución con tareas en background
        await asyncio.gather(
            client.run_until_disconnected(),
            *dashboard_tasks,
            return_exceptions=True
        )

    except asyncio.CancelledError:
        logger.info("📴 Deteniendo el bot...")
    except KeyboardInterrupt:
        logger.info("📴 Interrupción solicitada por el usuario...")
    except Exception as e:
        logger.error(f"💥 Error inesperado: {e}", exc_info=True)
        return 1
    finally:
        # Asegurarse de que el cliente se detenga correctamente
        try:
            if 'client' in locals() and hasattr(client, 'is_connected') and client.is_connected():
                await client.disconnect()
                logger.info("✅ Sesión de Telegram finalizada correctamente.")

            # Detener dashboard integration
            if 'dashboard_integration' in globals():
                await dashboard_integration.stop()
                logger.info("✅ Dashboard integration detenido correctamente.")

        except Exception as e:
            logger.error(f"Error durante el apagado: {e}")

        return 0

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
