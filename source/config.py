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
    API_HASH: str = "f9a7ab46494a09f801e3bde68b93f5c1"  # Reemplaza con tu API_HASH
    PHONE: str = "+526143037341"  # Tu número de teléfono con código de país

    # Si quieres excluir algún chat específico, agrega su ID aquí con un signo negativo
    EXCLUDED_CHATS: List[int] = field(default_factory=list)

    # Encabezados para Binance (completos)
    HEADERS = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'es-419,es;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'bnc-uuid': 'c14219da-ab9f-4a66-9358-bef22e74dfdb',
        'clienttype': 'web',
        'csrftoken': '0f452b5fd6b22552f3c5b968cfe8d89e',
        'device-info': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVzLU1YIiwicGxhdGZvcm0iOiJXaW5kb3dzIiwib3NfdmVyc2lvbiI6IjEwIiwicGxhdGZvcm1WZXJzaW9uIjoiMTUuMC4wIiwid2luMzJfY3B1IjoieDY0Iiwic2FmYXJpX3ZlcnNpb24iOiI1MzcuMzYiLCJicm93c2VyVmVyc2lvbiI6IjEyNS4wLjAuMCIsImJyb3dzZXJfbmFtZSI6IkNocm9tZSIsInJlZmVycmVyIjoiaHR0cHM6Ly93d3cuYmluYW5jZS5jb20vIiwicmVmZXJyaW5fZG9tYWluIjoiYmluYW5jZS5jb20iLCJzY3JlZW5fd2lkdGgiOjE1MzYsInNjcmVlbl9oZWlnaHQiOjg2NCwiY29va2llX2VuYWJsZWQiOnRydWUsIndlYmdsIjoiV2ViR0wgMy4wIChPcGVuR0wgRVMgMy4wIFdpbmRvd3MpIiwid2Vic29ja2V0IjpudWxsLCJpZ25vcmVfZGlzYWJsZV9zd2lwZV9iYWNrIjp0cnVlLCJ0b3VjaCI6dHJ1ZSwiaXNfY3Jvc3NfaWZyYW1lIjpmYWxzZSwic2NyZWVuX3NjYWxlIjoxLCJkZXZpY2VfbmFtZSI6IiIsInN0YW5kYWxvbmUiOiJ3ZWJnbCIsInJlZmVycmVyX2N1cnJlbnQiOiJodHRwczovL3d3dy5iaW5hbmNlLmNvbS9lcyIsImNsaWVudF9uYW1lIjoiYmluYW5jZWNvbS1hcGktc3RhdGljIiwiZXhwZXJpbWVudHMiOltdfQ==',
        'fvideo-id': '3348ba6afc04ae228bcfd1431f6c11c76ef27302',
        'fvideo-token': 'W8L8mTSCNQna0JYQZTBuEdpUsK1545z6cGAiW7QNqeV3EgPlT6Yiii6SiMmbYjnjOJS49WhAdUhV3wrTSk7/kC3fvw5jhqgZueSRGJ7REBadhBnb3/IFKNvW/J5QmmhuvooxltpOzSOQ11Azuy+1DEJpOeokUpuyzvcqlJhQx/q5MU5hpTHKlM9CpJzfmmMNs=7d',
        'lang': 'es-419',
        'origin': 'https://www.binance.com',
        'referer': 'https://www.binance.com/es/my/wallet/account/payment/cryptobox',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'x-trace-id': 'f60697d6-26dd-4cc8-a233-4f534d46985b',
        'x-ui-request-trace': 'f60697d6-26dd-4cc8-a233-4f534d46985b'
    }
    
    def __getelement__(self, element: str) -> Union[int, float, bool, str]:
        return getattr(self, element, None)
