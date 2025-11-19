import asyncio
import re
import time
from collections import deque
from telethon import TelegramClient, events
from typing import List, Set, Optional

from core.config import config
from core.binance.redpacket import EnhancedRedpacketHandler
from core.utils import logger
from dashboard_integration import dashboard_integration

# Enhanced regex for better code detection
BINANCE_CODE_REGEX = re.compile(r'\b([a-zA-Z0-9]{8})\b')

class EnhancedTelegramClient:
    """Enhanced Telegram client with code queueing, priority processing, and dashboard integration."""

    def __init__(self):
        self.CLIENT: TelegramClient = TelegramClient(
            config.CLIENT_NAME, config.API_ID, config.API_HASH
        )
        self.HANDLER = EnhancedRedpacketHandler()

        # Code queue management
        self.code_queue = deque()
        self.processed_codes: Set[str] = set()
        self.processing_lock = asyncio.Lock()

        # Rate limiting
        self.last_code_time = 0
        self.codes_per_minute = 0
        self.rate_limit_window = 60  # 1 minute window

        # Dashboard integration
        self.dashboard_enabled = True

        # Setup event handlers
        self.setup_message_handlers()
        self.setup_admin_commands()

    def setup_message_handlers(self):
        """Setup message handlers for code detection."""

        @self.CLIENT.on(events.NewMessage(chats=config.CHATS))
        async def handle_regular_message(event: events.NewMessage.Event):
            """Handle regular messages for code detection."""
            try:
                logger.debug(f"New message from chat {event.chat_id}: {event.raw_text[:100]}...")

                # Rate limiting check
                current_time = time.time()
                if not self._check_rate_limit(current_time):
                    logger.warning("Rate limit exceeded - skipping message processing")
                    return

                # Find codes in message
                found_codes = BINANCE_CODE_REGEX.findall(event.raw_text)

                if not found_codes:
                    logger.debug("No Binance codes found in message")
                    return

                # Process each found code
                for token in found_codes:
                    await self._process_detected_code(token, event.chat_id, "regular_message")

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    def setup_admin_commands(self):
        """Setup admin command handlers."""

        @self.CLIENT.on(events.NewMessage(chats=config.NOTIFICATION_SETTINGS.get("admin_chat_id", []), pattern=r'/status'))
        async def handle_status_command(event: events.NewMessage.Event):
            """Handle /status command from admin."""
            try:
                stats = self.HANDLER.get_statistics()

                status_message = (
                    f"📊 **Bot Status**\n"
                    f"🎯 Today's Claims: {stats['claims']}\n"
                    f"💰 BNB Earned: {stats['bnb_earned']:.4f}\n"
                    f"✅ Success Rate: {stats.get('success_rate', 0):.1f}%\n"
                    f"❌ Failures: {stats['consecutive_failures']}\n"
                    f"⚡ Risk Score: {stats['current_risk_score']}\n"
                    f"🚨 Emergency Mode: {'Yes' if stats['emergency_mode_active'] else 'No'}\n"
                    f"📱 Processed Codes: {stats['processed_codes_count']}"
                )

                await event.reply(status_message)

            except Exception as e:
                logger.error(f"Error handling status command: {e}")
                await event.reply(f"❌ Error getting status: {e}")

        @self.CLIENT.on(events.NewMessage(chats=config.NOTIFICATION_SETTINGS.get("admin_chat_id", []), pattern=r'/emergency'))
        async def handle_emergency_command(event: events.NewMessage.Event):
            """Handle /emergency command to activate emergency mode."""
            try:
                # Extract duration from command (default 12 hours)
                command_parts = event.message.text.split()
                duration = 12
                if len(command_parts) > 1:
                    try:
                        duration = int(command_parts[1])
                        duration = max(1, min(24, duration))  # Limit between 1-24 hours
                    except ValueError:
                        pass

                # Activate emergency mode
                self.HANDLER.activate_emergency_mode(duration, "Telegram admin command")

                # Send to dashboard
                await dashboard_integration.emit_emergency_stop(
                    "telegram_admin", duration, "Manual activation via Telegram"
                )

                await event.reply(f"🚨 **MODO SIERPE ACTIVADO**\nDuración: {duration} horas\nMotivo: Comando de admin")

            except Exception as e:
                logger.error(f"Error handling emergency command: {e}")
                await event.reply(f"❌ Error activating emergency mode: {e}")

        @self.CLIENT.on(events.NewMessage(chats=config.NOTIFICATION_SETTINGS.get("admin_chat_id", []), pattern=r'/resume'))
        async def handle_resume_command(event: events.NewMessage.Event):
            """Handle /resume command to deactivate emergency mode."""
            try:
                self.HANDLER.deactivate_emergency_mode()
                await event.reply("✅ **MODO SIERPE DESACTIVADO**\nBot reanudado normalmente")

            except Exception as e:
                logger.error(f"Error handling resume command: {e}")
                await event.reply(f"❌ Error deactivating emergency mode: {e}")

        @self.CLIENT.on(events.NewMessage(chats=config.NOTIFICATION_SETTINGS.get("admin_chat_id", []), pattern=r'/claim'))
        async def handle_manual_claim(event: events.NewMessage.Event):
            """Handle /claim command for manual testing."""
            try:
                command_parts = event.message.text.split()
                if len(command_parts) < 2:
                    await event.reply("❌ Uso: /claim <codigo_8_caracteres>")
                    return

                code = command_parts[1].upper().strip()
                if len(code) != 8:
                    await event.reply("❌ El código debe tener exactamente 8 caracteres")
                    return

                await event.reply(f"🎯 Procesando claim manual: {code}")

                # Process the code
                await self._process_detected_code(code, event.chat_id, "admin_command")

            except Exception as e:
                logger.error(f"Error handling manual claim command: {e}")
                await event.reply(f"❌ Error processing manual claim: {e}")

    def _check_rate_limit(self, current_time: float) -> bool:
        """Check if we're within rate limits."""
        max_requests = config.ANTI_BAN_SETTINGS["ban_detection_signals"]["max_requests_per_minute"]

        # Reset counter if window has passed
        if current_time - self.last_code_time > self.rate_limit_window:
            self.codes_per_minute = 0
            self.last_code_time = current_time

        if self.codes_per_minute >= max_requests:
            return False

        self.codes_per_minute += 1
        return True

    async def _process_detected_code(self, code: str, chat_id: int, source: str):
        """Process a detected code with queueing and deduplication."""
        try:
            code = code.upper()

            # Check if already processed
            if code in self.processed_codes:
                logger.debug(f"Code {code} already processed, skipping")
                return

            # Check for duplicates in queue
            if code in self.code_queue:
                logger.debug(f"Code {code} already in queue, skipping")
                return

            # Add to queue
            self.code_queue.append({
                'code': code,
                'chat_id': chat_id,
                'source': source,
                'timestamp': time.time()
            })

            logger.info(f"🎯 Code queued: {code} (from {source})")

            # Process queue
            asyncio.create_task(self._process_queue())

        except Exception as e:
            logger.error(f"Error processing detected code {code}: {e}")

    async def _process_queue(self):
        """Process the code queue with controlled rate."""
        async with self.processing_lock:
            try:
                if not self.code_queue:
                    return

                code_data = self.code_queue.popleft()
                code = code_data['code']

                # Add to processed codes
                self.processed_codes.add(code)

                logger.info(f"🔄 Processing queued code: {code}")

                # Process with enhanced handler
                await self.HANDLER.handle_codes(code)

                # Emit to dashboard
                claim_stats = self.HANDLER.get_statistics()

                dashboard_event = {
                    'code': code,
                    'timestamp': time.time(),
                    'source': code_data['source'],
                    'chat_id': code_data['chat_id'],
                    'queue_length': len(self.code_queue),
                    'stats': claim_stats
                }

                await dashboard_integration.emit_claim_update(dashboard_event)

            except Exception as e:
                logger.error(f"Error processing queue: {e}")

    async def start_background_tasks(self):
        """Start background tasks for monitoring and maintenance."""
        try:
            # Clean up processed codes periodically
            asyncio.create_task(self._cleanup_processed_codes())

            # Monitor emergency mode status
            asyncio.create_task(self._monitor_emergency_mode())

        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")

    async def _cleanup_processed_codes(self):
        """Clean up old processed codes to prevent memory buildup."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                # Clear processed codes periodically to prevent memory issues
                if len(self.processed_codes) > 1000:
                    self.processed_codes.clear()
                    logger.info("Cleared processed codes cache")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error

    async def _monitor_emergency_mode(self):
        """Monitor emergency mode and send alerts."""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds

                stats = self.HANDLER.get_statistics()

                # Check for high risk scores
                if stats['current_risk_score'] >= 85:
                    await dashboard_integration.emit_ban_warning(
                        stats['current_risk_score'],
                        ["High risk score detected", "Immediate action required"]
                    )

            except Exception as e:
                logger.error(f"Error in emergency monitoring: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error

    async def start(self):
        """Start the enhanced Telegram client."""
        logger.info("🚀 Starting enhanced Telegram client...")

        # Start background tasks
        await self.start_background_tasks()

        # Start Telegram client
        self.CLIENT.start()
        logger.info("✅ Telethon client started")

        # Show startup information
        logger.info(f"📱 Monitoring {len(config.CHATS)} chat(s)")
        logger.info(f"🎯 Code queue ready")
        logger.info(f"🚨 Emergency commands available for admin chat {config.NOTIFICATION_SETTINGS.get('admin_chat_id', 'Not configured')}")

        # Run until disconnected
        await self.CLIENT.run_until_disconnected()

    def get_statistics(self) -> dict:
        """Get current client statistics."""
        return {
            'queue_length': len(self.code_queue),
            'processed_codes_count': len(self.processed_codes),
            'codes_per_minute_current': self.codes_per_minute,
            'dashboard_enabled': self.dashboard_enabled,
            'handler_stats': self.HANDLER.get_statistics()
        }


# Maintain backward compatibility
BaseClient = EnhancedTelegramClient
