from dataclasses import dataclass, field
from typing import Union, List

@dataclass
class Config:
    # Canales a monitorear (puedes agregar o quitar según necesites)
    CHATS = [
        -1001515379979,  # Binance Crypto Box Code
        -1001813092752,  # Binance Red packet crypto box
        -1001610472708,  # 🐋 Chat Whale Box 🎁
    ]

    # Configuración de Telegram
    CLIENT_NAME: str = "BinanceUser"  # Puedes cambiar esto
    API_ID: int = 25388732  # Reemplaza con tu API_ID
    API_HASH: str = "***REMOVED***"  # Reemplaza con tu API_HASH
    PHONE: str = "+526143037341"  # Tu número de teléfono con código de país

    # Si quieres excluir algún chat específico, agrega su ID aquí con un signo negativo
    EXCLUDED_CHATS: List[int] = field(default_factory=list)

    # Encabezados para Binance (completos)
    HEADERS = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'es-419,es;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'bnc-uuid': '***REMOVED***',
        'clienttype': 'web',
        'csrftoken': '***REMOVED***',
        'device-info': '***REMOVED***',
        'fvideo-id': '***REMOVED***',
        'fvideo-token': '***REMOVED***',
        'lang': 'es-419',
        'origin': 'https://www.binance.com',
        'referer': 'https://www.binance.com/es/my/wallet/account/payment/cryptobox',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-trace-id': '***REMOVED***',
        'x-ui-request-trace': '***REMOVED***'
    }
    
    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
