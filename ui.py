# ui.py - Функции отображения пользовательского интерфейса

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import os

from data_service import pollutant_info, fetch_pollution_history
from config import HISTORY_HOURS, HAZARD_THRESHOLDS

def render_header() -> None:
    """Отображает заголовок приложения и CSS стили."""
    # Add custom CSS for alerts
    st.markdown("""
    <style>
    .danger-alert {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 4px 8px rgba(244, 67, 54, 0.1); }
        50% { box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4); }
        100% { box-shadow: 0 4px 8px rgba(244, 67, 54, 0.1); }
    }
    
    .alert-title {
        color: #d32f2f;
        font-size: 1.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .alert-body {
        color: #333;
        font-size: 1.1em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🏭 Real-Time Industry Air Quality Dashboard")
    st.caption(f"Role: {st.session_state.role} | Last updated: {datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC")

def render_weather_cards(data: Dict[str, Any], container: Optional[st.container] = None) -> None:
    """
    Отображает карточки с данными о погоде.
    
    Args:
        data: Данные о погоде
        container: Контейнер Streamlit для вывода (опционально)
    """
    target = container if container else st
    c1, c2, c3 = target.columns(3)
    c1.metric("🌡️ Temp (°C)", data.get("main", {}).get("temp", "N/A"))
    c2.metric("💧 Humidity (%)", data.get("main", {}).get("humidity", "N/A"))
    c3.metric("💨 Wind (m/s)", data.get("wind", {}).get("speed", "N/A"))

def render_pollutant_cards(poll: Dict[str, float], container: Optional[st.container] = None) -> None:
    """
    Отображает карточки с данными о загрязнителях.
    
    Args:
        poll: Данные о загрязнителях
        container: Контейнер Streamlit для вывода (опционально)
    """
    target = container if container else st
    target.markdown("---")
    target.markdown("### 🔎 Current Pollutants (µg/m³)")
    cols = target.columns(4)
    for i, (k, v) in enumerate(poll.items()):
        lbl, _ = pollutant_info(k)
        cols[i % 4].metric(lbl, f"{v}")

def render_trends(lat: float, lon: float, hours: int = HISTORY_HOURS, container: Optional[st.container] = None) -> None:
    """
    Отображает график трендов загрязнения.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        hours: Количество часов истории для отображения
        container: Контейнер Streamlit для вывода (опционально)
    """
    target = container if container else st
    target.markdown(f"### 📈 Last {hours}-Hour Trends")
    df = fetch_pollution_history(lat, lon, hours)
    if df.empty:
        target.write("No historical data.")
        return
    df['label'] = df['pollutant'].map(lambda k: pollutant_info(k)[0])
    piv = df.groupby('label')['value'].resample('1H').mean().unstack(level=0).ffill()
    fig = go.Figure()
    for col in piv.columns:
        fig.add_trace(go.Scatter(x=piv.index, y=piv[col], mode='lines+markers', name=col))
    fig.update_layout(template='plotly_dark', xaxis_title='UTC Time', yaxis_title='µg/m³')
    target.plotly_chart(fig, use_container_width=True)

def check_pollutant_alerts(pollutants: dict, container=None) -> list:
    """
    Проверяет превышение опасных порогов загрязнителей.
    
    Args:
        pollutants: Словарь с текущими значениями загрязнителей
        container: Опциональный контейнер Streamlit для вывода
    
    Returns:
        Список превышений в формате [(загрязнитель, значение, порог), ...]
    """
    target = container if container else st
    exceedances = []
    
    for pollutant, value in pollutants.items():
        threshold = HAZARD_THRESHOLDS.get(pollutant)
        if threshold and float(value) > threshold:
            exceedances.append((pollutant, value, threshold))
    
    return exceedances

def display_alert_modal(exceedances: list, facility_name: str) -> None:
    """
    Отображает модальное окно с предупреждением о превышении опасных уровней загрязнителей
    и отправляет email-оповещение при необходимости.
    
    Args:
        exceedances: Список превышений в формате [(загрязнитель, значение, порог), ...]
        facility_name: Название объекта наблюдения
    """
    # Import email functionality if available
    try:
        from email_service import send_email_alert
        email_service_available = True
    except ImportError:
        email_service_available = False
    
    # Создаем модальное окно
    if not exceedances:
        return
    
    # Create HTML for styled alert - combined into one complete HTML string
    alert_html = f"""
    <div class="danger-alert">
        <div class="alert-title">⚠️ DANGEROUS POLLUTION LEVEL DETECTED!</div>
        <div class="alert-body">
            <p><strong>Facility:</strong> {facility_name}</p>
            <p><strong>Threshold Exceedances:</strong></p>
            <ul>
    """
    
    # Add each exceedance to the HTML
    for pollutant, value, threshold in exceedances:
        name, _ = pollutant_info(pollutant)
        alert_html += f"<li><strong>{name}:</strong> {value} µg/m³ (exceeds threshold of {threshold} µg/m³)</li>"
    
    alert_html += """
            </ul>
            <p><strong>Immediate action required!</strong></p>
        </div>
    </div>
    """
    
    # Display the styled alert
    st.markdown(alert_html, unsafe_allow_html=True)
    
    # Create a more visible form for sending alerts
    st.markdown("---")
    st.subheader("📧 Send Alert to Meteorologist")
    
    col1, col2 = st.columns([3, 1])
    
    contact_email = "bktzhnd@gmail.com"
    
    with col1:
        message = st.text_area(
            "Additional Information:", 
            value=f"Dangerous pollutant levels detected at {facility_name} facility. Immediate inspection required.\n\nExceedances detected:\n" + 
                  "\n".join([f"- {pollutant_info(p)[0]}: {v} µg/m³ (threshold: {t} µg/m³)" for p, v, t in exceedances]),
            height=150
        )
    
    with col2:
        st.markdown("### Contact:")
        st.info(contact_email)
    
    # Create email subject
    subject = f"ALERT: Dangerous Pollution Levels at {facility_name}"
    
    if st.button("🚨 SEND EMERGENCY ALERT", use_container_width=True):
        if email_service_available:
            # Try to send a real email
            success = send_email_alert(contact_email, subject, message)
            if success:
                st.success(f"✅ Alert sent to meteorologist ({contact_email})")
            else:
                st.error("Failed to send email alert. Check the email configuration.")
                st.info("To enable email alerts, add your email credentials to .streamlit/secrets.toml")
        else:
            # If email service is not available, show demo message
            st.warning("📧 Email service is not configured.")
            st.info("""
            To enable sending real emails, create an email_service.py file with the provided code and add the following to your .streamlit/secrets.toml file:
            
            ```
            EMAIL_ADDRESS = "your-email@gmail.com"
            EMAIL_PASSWORD = "your-app-password"
            SMTP_SERVER = "smtp.gmail.com"
            SMTP_PORT = 587
            ```
            
            Note: For Gmail, you need to use an App Password, not your regular password.
            """)
            
            # Show the email that would be sent
            with st.expander("View Email Content"):
                st.code(f"To: {contact_email}\nSubject: {subject}\n\n{message}")
    
    # Option to auto-send alerts without manual confirmation
    st.checkbox("Auto-send alerts for future exceedances", value=False, key="auto_send_alerts", 
               help="If checked, alerts will be sent automatically when dangerous levels are detected, without requiring manual confirmation.")
    
    # If auto-send is enabled and this is the first alert detection, send automatically
    if st.session_state.get("auto_send_alerts", False) and not st.session_state.get("alert_sent", False):
        if email_service_available:
            success = send_email_alert(contact_email, subject, message)
            if success:
                st.session_state.alert_sent = True
                st.info("✉️ Auto-alert sent to meteorologist due to your settings.")
        else:
            st.session_state.alert_sent = True
            st.info("Auto-alert would be sent if email service was configured.")

def add_test_controls(container=None):
    """
    Adds controls to simulate dangerous pollution levels for testing alerts.
    
    Args:
        container: Optional Streamlit container for output
    """
    target = container if container else st
    
    with target.expander("🧪 Test Alert System"):
        st.write("Use these controls to simulate dangerous pollution levels and test the alert system")
        
        enable_test = st.checkbox("Enable Test Mode", value=False)
        
        if enable_test:
            st.warning("⚠️ Test mode is active - simulated values will be used instead of real data")
            
            test_pollutant = st.selectbox(
                "Select pollutant to simulate", 
                ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10"]
            )
            
            # Get the threshold for the selected pollutant
            threshold = HAZARD_THRESHOLDS.get(test_pollutant, 100)
            
            # Set a default value slightly above the threshold
            default_value = threshold * 1.5
            
            test_value = st.slider(
                f"Simulated value for {test_pollutant} (threshold: {threshold})",
                0.0, threshold * 3.0, default_value, 0.1
            )
            
            # Store test settings in session state
            if st.button("Apply Test Values"):
                st.session_state.test_mode = True
                st.session_state.test_pollutant = test_pollutant
                st.session_state.test_value = test_value
                st.success(f"Test mode activated for {test_pollutant} with value {test_value}")
                st.info("The simulated dangerous levels will appear when you return to the dashboard")
        else:
            # Disable test mode if checkbox is unchecked
            if st.session_state.get('test_mode', False):
                if st.button("Disable Test Mode"):
                    st.session_state.test_mode = False
                    st.success("Test mode disabled - returning to real data")

def apply_test_values(pollutants):
    """
    Applies test values to the pollutant data if test mode is enabled.
    
    Args:
        pollutants: Dictionary of real pollutant values
        
    Returns:
        Modified dictionary with test values if test mode is enabled,
        otherwise returns the original dictionary
    """
    if st.session_state.get('test_mode', False):
        # Make a copy to avoid modifying the original
        modified = pollutants.copy()
        
        # Apply the test value to the selected pollutant
        pollutant = st.session_state.get('test_pollutant')
        value = st.session_state.get('test_value')
        
        if pollutant and pollutant in modified:
            modified[pollutant] = value
            
        return modified
    
    return pollutants