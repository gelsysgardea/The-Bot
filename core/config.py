"""
Configuración del bot de Binance RedPacket.

Este módulo maneja la configuración de la aplicación, incluyendo credenciales de API
parámetros de conexión y configuraciones de usuario.
"""
import os
import uuid
import time
import random
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

    # Anti-Ban Configuration - 2025 Advanced Settings
    @property
    def USER_AGENT_ROTATION(self) -> List[str]:
        """10 Android user agents for rotation evading 2025 bot detection."""
        return [
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Redmi Note 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; OnePlus 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Galaxy S23) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
        ]

    @property
    def DEVICE_FINGERPRINTS(self) -> List[str]:
        """3 Android device hashes for TLS fingerprint rotation."""
        return [
            "ANDROID_9F2A8B3C7D4E5F6A",  # Samsung Galaxy S22 fingerprint
            "ANDROID_7B4C6D1E9F8A2B3C",  # Google Pixel 6 fingerprint
            "ANDROID_3D8E5F2A9C1B7D4E"   # Xiaomi Redmi Note 12 fingerprint
        ]

    @property
    def ANTI_BAN_SETTINGS(self) -> Dict[str, Any]:
        """Advanced anti-ban configuration for 2025 Binance detection."""
        return {
            "base_delay_range": (8, 15),  # Base delay between claims (seconds)
            "risk_based_delays": {
                "0-50": (8, 15),     # Normal delays
                "51-70": (15, 25),   # Extended delays
                "71-85": (25, 40),   # Conservative delays
                "86+": (60, 90)      # Emergency mode delays
            },
            "header_rotation_interval": 5,  # Rotate headers every 5 claims
            "consecutive_failures_threshold": 3,  # Siesta mode after 3 failures
            "siesta_mode_duration": 7200,  # 2 hours in seconds
            "captcha_timeout": 3600,  # 1 hour timeout on CAPTCHA
            "session_refresh_threshold": 3,  # Session failures per 24h
            "lockdown_duration": 21600,  # 6 hours lockdown
            "claim_success_bonus_delay": 5,  # Extra 5s after successful claim
            "exponential_backoff_sequence": [3, 9, 27],  # Retry delays
            "ban_detection_signals": {
                "risk_score_threshold": 85,  # Critical risk score
                "max_requests_per_minute": 10,  # Rate limit for incoming codes
                "claim_threshold_notification": 0.01  # Notify for claims > 0.01 BNB
            }
        }

    @property
    def ADB_SETTINGS(self) -> Dict[str, Any]:
        """ADB fallback system configuration for Redmi Note 12."""
        return {
            "device_id": os.getenv('ADB_DEVICE_ID', ''),
            "coordinates_uhd": {
                "binance_launcher": (720, 1944),
                "redpacket_section": (1080, 1620),
                "claim_input_focus": (1920, 1080),
                "submit_button": (2160, 1800),
                "captcha_skip": (1080, 1400),
                "back_navigation": (360, 216),
                "app_close": (3600, 180)
            },
            "timeout_screenshot": 10,
            "timeout_step_delay": 3,
            "screenshot_path": "C:\\bots\\redpackets\\screenshots\\",
            "fallback_triggers": {
                "api_failure_count": 3,
                "ban_detection": True,
                "session_expiry": True
            }
        }

    @property
    def NOTIFICATION_SETTINGS(self) -> Dict[str, Any]:
        """Telegram and dashboard notification settings."""
        return {
            "admin_chat_id": int(os.getenv('TELEGRAM_ADMIN_CHAT_ID', '0')),
            "minimum_claim_bnb": float(os.getenv('MINIMUM_CLAIM_BNB', '0.01')),
            "critical_alerts_enabled": True,
            "success_notifications": True,
            "failure_notifications": False,  # Only notify for critical failures
            "ban_warning_notifications": True
        }

    @property
    def COOKIE_STORAGE(self) -> Dict[str, str]:
        """Cookie and session persistence paths."""
        return {
            "cookies_file": "C:\\bots\\binance_cookies.txt",
            "cf_bm_file": "C:\\bots\\cf_bm_cookies.txt",
            "session_file": "C:\\bots\\binance_session.json",
            "rotation_interval": 86400  # 24 hours
        }

    @property
    def LOG_STORAGE(self) -> Dict[str, str]:
        """Logging configuration."""
        return {
            "claims_csv": "C:\\bots\\redpackets\\claims_log.csv",
            "errors_csv": "C:\\bots\\redpackets\\errors_log.csv",
            "ban_signals_csv": "C:\\bots\\redpackets\\ban_signals.csv"
        }

    def generate_trace_id(self) -> str:
        """Generate x-trace-id with UUIDv4 + timestamp format."""
        return f"{uuid.uuid4().hex}{int(time.time() * 1000)}"

    def generate_device_id(self) -> str:
        """Generate Android device ID in ANDROID_XXXXX format."""
        return f"ANDROID_{random.randint(10000, 99999)}"

    def get_rotating_user_agent(self, claim_count: int) -> str:
        """Get rotating user agent based on claim count."""
        index = (claim_count // self.ANTI_BAN_SETTINGS["header_rotation_interval"]) % len(self.USER_AGENT_ROTATION)
        return self.USER_AGENT_ROTATION[index]

    def get_rotating_device_fingerprint(self, claim_count: int) -> str:
        """Get rotating device fingerprint based on claim count."""
        index = (claim_count // self.ANTI_BAN_SETTINGS["header_rotation_interval"]) % len(self.DEVICE_FINGERPRINTS)
        return self.DEVICE_FINGERPRINTS[index]

    def get_risk_based_delay(self, risk_score: int) -> tuple:
        """Get delay range based on risk score."""
        settings = self.ANTI_BAN_SETTINGS["risk_based_delays"]
        for score_range, delay_range in settings.items():
            low, high = map(int, score_range.split('-'))
            if low <= risk_score <= high:
                return delay_range
        return settings["86+"]  # Emergency delays for very high scores
    
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
