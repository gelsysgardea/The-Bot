import asyncio
import httpx
import random
from datetime import datetime

from core.binance.api import BinanceAPI
from core.utils import logger

from typing import Literal


class RedpacketHandler:
    TYPES = Literal[
        "processed", "claimed", "captcha", "too_many_requests", "session_expired"
    ]

    def __init__(self) -> None:
        # Timestamp of the start of the current hour, used to reset PROCESSED_CODES hourly.
        self.LAST_TIMESTAMP = 0
        # Stores codes that have been processed in the current hour to prevent duplicates.
        self.PROCESSED_CODES: list = []
        # Flag indicating if a timeout (e.g., captcha, rate limit) is active, pausing operations for an hour.
        self.IS_TIMEOUT: bool = False
        # Flag to ensure codes are processed sequentially and to halt processing during a timeout.
        # True if the last code was processed successfully or if ready for a new code.
        # False if a code is currently being processed or if a timeout is active.
        self.IS_LAST_PROCESSED: bool = True

    async def handle_response(self, response: httpx.Response) -> TYPES:
        """
        Handle the response codes/messages/data an return the according type.

        :response: httpx.Response
        :return: Literal[...]
        """
        response_json = response.json()
        data = response_json.get("data", None)
        code = response_json.get("code", None)

        if response_json["success"]:
            currency = response_json["data"]["currency"]
            amount = response_json["data"]["grabAmountStr"]
            logger.success(f"CLAIMED: {amount} {currency}")
            return "claimed"

        elif data and "validateId" in data:
            logger.warning("Captcha detected. Pausing operations for 1 hour.")
            return "captcha"

        elif code not in [
            "100002001",
            "403067",
            "403802",
            "403803",
            "PAY4001COM000",
        ]:
            logger.error(f"Unexpected Binance API response: {response_json}")
            return "processed"

        match code:
            case "100002001":
                logger.error("Binance session expired. Please update credentials in .env file.")
                return "session_expired"
            case "403067":
                logger.warning("Too many requests to Binance API. Pausing operations for 1 hour.")
                return "too_many_requests"
            case "403802":
                logger.info("Redpacket already fully claimed.")
                return "processed"
            case "403803":
                logger.info("Invalid redpacket code entered.")
                return "processed"
            case "PAY4001COM000":
                logger.info("Invalid redpacket code entered.")
                return "processed"

    async def handle_codes(self, code: str) -> None:
        """
        Handle codes fetched from telegram channels

        :code: str
        :return: None
        """
        timestamp = (
            datetime.now().replace(minute=0, second=0, microsecond=0).timestamp()
        )

        if timestamp > self.LAST_TIMESTAMP:
            self.PROCESSED_CODES.clear()
            self.IS_LAST_PROCESSED = True
            self.IS_TIMEOUT = False
            self.LAST_TIMESTAMP = timestamp

        if (code in self.PROCESSED_CODES) or (not self.IS_LAST_PROCESSED):
            return

        if not self.IS_TIMEOUT:
            self.PROCESSED_CODES.append(code)
            self.IS_LAST_PROCESSED = False

            logger.info(f"Processing code: {code}")

            await asyncio.sleep(random.randint(1, 5))
            result: RedpacketHandler.TYPES = await self.handle_response(
                await BinanceAPI.request_redpacket(code)
            )

            match result:
                case "captcha" | "too_many_requests" | "session_expired":
                    self.IS_LAST_PROCESSED = False
                    self.IS_TIMEOUT = True

                case "claimed" | "processed":
                    self.IS_LAST_PROCESSED = True
                    self.PROCESSED_CODES.append(code)

        else:
            logger.info("Timeout active. Sleeping for one hour.")
            self.IS_TIMEOUT = True
            self.IS_LAST_PROCESSED = False
            self.PROCESSED_CODES.clear()
