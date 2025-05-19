# app.py - Главный файл приложения

import streamlit as st
from datetime import datetime
import time

# Импортируем модули
from config import (
    initialize_session_state, 
    ROLES, PASSWORD, MAX_LOGIN_ATTEMPTS, 
    DEFAULT_REFRESH_INTERVAL
)
from data_service import fetch_weather, fetch_pollution_current, fetch_pollution_history
from streaming import start_streaming_data, stop_streaming_data
from ui import render_header, render_weather_cards, render_pollutant_cards, render_trends
from forecasting import render_forecast
from ai_reporting import render_ai_insights
from auth import show_login

# Безопасный перезапуск Streamlit
try:
    from streamlit import experimental_rerun
except ImportError:
    def experimental_rerun():
        st.stop()

def render_sidebar():
    """Отображение боковой панели с навигацией и настройками"""
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to", ["Dashboard", "Forecast", "AI Insights"])
        st.markdown("---")
        st.header("Settings & Logout")
        st.info(f"Logged in as: {st.session_state.role}")
        if st.button("Logout"):
            # Stop any streaming that might be happening
            stop_streaming_data()
            for k in ["logged_in","role","login_attempts","streaming_active"]:
                st.session_state.pop(k, None)
            experimental_rerun()
        st.markdown("---")
        
        # Auto-refresh options
        stream_mode = st.radio(
            "Data Update Mode",
            ["Manual", "Real-time Streaming", "Page Refresh"],
            index=0
        )
        
        interval = st.slider("Update Interval (s)", 5, 600, DEFAULT_REFRESH_INTERVAL, 5)
        
        if stream_mode == "Page Refresh" and st.button("Manual Refresh Now"):
            experimental_rerun()
            
    return page, stream_mode, interval



def render_dashboard():
    """Отображение основной страницы мониторинга"""
    from config import FACILITIES_COORD
    from ui import render_weather_cards, render_pollutant_cards, render_trends
    from ui import check_pollutant_alerts, display_alert_modal
    from ui import add_test_controls, apply_test_values
    
    # Initialize test mode in session state if not present
    if 'test_mode' not in st.session_state:
        st.session_state.test_mode = False
    
    facility = st.selectbox("Select Facility", list(FACILITIES_COORD.keys()))
    st.session_state.selected_facility = facility
    lat, lon = FACILITIES_COORD[facility]
    st.subheader(f"📍 {facility}")
    
    # Create containers for live-updating data
    weather_container = st.container()
    pollutant_container = st.container()
    trends_container = st.container()
    alert_container = st.container()  # New container for alerts
    test_container = st.container()   # Container for test controls
    
    # Add testing controls
    with test_container:
        add_test_controls()
    
    # Get initial data
    try:
        weather = fetch_weather(lat, lon)
        current = fetch_pollution_current(lat, lon)
        
        # Apply test values if test mode is enabled
        current = apply_test_values(current)
        
    except Exception as e:
        st.error(f"Fetch error: {e}")
        return
    
    # Check for dangerous levels and display alert if needed
    with alert_container:
        exceedances = check_pollutant_alerts(current)
        if exceedances:
            display_alert_modal(exceedances, facility)
    
    # Render initial data
    render_weather_cards(weather, weather_container)
    render_pollutant_cards(current, pollutant_container)
    render_trends(lat, lon, container=trends_container)
    
    return lat, lon, weather_container, pollutant_container, alert_container

def render_streaming_dashboard(lat, lon, interval, weather_container, pollutant_container, alert_container):
    """Отображает панель мониторинга с обновлением в реальном времени"""
    from ui import check_pollutant_alerts, display_alert_modal
    from ui import apply_test_values
    
    # Start the streaming data
    start_streaming_data(lat, lon, interval)
    
    # Create a placeholder for last update time
    last_update = st.empty()
    
    # Start the streaming UI update loop
    streaming_status = st.empty()
    streaming_status.info("Real-time data streaming active. Data updates every " + 
                         f"{interval} seconds without page refresh.")
    
    # Create a stop button
    if st.button("Stop Real-time Updates"):
        stop_streaming_data()
        streaming_status.warning("Real-time updates stopped.")
        st.experimental_rerun()
    
    # This will run in the main thread and continuously check for new data
    counter = 0
    placeholder = st.empty()
    
    while st.session_state.streaming_active:
        try:
            # Check if there's new data in the queue
            if not st.session_state.stream_data_queue.empty():
                data = st.session_state.stream_data_queue.get()
                weather = data["weather"]
                pollution = data["pollution"]
                timestamp = data["timestamp"]
                
                # Apply test values if test mode is enabled
                pollution = apply_test_values(pollution)
                
                # Update the displayed data
                with weather_container:
                    render_weather_cards(weather)
                
                with pollutant_container:
                    render_pollutant_cards(pollution)
                
                # Check for alerts with every data update
                with alert_container:
                    exceedances = check_pollutant_alerts(pollution)
                    if exceedances:
                        display_alert_modal(exceedances, st.session_state.selected_facility)
                
                # Update the timestamp
                last_update.caption(f"Last updated: {timestamp:%Y-%m-%d %H:%M:%S} UTC")
                
                # Show a pulsing indicator during updates
                counter += 1
                animation = ["⏳", "⌛", "⏳", "⌛"][counter % 4]
                placeholder.text(f"{animation} Live data streaming active...")
            
            # Short sleep to prevent UI freezing
            time.sleep(0.1)
        except Exception as e:
            st.error(f"Error updating streaming data: {e}")
            time.sleep(5)

def main():
    """Основная функция приложения"""
    st.set_page_config(page_title="Industry Air Quality", layout="wide")
    
    # Инициализируем состояние сессии
    initialize_session_state()
    
    if not st.session_state.logged_in:
        show_login()
        return

    page, stream_mode, interval = render_sidebar()
    render_header() 

    if page == 'Dashboard':
        # Обновлено: теперь функция возвращает контейнер для алертов
        lat, lon, weather_container, pollutant_container, alert_container = render_dashboard()
        
        # Handle different update modes
        if stream_mode == "Real-time Streaming":
            # Обновлено: передаем контейнер для алертов
            render_streaming_dashboard(lat, lon, interval, weather_container, pollutant_container, alert_container)
        elif stream_mode == "Page Refresh":
            # Stop any existing streaming
            stop_streaming_data()
            time.sleep(interval)
            experimental_rerun()
        else:  # Manual mode
            # Stop any existing streaming
            stop_streaming_data()
            
    elif page == 'Forecast':
        # Stop any streaming that might be happening when we leave the dashboard
        stop_streaming_data()
        render_forecast()
    else:
        # Stop any streaming that might be happening when we leave the dashboard
        stop_streaming_data()
        render_ai_insights()


if __name__ == '__main__':
    main()

