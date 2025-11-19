#!/usr/bin/env python3
"""
📊 SISTEMA ZERO BUDGET - DASHBOARD DE TRACKING
🎯 Objetivo: Monitorear capital acumulado GRATIS en tiempo real
💰 Método: Dashboard interactivo con estadísticas y progreso
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sqlite3
import asyncio
from typing import Dict, List
import time

class ZeroBudgetDashboard:
    """
    Dashboard principal para monitorear sistema ZERO BUDGET
    Muestra progreso de capital acumulado GRATIS
    """

    def __init__(self):
        # Configuración de la página
        st.set_page_config(
            page_title="💰 Crypto Income Zero Budget",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Inicializar base de datos
        self.init_database()

        # Objetivos del sistema
        self.targets = {
            "daily": 15.0,      # €15 por día = €450/mes
            "weekly": 100.0,    # €100 por semana
            "monthly": 450.0,   # €450 por mes
            "milestone_1": 500.0,    # Primer €500
            "milestone_2": 1000.0,   # Primer €1000
            "milestone_3": 2000.0    # Primer €2000
        }

    def init_database(self):
        """
        Inicializar base de datos SQLite para tracking
        """
        conn = sqlite3.connect('zero_budget_crypto.db')
        cursor = conn.cursor()

        # Tabla de ingresos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'EUR',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                code_id TEXT
            )
        ''')

        # Tabla de progreso diario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_progress (
                date DATE PRIMARY KEY,
                redpacket_income REAL DEFAULT 0,
                airdrop_income REAL DEFAULT 0,
                total_income REAL DEFAULT 0,
                codes_found INTEGER DEFAULT 0,
                airdrops_completed INTEGER DEFAULT 0
            )
        ''')

        # Tabla de estadísticas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY,
                start_date DATE DEFAULT CURRENT_DATE,
                total_accumulated REAL DEFAULT 0,
                redpacket_codes_found INTEGER DEFAULT 0,
                redpacket_codes_claimed INTEGER DEFAULT 0,
                airdrops_found INTEGER DEFAULT 0,
                airdrops_claimed INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def get_system_stats(self) -> Dict:
        """
        Obtener estadísticas actuales del sistema
        """
        conn = sqlite3.connect('zero_budget_crypto.db')
        cursor = conn.cursor()

        # Obtener ingresos totales
        cursor.execute("SELECT SUM(amount) FROM income_logs")
        total_income = cursor.fetchone()[0] or 0

        # Obtener ingresos por fuente
        cursor.execute("""
            SELECT source, SUM(amount) as total
            FROM income_logs
            GROUP BY source
        """)
        income_by_source = dict(cursor.fetchall())

        # Obtener ingresos de hoy
        cursor.execute("""
            SELECT SUM(amount) FROM income_logs
            WHERE DATE(timestamp) = DATE('now')
        """)
        today_income = cursor.fetchone()[0] or 0

        # Obtener ingresos del mes
        cursor.execute("""
            SELECT SUM(amount) FROM income_logs
            WHERE DATE(timestamp) >= DATE('now', '-30 days')
        """)
        monthly_income = cursor.fetchone()[0] or 0

        # Calcular progreso hacia metas
        daily_progress = (today_income / self.targets["daily"]) * 100
        monthly_progress = (monthly_income / self.targets["monthly"]) * 100

        # Milestones
        milestones_progress = {
            "€500": (total_income / self.targets["milestone_1"]) * 100,
            "€1000": (total_income / self.targets["milestone_2"]) * 100,
            "€2000": (total_income / self.targets["milestone_3"]) * 100
        }

        conn.close()

        return {
            "total_accumulated": total_income,
            "today_income": today_income,
            "monthly_income": monthly_income,
            "income_by_source": income_by_source,
            "daily_progress": daily_progress,
            "monthly_progress": monthly_progress,
            "milestones_progress": milestones_progress,
            "start_date": datetime.now() - timedelta(days=30)
        }

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """
        Obtener actividad reciente
        """
        conn = sqlite3.connect('zero_budget_crypto.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT source, amount, timestamp, details
            FROM income_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        activity = []
        for row in cursor.fetchall():
            activity.append({
                "source": row[0],
                "amount": row[1],
                "timestamp": row[2],
                "details": row[3]
            })

        conn.close()
        return activity

    def get_daily_chart_data(self, days: int = 30) -> pd.DataFrame:
        """
        Obtener datos para gráfico diario
        """
        conn = sqlite3.connect('zero_budget_crypto.db')

        query = """
            SELECT DATE(timestamp) as date,
                   SUM(amount) as daily_income,
                   COUNT(*) as transactions
            FROM income_logs
            WHERE DATE(timestamp) >= DATE('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """.format(days)

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def render_header(self, stats: Dict):
        """
        Renderizar header del dashboard
        """
        st.title("🚀 CRYPTO INCOME - SISTEMA ZERO BUDGET")
        st.markdown("---")

        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "💰 Total Acumulado",
                f"€{stats['total_accumulated']:.2f}",
                delta=f"€{stats['today_income']:.2f} hoy"
            )

        with col2:
            st.metric(
                "📈 Ingresos Hoy",
                f"€{stats['today_income']:.2f}",
                delta=f"{stats['daily_progress']:.1f}% del objetivo"
            )

        with col3:
            st.metric(
                "📅 Ingresos Mensuales",
                f"€{stats['monthly_income']:.2f}",
                delta=f"{stats['monthly_progress']:.1f}% del objetivo"
            )

        with col4:
            st.metric(
                "🎯 Meta Mensual",
                f"€{self.targets['monthly']:.0f}",
                delta=f"€{self.targets['monthly'] - stats['monthly_income']:.0f} restantes"
            )

    def render_progress_bars(self, stats: Dict):
        """
        Renderizar barras de progreso
        """
        st.markdown("### 📊 Progreso de Metas")

        # Progreso diario
        st.markdown("**Progreso Diario:**")
        daily_progress = min(stats['daily_progress'], 100)
        st.progress(daily_progress / 100)
        st.write(f"€{stats['today_income']:.2f} / €{self.targets['daily']:.0f} ({daily_progress:.1f}%)")

        # Progreso mensual
        st.markdown("**Progreso Mensual:**")
        monthly_progress = min(stats['monthly_progress'], 100)
        st.progress(monthly_progress / 100)
        st.write(f"€{stats['monthly_income']:.2f} / €{self.targets['monthly']:.0f} ({monthly_progress:.1f}%)")

        # Milestones
        st.markdown("### 🏆 Milestones")
        cols = st.columns(3)

        for i, (milestone, progress) in enumerate(stats['milestones_progress'].items()):
            with cols[i]:
                # Color del progreso
                if progress >= 100:
                    color = "🟢"
                elif progress >= 50:
                    color = "🟡"
                else:
                    color = "🔴"

                st.write(f"**{color} {milestone}**")
                milestone_progress = min(progress, 100)
                st.progress(milestone_progress / 100)
                st.write(f"{milestone_progress:.1f}% completado")

    def render_income_sources(self, stats: Dict):
        """
        Renderizar gráfico de fuentes de ingresos
        """
        st.markdown("### 💰 Fuentes de Ingresos")

        if stats['income_by_source']:
            # Crear DataFrame para el gráfico
            df_sources = pd.DataFrame(
                list(stats['income_by_source'].items()),
                columns=['Fuente', 'Monto (EUR)']
            )

            # Gráfico de pie
            fig = px.pie(
                df_sources,
                values='Monto (EUR)',
                names='Fuente',
                title="Distribución de Ingresos por Fuente"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabla de detalles
            st.markdown("**Detalles por Fuente:**")
            for source, amount in stats['income_by_source'].items():
                percentage = (amount / stats['total_accumulated']) * 100 if stats['total_accumulated'] > 0 else 0
                st.write(f"• {source}: €{amount:.2f} ({percentage:.1f}%)")
        else:
            st.info("📭 No hay ingresos registrados aún. El sistema está trabajando en generar las primeras ganancias.")

    def render_daily_chart(self):
        """
        Renderizar gráfico de ingresos diarios
        """
        st.markdown("### 📈 Evolución de Ingresos Diarios")

        # Obtener datos
        df = self.get_daily_chart_data()

        if not df.empty:
            # Crear gráfico de líneas
            fig = px.line(
                df,
                x='date',
                y='daily_income',
                title='Ingresos Diarios (Últimos 30 días)',
                labels={'daily_income': 'Ingresos (EUR)', 'date': 'Fecha'}
            )

            # Añadir línea de objetivo diario
            fig.add_hline(
                y=self.targets['daily'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Objetivo: €{self.targets['daily']}/día"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Estadísticas del gráfico
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_daily = df['daily_income'].mean()
                st.metric("📊 Promedio Diario", f"€{avg_daily:.2f}")

            with col2:
                max_daily = df['daily_income'].max()
                st.metric("🔝 Mejor Día", f"€{max_daily:.2f}")

            with col3:
                total_days = len(df)
                st.metric("📅 Días Activos", total_days)

        else:
            st.info("📈 No hay datos históricos aún. El sistema comenzará a registrar ingresos pronto.")

    def render_recent_activity(self):
        """
        Renderizar actividad reciente
        """
        st.markdown("### ⚡ Actividad Reciente")

        activity = self.get_recent_activity()

        if activity:
            for item in activity:
                # Formatear timestamp
                timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')

                # Iconos por fuente
                source_icons = {
                    "redpacket": "🔴",
                    "airdrop": "🪂",
                    "vip_signals": "💎",
                    "arbitrage": "⚡"
                }

                icon = source_icons.get(item['source'], "💰")

                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 2])

                    with col1:
                        st.write(f"{icon}")

                    with col2:
                        st.write(f"**{item['source'].title()}**")
                        if item['details']:
                            st.caption(item['details'])

                    with col3:
                        st.success(f"€{item['amount']:.2f}")
                        st.caption(timestamp)

                st.markdown("---")
        else:
            st.info("⏳ Esperando primera transacción... El sistema está trabajando activamente.")

    def render_control_panel(self):
        """
        Renderizar panel de control
        """
        st.markdown("### 🎛️ Panel de Control")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Estado del Sistema:**")
            system_status = st.selectbox(
                "Estado:",
                ["🟢 Activo", "🟡 Pausado", "🔴 Detenido"],
                index=0
            )

            if system_status == "🟢 Activo":
                st.success("✅ Sistema funcionando 24/7")
            elif system_status == "🟡 Pausado":
                st.warning("⏸️ Sistema temporalmente pausado")
            else:
                st.error("❌ Sistema detenido")

        with col2:
            st.markdown("**Configuración:**")

            target_daily = st.number_input(
                "Objetivo Diario (€):",
                min_value=1.0,
                max_value=100.0,
                value=self.targets['daily'],
                step=1.0
            )

            notification_enabled = st.checkbox(
                "🔔 Notificaciones Activadas",
                value=True
            )

        # Botones de acción
        st.markdown("**Acciones Rápidas:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Forzar Sync", type="secondary"):
                st.rerun()

        with col2:
            if st.button("📊 Exportar Datos", type="secondary"):
                st.info("📥 Función de exportación en desarrollo")

        with col3:
            if st.button("🎯 Optimizar", type="primary"):
                st.info("🚀 Función de optimización en desarrollo")

    def render_income_projection(self, stats: Dict):
        """
        Renderizar proyección de ingresos
        """
        st.markdown("### 🔮 Proyección de Ingresos")

        # Calcular promedio diario
        days_active = max((datetime.now() - stats['start_date']).days, 1)
        avg_daily = stats['total_accumulated'] / days_active

        # Proyecciones
        col1, col2, col3 = st.columns(3)

        with col1:
            # Proyección mensual basada en promedio actual
            monthly_projection = avg_daily * 30
            st.metric("📅 Proyección Mensual", f"€{monthly_projection:.2f}")

        with col2:
            # Proyección trimestral
            quarterly_projection = avg_daily * 90
            st.metric("📊 Proyección Trimestral", f"€{quarterly_projection:.2f}")

        with col3:
            # Tiempo para €1000
            if avg_daily > 0:
                days_to_1000 = (1000 - stats['total_accumulated']) / avg_daily
                st.metric("🎯 Días para €1000", f"{max(days_to_1000, 0):.0f}")
            else:
                st.metric("🎯 Días para €1000", "∞")

        # Escenarios
        st.markdown("**Escenarios Posibles:**")
        scenarios = {
            "Conservador": avg_daily * 0.8,
            "Actual": avg_daily,
            "Optimista": avg_daily * 1.5,
            "Agresivo": avg_daily * 2.0
        }

        for scenario, daily_rate in scenarios.items():
            monthly = daily_rate * 30
            st.write(f"• {scenario}: €{monthly:.2f}/mes (€{daily_rate:.2f}/día)")

    def run(self):
        """
        Ejecutar dashboard principal
        """
        # Obtener estadísticas
        stats = self.get_system_stats()

        # Renderizar secciones
        self.render_header(stats)

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "📈 Gráficos",
            "⚡ Actividad",
            "🔮 Proyecciones",
            "🎛️ Control"
        ])

        with tab1:
            self.render_progress_bars(stats)
            self.render_income_sources(stats)

        with tab2:
            self.render_daily_chart()

        with tab3:
            self.render_recent_activity()

        with tab4:
            self.render_income_projection(stats)

        with tab5:
            self.render_control_panel()

        # Auto-refresh
        st.markdown("---")
        st.caption("🔄 Auto-refresh cada 30 segundos • Sistema funcionando 24/7")

        # Script de auto-refresh
        st.markdown("""
        <script>
            setTimeout(function(){
                st.rerun();
            }, 30000);
        </script>
        """, unsafe_allow_html=True)

def main():
    """
    Función principal del dashboard
    """
    dashboard = ZeroBudgetDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()