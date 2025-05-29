import httpx

from core.config import config
from core.utils import logger

from typing import Optional


class BinanceAPI:
    def __init__(self) -> None: ...

    async def request_redpacket(self, redpacket_code: str) -> Optional[httpx.Response]:
        """
        Send request to Binance API and call the
        """
        async with httpx.AsyncClient(headers=config.HEADERS) as client:
            try:
                response = await client.post(
                    "https://www.binance.com/bapi/pay/v1/private/binance-pay/gift-box/code/grabV2",
                    json={
                        "channel": "DEFAULT",
                        "grabCode": redpacket_code,
                        "scene": None,
                    },
                    timeout=10.0  # Added timeout
                )
                return response # Return response directly for RedpacketHandler to process
            except httpx.TimeoutException as e:
                logger.error(f"Binance API request timed out for code {redpacket_code}: {e}")
                return None
            except httpx.RequestError as e:
                logger.error(f"Binance API request failed for code {redpacket_code} (network/request issue): {e}")
                return None
            except Exception as e:
                logger.error(f"An unexpected error occurred during Binance API POST request for code {redpacket_code}: {e}", exc_info=True)
                return None
