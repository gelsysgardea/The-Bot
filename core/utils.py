"""
Módulo de utilidades para el manejo de consola y logging.
"""
import sys
import os
import platform
from loguru import logger
from pathlib import Path

def setup_console():
    """Configura la consola para soporte UTF-8 y título en Windows."""
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleTitleW("Binance RedPacket Bot")
        except Exception as e:
            logger.warning(f"No se pudo establecer el título de la consola: {e}")
        
        # Configurar UTF-8 en Windows
        try:
            if hasattr(sys, 'version_info') and sys.version_info >= (3, 7):
                import _locale
                _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])
                
            # Configurar la codificación de la consola
            if sys.stdout.encoding != 'utf-8':
                import io
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
                
            # Configurar la variable de entorno para forzar UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # Intentar establecer la página de códigos a UTF-8
            os.system('chcp 65001 >nul 2>&1')
            
        except Exception as e:
            logger.error(f"Error al configurar la consola: {e}")
            raise

def setup_logging(log_level: str = "INFO"):
    """Configura el sistema de logging.
    
    Args:
        log_level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logger
    logger.remove()  # Eliminar el manejador por defecto
    
    # Configurar archivo de log con rotación
    logger.add(
        log_dir / "bot_debug.log",
        rotation="10 MB",
        retention="1 month",
        level=log_level,
        encoding='utf-8',
        backtrace=True,
        diagnose=True
    )
    
    # Configurar salida a consola
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    return logger
