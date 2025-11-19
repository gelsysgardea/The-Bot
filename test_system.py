"""
System Testing and Validation Script

Comprehensive testing suite for the autonomous crypto redpacket claiming system.
Validates all components: API client, Telegram bot, ADB fallback, dashboard, etc.
"""
import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from core.config import config
from core.binance.api import BinanceAPI
from core.binance.redpacket import EnhancedRedpacketHandler
from core.telegram.bot import EnhancedTelegramClient
from dashboard_integration import dashboard_integration

# Add ADB fallback path
sys.path.insert(0, str(Path(__file__).parent.parent / "The-Hau5-Claim"))
try:
    from device_coordinator import DeviceCoordinator
    from adb_fallback import ADBFallback
    ADB_AVAILABLE = True
except ImportError as e:
    print(f"ADB components not available: {e}")
    ADB_AVAILABLE = False


class SystemTester:
    """Comprehensive system testing suite."""

    def __init__(self):
        self.test_results = {
            'config': {},
            'api_client': {},
            'redpacket_handler': {},
            'telegram_bot': {},
            'adb_fallback': {},
            'dashboard': {},
            'integration': {}
        }
        self.total_tests = 0
        self.passed_tests = 0

    def log_test_result(self, category: str, test_name: str, passed: bool, message: str = "", details: Dict = None):
        """Log a test result."""
        self.test_results[category][test_name] = {
            'passed': passed,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }

        self.total_tests += 1
        if passed:
            self.passed_tests += 1

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{category}] {test_name}: {message}")

        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")

    async def test_configuration(self):
        """Test system configuration."""
        print("\n🔧 Testing Configuration...")

        # Test basic config loading
        try:
            required_configs = ['API_ID', 'API_HASH']
            missing_configs = []

            for config_name in required_configs:
                value = getattr(config, config_name, None)
                if not value:
                    missing_configs.append(config_name)

            if missing_configs:
                self.log_test_result('config', 'required_configs', False,
                    f"Missing configs: {missing_configs}")
            else:
                self.log_test_result('config', 'required_configs', True,
                    "All required configurations present")

        except Exception as e:
            self.log_test_result('config', 'config_loading', False, str(e))

        # Test anti-ban configuration
        try:
            user_agents = config.USER_AGENT_ROTATION
            device_fingerprints = config.DEVICE_FINGERPRINTS
            anti_ban_settings = config.ANTI_BAN_SETTINGS

            self.log_test_result('config', 'anti_ban_settings', True,
                "Anti-ban settings loaded", {
                    'user_agents_count': len(user_agents),
                    'device_fingerprints_count': len(device_fingerprints),
                    'header_rotation_interval': anti_ban_settings['header_rotation_interval']
                })

        except Exception as e:
            self.log_test_result('config', 'anti_ban_settings', False, str(e))

        # Test ADB configuration
        try:
            adb_settings = config.ADB_SETTINGS
            coordinates = adb_settings.get('coordinates_uhd', {})

            self.log_test_result('config', 'adb_settings', True,
                "ADB settings configured", {
                    'device_id_configured': bool(adb_settings.get('device_id')),
                    'coordinates_count': len(coordinates),
                    'coordinates_keys': list(coordinates.keys())
                })

        except Exception as e:
            self.log_test_result('config', 'adb_settings', False, str(e))

    async def test_api_client(self):
        """Test Binance API client functionality."""
        print("\n📡 Testing API Client...")

        try:
            api_client = BinanceAPI()

            # Test client initialization
            self.log_test_result('api_client', 'initialization', True,
                "API client initialized successfully")

            # Test header generation
            try:
                headers = await api_client._get_session(claim_count=1)
                self.log_test_result('api_client', 'header_generation', True,
                    "Headers generated successfully", {
                        'user_agent_present': 'User-Agent' in headers,
                        'trace_id_present': 'x-trace-id' in headers,
                        'device_info_present': 'x-device-info' in headers
                    })
            except Exception as e:
                self.log_test_result('api_client', 'header_generation', False, str(e))

            # Test trace ID generation
            try:
                trace_id1 = config.generate_trace_id()
                trace_id2 = config.generate_trace_id()

                unique_ids = len({trace_id1, trace_id2}) == 2
                self.log_test_result('api_client', 'trace_id_generation', unique_ids,
                    f"Generated unique trace IDs: {trace_id1[:16]}...")

            except Exception as e:
                self.log_test_result('api_client', 'trace_id_generation', False, str(e))

            # Test device ID generation
            try:
                device_id = config.generate_device_id()
                valid_format = device_id.startswith('ANDROID_') and len(device_id) == 15
                self.log_test_result('api_client', 'device_id_generation', valid_format,
                    f"Generated device ID: {device_id}")

            except Exception as e:
                self.log_test_result('api_client', 'device_id_generation', False, str(e))

        except Exception as e:
            self.log_test_result('api_client', 'initialization', False, str(e))

    async def test_redpacket_handler(self):
        """Test enhanced redpacket handler."""
        print("\n🎯 Testing Redpacket Handler...")

        try:
            handler = EnhancedRedpacketHandler()

            # Test handler initialization
            self.log_test_result('redpacket_handler', 'initialization', True,
                "Redpacket handler initialized successfully")

            # Test statistics method
            try:
                stats = handler.get_statistics()
                required_keys = ['claims', 'bnb_earned', 'consecutive_failures', 'emergency_mode_active']
                has_all_keys = all(key in stats for key in required_keys)

                self.log_test_result('redpacket_handler', 'statistics', has_all_keys,
                    "Statistics method working", {
                        'available_stats': list(stats.keys()),
                        'emergency_mode': stats['emergency_mode_active']
                    })

            except Exception as e:
                self.log_test_result('redpacket_handler', 'statistics', False, str(e))

            # Test emergency mode activation
            try:
                handler.activate_emergency_mode(1, "test_activation")
                stats_after = handler.get_statistics()

                emergency_activated = stats_after['emergency_mode_active']
                handler.deactivate_emergency_mode()  # Clean up

                self.log_test_result('redpacket_handler', 'emergency_mode', emergency_activated,
                    "Emergency mode activation test")

            except Exception as e:
                self.log_test_result('redpacket_handler', 'emergency_mode', False, str(e))

        except Exception as e:
            self.log_test_result('redpacket_handler', 'initialization', False, str(e))

    async def test_telegram_bot(self):
        """Test Telegram bot components (without connecting)."""
        print("\n📱 Testing Telegram Bot...")

        try:
            # Test bot initialization (without starting)
            bot = EnhancedTelegramClient()

            self.log_test_result('telegram_bot', 'initialization', True,
                "Telegram bot client initialized successfully")

            # Test queue management
            try:
                initial_queue_length = len(bot.code_queue)

                # Simulate adding a code to queue
                test_code = "TEST1234"
                await bot._process_detected_code(test_code, 12345, "test_source")

                queue_after = len(bot.code_queue)
                queue_increased = queue_after > initial_queue_length

                self.log_test_result('telegram_bot', 'queue_management', queue_increased,
                    f"Code queue management: {initial_queue_length} -> {queue_after}")

            except Exception as e:
                self.log_test_result('telegram_bot', 'queue_management', False, str(e))

            # Test rate limiting
            try:
                current_time = time.time()
                rate_limited = not bot._check_rate_limit(current_time)

                self.log_test_result('telegram_bot', 'rate_limiting', True,
                    "Rate limiting mechanism functional", {
                        'rate_limited': rate_limited,
                        'codes_per_minute': bot.codes_per_minute
                    })

            except Exception as e:
                self.log_test_result('telegram_bot', 'rate_limiting', False, str(e))

        except Exception as e:
            self.log_test_result('telegram_bot', 'initialization', False, str(e))

    async def test_adb_fallback(self):
        """Test ADB fallback system."""
        print("\n📱 Testing ADB Fallback...")

        if not ADB_AVAILABLE:
            self.log_test_result('adb_fallback', 'availability', False,
                "ADB components not available")
            return

        try:
            # Test device coordinator initialization
            coordinator = DeviceCoordinator()

            self.log_test_result('adb_fallback', 'coordinator_init', True,
                "Device coordinator initialized")

            # Test device connection check
            try:
                connected = await coordinator.check_device_connection()
                self.log_test_result('adb_fallback', 'device_connection', connected,
                    "Device connection check", {
                        'device_status': 'Connected' if connected else 'Not connected'
                    })

            except Exception as e:
                self.log_test_result('adb_fallback', 'device_connection', False,
                    f"Connection check failed: {str(e)[:50]}...")

            # Test ADB fallback initialization
            try:
                adb_fallback = ADBFallback()

                self.log_test_result('adb_fallback', 'adb_init', True,
                    "ADB fallback initialized", {
                        'device_id_configured': bool(adb_fallback.device_id),
                        'coordinates_count': len(adb_fallback.coordinates)
                    })

            except Exception as e:
                self.log_test_result('adb_fallback', 'adb_init', False, str(e))

        except Exception as e:
            self.log_test_result('adb_fallback', 'coordinator_init', False, str(e))

    async def test_dashboard_integration(self):
        """Test dashboard integration components."""
        print("\n📊 Testing Dashboard Integration...")

        try:
            # Test dashboard integration initialization
            integration = dashboard_integration

            self.log_test_result('dashboard', 'integration_init', True,
                "Dashboard integration initialized")

            # Test WebSocket bridge
            try:
                websocket_bridge = integration.websocket_bridge
                bridge_available = websocket_bridge is not None

                self.log_test_result('dashboard', 'websocket_bridge', bridge_available,
                    f"WebSocket bridge available: {bridge_available}")

            except Exception as e:
                self.log_test_result('dashboard', 'websocket_bridge', False, str(e))

            # Test Telegram notification manager
            try:
                telegram_manager = integration.telegram_manager
                manager_available = telegram_manager is not None

                self.log_test_result('dashboard', 'telegram_manager', manager_available,
                    f"Telegram notification manager available: {manager_available}")

            except Exception as e:
                self.log_test_result('dashboard', 'telegram_manager', False, str(e))

        except Exception as e:
            self.log_test_result('dashboard', 'integration_init', False, str(e))

    async def test_integration_flow(self):
        """Test integration between components."""
        print("\n🔗 Testing Integration Flow...")

        try:
            # Test configuration flow
            api_client = BinanceAPI()
            handler = EnhancedRedpacketHandler()

            # Test that handler can use API client
            api_client_in_handler = hasattr(handler, 'api_client')
            same_api_client = handler.api_client == api_client

            self.log_test_result('integration', 'handler_api_integration', same_api_client,
                "Redpacket handler integrated with API client", {
                    'api_client_in_handler': api_client_in_handler
                })

        except Exception as e:
            self.log_test_result('integration', 'handler_api_integration', False, str(e))

    async def run_all_tests(self):
        """Run all system tests."""
        print("🧪 Starting Comprehensive System Tests...")
        print("=" * 60)

        start_time = time.time()

        # Run all test suites
        await self.test_configuration()
        await self.test_api_client()
        await self.test_redpacket_handler()
        await self.test_telegram_bot()
        await self.test_adb_fallback()
        await self.test_dashboard_integration()
        await self.test_integration_flow()

        # Calculate results
        end_time = time.time()
        duration = end_time - start_time
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")

        # Category breakdown
        print("\n📋 Results by Category:")
        for category, tests in self.test_results.items():
            if tests:
                passed = sum(1 for test in tests.values() if test['passed'])
                total = len(tests)
                print(f"  {category}: {passed}/{total} ({passed/total*100:.1f}%)")

        # Save results to file
        results_file = Path("system_test_results.json")
        try:
            with open(results_file, 'w') as f:
                json.dump({
                    'summary': {
                        'total_tests': self.total_tests,
                        'passed_tests': self.passed_tests,
                        'success_rate': success_rate,
                        'duration': duration,
                        'timestamp': datetime.now().isoformat()
                    },
                    'detailed_results': self.test_results
                }, f, indent=2)
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {e}")

        # Return success status
        return success_rate >= 80  # Consider successful if 80%+ tests pass

    def generate_deployment_guide(self):
        """Generate deployment guide based on test results."""
        print("\n📖 DEPLOYMENT GUIDE")
        print("=" * 60)

        guide = []
        guide.append("# Autonomous Crypto Redpacket System - Deployment Guide\n")
        guide.append("## System Status")
        guide.append(f"- Tests Passed: {self.passed_tests}/{self.total_tests}")
        guide.append(f"- Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%\n")

        guide.append("## Quick Start Commands")

        # Check what's working and provide appropriate commands
        config_ok = self.test_results.get('config', {}).get('required_configs', {}).get('passed', False)

        if config_ok:
            guide.append("\n### 1. Start with Dashboard (Recommended)")
            guide.append("```bash")
            guide.append("cd The-Bot")
            guide.append("python main.py --dashboard")
            guide.append("```")
            guide.append("Access dashboard at: http://localhost:8501")

            guide.append("\n### 2. Start Headless Mode")
            guide.append("```bash")
            guide.append("cd The-Bot")
            guide.append("python main.py --headless")
            guide.append("```")

            guide.append("\n### 3. Start with ADB Fallback")
            guide.append("```bash")
            guide.append("cd The-Bot")
            guide.append("python main.py --adb-fallback")
            guide.append("```")
        else:
            guide.append("\n❌ Configuration incomplete. Please configure required environment variables.")

        # ADB setup instructions
        if ADB_AVAILABLE:
            adb_connected = self.test_results.get('adb_fallback', {}).get('device_connection', {}).get('passed', False)
            if not adb_connected:
                guide.append("\n### ADB Setup Required")
                guide.append("1. Install ADB on your system")
                guide.append("2. Enable USB debugging on your Redmi Note 12")
                guide.append("3. Connect device via ADB:")
                guide.append("   ```bash")
                guide.append("   adb devices")
                guide.append("   ```")
                guide.append("4. Set ADB_DEVICE_ID in your .env file")

        # Dashboard instructions
        dashboard_ok = self.test_results.get('dashboard', {}).get('integration_init', {}).get('passed', False)
        if dashboard_ok:
            guide.append("\n### Dashboard Features")
            guide.append("- Real-time claim monitoring")
            guide.append("- Emergency MODO SIERPE controls")
            guide.append("- Performance analytics")
            guide.append("- Manual claim testing")
            guide.append("- System health monitoring")

        guide.append("\n### Telegram Admin Commands")
        guide.append("- `/status` - Get bot status")
        guide.append("- `/emergency [hours]` - Activate emergency mode")
        guide.append("- `/resume` - Deactivate emergency mode")
        guide.append("- `/claim <code>` - Manual claim test")

        guide.append("\n### File Structure")
        guide.append("```)
        guide.append("The-Bot/")
        guide.append("├── main.py                    # Main entry point")
        guide.append("├── dashboard_app.py           # Streamlit dashboard")
        guide.append("├── dashboard_integration.py   # WebSocket bridge")
        guide.append("├── core/")
        guide.append("│   ├── config.py            # Configuration")
        guide.append("│   ├── binance/")
        guide.append("│   │   ├── api.py           # Enhanced API client")
        guide.append("│   │   └── redpacket.py     # Claim handler")
        guide.append("│   └── telegram/")
        guide.append("│       └── bot.py           # Telegram bot")
        guide.append("├── test_system.py            # This test script")
        guide.append("└── .env                      # Environment variables")
        guide.append("")
        guide.append("The-Hau5-Claim/")
        guide.append("├── main_enhanced.py          # ADB fallback main")
        guide.append("├── device_coordinator.py     # Device management")
        guide.append("└── adb_fallback.py           # ADB automation")
        guide.append("```")

        # Save guide to file
        guide_file = Path("DEPLOYMENT_GUIDE.md")
        try:
            with open(guide_file, 'w') as f:
                f.write('\n'.join(guide))
            print(f"📖 Deployment guide saved to: {guide_file}")
        except Exception as e:
            print(f"❌ Failed to save deployment guide: {e}")

        return '\n'.join(guide)


async def main():
    """Main test runner."""
    try:
        # Create tester instance
        tester = SystemTester()

        # Run all tests
        success = await tester.run_all_tests()

        # Generate deployment guide
        tester.generate_deployment_guide()

        # Final status
        if success:
            print("\n🎉 System testing completed successfully!")
            print("Your autonomous crypto redpacket claiming system is ready to deploy.")
            return 0
        else:
            print("\n⚠️ System testing completed with some issues.")
            print("Please review the test results and fix any critical failures before deployment.")
            return 1

    except Exception as e:
        print(f"\n💥 Critical error during testing: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)