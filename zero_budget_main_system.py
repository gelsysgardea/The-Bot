#!/usr/bin/env python3
"""
🚀 SISTEMA ZERO BUDGET - MAIN SYSTEM
🎯 Objetivo: Sistema completo de acumulación GRATIS 24/7
💰 Método: Integración de todos los componentes + Automatización total
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Importar componentes
from zero_budget_redpacket_system import ZeroBudgetRedpacketHunter
from zero_budget_airdrop_system import ZeroBudgetAirdropHunter

# Configurar logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('zero_budget_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ZeroBudgetMainSystem:
    """
    Sistema principal ZERO BUDGET
    Coordina todos los componentes para acumulación GRATIS 24/7
    """

    def __init__(self):
        logger.info("🚀 INICIANDO SISTEMA ZERO BUDGET COMPLETO")

        # Inicializar componentes
        self.redpacket_hunter = ZeroBudgetRedpacketHunter()
        self.airdrop_hunter = ZeroBudgetAirdropHunter()

        # Inicializar base de datos
        self.init_database()

        # Configuración y metas
        self.config = self.load_config()
        self.targets = {
            "daily": 15.0,        # €15/día = €450/mes
            "weekly": 100.0,      # €100/semana
            "monthly": 450.0,     # €450/mes
            "quarterly": 1350.0,  # €1350/trimestre
            "yearly": 5400.0      # €5400/año
        }

        # Estadísticas globales
        self.global_stats = {
            "start_time": datetime.now(),
            "total_income": 0.0,
            "redpacket_income": 0.0,
            "airdrop_income": 0.0,
            "daily_income": 0.0,
            "codes_found": 0,
            "codes_claimed": 0,
            "airdrops_found": 0,
            "airdrops_completed": 0,
            "success_rate": 0.0,
            "uptime_hours": 0
        }

        # Sistema de notificaciones
        self.notifications_enabled = True
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', None)
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', None)

    def init_database(self):
        """Inicializar base de datos SQLite"""
        try:
            conn = sqlite3.connect('zero_budget_crypto.db')
            cursor = conn.cursor()

            # Tabla principal de ingresos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS income_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    sub_source TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    code_id TEXT,
                    transaction_hash TEXT
                )
            ''')

            # Tabla de progreso diario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    date DATE PRIMARY KEY,
                    redpacket_income REAL DEFAULT 0,
                    airdrop_income REAL DEFAULT 0,
                    total_income REAL DEFAULT 0,
                    codes_found INTEGER DEFAULT 0,
                    codes_claimed INTEGER DEFAULT 0,
                    airdrops_found INTEGER DEFAULT 0,
                    airdrops_completed INTEGER DEFAULT 0,
                    system_uptime_hours REAL DEFAULT 0
                )
            ''')

            # Tabla de hitos (milestones)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    milestone_name TEXT UNIQUE,
                    target_amount REAL,
                    achieved_at DATETIME,
                    achieved_amount REAL,
                    notified BOOLEAN DEFAULT FALSE
                )
            ''')

            # Insertar milestones iniciales
            milestones = [
                ("First €100", 100.0),
                ("First €500", 500.0),
                ("First €1000", 1000.0),
                ("First €2000", 2000.0),
                ("Monthly Goal", 450.0),
                ("Quarterly Goal", 1350.0)
            ]

            for name, target in milestones:
                cursor.execute('''
                    INSERT OR IGNORE INTO milestones (milestone_name, target_amount)
                    VALUES (?, ?)
                ''', (name, target))

            conn.commit()
            conn.close()

            logger.info("✅ Base de datos inicializada exitosamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")

    def load_config(self) -> Dict:
        """Cargar configuración desde archivo o valores por defecto"""
        try:
            if os.path.exists('zero_budget_config.json'):
                with open('zero_budget_config.json', 'r') as f:
                    config = json.load(f)
                logger.info("✅ Configuración cargada desde archivo")
            else:
                # Configuración por defecto
                config = {
                    "redpacket_enabled": True,
                    "airdrop_enabled": True,
                    "auto_reinvest": False,
                    "risk_level": "conservative",
                    "max_daily_attempts": 100,
                    "notification_threshold": 10.0,
                    "backup_frequency_hours": 6
                }
                self.save_config(config)
                logger.info("✅ Configuración por defecto creada")
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            config = {}

        return config

    def save_config(self, config: Dict):
        """Guardar configuración a archivo"""
        try:
            with open('zero_budget_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")

    async def log_income(self, source: str, amount: float, details: str = None, code_id: str = None):
        """Registrar ingreso en base de datos"""
        try:
            conn = sqlite3.connect('zero_budget_crypto.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO income_logs (source, amount, details, code_id)
                VALUES (?, ?, ?, ?)
            ''', (source, amount, details, code_id))

            conn.commit()
            conn.close()

            # Actualizar estadísticas globales
            self.global_stats["total_income"] += amount
            self.global_stats["daily_income"] += amount

            if source == "redpacket":
                self.global_stats["redpacket_income"] += amount
            elif source == "airdrop":
                self.global_stats["airdrop_income"] += amount

            logger.info(f"💰 Ingreso registrado: €{amount:.2f} de {source}")

            # Verificar milestones
            await self.check_milestones()

        except Exception as e:
            logger.error(f"❌ Error registrando ingreso: {e}")

    async def check_milestones(self):
        """Verificar y registrar milestones alcanzados"""
        try:
            conn = sqlite3.connect('zero_budget_crypto.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM milestones
                WHERE target_amount <= ? AND achieved_at IS NULL AND notified = FALSE
            ''', (self.global_stats["total_income"],))

            milestones = cursor.fetchall()

            for milestone in milestones:
                _, name, target, _, achieved, notified = milestone

                # Marcar como alcanzado
                cursor.execute('''
                    UPDATE milestones
                    SET achieved_at = ?, achieved_amount = ?, notified = TRUE
                    WHERE id = ?
                ''', (datetime.now(), self.global_stats["total_income"], milestone[0]))

                conn.commit()

                # Notificar milestone
                await self.send_notification(
                    f"🎉 MILESTONE ALCANZADO: {name}!",
                    f"💰 Meta: €{target:.0f}\n💎 Logrado: €{self.global_stats['total_income']:.2f}"
                )

                logger.info(f"🏆 MILESTONE ALCANZADO: {name} - €{target:.0f}")

            conn.close()

        except Exception as e:
            logger.error(f"❌ Error verificando milestones: {e}")

    async def send_notification(self, title: str, message: str):
        """Enviar notificación (Telegram, console, etc.)"""
        if not self.notifications_enabled:
            return

        # Notificación en consola
        notification_msg = f"\n🔔 {title}\n{message}\n{'='*50}"
        logger.info(notification_msg)

        # Aquí podría ir la integración con Telegram si tienes las credenciales
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                # Implementar notificación Telegram si es necesario
                pass
            except Exception as e:
                logger.error(f"❌ Error enviando notificación Telegram: {e}")

    async def run_redpacket_cycle(self):
        """Ejecutar ciclo de redpacket codes"""
        if not self.config.get("redpacket_enabled", True):
            return {"income": 0, "codes_found": 0, "codes_claimed": 0}

        try:
            logger.info("🔴 Iniciando ciclo REDPACKET")

            # Obtener códigos
            codes = await self.redpacket_hunter.monitor_telegram_groups()

            # Reclamar códigos
            results = await self.redpacket_hunter.claim_codes_automatically(codes)

            # Calcular ingresos
            income = sum(r["value"] for r in results if r["success"])

            # Registrar ingresos
            for result in results:
                if result["success"]:
                    await self.log_income(
                        "redpacket",
                        result["value"],
                        f"Código reclamado exitosamente"
                    )

            # Actualizar estadísticas
            self.global_stats["codes_found"] += len(codes)
            self.global_stats["codes_claimed"] += len([r for r in results if r["success"]])

            return {
                "income": income,
                "codes_found": len(codes),
                "codes_claimed": len([r for r in results if r["success"]])
            }

        except Exception as e:
            logger.error(f"❌ Error en ciclo REDPACKET: {e}")
            return {"income": 0, "codes_found": 0, "codes_claimed": 0}

    async def run_airdrop_cycle(self):
        """Ejecutar ciclo de airdrops"""
        if not self.config.get("airdrop_enabled", True):
            return {"income": 0, "airdrops_found": 0, "airdrops_completed": 0}

        try:
            logger.info("🪂 Iniciando ciclo AIRDROP")

            # Procesar oportunidades
            results = await self.airdrop_hunter.process_airdrop_opportunities()

            # Registrar ingresos
            if results["total_value"] > 0:
                await self.log_income(
                    "airdrop",
                    results["total_value"],
                    f"Airdrops reclamados exitosamente"
                )

            # Actualizar estadísticas
            # Estas vendrían de los sistemas individuales

            return {
                "income": results["total_value"],
                "airdrops_found": results["processed"],
                "airdrops_completed": results["successful"]
            }

        except Exception as e:
            logger.error(f"❌ Error en ciclo AIRDROP: {e}")
            return {"income": 0, "airdrops_found": 0, "airdrops_completed": 0}

    async def update_daily_summary(self):
        """Actualizar resumen diario"""
        try:
            conn = sqlite3.connect('zero_budget_crypto.db')
            cursor = conn.cursor()

            today = datetime.now().date()

            # Obtener ingresos del día
            cursor.execute('''
                SELECT source, SUM(amount) as daily_amount
                FROM income_logs
                WHERE DATE(timestamp) = ?
                GROUP BY source
            ''', (today,))

            daily_data = dict(cursor.fetchall())

            redpacket_income = daily_data.get("redpacket", 0)
            airdrop_income = daily_data.get("airdrop", 0)
            total_income = redpacket_income + airdrop_income

            # Calcular uptime
            uptime_hours = (datetime.now() - self.global_stats["start_time"]).total_seconds() / 3600

            # Insertar o actualizar resumen diario
            cursor.execute('''
                INSERT OR REPLACE INTO daily_summary
                (date, redpacket_income, airdrop_income, total_income,
                 codes_found, codes_claimed, airdrops_found, airdrops_completed, system_uptime_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (today, redpacket_income, airdrop_income, total_income,
                   self.global_stats["codes_found"], self.global_stats["codes_claimed"],
                   self.global_stats["airdrops_found"], self.global_stats["airdrops_completed"],
                   uptime_hours))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Error actualizando resumen diario: {e}")

    def calculate_performance_metrics(self) -> Dict:
        """Calcular métricas de rendimiento"""
        uptime_hours = (datetime.now() - self.global_stats["start_time"]).total_seconds() / 3600
        uptime_days = uptime_hours / 24

        if uptime_days > 0:
            daily_average = self.global_stats["total_income"] / uptime_days
            hourly_average = self.global_stats["total_income"] / uptime_hours
        else:
            daily_average = 0
            hourly_average = 0

        # Tasa de éxito general
        total_attempts = self.global_stats["codes_found"] + self.global_stats["airdrops_found"]
        if total_attempts > 0:
            success_rate = ((self.global_stats["codes_claimed"] + self.global_stats["airdrops_completed"]) / total_attempts) * 100
        else:
            success_rate = 0

        return {
            "uptime_hours": uptime_hours,
            "uptime_days": uptime_days,
            "daily_average": daily_average,
            "hourly_average": hourly_average,
            "success_rate": success_rate,
            "efficiency_score": daily_average / self.targets["daily"] if self.targets["daily"] > 0 else 0
        }

    async def run_main_cycle(self):
        """Ciclo principal del sistema"""
        try:
            logger.info("🔄 Iniciando ciclo principal del sistema")

            # Resetear ingresos diarios si es nuevo día
            today = datetime.now().date()
            last_check = self.global_stats.get("last_date", None)

            if last_check != today:
                self.global_stats["daily_income"] = 0
                self.global_stats["last_date"] = today
                logger.info("📅 Nuevo día detected - ingresos diarios reseteados")

            # Ejecutar ciclos en paralelo
            redpacket_task = asyncio.create_task(self.run_redpacket_cycle())
            airdrop_task = asyncio.create_task(self.run_airdrop_cycle())

            # Esperar resultados
            redpacket_results = await redpacket_task
            airdrop_results = await airdrop_task

            # Combinar resultados
            cycle_results = {
                "total_income": redpacket_results["income"] + airdrop_results["income"],
                "redpacket": redpacket_results,
                "airdrop": airdrop_results
            }

            # Actualizar resumen diario
            await self.update_daily_summary()

            # Calcular métricas
            metrics = self.calculate_performance_metrics()
            self.global_stats.update(metrics)

            # Imprimir resumen del ciclo
            logger.info("📊 RESUMEN DEL CICLO:")
            logger.info(f"   💰 Ingresos totales: €{cycle_results['total_income']:.2f}")
            logger.info(f"   🔴 Redpacket: €{redpacket_results['income']:.2f} ({redpacket_results['codes_claimed']}/{redpacket_results['codes_found']})")
            logger.info(f"   🪂 Airdrops: €{airdrop_results['income']:.2f} ({airdrop_results['airdrops_completed']}/{airdrop_results['airdrops_found']})")
            logger.info(f"   ⏱️ Uptime: {metrics['uptime_hours']:.1f} horas")
            logger.info(f"   📈 Promedio diario: €{metrics['daily_average']:.2f}")
            logger.info(f"   🎯 Eficiencia: {metrics['efficiency_score']*100:.1f}%")

            # Notificar si hay ingresos significativos
            if cycle_results["total_income"] >= self.config.get("notification_threshold", 10.0):
                await self.send_notification(
                    "💰 Buenas Noticias!",
                    f"📊 Ingresos del ciclo: €{cycle_results['total_income']:.2f}\n📅 Total acumulado: €{self.global_stats['total_income']:.2f}"
                )

            return cycle_results

        except Exception as e:
            logger.error(f"❌ Error en ciclo principal: {e}")
            return {"total_income": 0, "redpacket": {}, "airdrop": {}}

    async def run_zero_budget_system(self):
        """Ejecutar sistema completo 24/7"""
        logger.info("🚀 SISTEMA ZERO BUDGET INICIADO")
        logger.info("📋 Objetivo: Acumular capital GRATIS automáticamente")
        logger.info("⏰ Funcionamiento: 24/7 sin intervención manual")
        logger.info("💰 Meta: €15/día = €450/mes = €5400/año")
        logger.info("🎯 Riesgo: 0% - No requiere inversión")

        # Ciclo principal
        cycle_count = 0
        while True:
            try:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 CICLO #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*60}")

                # Ejecutar ciclo principal
                results = await self.run_main_cycle()

                # Mostrar progreso hacia metas
                daily_progress = (self.global_stats["daily_income"] / self.targets["daily"]) * 100
                logger.info(f"🎯 Progreso diario: {daily_progress:.1f}% (€{self.global_stats['daily_income']:.2f}/€{self.targets['daily']:.0f})")

                # Guardar configuración actualizada
                self.save_config(self.config)

                # Esperar para siguiente ciclo
                if self.global_stats["daily_income"] >= self.targets["daily"]:
                    # Si ya alcanzamos meta diaria, esperar más tiempo
                    wait_time = 3600  # 1 hora
                    logger.info("✅ Meta diaria alcanzada - pausa extendida")
                else:
                    # Ciclo normal
                    wait_time = 900  # 15 minutos

                logger.info(f"⏳ Esperando {wait_time/60:.0f} minutos para siguiente ciclo...")
                await asyncio.sleep(wait_time)

            except KeyboardInterrupt:
                logger.info("\n🛑 Sistema detenido por usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error crítico: {e}")
                logger.info("⏳ Esperando 5 minutos antes de reintentar...")
                await asyncio.sleep(300)

        # Resumen final
        logger.info("📊 RESUMEN FINAL DE SESIÓN:")
        logger.info(f"   💰 Total acumulado: €{self.global_stats['total_income']:.2f}")
        logger.info(f"   ⏱️ Tiempo activo: {self.global_stats['uptime_hours']:.1f} horas")
        logger.info(f"   📈 Promedio diario: €{self.global_stats.get('daily_average', 0):.2f}")
        logger.info(f"   🎯 Eficiencia: {self.global_stats.get('efficiency_score', 0)*100:.1f}%")
        logger.info("🚀 Sistema detenido. Reinicia cuando quieras continuar acumulando.")

async def main():
    """Función principal"""
    print("""
    🚀 SISTEMA ZERO BUDGET - INGRESOS CRYPTO AUTOMÁTICOS
    =====================================================
    💰 Objetivo: Acumular €450-1000/mes SIN inversión inicial
    📋 Método: Redpacket codes + Airdrops GRATIS 24/7
    ⏰ Funcionamiento: Totalmente automático
    🎯 Riesgo: 0% (No requiere capital propio)
    📈 Potencial: €5400+ al año con optimización

    Iniciando sistema completo...
    """)

    # Crear y ejecutar sistema principal
    system = ZeroBudgetMainSystem()
    await system.run_zero_budget_system()

if __name__ == "__main__":
    asyncio.run(main())