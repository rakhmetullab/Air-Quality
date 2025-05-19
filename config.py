# config.py - Настройки и конфигурация приложения

import streamlit as st
import queue
from typing import Dict, Tuple, List, Any

# === API KEYS ===
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")

# === COORDINATES AND SETTINGS ===
FACILITIES_COORD: Dict[str, Tuple[float, float]] = {
    "Refinery A": (51.1414, 71.4861),
    "Compressor Station B": (47.1001, 51.9265),
    "Gas Terminal C": (42.8820, 74.5827),
    "Storage Site D": (43.2220, 76.8512)
}

POLLUTANTS: List[str] = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10"]

HAZARD_THRESHOLDS: Dict[str, int] = {
    'co': 10000, 'no': 200, 'no2': 200, 'o3': 100, 'so2': 20, 'pm2_5': 25, 'pm10': 50
}

# === USER ROLES AND AUTHENTICATION ===
ROLES: List[str] = ["Admin", "Engineer", "Safety", "Viewer"]
PASSWORD: str = "123"
MAX_LOGIN_ATTEMPTS: int = 3

# === APP SETTINGS ===
DEFAULT_REFRESH_INTERVAL: int = 120
HISTORY_HOURS: int = 24
FORECAST_HOURS: int = 24
MODEL_HISTORY_HOURS: int = 168

# === COLOR AND VISUALIZATION SETTINGS ===
POLLUTANT_COLORS: Dict[str, str] = {
    "co": "rgba(102,197,207,0.8)",
    "no": "rgba(197,90,17,0.8)",
    "no2": "rgba(30,144,255,0.8)",
    "o3": "rgba(255,165,0,0.8)",
    "so2": "rgba(105,105,105,0.8)",
    "pm2_5": "rgba(0,128,0,0.8)",
    "pm10": "rgba(128,0,128,0.8)"
}

# === SESSION STATE INITIALIZATION ===
def initialize_session_state() -> None:
    """Инициализирует переменные состояния сессии Streamlit"""
    default_states = {
        "logged_in": False,
        "login_error": False,
        "role": None,
        "login_attempts": 0,
        "streaming_active": False,
        "stream_data_queue": queue.Queue(),
        "selected_facility": None
    }
    
    for key, default in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default