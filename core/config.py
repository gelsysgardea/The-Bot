"""
Configuración del bot de Binance RedPacket.

Este módulo maneja la configuración de la aplicación, incluyendo credenciales de API
parámetros de conexión y configuraciones de usuario.
"""
import os
from dataclasses import dataclass
from typing import Union, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

def _parse_chat_ids(chat_ids_str: str) -> List[int]:
    """Parsea una cadena de IDs de chat separados por comas a una lista de enteros."""
    if not chat_ids_str:
        return []
    return [int(chat_id.strip()) for chat_id in chat_ids_str.split(',') if chat_id.strip()]

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

@dataclass
class BaseConfig:
    """Clase base de configuración para el bot de Binance RedPacket.
    
    Esta clase maneja toda la configuración necesaria para el funcionamiento del bot.
    """
    """Clase base de configuración para el bot de Binance RedPacket."""

    # Configuración de la API de Telegram
    CLIENT_NAME: str = os.getenv('TELEGRAM_CLIENT_NAME', 'BinanceRedPacketBot')
    API_ID: int = int(os.getenv('TELEGRAM_API_ID', 0))  # Debe ser configurado en .env
    API_HASH: str = os.getenv('TELEGRAM_API_HASH', '')  # Debe ser configurado en .env
    SESSION_NAME: str = 'binance_redpacket_session'

    # Configuración de Binance
    BINANCE_REFERRAL_CODE: str = os.getenv('BINANCE_REFERRAL_CODE', '')
    
    # Configuración de la aplicación
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'

    @property
    def CHATS(self) -> List[int]:
        """Devuelve la lista de chats a monitorear desde variables de entorno o un valor por defecto."""
        default_chats_string = "-1001515379979,-1001813092752,-1001610472708"
        chats_str = os.getenv('TELEGRAM_CHAT_IDS', default_chats_string)
        return _parse_chat_ids(chats_str)
    
    # Headers para las peticiones HTTP
    @property
    def HEADERS(self) -> Dict[str, str]:
        """Devuelve los headers HTTP para las peticiones a la API de Binance."""
        return {
            "User-Agent": os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
            "bnc-uuid": os.getenv('BNC_UUID', ''),  # Obtener del navegador al iniciar sesión
            "device-info": os.getenv('DEVICE_INFO', ''),  # Obtener del navegador
            "clienttype": "web",
            "csrftoken": os.getenv('CSRF_TOKEN', ''),  # Obtener de la respuesta de inicio de sesión
            "fvideo-id": os.getenv('FVIDEO_ID', ''),  # Obtener del navegador
            "fvideo-token": os.getenv('FVIDEO_TOKEN', ''),  # Obtener del navegador
            "x-trace-id": '',  # Se genera dinámicamente
            "x-ui-request-trace": '',  # Se genera dinámicamente
            "lang": "uk-UA",
            "Referer": "https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox",
            "Cookie": os.getenv('BINANCE_COOKIE', ''),  # Obtener del navegador
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración.
        
        Args:
            key: Nombre de la configuración a obtener
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor de la configuración o el valor por defecto
        """
        return getattr(self, key, default)
    
    def update(self, **kwargs) -> None:
        """Actualiza múltiples configuraciones a la vez.
        
        Args:
            **kwargs: Pares clave-valor con las configuraciones a actualizar
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

# Instancia global de configuración
config = BaseConfig()

# Validación de configuración requerida
if not config.API_ID or not config.API_HASH:
    raise ValueError("TELEGRAM_API_ID y TELEGRAM_API_HASH deben estar configurados en el archivo .env")
