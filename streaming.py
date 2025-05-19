# streaming.py - Функционал потокового обновления данных

import streamlit as st
import threading
import time
from datetime import datetime
from data_service import fetch_weather, fetch_pollution_current

def fetch_data_for_streaming(lat: float, lon: float, interval: int) -> None:
    """
    Фоновая функция для периодического получения данных и их помещения в очередь.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        interval: Интервал обновления в секундах
    """
    while st.session_state.streaming_active:
        try:
            weather = fetch_weather(lat, lon)
            pollution = fetch_pollution_current(lat, lon)
            timestamp = datetime.utcnow()
            
            # Put the new data in the queue
            st.session_state.stream_data_queue.put({
                "weather": weather,
                "pollution": pollution,
                "timestamp": timestamp
            })
            
            # Sleep for the specified interval
            time.sleep(interval)
        except Exception as e:
            print(f"Error in data streaming thread: {e}")
            time.sleep(5)  # Retry after a short delay

def start_streaming_data(lat: float, lon: float, interval: int) -> bool:
    """
    Запуск фонового потока для регулярного получения данных.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        interval: Интервал обновления в секундах
        
    Returns:
        True при успешном запуске потока, иначе False
    """
    if not st.session_state.streaming_active:
        st.session_state.streaming_active = True
        # Clear any existing data in the queue
        while not st.session_state.stream_data_queue.empty():
            st.session_state.stream_data_queue.get()
        
        # Start the background thread
        thread = threading.Thread(
            target=fetch_data_for_streaming,
            args=(lat, lon, interval),
            daemon=True
        )
        thread.start()
        return True
    return False

def stop_streaming_data() -> None:
    """Остановка фонового потока обновления данных."""
    st.session_state.streaming_active = False