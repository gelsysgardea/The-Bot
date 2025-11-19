import asyncio
import json
import os
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
    def __init__(self) -> None:
        """Initialize Binance API client with TLS fingerprinting capabilities."""
        self.claim_count = 0
        self.session_failures = 0
        self.last_session_refresh = 0

    async def _get_session(self, claim_count: int = 0) -> AsyncSession:
        """Create HTTP session with TLS fingerprinting and rotating headers."""

        # Generate rotating headers based on claim count
        headers = {
            "User-Agent": config.get_rotating_user_agent(claim_count),
            "x-trace-id": config.generate_trace_id(),
            "x-device-info": config.get_rotating_device_fingerprint(claim_count),
            "bnc-uuid": os.getenv('BNC_UUID', ''),
            "device-id": config.generate_device_id(),
            "clienttype": "web",
            "csrftoken": os.getenv('CSRF_TOKEN', ''),
            "lang": "uk-UA",
            "Referer": "https://www.binance.com/uk-UA/my/wallet/account/payment/cryptobox",
        }

        # Add cf_bm cookie if available
        cf_bm = await self._load_cf_bm_cookie()
        if cf_bm:
            headers["Cookie"] = f"cf_bm={cf_bm}; {os.getenv('BINANCE_COOKIE', '')}"
        else:
            headers["Cookie"] = os.getenv('BINANCE_COOKIE', '')

        # Create session with TLS fingerprinting
        if CURL_CFFI_AVAILABLE:
            # curl_cffi provides advanced TLS fingerprinting
            session = AsyncSession(
                impersonate="chrome110_android",  # Android Chrome fingerprint
                headers=headers,
                timeout=30.0,
                verify=True
            )
        else:
            # Fallback to httpx with basic headers
            session = AsyncSession(
                headers=headers,
                timeout=30.0
            )

        return session

    async def _load_cf_bm_cookie(self) -> Optional[str]:
        """Load cf_bm cookie from persistent storage."""
        try:
            cf_bm_file = config.COOKIE_STORAGE["cf_bm_file"]
            if os.path.exists(cf_bm_file):
                with open(cf_bm_file, 'r') as f:
                    cookie_data = json.load(f)

                # Check if cookie is still valid (24 hour rotation)
                cookie_age = time.time() - cookie_data.get("timestamp", 0)
                if cookie_age < config.COOKIE_STORAGE["rotation_interval"]:
                    return cookie_data.get("cf_bm")

        except Exception as e:
            logger.debug(f"Could not load cf_bm cookie: {e}")

        return None

    async def _save_cf_bm_cookie(self, response: AsyncResponse) -> None:
        """Extract and save cf_bm cookie from response."""
        try:
            # Extract cf_bm from response headers
            set_cookie_header = response.headers.get("set-cookie", "")
            if "cf_bm=" in set_cookie_header:
                cf_bm_start = set_cookie_header.find("cf_bm=") + 6
                cf_bm_end = set_cookie_header.find(";", cf_bm_start)
                cf_bm_value = set_cookie_header[cf_bm_start:cf_bm_end]

                cookie_data = {
                    "cf_bm": cf_bm_value,
                    "timestamp": time.time()
                }

                # Save to file
                cf_bm_file = config.COOKIE_STORAGE["cf_bm_file"]
                os.makedirs(os.path.dirname(cf_bm_file), exist_ok=True)
                with open(cf_bm_file, 'w') as f:
                    json.dump(cookie_data, f)

                logger.debug("Saved new cf_bm cookie")

        except Exception as e:
            logger.debug(f"Could not save cf_bm cookie: {e}")

    async def _detect_ban_signals(self, response: AsyncResponse) -> Dict[str, Any]:
        """Analyze response for ban signals and risk indicators."""
        ban_signals = {
            "detected": False,
            "risk_score": 0,
            "signals": [],
            "recommended_action": "continue"
        }

        try:
            # Check for high risk score header
            if "x-risk-score" in response.headers:
                risk_score = int(response.headers["x-risk-score"])
                ban_signals["risk_score"] = risk_score

                if risk_score >= config.ANTI_BAN_SETTINGS["ban_detection_signals"]["risk_score_threshold"]:
                    ban_signals["detected"] = True
                    ban_signals["signals"].append(f"High risk score: {risk_score}")
                    ban_signals["recommended_action"] = "emergency_siesta"
                elif risk_score > 70:
                    ban_signals["signals"].append(f"Elevated risk score: {risk_score}")
                    ban_signals["recommended_action"] = "extended_delays"

            # Check response status for ban indicators
            if response.status_code == 403:
                ban_signals["detected"] = True
                ban_signals["signals"].append("HTTP 403 Forbidden")
                ban_signals["recommended_action"] = "emergency_siesta"

            # Check response body for ban/captcha indicators
            try:
                response_json = response.json()
                data = response_json.get("data", {})

                if "validateId" in data:
                    ban_signals["detected"] = True
                    ban_signals["signals"].append("CAPTCHA validation required")
                    ban_signals["recommended_action"] = "captcha_timeout"

                code = response_json.get("code", "")
                if code == "100002001":
                    ban_signals["signals"].append("Session expiration detected")
                    ban_signals["recommended_action"] = "session_refresh"

            except (json.JSONDecodeError, KeyError):
                pass

        except Exception as e:
            logger.debug(f"Error analyzing ban signals: {e}")

        return ban_signals

    async def request_redpacket(self, redpacket_code: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced redpacket request with TLS fingerprinting, header rotation, and ban detection.

        Returns:
            Dict with response data and ban signals, or None on critical failure
        """
        self.claim_count += 1

        # Get session with rotating headers
        session = await self._get_session(self.claim_count)

        try:
            logger.info(f"Requesting redpacket claim for code: {redpacket_code} (claim #{self.claim_count})")

            # Prepare request payload
            payload = {
                "channel": "DEFAULT",
                "grabCode": redpacket_code,
                "scene": None,
            }

            # Make request with TLS fingerprinting
            response = await session.post(
                "https://www.binance.com/bapi/pay/v1/private/binance-pay/gift-box/code/grabV2",
                json=payload
            )

            # Save cf_bm cookie if present in response
            await self._save_cf_bm_cookie(response)

            # Analyze response for ban signals
            ban_signals = await self._detect_ban_signals(response)

            # Prepare response data
            response_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_json": None,
                "ban_signals": ban_signals,
                "claim_count": self.claim_count,
                "success": False
            }

            try:
                response_data["response_json"] = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data["response_text"] = response.text

            # Check if request was successful
            if response.status_code == 200:
                response_data["success"] = True
                logger.info(f"Redpacket request successful for code: {redpacket_code}")
            else:
                logger.warning(f"Redpacket request failed with status {response.status_code} for code: {redpacket_code}")

            return response_data

        except asyncio.TimeoutError as e:
            logger.error(f"Binance API request timed out for code {redpacket_code}: {e}")
            self.session_failures += 1
            return None

        except Exception as e:
            logger.error(f"Binance API request failed for code {redpacket_code}: {e}", exc_info=True)
            self.session_failures += 1
            return None

        finally:
            if hasattr(session, 'close'):
                await session.close()

    async def refresh_session(self) -> bool:
        """Force session refresh via ADB (if configured) or clear session data."""
        try:
            logger.info("Refreshing Binance session...")

            # Clear cf_bm cookie
            cf_bm_file = config.COOKIE_STORAGE["cf_bm_file"]
            if os.path.exists(cf_bm_file):
                os.remove(cf_bm_file)

            # Reset failure counters
            self.session_failures = 0
            self.last_session_refresh = time.time()

            # If ADB is configured, force-stop Binance app
            if config.ADB_SETTINGS["device_id"]:
                adb_cmd = f'adb -s {config.ADB_SETTINGS["device_id"]} shell am force-stop com.binance.dev'
                process = await asyncio.create_subprocess_shell(
                    adb_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info("Successfully force-stopped Binance app via ADB")
                else:
                    logger.warning(f"ADB command failed: {stderr.decode().strip()}")

            logger.info("Session refresh completed")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh session: {e}", exc_info=True)
            return False

    def get_failure_count(self) -> int:
        """Get current session failure count."""
        return self.session_failures

    def reset_failure_count(self) -> None:
        """Reset session failure count."""
        self.session_failures = 0
