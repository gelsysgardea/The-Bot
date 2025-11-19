import asyncio
import json
import time
from typing import Optional, Dict, Any

try:
    from curl_cffi.requests import AsyncSession, AsyncResponse
    CURL_CFFI_AVAILABLE = True
except ImportError:
    try:
        import httpx
        from httpx import AsyncClient as AsyncSession, Response as AsyncResponse
        CURL_CFFI_AVAILABLE = False
    except ImportError:
        raise ImportError("Neither curl_cffi nor httpx is available. Install curl_cffi for best anti-bot protection.")

from core.config import config
from core.utils import logger


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
