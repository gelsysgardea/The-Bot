"""
Dashboard Integration Module

Provides real-time data streaming and event handling for the Streamlit dashboard.
Integrates with both Telegram notifications and dashboard visual alerts.
"""
import asyncio
import json
import time
import websockets
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import logging

from core.config import config
from core.utils import logger


class EventType(Enum):
    """Event types for dashboard communication."""
    CLAIM_UPDATE = "claim_update"
    METRICS_UPDATE = "metrics_update"
    EMERGENCY_STOP = "emergency_stop"
    BAN_WARNING = "ban_warning"
    SYSTEM_STATUS = "system_status"
    TELEGRAM_MESSAGE = "telegram_message"


@dataclass
class DashboardEvent:
    """Dashboard event structure."""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    source: str = "system"


class WebSocketBridge:
    """WebSocket bridge for real-time dashboard communication."""

    def __init__(self):
        self.connected_clients = set()
        self.event_queue = queue.Queue()
        self.running = False
        self.server = None
        self.port = 8765
        self.host = "localhost"

    async def register_client(self, websocket, path):
        """Register a new WebSocket client."""
        self.connected_clients.add(websocket)
        logger.info(f"Dashboard client connected: {websocket.remote_address}")

        try:
            # Send initial system status
            await self.send_system_status(websocket)

            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {message}")
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Dashboard client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            self.connected_clients.discard(websocket)

    async def handle_client_message(self, websocket, data: Dict[str, Any]):
        """Handle incoming messages from dashboard clients."""
        message_type = data.get("type")

        if message_type == "emergency_stop":
            # Handle emergency stop from dashboard
            duration_hours = data.get("duration_hours", 12)
            await self.handle_emergency_stop("dashboard", duration_hours)

        elif message_type == "manual_claim":
            # Handle manual claim request from dashboard
            code = data.get("code")
            method = data.get("method", "api")
            if code:
                await self.handle_manual_claim(code, method)

        elif message_type == "get_status":
            # Send current system status
            await self.send_system_status(websocket)

        elif message_type == "toggle_fallback":
            # Toggle ADB fallback
            enabled = data.get("enabled", True)
            await self.toggle_fallback(enabled)

    async def send_system_status(self, websocket=None):
        """Send current system status to clients."""
        # Get status from main system
        # This would integrate with the actual redpacket handler and device coordinator
        status_data = {
            "event_type": EventType.SYSTEM_STATUS.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "api_client": "online",
                "adb_device": "connected",
                "telegram_bot": "active",
                "emergency_mode": False,
                "total_claims_today": 0,
                "success_rate": 0.0,
                "current_risk_score": 0
            }
        }

        message = json.dumps(status_data)

        if websocket:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                self.connected_clients.discard(websocket)
        else:
            # Broadcast to all connected clients
            await self.broadcast_message(message)

    async def broadcast_claim_update(self, claim_data: Dict[str, Any]):
        """Broadcast claim update to all dashboard clients."""
        event = DashboardEvent(
            event_type=EventType.CLAIM_UPDATE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=claim_data
        )

        message = json.dumps(asdict(event))
        await self.broadcast_message(message)

    async def broadcast_metrics_update(self, metrics_data: Dict[str, Any]):
        """Broadcast metrics update to all dashboard clients."""
        event = DashboardEvent(
            event_type=EventType.METRICS_UPDATE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=metrics_data
        )

        message = json.dumps(asdict(event))
        await self.broadcast_message(message)

    async def broadcast_emergency_stop(self, trigger_source: str, duration_hours: int, reason: str):
        """Broadcast emergency stop activation."""
        event = DashboardEvent(
            event_type=EventType.EMERGENCY_STOP,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "triggered_by": trigger_source,
                "duration_hours": duration_hours,
                "reason": reason,
                "emergency_mode": True
            }
        )

        message = json.dumps(asdict(event))
        await self.broadcast_message(message)

    async def broadcast_ban_warning(self, risk_score: int, signals: List[str]):
        """Broadcast ban warning to dashboard."""
        event = DashboardEvent(
            event_type=EventType.BAN_WARNING,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "risk_score": risk_score,
                "signals": signals,
                "recommended_action": "emergency_siesta" if risk_score >= 85 else "extended_delays"
            }
        )

        message = json.dumps(asdict(event))
        await self.broadcast_message(message)

    async def broadcast_message(self, message: str):
        """Broadcast message to all connected clients."""
        if not self.connected_clients:
            return

        disconnected_clients = set()

        for client in self.connected_clients.copy():
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

    async def handle_emergency_stop(self, source: str, duration_hours: int):
        """Handle emergency stop activation."""
        reason = f"Emergency stop triggered by {source}"
        await self.broadcast_emergency_stop(source, duration_hours, reason)

        # TODO: Integrate with actual emergency stop in redpacket handler
        logger.warning(f"Emergency stop activated: {reason}")

    async def handle_manual_claim(self, code: str, method: str):
        """Handle manual claim request from dashboard."""
        # TODO: Integrate with actual claim processing
        logger.info(f"Manual claim requested: {code} via {method}")

    async def toggle_fallback(self, enabled: bool):
        """Toggle ADB fallback on/off."""
        # TODO: Integrate with device coordinator
        logger.info(f"ADB fallback {'enabled' if enabled else 'disabled'}")

    async def start_server(self):
        """Start the WebSocket server."""
        try:
            self.running = True
            self.server = await websockets.serve(
                self.register_client,
                self.host,
                self.port
            )
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            self.running = False

    async def stop_server(self):
        """Stop the WebSocket server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running


class TelegramNotificationManager:
    """Manages Telegram notifications for critical events."""

    def __init__(self):
        self.enabled = config.NOTIFICATION_SETTINGS.get("critical_alerts_enabled", True)
        self.admin_chat_id = config.NOTIFICATION_SETTINGS.get("admin_chat_id", 0)
        self.minimum_claim_bnb = config.NOTIFICATION_SETTINGS.get("minimum_claim_bnb", 0.01)

    async def send_success_notification(self, claim_data: Dict[str, Any]):
        """Send Telegram notification for successful claim."""
        if not self.enabled or self.admin_chat_id == 0:
            return

        try:
            amount = float(claim_data.get("amount", 0))
            if amount < self.minimum_claim_bnb:
                return

            message = (
                f"🔥 ¡Nuevo claim! +{claim_data.get('amount', 0)} {claim_data.get('currency', 'BNB')}\n"
                f"Código: {claim_data.get('code', 'N/A')}\n"
                f"Método: {claim_data.get('method', 'API').title()}\n"
                f"TX: {claim_data.get('txid', 'N/A')}\n"
                f"Hora: {datetime.now().strftime('%H:%M:%S')}"
            )

            # TODO: Implement actual Telegram bot sending
            logger.info(f"Telegram notification ready: {message}")

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    async def send_critical_alert(self, alert_type: str, details: Dict[str, Any]):
        """Send critical alert notification."""
        if not self.enabled or self.admin_chat_id == 0:
            return

        try:
            if alert_type == "ban_warning":
                risk_score = details.get("risk_score", 0)
                message = (
                    f"⚠️ ALERTA CRÍTICA\n"
                    f"Risk Score: {risk_score} (BAN INMINENTE)\n"
                    f"Acción: Modo siesta 2h activado\n"
                    f"Revisar: https://dashboard.local:8501"
                )

            elif alert_type == "emergency_mode":
                duration = details.get("duration_hours", 12)
                reason = details.get("reason", "Unknown")
                message = (
                    f"🚨 MODO SIERPE ACTIVADO\n"
                    f"Duración: {duration} horas\n"
                    f"Motivo: {reason}\n"
                    f"Todos los workers pausados"
                )

            elif alert_type == "system_error":
                error = details.get("error", "Unknown error")
                message = (
                    f"🔥 ERROR DEL SISTEMA\n"
                    f"Error: {error}\n"
                    f"Hora: {datetime.now().strftime('%H:%M:%S')}"
                )

            else:
                return

            # TODO: Implement actual Telegram bot sending
            logger.warning(f"Critical alert ready: {message}")

        except Exception as e:
            logger.error(f"Failed to send critical alert: {e}")


class DashboardIntegrationManager:
    """Main integration manager for dashboard communication."""

    def __init__(self):
        self.websocket_bridge = WebSocketBridge()
        self.telegram_manager = TelegramNotificationManager()
        self.event_handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self.metrics_cache = {}
        self.last_metrics_update = 0
        self.update_interval = 5  # seconds

    async def start(self):
        """Start the dashboard integration system."""
        logger.info("Starting dashboard integration system...")

        # Start WebSocket server
        await self.websocket_bridge.start_server()

        # Start background tasks
        asyncio.create_task(self.metrics_updater())

        logger.info("Dashboard integration system started")

    async def stop(self):
        """Stop the dashboard integration system."""
        logger.info("Stopping dashboard integration system...")

        await self.websocket_bridge.stop_server()
        logger.info("Dashboard integration system stopped")

    def register_event_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler for specific event types."""
        self.event_handlers[event_type].append(handler)

    async def emit_claim_update(self, claim_data: Dict[str, Any]):
        """Emit claim update to dashboard and Telegram."""
        # Send to dashboard
        await self.websocket_bridge.broadcast_claim_update(claim_data)

        # Send Telegram notification if significant
        if claim_data.get("status") == "success":
            await self.telegram_manager.send_success_notification(claim_data)

        # Call registered handlers
        for handler in self.event_handlers[EventType.CLAIM_UPDATE]:
            try:
                await handler(claim_data)
            except Exception as e:
                logger.error(f"Error in claim update handler: {e}")

    async def emit_ban_warning(self, risk_score: int, signals: List[str]):
        """Emit ban warning to dashboard and Telegram."""
        # Send to dashboard
        await self.websocket_bridge.broadcast_ban_warning(risk_score, signals)

        # Send Telegram notification
        await self.telegram_manager.send_critical_alert("ban_warning", {
            "risk_score": risk_score,
            "signals": signals
        })

        # Call registered handlers
        for handler in self.event_handlers[EventType.BAN_WARNING]:
            try:
                await handler({"risk_score": risk_score, "signals": signals})
            except Exception as e:
                logger.error(f"Error in ban warning handler: {e}")

    async def emit_emergency_stop(self, trigger_source: str, duration_hours: int, reason: str):
        """Emit emergency stop notification."""
        # Send to dashboard
        await self.websocket_bridge.broadcast_emergency_stop(trigger_source, duration_hours, reason)

        # Send Telegram notification
        await self.telegram_manager.send_critical_alert("emergency_mode", {
            "duration_hours": duration_hours,
            "reason": reason
        })

        # Call registered handlers
        for handler in self.event_handlers[EventType.EMERGENCY_STOP]:
            try:
                await handler({
                    "triggered_by": trigger_source,
                    "duration_hours": duration_hours,
                    "reason": reason
                })
            except Exception as e:
                logger.error(f"Error in emergency stop handler: {e}")

    async def metrics_updater(self):
        """Background task to update metrics periodically."""
        while self.websocket_bridge.is_running():
            try:
                current_time = time.time()
                if current_time - self.last_metrics_update >= self.update_interval:
                    # Get current metrics from system
                    # TODO: Integrate with actual redpacket handler and device coordinator
                    metrics_data = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "today_claims": 0,
                        "today_bnb": 0.0,
                        "failures": 0,
                        "success_rate": 0.0,
                        "active_workers": 0,
                        "emergency_mode": False,
                        "current_risk_score": 0,
                        "adb_fallback_enabled": True,
                        "telegram_bot_active": True
                    }

                    # Send to dashboard
                    await self.websocket_bridge.broadcast_metrics_update(metrics_data)

                    self.last_metrics_update = current_time

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in metrics updater: {e}")
                await asyncio.sleep(5)

    def get_dashboard_url(self) -> str:
        """Get the dashboard URL for access."""
        return f"http://localhost:8501"

    def get_websocket_url(self) -> str:
        """Get the WebSocket URL for dashboard connection."""
        return f"ws://{self.websocket_bridge.host}:{self.websocket_bridge.port}"


# Global instance for application-wide access
dashboard_integration = DashboardIntegrationManager()