# data_service.py - Сервис для получения данных API

import requests
import pandas as pd
from datetime import datetime
import streamlit as st
from typing import Dict, Any, List
from config import API_KEY

@st.cache_data(ttl=600)
def fetch_pollution_current(lat: float, lon: float) -> Dict[str, float]:
    """
    Получает текущие данные о загрязнении воздуха.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        
    Returns:
        Словарь с данными о загрязнителях
    """
    if not API_KEY:
        st.error("OpenWeather API key is missing. Please set it in .streamlit/secrets.toml")
        return {}
        
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": API_KEY}
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    data = r.json().get("list", [])
    return data[0].get("components", {}) if data else {}

@st.cache_data(ttl=600)
def fetch_pollution_history(lat: float, lon: float, hours: int) -> pd.DataFrame:
    """
    Получает исторические данные о загрязнении воздуха.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        hours: Количество часов истории для получения
        
    Returns:
        DataFrame с историческими данными
    """
    if not API_KEY:
        st.error("OpenWeather API key is missing. Please set it in .streamlit/secrets.toml")
        return pd.DataFrame()
        
    end = int(datetime.utcnow().timestamp())
    start = end - hours * 3600
    url = "http://api.openweathermap.org/data/2.5/air_pollution/history"
    params = {"lat": lat, "lon": lon, "start": start, "end": end, "appid": API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    recs = []
    for ent in r.json().get("list", []):
        dt = datetime.utcfromtimestamp(ent.get("dt", 0))
        for pol, val in ent.get("components", {}).items():
            recs.append({"datetime": dt, "pollutant": pol, "value": val})
    df = pd.DataFrame(recs)
    if not df.empty:
        df = df.set_index('datetime').sort_index()
    return df

@st.cache_data(ttl=300)
def fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    """
    Получает текущие данные о погоде.
    
    Args:
        lat: Широта местоположения
        lon: Долгота местоположения
        
    Returns:
        Словарь с данными о погоде
    """
    if not API_KEY:
        st.error("OpenWeather API key is missing. Please set it in .streamlit/secrets.toml")
        return {}
        
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "units": "metric", "appid": API_KEY}
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json()

def pollutant_info(key: str) -> tuple:
    """
    Возвращает информацию о загрязнителе по его ключу.
    
    Args:
        key: Код загрязнителя
        
    Returns:
        Кортеж (название для отображения, цвет)
    """
    mapping = {"co": ("CO", "rgba(102,197,207,0.8)"),
               "no": ("NO", "rgba(197,90,17,0.8)"),
               "no2": ("NO₂", "rgba(30,144,255,0.8)"),
               "o3": ("O₃", "rgba(255,165,0,0.8)"),
               "so2": ("SO₂", "rgba(105,105,105,0.8)"),
               "pm2_5": ("PM₂.₅", "rgba(0,128,0,0.8)"),
               "pm10": ("PM₁₀", "rgba(128,0,128,0.8)")}
    return mapping.get(key, (key.upper(), "rgba(150,150,150,0.8)"))

def get_pollutant_name_safe(key: str) -> str:
    """
    Возвращает безопасную для Unicode версию названия загрязнителя.
    
    Args:
        key: Код загрязнителя
        
    Returns:
        Безопасное название загрязнителя
    """
    mapping = {"co": "CO", 
               "no": "NO",
               "no2": "NO2",
               "o3": "O3",
               "so2": "SO2",
               "pm2_5": "PM2.5",
               "pm10": "PM10"}
    return mapping.get(key, key.upper())