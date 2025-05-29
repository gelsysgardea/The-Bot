import re
from telethon import TelegramClient, events

from core.config import config
from core.binance.redpacket import RedpacketHandler
from core.utils import logger

BINANCE_CODE_REGEX = re.compile(r'\b([a-zA-Z0-9]{8})\b')

class BaseClient:
    def __init__(self):
        self.CLIENT: TelegramClient = TelegramClient(
            config.CLIENT_NAME, config.API_ID, config.API_HASH
        )
        self.HANDLER = RedpacketHandler()
        self.setup_event_handler()

    def setup_event_handler(self) -> None:
        @self.CLIENT.on(events.NewMessage(chats=config.CHATS))
        async def _(event: events.NewMessage.Event):
            try:
                logger.debug(f"New message from chat {event.chat_id}: {event.raw_text}")
                
                found_codes = BINANCE_CODE_REGEX.findall(event.raw_text)
                
                if not found_codes:
                    logger.debug(f"No Binance codes found in message: {event.raw_text}")
                    return

                for token in found_codes:
                    logger.info(f"Potential Binance code found: {token}")
                    await self.HANDLER.handle_codes(token)
            
            except Exception as e:
                logger.error(f"Error processing message: {event.raw_text}. Error: {e}", exc_info=True)

    def start(self)-> None:
        logger.info("Starting the processes...")
        self.CLIENT.start()
        logger.info("Telethon started, waiting for messages")
        self.CLIENT.run_until_disconnected()
