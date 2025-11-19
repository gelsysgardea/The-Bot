import asyncio
import random
import csv
import os
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.binance.api import BinanceAPI
from core.utils import logger
from core.config import config


class ClaimResult(Enum):
    """Enum for standardized claim results."""
    SUCCESS = "success"
    FAILED = "failed"
    CAPTCHA = "captcha"
    RATE_LIMITED = "rate_limited"
    SESSION_EXPIRED = "session_expired"
    BAN_DETECTED = "ban_detected"
    PROCESSED = "processed"


@dataclass
class ClaimRecord:
    """Data class for claim logging."""
    timestamp: str
    code: str
    amount: str
    currency: str
    txid: str
    status: str
    method: str
    retry_count: int
    delay_seconds: float
    user_agent: str
    risk_score: int


class EnhancedRedpacketHandler:
    """Enhanced redpacket handler with advanced anti-ban detection and mitigation."""

    def __init__(self) -> None:
        # Initialize API client
        self.api_client = BinanceAPI()

        # Timing and rate limiting
        self.last_claim_time = 0
        self.consecutive_failures = 0
        self.current_risk_score = 0

        # Emergency states
        self.emergency_mode_active = False
        self.emergency_mode_until = 0
        self.captcha_timeout_until = 0
        self.siesta_mode_until = 0

        # Code processing state
        self.processed_codes: List[str] = []
        self.hourly_reset_timestamp = 0

        # Statistics
        self.today_stats = {
            "claims": 0,
            "bnb_earned": 0.0,
            "failures": 0,
            "successful_claims": []
        }

        # Ensure log directories exist
        self._ensure_log_directories()

    def _ensure_log_directories(self) -> None:
        """Create log directories if they don't exist."""
        for log_path in config.LOG_STORAGE.values():
            directory = os.path.dirname(log_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def _is_emergency_mode_active(self) -> bool:
        """Check if emergency MODO SIERPE is active."""
        if time.time() < self.emergency_mode_until:
            return True

        # Check for consecutive failure threshold
        if self.consecutive_failures >= config.ANTI_BAN_SETTINGS["consecutive_failures_threshold"]:
            self._activate_emergency_mode(
                duration=config.ANTI_BAN_SETTINGS["siesta_mode_duration"],
                reason=f"Consecutive failures: {self.consecutive_failures}"
            )
            return True

        return False

    def _activate_emergency_mode(self, duration: int, reason: str) -> None:
        """Activate emergency MODO SIERPE mode."""
        self.emergency_mode_active = True
        self.emergency_mode_until = time.time() + duration

        logger.warning(f"🚨 MODO SIERPE ACTIVADO - Duración: {duration//3600}h - Motivo: {reason}")

        # TODO: Send notification to Telegram when notification system is implemented
        # await self._send_emergency_notification(reason, duration)

    def _reset_hourly_codes(self) -> None:
        """Reset processed codes every hour to prevent memory buildup."""
        current_hour_timestamp = int(datetime.now().replace(minute=0, second=0, microsecond=0).timestamp())

        if current_hour_timestamp > self.hourly_reset_timestamp:
            self.processed_codes.clear()
            self.hourly_reset_timestamp = current_hour_timestamp
            logger.debug("Hourly code reset completed")

    def _calculate_delay(self, ban_signals: Dict[str, Any]) -> float:
        """Calculate adaptive delay based on risk score and anti-ban settings."""
        base_delay = random.uniform(*config.ANTI_BAN_SETTINGS["base_delay_range"])

        # Adjust delay based on risk score
        risk_score = ban_signals.get("risk_score", 0)
        if risk_score > 0:
            delay_range = config.get_risk_based_delay(risk_score)
            base_delay = random.uniform(*delay_range)

            # Update current risk score for tracking
            self.current_risk_score = risk_score
            logger.info(f"Risk-based delay applied: {base_delay:.1f}s (risk score: {risk_score})")

        return base_delay

    async def _handle_ban_signals(self, ban_signals: Dict[str, Any]) -> bool:
        """Handle detected ban signals with appropriate mitigation strategies."""
        if not ban_signals["detected"]:
            return False

        signals = ban_signals["signals"]
        recommended_action = ban_signals["recommended_action"]

        logger.warning(f"Ban signals detected: {signals}")

        if recommended_action == "emergency_siesta":
            # Immediate emergency mode for high risk scores
            self._activate_emergency_mode(
                duration=config.ANTI_BAN_SETTINGS["siesta_mode_duration"],
                reason=f"High ban risk: {', '.join(signals)}"
            )

            # Attempt session refresh
            await self.api_client.refresh_session()
            return True

        elif recommended_action == "extended_delays":
            # Extend delays for elevated risk
            logger.info("Applying extended delays due to elevated risk score")
            # Extended delays are handled in _calculate_delay method
            return False

        elif recommended_action == "captcha_timeout":
            # CAPTCHA detected - pause operations
            self.captcha_timeout_until = time.time() + config.ANTI_BAN_SETTINGS["captcha_timeout"]
            logger.warning(f"CAPTCHA detected - pausing for {config.ANTI_BAN_SETTINGS['captcha_timeout']} seconds")
            return True

        elif recommended_action == "session_refresh":
            # Session expired - attempt refresh
            logger.info("Session expired - attempting refresh")
            await self.api_client.refresh_session()
            return False

        return False

    async def _log_claim_attempt(self, claim_record: ClaimRecord) -> None:
        """Log claim attempt to CSV file."""
        try:
            csv_file = config.LOG_STORAGE["claims_csv"]
            file_exists = os.path.exists(csv_file)

            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header if file doesn't exist
                if not file_exists:
                    writer.writerow([
                        'timestamp', 'code', 'amount', 'currency', 'txid',
                        'status', 'method', 'retry_count', 'delay_seconds',
                        'user_agent', 'risk_score'
                    ])

                writer.writerow([
                    claim_record.timestamp,
                    claim_record.code,
                    claim_record.amount,
                    claim_record.currency,
                    claim_record.txid,
                    claim_record.status,
                    claim_record.method,
                    claim_record.retry_count,
                    claim_record.delay_seconds,
                    claim_record.user_agent,
                    claim_record.risk_score
                ])

        except Exception as e:
            logger.error(f"Failed to log claim attempt: {e}")

    async def _extract_claim_details(self, response_data: Dict[str, Any]) -> ClaimRecord:
        """Extract claim details from API response."""
        response_json = response_data.get("response_json", {})
        ban_signals = response_data.get("ban_signals", {})

        # Default values
        amount = "0.0"
        currency = "BNB"
        txid = ""
        status = ClaimResult.FAILED.value

        if response_json.get("success") and response_json.get("data"):
            data = response_json["data"]
            amount = data.get("grabAmountStr", "0.0")
            currency = data.get("currency", "BNB")
            txid = data.get("id", "")
            status = ClaimResult.SUCCESS.value
        else:
            # Determine failure type
            code = response_json.get("code", "")
            if code == "100002001":
                status = ClaimResult.SESSION_EXPIRED.value
            elif code == "403067":
                status = ClaimResult.RATE_LIMITED.value
            elif response_json.get("data", {}).get("validateId"):
                status = ClaimResult.CAPTCHA.value
            elif ban_signals.get("detected"):
                status = ClaimResult.BAN_DETECTED.value

        return ClaimRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            code=response_data.get("code", ""),
            amount=amount,
            currency=currency,
            txid=txid,
            status=status,
            method="api",
            retry_count=self.api_client.get_failure_count(),
            delay_seconds=self._calculate_delay(ban_signals),
            user_agent=response_data.get("headers", {}).get("User-Agent", ""),
            risk_score=ban_signals.get("risk_score", 0)
        )

    async def _handle_successful_claim(self, claim_record: ClaimRecord) -> None:
        """Handle successful claim with notifications and statistics."""
        try:
            amount_bnb = float(claim_record.amount)

            # Update statistics
            self.today_stats["claims"] += 1
            self.today_stats["bnb_earned"] += amount_bnb
            self.today_stats["successful_claims"].append({
                "code": claim_record.code,
                "amount": amount_bnb,
                "timestamp": claim_record.timestamp,
                "txid": claim_record.txid
            })

            # Reset consecutive failures on success
            self.consecutive_failures = 0
            self.api_client.reset_failure_count()

            logger.success(f"✅ CLAIM EXITOSO: +{claim_record.amount} {claim_record.currency} | Código: {claim_record.code}")

            # Send Telegram notification for significant claims
            if amount_bnb >= config.NOTIFICATION_SETTINGS["minimum_claim_bnb"]:
                await self._send_success_notification(claim_record)

        except Exception as e:
            logger.error(f"Error handling successful claim: {e}")

    async def _send_success_notification(self, claim_record: ClaimRecord) -> None:
        """Send Telegram notification for successful claim."""
        # TODO: Implement when Telegram notification system is ready
        notification_message = (
            f"🔥 ¡Nuevo claim! +{claim_record.amount} {claim_record.currency}\n"
            f"Código: {claim_record.code}\n"
            f"Método: API\n"
            f"TX: {claim_record.txid}\n"
            f"Hora: {datetime.fromisoformat(claim_record.timestamp).strftime('%H:%M:%S')}"
        )
        logger.info(f"Telegram notification ready: {notification_message}")

    async def process_code_with_retry(self, code: str, max_retries: int = 3) -> ClaimRecord:
        """Process redpacket code with exponential backoff retry logic."""
        for attempt in range(max_retries):
            try:
                # Check if we're in emergency mode
                if self._is_emergency_mode_active():
                    logger.warning("Emergency mode active - skipping code processing")
                    return ClaimRecord(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        code=code,
                        amount="0.0",
                        currency="BNB",
                        txid="",
                        status=ClaimResult.FAILED.value,
                        method="api",
                        retry_count=attempt,
                        delay_seconds=0,
                        user_agent="",
                        risk_score=0
                    )

                # Apply delay before request
                if attempt > 0:
                    backoff_delay = config.ANTI_BAN_SETTINGS["exponential_backoff_sequence"][min(attempt-1, 2)]
                    logger.info(f"Retry attempt {attempt + 1} - waiting {backoff_delay}s...")
                    await asyncio.sleep(backoff_delay)
                else:
                    # Apply base delay with risk-based adjustments
                    await asyncio.sleep(random.uniform(*config.ANTI_BAN_SETTINGS["base_delay_range"]))

                # Make API request
                response_data = await self.api_client.request_redpacket(code)

                if response_data is None:
                    # Network failure
                    logger.error(f"API request failed for code {code} (attempt {attempt + 1})")
                    continue

                # Handle ban signals
                ban_signals = response_data.get("ban_signals", {})
                if await self._handle_ban_signals(ban_signals):
                    # Emergency mode activated - stop processing
                    break

                # Extract claim details
                claim_record = await self._extract_claim_details(response_data)
                claim_record.code = code  # Ensure code is set
                claim_record.retry_count = attempt

                # Log the attempt
                await self._log_claim_attempt(claim_record)

                # Handle successful claim
                if claim_record.status == ClaimResult.SUCCESS.value:
                    await self._handle_successful_claim(claim_record)
                    return claim_record

                # Handle various failure types
                if claim_record.status in [ClaimResult.CAPTCHA.value, ClaimResult.RATE_LIMITED.value]:
                    logger.warning(f"Temporary failure detected: {claim_record.status}")
                    # Continue to retry with exponential backoff
                    continue

                # For other failures (processed, session expired, etc.), don't retry
                logger.info(f"Non-retryable failure: {claim_record.status}")
                return claim_record

            except Exception as e:
                logger.error(f"Unexpected error processing code {code} (attempt {attempt + 1}): {e}", exc_info=True)
                continue

        # All retries failed
        logger.error(f"Failed to process code {code} after {max_retries} attempts")
        self.consecutive_failures += 1

        return ClaimRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            code=code,
            amount="0.0",
            currency="BNB",
            txid="",
            status=ClaimResult.FAILED.value,
            method="api",
            retry_count=max_retries,
            delay_seconds=0,
            user_agent="",
            risk_score=0
        )

    async def handle_codes(self, code: str) -> None:
        """
        Enhanced code handler with anti-ban detection and queue management.

        Args:
            code: 8-character Binance redpacket code
        """
        # Reset hourly codes if needed
        self._reset_hourly_codes()

        # Check if code was already processed
        if code in self.processed_codes:
            logger.debug(f"Code {code} already processed, skipping")
            return

        # Check for timeout states
        current_time = time.time()
        if current_time < self.captcha_timeout_until:
            logger.info("CAPTCHA timeout active - skipping code processing")
            return

        if current_time < self.siesta_mode_until:
            logger.info("Siesta mode active - skipping code processing")
            return

        # Add to processed codes
        self.processed_codes.append(code)

        logger.info(f"🎯 Processing code: {code}")

        # Process code with retry logic
        claim_record = await self.process_code_with_retry(code)

        # Apply bonus delay after processing
        if claim_record.status == ClaimResult.SUCCESS.value:
            bonus_delay = config.ANTI_BAN_SETTINGS["claim_success_bonus_delay"]
            logger.info(f"Applying success bonus delay: {bonus_delay}s")
            await asyncio.sleep(bonus_delay)

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics for dashboard."""
        return {
            **self.today_stats,
            "consecutive_failures": self.consecutive_failures,
            "current_risk_score": self.current_risk_score,
            "emergency_mode_active": self.emergency_mode_active,
            "emergency_mode_remaining": max(0, self.emergency_mode_until - time.time()),
            "captcha_timeout_remaining": max(0, self.captcha_timeout_until - time.time()),
            "processed_codes_count": len(self.processed_codes)
        }

    def activate_emergency_mode(self, duration_hours: int = 12, reason: str = "Manual activation") -> None:
        """Manually activate emergency MODO SIERPE mode."""
        duration_seconds = duration_hours * 3600
        self._activate_emergency_mode(duration_seconds, reason)

    def deactivate_emergency_mode(self) -> None:
        """Manually deactivate emergency mode."""
        self.emergency_mode_active = False
        self.emergency_mode_until = 0
        self.consecutive_failures = 0
        logger.info("Emergency MODO SIERPE deactivated")


# Maintain backward compatibility
RedpacketHandler = EnhancedRedpacketHandler
