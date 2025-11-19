"""
Real-Time Dashboard for Autonomous Crypto Redpacket Claiming System

Streamlit dashboard providing live monitoring, control, and analytics
for the complete redpacket claiming operation.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import asyncio
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading

# Configuration
st.set_page_config(
    page_title="🚀 Crypto Redpacket Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
}
.emergency-button {
    background: linear-gradient(135deg, #f93b1d 0%, #ea1e63 100%);
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    font-size: 1.2rem;
}
.status-running { color: #4CAF50; }
.status-warning { color: #FF9800; }
.status-error { color: #F44336; }
</style>
""", unsafe_allow_html=True)


class DashboardData:
    """Data manager for the dashboard."""

    def __init__(self):
        self.data_dir = Path("C:/bots/redpackets")
        self.claims_file = self.data_dir / "claims_log.csv"
        self.metrics_cache = {}
        self.last_update = 0

    def load_claims_data(self) -> pd.DataFrame:
        """Load claims data from CSV file."""
        try:
            if self.claims_file.exists():
                df = pd.read_csv(self.claims_file)
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            else:
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    'timestamp', 'code', 'amount', 'currency', 'txid',
                    'status', 'method', 'retry_count', 'delay_seconds',
                    'user_agent', 'risk_score'
                ])
        except Exception as e:
            st.error(f"Error loading claims data: {e}")
            return pd.DataFrame()

    def get_today_stats(self) -> Dict[str, Any]:
        """Calculate today's statistics."""
        try:
            df = self.load_claims_data()
            today = datetime.now().date()

            # Filter today's data
            today_df = df[df['timestamp'].dt.date == today]

            # Calculate statistics
            total_claims = len(today_df)
            successful_claims = len(today_df[today_df['status'] == 'success'])
            failed_claims = len(today_df[today_df['status'] == 'failed'])

            # Calculate BNB earned
            successful_df = today_df[today_df['status'] == 'success']
            bnb_earned = successful_df['amount'].astype(float).sum() if not successful_df.empty else 0.0

            # Success rate
            success_rate = (successful_claims / total_claims * 100) if total_claims > 0 else 0.0

            # Average delay
            avg_delay = today_df['delay_seconds'].mean() if not today_df.empty else 0.0

            # Risk score tracking
            avg_risk_score = today_df['risk_score'].mean() if not today_df.empty else 0.0
            max_risk_score = today_df['risk_score'].max() if not today_df.empty else 0

            return {
                'total_claims': total_claims,
                'successful_claims': successful_claims,
                'failed_claims': failed_claims,
                'bnb_earned': bnb_earned,
                'success_rate': success_rate,
                'avg_delay': avg_delay,
                'avg_risk_score': avg_risk_score,
                'max_risk_score': max_risk_score
            }

        except Exception as e:
            st.error(f"Error calculating today's stats: {e}")
            return {
                'total_claims': 0, 'successful_claims': 0, 'failed_claims': 0,
                'bnb_earned': 0.0, 'success_rate': 0.0, 'avg_delay': 0.0,
                'avg_risk_score': 0.0, 'max_risk_score': 0
            }

    def get_recent_claims(self, limit: int = 20) -> pd.DataFrame:
        """Get most recent claims."""
        try:
            df = self.load_claims_data()
            if not df.empty:
                # Sort by timestamp descending and get last N
                recent_df = df.sort_values('timestamp', ascending=False).head(limit)
                # Format for display
                recent_df = recent_df.copy()
                recent_df['time'] = recent_df['timestamp'].dt.strftime('%H:%M:%S')
                recent_df['amount_display'] = recent_df['amount'] + ' ' + recent_df['currency']
                return recent_df[['time', 'code', 'amount_display', 'status', 'method', 'risk_score']]
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error getting recent claims: {e}")
            return pd.DataFrame()

    def get_hourly_claims_chart(self) -> Dict[str, List]:
        """Get hourly claims data for chart."""
        try:
            df = self.load_claims_data()
            if df.empty:
                return {'hours': [], 'claims': [], 'successful': []}

            # Filter today's data
            today = datetime.now().date()
            today_df = df[df['timestamp'].dt.date == today]

            # Group by hour
            hourly_data = today_df.groupby(today_df['timestamp'].dt.hour).agg({
                'code': 'count',
                'status': lambda x: (x == 'success').sum()
            }).reset_index()
            hourly_data.columns = ['hour', 'total_claims', 'successful_claims']

            # Fill missing hours with zeros
            all_hours = list(range(24))
            chart_data = {'hours': all_hours, 'claims': [], 'successful': []}

            for hour in all_hours:
                hour_data = hourly_data[hourly_data['hour'] == hour]
                if not hour_data.empty:
                    chart_data['claims'].append(hour_data['total_claims'].iloc[0])
                    chart_data['successful'].append(hour_data['successful_claims'].iloc[0])
                else:
                    chart_data['claims'].append(0)
                    chart_data['successful'].append(0)

            return chart_data

        except Exception as e:
            st.error(f"Error creating hourly chart data: {e}")
            return {'hours': [], 'claims': [], 'successful': []}


class DashboardController:
    """Main dashboard controller."""

    def __init__(self):
        self.data = DashboardData()
        self.emergency_mode_active = False
        self.emergency_mode_until = None

    def run_dashboard(self):
        """Run the main dashboard."""
        st.title("🚀 Crypto Redpacket Claiming Dashboard")
        st.markdown("---")

        # Sidebar configuration
        self.render_sidebar()

        # Main content area
        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_metrics_cards()
            self.render_charts()

        with col2:
            self.render_controls()
            self.render_recent_claims()

        # Status bar at bottom
        self.render_status_bar()

    def render_sidebar(self):
        """Render sidebar configuration."""
        st.sidebar.markdown("## ⚙️ Configuration")

        # Auto-refresh
        auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh", value=True)
        if auto_refresh:
            refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)

        # Emergency controls
        st.sidebar.markdown("## 🚨 Emergency Controls")
        emergency_duration = st.sidebar.selectbox(
            "Emergency duration",
            options=[1, 2, 6, 12, 24],
            format_func=lambda x: f"{x} hours",
            index=3
        )

        if st.sidebar.button("🛑 ACTIVATE MODO SIERPE", type="secondary"):
            self.activate_emergency_mode(emergency_duration)

        if self.emergency_mode_active:
            st.sidebar.error(f"🚨 EMERGENCY MODE ACTIVE")
            if self.emergency_mode_until:
                remaining = self.emergency_mode_until - datetime.now()
                if remaining > timedelta(0):
                    st.sidebar.write(f"Time remaining: {remaining}")
                else:
                    self.emergency_mode_active = False
                    st.rerun()

        # System controls
        st.sidebar.markdown("## 🎛️ System Controls")
        if st.sidebar.button("📊 Refresh Data"):
            st.rerun()

        if st.sidebar.button("🧹 Clear Cache"):
            self.clear_cache()
            st.rerun()

    def render_metrics_cards(self):
        """Render main metrics cards."""
        stats = self.data.get_today_stats()

        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self.render_metric_card(
                "📊 Today's Claims",
                f"{stats['total_claims']}",
                f"Success rate: {stats['success_rate']:.1f}%"
            )

        with col2:
            self.render_metric_card(
                "💰 BNB Earned",
                f"{stats['bnb_earned']:.4f}",
                f"From {stats['successful_claims']} claims"
            )

        with col3:
            self.render_metric_card(
                "⚡ Avg Delay",
                f"{stats['avg_delay']:.1f}s",
                f"Risk score: {stats['avg_risk_score']:.0f}"
            )

        with col4:
            status_color = "🟢" if stats['success_rate'] > 80 else "🟡" if stats['success_rate'] > 50 else "🔴"
            self.render_metric_card(
                f"{status_color} System Health",
                f"{stats['success_rate']:.1f}%",
                f"Failed: {stats['failed_claims']}"
            )

    def render_metric_card(self, title: str, value: str, subtitle: str):
        """Render a single metric card."""
        st.markdown(f"""
        <div class="metric-card">
            <h4>{title}</h4>
            <h2>{value}</h2>
            <p>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    def render_charts(self):
        """Render charts section."""
        st.markdown("## 📈 Analytics")

        chart_data = self.data.get_hourly_claims_chart()

        if chart_data['claims']:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=("Hourly Claims", "Success Rate", "Risk Score Trend", "Method Distribution"),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"type": "domain"}]]
            )

            # Hourly claims chart
            fig.add_trace(
                go.Scatter(
                    x=chart_data['hours'],
                    y=chart_data['claims'],
                    mode='lines+markers',
                    name='Total Claims',
                    line=dict(color='#1f77b4', width=3)
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Scatter(
                    x=chart_data['hours'],
                    y=chart_data['successful'],
                    mode='lines+markers',
                    name='Successful Claims',
                    line=dict(color='#2ca02c', width=3)
                ),
                row=1, col=1
            )

            # Success rate chart
            total_claims = [t if t > 0 else 1 for t in chart_data['claims']]  # Avoid division by zero
            success_rates = [s/t*100 for s, t in zip(chart_data['successful'], total_claims)]

            fig.add_trace(
                go.Scatter(
                    x=chart_data['hours'],
                    y=success_rates,
                    mode='lines+markers',
                    name='Success Rate %',
                    line=dict(color='#ff7f0e', width=3)
                ),
                row=1, col=2
            )

            # Risk score trend
            df = self.data.load_claims_data()
            if not df.empty:
                today = datetime.now().date()
                today_df = df[df['timestamp'].dt.date == today]
                if not today_df.empty:
                    hourly_risk = today_df.groupby(today_df['timestamp'].dt.hour)['risk_score'].mean()
                    fig.add_trace(
                        go.Scatter(
                            x=list(hourly_risk.index),
                            y=list(hourly_risk.values),
                            mode='lines+markers',
                            name='Avg Risk Score',
                            line=dict(color='#d62728', width=3)
                        ),
                        row=2, col=1
                    )

            # Method distribution pie chart
            method_counts = df['method'].value_counts() if not df.empty else pd.Series()
            if not method_counts.empty:
                fig.add_trace(
                    go.Pie(
                        labels=method_counts.index,
                        values=method_counts.values,
                        name="Claim Methods"
                    ),
                    row=2, col=2
                )

            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                title_text="Redpacket Claiming Analytics"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for charts yet. Start claiming to see analytics.")

    def render_controls(self):
        """Render control panel."""
        st.markdown("## 🎮 Control Panel")

        # Manual claim input
        with st.expander("🎯 Manual Claim Test"):
            code = st.text_input("Enter 8-character code:", max_chars=8, key="manual_code")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📡 Claim via API", type="primary"):
                    if code and len(code) == 8:
                        st.success(f"API claim initiated for: {code}")
                        # TODO: Integrate with actual API claim
                    else:
                        st.error("Please enter a valid 8-character code")

            with col2:
                if st.button("📱 Claim via ADB", type="secondary"):
                    if code and len(code) == 8:
                        st.success(f"ADB claim initiated for: {code}")
                        # TODO: Integrate with ADB fallback
                    else:
                        st.error("Please enter a valid 8-character code")

        # System status
        st.markdown("### 🖥️ System Status")

        # Mock status data - replace with real system status
        status_data = {
            "API Client": "🟢 Online",
            "ADB Device": "🟡 Connected (Testing)",
            "Telegram Bot": "🟢 Active",
            "Dashboard": "🟢 Running"
        }

        for service, status in status_data.items():
            st.write(f"{service}: {status}")

        # Performance metrics
        st.markdown("### ⚡ Performance")

        stats = self.data.get_today_stats()
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Avg Response Time", f"{stats['avg_delay']:.1f}s")
            st.metric("Risk Score", f"{stats['avg_risk_score']:.0f}")

        with col2:
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
            st.metric("Total Claims", stats['total_claims'])

    def render_recent_claims(self):
        """Render recent claims table."""
        st.markdown("## 📋 Recent Claims")

        recent_df = self.data.get_recent_claims()

        if not recent_df.empty:
            # Add status emojis
            def format_status(status):
                emoji_map = {
                    'success': '✅',
                    'failed': '❌',
                    'captcha': '🧩',
                    'rate_limited': '⏱️',
                    'session_expired': '🔑',
                    'ban_detected': '🚨'
                }
                return f"{emoji_map.get(status, '❓')} {status}"

            recent_df['status'] = recent_df['status'].apply(format_status)

            # Format method
            def format_method(method):
                method_map = {
                    'api': '📡 API',
                    'adb': '📱 ADB',
                    'adb_fallback': '📱 ADB'
                }
                return method_map.get(method, method)

            recent_df['method'] = recent_df['method'].apply(format_method)

            # Risk score color coding
            def risk_score_color(score):
                if score >= 85:
                    return f"🔴 {score}"
                elif score >= 70:
                    return f"🟡 {score}"
                else:
                    return f"🟢 {score}"

            recent_df['risk_score'] = recent_df['risk_score'].apply(risk_score_color)

            st.dataframe(
                recent_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent claims to display")

    def render_status_bar(self):
        """Render status bar at bottom."""
        st.markdown("---")

        # Create status columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')}")

        with col2:
            if self.emergency_mode_active:
                st.error("🚨 EMERGENCY MODE")
            else:
                st.success("🟢 NORMAL OPERATION")

        with col3:
            # Check if data files exist
            data_files_exist = self.data.claims_file.exists()
            if data_files_exist:
                st.success("📁 Data files OK")
            else:
                st.warning("⚠️ No data files")

        with col4:
            st.write(f"💾 Total records: {len(self.data.load_claims_data())}")

    def activate_emergency_mode(self, duration_hours: int):
        """Activate emergency mode."""
        self.emergency_mode_active = True
        self.emergency_mode_until = datetime.now() + timedelta(hours=duration_hours)
        st.error(f"🚨 MODO SIERPE ACTIVATED for {duration_hours} hours!")
        st.rerun()

    def clear_cache(self):
        """Clear dashboard cache."""
        self.data.metrics_cache.clear()
        st.success("Cache cleared successfully!")


def main():
    """Main dashboard entry point."""
    # Initialize dashboard controller
    dashboard = DashboardController()

    # Run the dashboard
    dashboard.run_dashboard()

    # Auto-refresh functionality
    if st.sidebar.checkbox("🔄 Auto-refresh", value=True):
        refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()